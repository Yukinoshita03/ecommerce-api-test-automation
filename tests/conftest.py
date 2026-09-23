import os

import pytest

from common.api_client import ApiClient


@pytest.fixture
def base_url():
    return os.getenv("TEST_BASE_URL", "http://localhost:8000")


@pytest.fixture
def api_client(base_url):
    return ApiClient(base_url)
