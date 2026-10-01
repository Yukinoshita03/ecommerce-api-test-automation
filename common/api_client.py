import logging
from time import perf_counter

import allure
import requests

from common.allure_reporting import attach_json, attach_response
from common.sendrequest import send_request_session


logger = logging.getLogger(__name__)


class ApiClient:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def request(self, method, path, **kwargs):
        method = method.upper()
        url = f"{self.base_url}/{path.lstrip('/')}"
        # 日志和步骤只展示路径，不展示可能包含凭据的查询字符串。
        report_path = path.split("?", 1)[0]
        logger.info("发送请求：method=%s path=%s", method, report_path)

        with allure.step(f"发送 {method} {report_path}"):
            request_info = {
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
            }
            attach_json("接口请求", request_info)

            # 只测量实际请求调用的耗时，不包含报告附件写入时间。
            started_at = perf_counter()
            try:
                response = send_request_session(method, url, self.session, **kwargs)
            except requests.RequestException as error:
                elapsed_ms = (perf_counter() - started_at) * 1000
                logger.error(
                    "请求异常：method=%s path=%s type=%s elapsed_ms=%.2f",
                    method,
                    report_path,
                    type(error).__name__,
                    elapsed_ms,
                )
                attach_json("请求异常", {"type": type(error).__name__})
                raise

            elapsed_ms = (perf_counter() - started_at) * 1000
            logger.info(
                "请求完成：method=%s path=%s status=%s elapsed_ms=%.2f",
                method,
                report_path,
                response.status_code,
                elapsed_ms,
            )
            attach_response(response)
            return response

    def close(self):
        self.session.close()
