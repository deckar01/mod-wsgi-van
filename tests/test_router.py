import sys
import threading
from typing import Generator

import pytest
import pytest_mock

from mod_wsgi_van import Router, Environ


def flush(gen: Generator):
    return "".join(gen)


@pytest.fixture
def base_environ():
    yield {"mod_wsgi.script_name": "test"}


@pytest.fixture
def aries(base_environ: Environ):
    yield {**base_environ, "HTTP_HOST": "aries"}


@pytest.fixture
def taurus(base_environ: Environ):
    yield {**base_environ, "HTTP_HOST": "taurus"}


@pytest.fixture
def virgo(base_environ: Environ):
    yield {**base_environ, "HTTP_HOST": "virgo"}


@pytest.fixture
def router():
    router = Router(base_path="tests/fixtures")
    yield router
    router.shutdown()


@pytest.fixture
def hot_router():
    router = Router(base_path="tests/fixtures", update_interval=0)
    yield router
    router.shutdown()


def test_isolation(router: Router, aries: Environ):
    assert flush(router.application(aries, None)) == "aries test"
    assert "dep" not in sys.modules


def test_runtime_isolation(router: Router, taurus: Environ):
    assert flush(router.application(taurus, None)) == "taurus delta"
    assert "dep" not in sys.modules


def test_venv_isolation(router: Router, virgo: Environ):
    assert flush(router.application(virgo, None)) == "virgo true"
    assert "dep" not in sys.modules


def test_vhost_isolation(router: Router, aries: Environ, taurus: Environ):
    assert flush(router.application(aries, None)) == "aries test"
    assert flush(router.application(taurus, None)) == "taurus delta"
    assert flush(router.application(aries, None)) == "aries test"
    assert flush(router.application(taurus, None)) == "taurus delta"


def test_reload(hot_router: Router, aries: Environ, mocker: pytest_mock.MockerFixture):
    mock_version = mocker.Mock(return_value=1)
    mocker.patch.object(hot_router, "get_version", mock_version)

    server = hot_router.get_server(aries)
    reloaded = threading.Event()
    load_spy = mocker.spy(server, "load")
    load_spy.side_effect = reloaded.set

    mock_version.return_value = 2

    assert reloaded.wait(1)
    assert server.version == 2


def test_delete(hot_router: Router, aries: Environ, mocker: pytest_mock.MockerFixture):
    mock_version = mocker.Mock()
    mocker.patch.object(hot_router, "get_version", mock_version)
    hot_router.get_server(aries)

    assert "aries" in hot_router.servers

    mock_version.side_effect = Exception("Deleted")
    looped = threading.Event()
    loop_spy = mocker.spy(hot_router.stop_watcher, "wait")
    loop_spy.side_effect = lambda _: looped.set()

    assert looped.wait(1)
    assert "aries" not in hot_router.servers


def test_break(hot_router: Router, aries: Environ, mocker: pytest_mock.MockerFixture):
    mock_version = mocker.Mock()
    mocker.patch.object(hot_router, "get_version", mock_version)
    hot_router.get_server(aries)

    assert "aries" in hot_router.servers

    mock_version.side_effect = Exception("Broken")
    looped = threading.Event()
    loop_spy = mocker.spy(hot_router.stop_watcher, "wait")
    loop_spy.side_effect = lambda _: looped.set()

    assert looped.wait(1)
    assert "aries" not in hot_router.servers
