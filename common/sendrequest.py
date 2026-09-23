import requests


def send_request(method, url, **kwargs):
    response = requests.request(
        method,
        url,
        timeout=5,
        **kwargs,
    )
    return response


if __name__ == "__main__":
    response = send_request("GET", "http://localhost:8000/products")
    print(response.json())
