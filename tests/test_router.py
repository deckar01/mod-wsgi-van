import sys

from pytest_mock import MockerFixture

from .fixtures.routers import Environ, TestRouter as Router


def test_isolation(router: Router, aries: Environ):
    assert router + aries == "aries test"
    assert "dep" not in sys.modules


def test_runtime_isolation(router: Router, taurus: Environ):
    assert router + taurus == "taurus delta"
    assert "dep" not in sys.modules


def test_venv_isolation(router: Router, virgo: Environ):
    assert router + virgo == "virgo true"
    assert "dep" not in sys.modules


def test_vhost_isolation(router: Router, aries: Environ, taurus: Environ):
    assert router + aries == "aries test"
    assert router + taurus == "taurus delta"
    assert router + aries == "aries test"
    assert router + taurus == "taurus delta"


def test_reload(hot_router: Router, aries: Environ, mocker: MockerFixture):
    hot_router.mocker = mocker
    version = hot_router.mock_version()
    server, load = hot_router.spy_on_server(aries, "load")

    version.return_value = 2

    hot_router.assert_updated()
    load.assert_called()
    assert server.version == 2


def test_delete(hot_router: Router, aries: Environ, mocker: MockerFixture):
    hot_router.mocker = mocker
    version = hot_router.mock_version()
    hot_router.get_server(aries)

    assert "aries" in hot_router.servers

    version.side_effect = Exception("Deleted")

    hot_router.assert_updated()
    assert "aries" not in hot_router.servers


def test_break(hot_router: Router, aries: Environ, mocker: MockerFixture):
    hot_router.mocker = mocker
    version = hot_router.mock_version()
    hot_router.get_server(aries)

    assert "aries" in hot_router.servers

    version.side_effect = Exception("Broken")

    hot_router.assert_updated()
    assert "aries" not in hot_router.servers
