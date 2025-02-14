import typing
import unittest

import fastapi
import fastapi.testclient

import inngest
import inngest.fast_api
from tests import base, dev_server, http_proxy

from . import cases

_framework = "fast_api"
_app_id = f"{_framework}-functions"

_client = inngest.Inngest(
    api_base_url=dev_server.origin,
    app_id=_app_id,
    event_api_base_url=dev_server.origin,
    is_production=False,
)

_cases = cases.create_async_cases(_client, _framework)
_fns: list[inngest.Function] = []
for case in _cases:
    if isinstance(case.fn, list):
        _fns.extend(case.fn)
    else:
        _fns.append(case.fn)


class TestFunctions(unittest.TestCase):
    app: fastapi.FastAPI
    client: inngest.Inngest
    dev_server_port: int
    fast_api_client: fastapi.testclient.TestClient
    proxy: http_proxy.Proxy

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.app = fastapi.FastAPI()
        cls.client = _client

        inngest.fast_api.serve(
            cls.app,
            cls.client,
            _fns,
        )
        cls.fast_api_client = fastapi.testclient.TestClient(cls.app)
        cls.proxy = http_proxy.Proxy(cls.on_proxy_request).start()
        base.register(cls.proxy.port)

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        cls.proxy.stop()

    @classmethod
    def on_proxy_request(
        cls,
        *,
        body: typing.Optional[bytes],
        headers: dict[str, list[str]],
        method: str,
        path: str,
    ) -> http_proxy.Response:
        return http_proxy.on_proxy_fast_api_request(
            cls.fast_api_client,
            body=body,
            headers=headers,
            method=method,
            path=path,
        )


for case in _cases:
    test_name = f"test_{case.name}"
    setattr(TestFunctions, test_name, case.run_test)


if __name__ == "__main__":
    unittest.main()
