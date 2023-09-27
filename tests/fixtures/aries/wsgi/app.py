import dep


def app(environ, start_response):
    start_response("200 OK", [])
    yield f"aries {dep.value}"
