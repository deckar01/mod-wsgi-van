import dep


def app(environ, start_response):
    yield f"aries {dep.value}"
