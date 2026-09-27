import requests


def send_request(method, url, **kwargs):
    """发送一次独立 HTTP 请求，不复用调用之间的 Session。"""
    kwargs.setdefault("timeout", 5)
    return requests.request(method, url, **kwargs)


def send_request_session(method, url, session, **kwargs):
    """通过传入的 Session 发送请求，以便复用连接和会话状态。"""
    kwargs.setdefault("timeout", 5)
    return session.request(method, url, **kwargs)

if __name__ == "__main__":
    response = send_request("GET", "http://localhost:8000/products")
    print(response.json())
