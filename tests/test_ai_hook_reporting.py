import json
import os
from pathlib import Path
import subprocess
import sys

import allure
import pytest


@allure.feature("失败 Hook AI 分析")
@pytest.mark.parametrize("scenario", ["fake", "timeout", "invalid", "off"])
def test_hook_only_analyzes_failed_phases_and_preserves_cleanup(tmp_path, scenario):
    root = Path(__file__).resolve().parents[1]
    conftest = (root / "tests/conftest.py").read_text()
    conftest += '''
from common.ai.client import AIClientError, FakeAIClient, OpenAICompatibleClient

original_analyze = FakeAIClient.analyze

def stub_analyze(self, context):
    with open("model-inputs.jsonl", "a", encoding="utf-8") as file:
        file.write(json.dumps(context, ensure_ascii=False) + "\\n")
    if os.getenv("STUB_SCENARIO") == "timeout":
        raise AIClientError("模型请求失败：Timeout")
    if os.getenv("STUB_SCENARIO") == "invalid":
        return {"summary": 123}
    return original_analyze(self, context)

# 子进程专用替换，持续到 teardown 报告生成后，不随 fixture 清理恢复。
FakeAIClient.analyze = stub_analyze
OpenAICompatibleClient.from_env = classmethod(lambda cls: FakeAIClient())
'''
    (tmp_path / "conftest.py").write_text(conftest)
    (tmp_path / "test_demo.py").write_text('''
import logging
from pathlib import Path
import pytest
import requests
from common.api_client import ApiClient
from common.allure_reporting import attach_json

@pytest.fixture
def bad_setup():
    attach_json("接口响应", {"access_token": "fixture-secret"})
    raise ValueError("setup fixture-secret")

@pytest.fixture
def bad_teardown():
    yield
    Path("cleanup-completed").write_text("yes")
    raise ValueError("cleanup failed")

def test_setup(bad_setup):
    pass

@pytest.mark.analysis_context(request_execution="mocked", purpose="检查名称", expected_behavior="名称为 Keyboard")
def test_call(monkeypatch):
    client = ApiClient("http://example.test")
    response = requests.Response()
    response.status_code = 200
    response._content = b'{"name":"Mouse"}'
    monkeypatch.setattr(client.session, "request", lambda *a, **k: response)
    try:
        assert client.request("GET", "/products/1").json()["name"] == "Keyboard"
    finally:
        client.close()
        Path("client-cleanup-completed").write_text("yes")

def test_teardown(bad_teardown):
    pass

def test_expected_404(monkeypatch):
    client = ApiClient("http://example.test")
    response = requests.Response()
    response.status_code = 404
    response._content = b'{}'
    monkeypatch.setattr(client.session, "request", lambda *a, **k: response)
    try:
        assert client.request("GET", "/products/99999").status_code == 404
    finally:
        client.close()

def test_expected_timeout(monkeypatch):
    client = ApiClient("http://example.test")
    def fail(*a, **k): raise requests.Timeout("expected timeout")
    monkeypatch.setattr(client.session, "request", fail)
    try:
        with pytest.raises(requests.Timeout):
            client.request("GET", "/products")
    finally:
        client.close()

@pytest.mark.skip(reason="不应分析")
def test_skip():
    pass
''')
    environment = {**os.environ, "PYTHONPATH": str(root), "STUB_SCENARIO": scenario,
                   "AI_ANALYSIS_MODE": "real" if scenario in {"timeout", "invalid"} else scenario}
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "test_demo.py", "-q",
         "--failure-dir=failures", "--alluredir=allure"],
        cwd=tmp_path, env=environment, text=True, capture_output=True,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert "INTERNALERROR" not in result.stdout
    assert (tmp_path / "cleanup-completed").exists()
    assert (tmp_path / "client-cleanup-completed").exists()
    files = list((tmp_path / "failures").glob("*/*.json"))
    contexts = [json.loads(p.read_text()) for p in files if not p.name.endswith("-ai.json")]
    assert len(contexts) == 3
    assert {c["phase"] for c in contexts} == {"setup", "call", "teardown"}
    analyses = [json.loads(p.read_text()) for p in files if p.name.endswith("-ai.json")]
    if scenario == "off":
        assert analyses == []
        assert not (tmp_path / "model-inputs.jsonl").exists()
    else:
        assert len(analyses) == 3
        assert all(a["status"] == ("available" if scenario == "fake" else "unavailable") for a in analyses)
        inputs = [json.loads(line) for line in (tmp_path / "model-inputs.jsonl").read_text().splitlines()]
        assert len(inputs) == 3
        call = next(c for c in inputs if c["phase"] == "call")
        assert call["test_metadata"]["request_execution"] == "mocked"
        assert call["evidence"][1]["data"]["status_code"] == 200
        assert "fixture-secret" not in json.dumps(inputs)
        attachments = list((tmp_path / "allure").glob("*-attachment.json"))
        assert any('"source": "pytest_failure"' in p.read_text() for p in attachments)
