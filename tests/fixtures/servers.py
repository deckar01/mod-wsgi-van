import pytest

from mod_wsgi_van.server import Environ


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
