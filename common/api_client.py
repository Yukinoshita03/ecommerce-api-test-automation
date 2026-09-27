import requests

from common.sendrequest import send_request_session


class ApiClient:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def request(self, method, path, **kwargs):
        url = f"{self.base_url}/{path.lstrip('/')}"
        return send_request_session(method, url, self.session, **kwargs)

    def close(self):
        self.session.close()
