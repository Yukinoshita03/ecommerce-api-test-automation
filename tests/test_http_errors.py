import allure
import pytest
import requests


@allure.feature('HTTP 异常')
@allure.title('404 响应主动抛出 HTTPError')
def test_raise_for_status_on_404(api_client):
    with allure.step("执行场景并检查预期结果"):
        response = api_client.request("GET", "/products/999999")

        assert response.status_code == 404

        with pytest.raises(requests.exceptions.HTTPError):
            response.raise_for_status()
