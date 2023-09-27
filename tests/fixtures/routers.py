import pytest
import threading
from pytest_mock import MockerFixture

from mod_wsgi_van import Router, Environ


class TestRouter(Router):
    mocker: MockerFixture

    def __add__(self, environ: Environ) -> str:
        return "".join(self.application(environ, lambda *_: None))

    def mock_version(self):
        mock_version = self.mocker.Mock(return_value=1)
        self.mocker.patch.object(self, "get_version", mock_version)
        return mock_version

    def spy_on_server(self, environ: Environ, call: str):
        server = self.get_server(environ)
        spy = self.mocker.spy(server, call)
        return server, spy

    def assert_updated(self):
        poll = threading.Event()
        loop_spy = self.mocker.spy(self.stop_watcher, "wait")

        # Wait for changes to be observed
        loop_spy.side_effect = lambda _: poll.set()
        assert poll.wait(1)

        # Wait for changes to be processed
        poll.clear()
        assert poll.wait(1)


@pytest.fixture
def router():
    router = TestRouter(base_path="tests/fixtures")
    yield router
    router.shutdown()


@pytest.fixture
def hot_router():
    router = TestRouter(base_path="tests/fixtures", update_interval=1e-6)
    yield router
    router.shutdown()
