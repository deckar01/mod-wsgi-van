import sys
import threading

import pytest
import pytest_mock

from mod_wsgi_van import Router, Environ


def noop():
    pass


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
    assert next(router.application(aries, noop)) == "aries test"
    assert "dep" not in sys.modules


def test_runtime_isolation(router: Router, taurus: Environ):
    assert next(router.application(taurus, noop)) == "taurus delta"
    assert "dep" not in sys.modules


def test_venv_isolation(router: Router, virgo: Environ):
    assert next(router.application(virgo, noop)) == "virgo true"
    assert "dep" not in sys.modules


def test_vhost_isolation(router: Router, aries: Environ, taurus: Environ):
    assert next(router.application(aries, noop)) == "aries test"
    assert next(router.application(taurus, noop)) == "taurus delta"
    assert next(router.application(aries, noop)) == "aries test"
    assert next(router.application(taurus, noop)) == "taurus delta"


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
    hot_router.stop_watcher.wait(0.001)

    assert "aries" not in hot_router.servers


def test_break(hot_router: Router, aries: Environ, mocker: pytest_mock.MockerFixture):
    mock_version = mocker.Mock()
    mocker.patch.object(hot_router, "get_version", mock_version)
    hot_router.get_server(aries)

    assert "aries" in hot_router.servers

    mock_version.side_effect = Exception("Broken")
    hot_router.stop_watcher.wait(0.001)

    assert "aries" not in hot_router.servers
