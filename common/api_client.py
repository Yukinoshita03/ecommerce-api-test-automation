from common.sendrequest import send_request


class ApiClient:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")

    def request(self, method, path, **kwargs):
        url = f"{self.base_url}/{path.lstrip('/')}"
        return send_request(method, url, **kwargs)
