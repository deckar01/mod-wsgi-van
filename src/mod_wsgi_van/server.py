import contextlib
import dataclasses
import importlib
import pathlib
import sys
import threading
import time
import typing


Environ = dict[str, str]
Response = typing.Generator
StartResponse = typing.Callable
Handler = typing.Callable[[Environ, StartResponse], Response]

IMPORT_LOCK = threading.Lock()
BASE_MODULES = set(sys.modules.keys())


@dataclasses.dataclass
class Server:
    host_name: str
    script_name: str
    path: pathlib.Path
    venv_paths: list[pathlib.Path]
    wsgi_dir: str
    module_name: str
    object_name: str

    def load(self) -> None:
        # Load one module at a time since sys is global
        with IMPORT_LOCK, self.time("load"):
            self.log(f"Loading {self.host_name}")
            self.hard_path = self.path.resolve(strict=True)

            # Prefix the import path with the server and venv
            for path in self.venv_paths:
                sys.path.insert(0, str(path))
            sys.path.insert(0, str(self.hard_path / self.wsgi_dir))

            # Isolate module imports between servers
            for name in set(sys.modules.keys()) - BASE_MODULES:
                del sys.modules[name]

            try:
                self.module = importlib.import_module(self.module_name)
                self.handler: Handler = getattr(self.module, self.object_name)
            finally:
                # Reset the path
                sys.path.pop(0)
                for _ in self.venv_paths:
                    sys.path.pop(0)

    def update(self) -> None:
        if self.path.resolve(strict=True) != self.hard_path:
            self.load()

    def serve(self, environ: Environ, start_response: typing.Callable) -> Response:
        return self.handler(environ, start_response)

    def log(self, message, timing=None) -> None:
        prefix = "" if timing is None else f"[{timing:.3g} s] "
        print(f"{prefix}(wsgi:{self.script_name}): {message}")

    @contextlib.contextmanager
    def time(self, event: str, start_time: float | None = None):
        start_time = start_time or time.perf_counter()
        try:
            yield None
        finally:
            end_time = time.perf_counter()
            timing = end_time - start_time
            self.log(f"[{timing:.3g} s] {event} {self.host_name}")
