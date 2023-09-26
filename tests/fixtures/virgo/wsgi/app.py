import dep


def app(environ, start_response):
    yield f"virgo {dep.value}"
