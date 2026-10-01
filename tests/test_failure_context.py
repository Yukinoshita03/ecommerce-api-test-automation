import json
import os
from pathlib import Path
import subprocess
import sys

import allure


@allure.feature("失败上下文")
@allure.title("验证三个失败阶段、证据脱敏和测试间隔离")
def test_failure_context_end_to_end(tmp_path):
    root = Path(__file__).resolve().parents[1]
    (tmp_path / "conftest.py").write_text((root / "tests/conftest.py").read_text(), encoding="utf-8")
    (tmp_path / "test_demo.py").write_text('''
import logging
import pytest
from common.allure_reporting import attach_json

@pytest.fixture
def bad_setup():
    attach_json("接口响应", {"access_token": "fixture-secret"})
    raise ValueError("setup fixture-secret")

@pytest.fixture
def bad_teardown():
    yield
    attach_json("接口响应", {"password": "teardown-secret"})
    raise ValueError("teardown teardown-secret")

def test_setup(bad_setup):
    pass

def test_call(caplog):
    caplog.set_level(logging.INFO)
    attach_json("接口请求", {"method": "GET", "path": "/products/1"})
    attach_json("接口响应", {"status_code": 200, "name": "Mouse", "access_token": "call-secret"})
    logging.info("response call-secret")
    assert False, "call call-secret"

def test_teardown(bad_teardown):
    pass

def test_clean():
    assert False, "independent failure"
''', encoding="utf-8")
    environment = {**os.environ, "PYTHONPATH": str(root), "AI_ANALYSIS_MODE": "off"}
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(tmp_path / "test_demo.py"),
         "--failure-dir", str(tmp_path / "failures"),
         "--alluredir", str(tmp_path / "allure"), "-q"],
        cwd=tmp_path, env=environment, capture_output=True, text=True,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    files = list((tmp_path / "failures").glob("*/*.json"))
    assert len(files) == 4
    contexts = [json.loads(p.read_text()) for p in files]
    assert {c["phase"] for c in contexts} == {"setup", "call", "teardown"}
    serialized = json.dumps(contexts)
    for secret in ("fixture-secret", "call-secret", "teardown-secret"):
        assert secret not in serialized
    call = next(c for c in contexts if c["test_name"].endswith("::test_call"))
    assert call["exception_type"] == "AssertionError"
    assert "response ***" in call["logs"]
    assert call["evidence"][1]["data"]["access_token"] == "***"
    clean = next(c for c in contexts if c["test_name"].endswith("::test_clean"))
    assert clean["evidence"] == []
    attachments = list((tmp_path / "allure").glob("*-attachment.json"))
    assert any('"phase": "teardown"' in p.read_text() for p in attachments)
