def app(environ, start_response):
    import dep

    yield f"taurus {dep.value}"
