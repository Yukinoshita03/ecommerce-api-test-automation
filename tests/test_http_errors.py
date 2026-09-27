import pytest
import requests


def test_raise_for_status_on_404(api_client):
    response = api_client.request("GET", "/products/999999")

    assert response.status_code == 404

    with pytest.raises(requests.exceptions.HTTPError):
        response.raise_for_status()
