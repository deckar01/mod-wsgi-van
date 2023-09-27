import contextlib
import dataclasses
import importlib
import pathlib
import sys
import time
import types
import typing


Environ = dict[str, str]
Response = typing.Generator
StartResponse = typing.Callable
Handler = typing.Callable[[Environ, StartResponse], Response]


@dataclasses.dataclass
class Server:
    host_name: str
    script_name: str
    path: pathlib.Path
    venv_paths: list[pathlib.Path]
    wsgi_dir: str
    module_name: str
    object_name: str
    version: typing.Any

    import_cache: dict[str, types.ModuleType] = dataclasses.field(default_factory=dict)

    def load(self) -> None:
        # Load one module at a time since sys is global
        self.log("Loading")
        with self.time("load"), self.environment():
            self.module = importlib.import_module(self.module_name)
            self.handler: Handler = getattr(self.module, self.object_name)

    def update(self, version: typing.Any) -> None:
        if self.version != version:
            # Clear import cache and reload
            self.import_cache = {}
            self.load()
            self.version = version

    def serve(self, environ: Environ, start_response: typing.Callable) -> Response:
        with self.environment():
            yield from self.handler(environ, start_response)

    @contextlib.contextmanager
    def environment(self):
        # Load cached imports
        global_modules = set(sys.modules.keys())
        sys.modules.update(self.import_cache)

        # Prefix the import path with the server and venv
        for path in self.venv_paths:
            sys.path.insert(0, str(path))
        sys.path.insert(0, str(self.path / self.wsgi_dir))

        try:
            yield None
        finally:
            # Reset the path
            sys.path.pop(0)
            for _ in self.venv_paths:
                sys.path.pop(0)

            # Unload imports into a cache
            self.import_cache = {
                name: sys.modules.pop(name)
                for name in set(sys.modules.keys()) - global_modules
            }

    def log(self, message) -> None:
        print(f"(wsgi:{self.script_name}:{self.host_name}): {message}")

    @contextlib.contextmanager
    def time(self, event: str, start_time: float | None = None):
        start_time = start_time or time.perf_counter()

        try:
            yield None
        finally:
            end_time = time.perf_counter()
            timing = end_time - start_time
            self.log(f"[{timing:.3g} s] {event}")
