import allure
import requests

from common.allure_reporting import attach_json, attach_response
from common.sendrequest import send_request_session


class ApiClient:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def request(self, method, path, **kwargs):
        method = method.upper()
        url = f"{self.base_url}/{path.lstrip('/')}"
        # 日志和步骤只展示路径，不展示可能包含凭据的查询字符串。
        report_path = path.split("?", 1)[0]

        with allure.step(f"发送 {method} {report_path}"):
            attach_json(
                "接口请求",
                {
                    "method": method,
                    "path": report_path,
                    "params": kwargs.get("params"),
                    "json": kwargs.get("json"),
                    "data": (
                        kwargs.get("data")
                        if isinstance(kwargs.get("data"), dict)
                        else None
                    ),
                    "timeout": kwargs.get("timeout", 5),
                },
            )

            try:
                response = send_request_session(method, url, self.session, **kwargs)
            except requests.RequestException as error:
                attach_json("请求异常", {"type": type(error).__name__})
                raise

            attach_response(response)
            return response

    def close(self):
        self.session.close()
