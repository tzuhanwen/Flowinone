from typing import Any, TypeAlias
import traceback
import requests

Data: TypeAlias = Any


class EagleApi:
    def __init__(self, port: int = 41595, raise_on_error: bool = False) -> None:
        self.port = port
        self.api_prefix = f"http://localhost:{port}/api/"
        self.raise_on_error = raise_on_error    

    def _send_request(
        self, endpoint: str, method: str = "GET", payload: dict | None = None
    ) -> Data:
        url = self.api_prefix + endpoint

        if method == "GET":
            response = requests.get(url, params=payload)
        elif method == "POST":
            response = requests.post(url, json=payload)

        if response.ok:
            data = response.json().get("data")
            return data

        response.raise_for_status()

    def request(
        self, endpoint: str, method: str = "GET", payload: dict | None = None, raise_on_error: bool | None = False
    ) -> Data:
        if raise_on_error is None:
            raise_on_error = self.raise_on_error

        try:
            return self._send_request(endpoint, method, payload)
        except requests.RequestException as e:
            if raise_on_error:
                raise RuntimeError(
                    f"Failed to fetch from Eagle, endpoint: {endpoint}"
                ) from e
            else:
                traceback.print_exc()
                print(f"Failed to fetch from Eagle, endpoint: {endpoint}")
                return None