import asyncio
import dataclasses
import json
import typing
import unittest

import inngest
import inngest.flask
from inngest._internal import const, errors
from tests import http_proxy


class TestSend(unittest.TestCase):
    def test_send_event_to_cloud_branch_env(self) -> None:
        """
        Test that the SDK correctly syncs itself with Cloud.

        We need to use a mock Cloud since the Dev Server doesn't have a mode
        that simulates Cloud.
        """

        @dataclasses.dataclass
        class State:
            headers: dict[str, list[str]]
            path: str

        state = State(headers={}, path="")

        def on_request(
            *,
            body: typing.Optional[bytes],
            headers: dict[str, list[str]],
            method: str,
            path: str,
        ) -> http_proxy.Response:
            state.path = path

            for k, v in headers.items():
                state.headers[k] = v

            return http_proxy.Response(
                body=json.dumps({"ids": ["abc123"]}).encode("utf-8"),
                headers={},
                status_code=200,
            )

        mock_cloud = http_proxy.Proxy(on_request).start()
        self.addCleanup(mock_cloud.stop)

        event_key = "event-key-123abc"
        client = inngest.Inngest(
            event_api_base_url=f"http://localhost:{mock_cloud.port}",
            app_id="my-app",
            env="my-env",
            event_key=event_key,
        )

        client.send_sync(inngest.Event(name="foo"))
        assert state.headers.get("X-Inngest-Env") == ["my-env"]
        assert state.headers.get("X-Inngest-SDK") == [
            f"inngest-py:v{const.VERSION}"
        ]
        assert event_key in state.path

    async def test_many_parallel_sends(self) -> None:
        """
        Ensure the client can run many sends in parallel
        """

        class_name = self.__class__.__name__
        method_name = self._testMethodName
        client = inngest.Inngest(
            app_id=f"{class_name}-{method_name}",
            is_production=False,
        )

        sends = []
        for _ in range(1000):
            sends.append(
                client.send(inngest.Event(name=f"{class_name}-{method_name}"))
            )

        await asyncio.gather(*sends)

    def test_cloud_mode_without_event_key(self) -> None:
        client = inngest.Inngest(app_id="my-app")

        with self.assertRaises(errors.EventKeyUnspecifiedError):
            client.send_sync(inngest.Event(name="foo"))


if __name__ == "__main__":
    unittest.main()
