import atexit
import dataclasses
import pathlib
import threading
import time

from .server import Server, Environ, StartResponse


@dataclasses.dataclass
class Router:
    base_path: str = "/var/www"
    venv_name: str = ".venv"
    wsgi_dir: str = "wsgi"
    module_name: str = "app"
    object_name: str = "app"
    update_interval: float = 1.0

    def __post_init__(self) -> None:
        self.servers: dict[str, Server] = {}
        self.stop = threading.Event()
        watcher = threading.Thread(target=self.poll_server_paths, daemon=True)
        watcher.start()
        atexit.register(self.stop.set)
        atexit.register(watcher.join)

    def poll_server_paths(self):
        # Update servers when their path changes
        while not self.stop.wait(self.update_interval):
            for server in list(self.servers.values()):
                try:
                    # Reload modules after a build
                    server.update()

                except FileNotFoundError:
                    # Purge deleted servers
                    server.log(f"Closing {server.host_name}")
                    del self.servers[server.host_name]

                except Exception:
                    # Purge broken servers
                    server.log(f"Closing {server.host_name}")
                    del self.servers[server.host_name]
                    raise

    def get_server_path(self, host_name: str) -> pathlib.Path:
        return pathlib.Path(self.base_path, host_name)

    def get_venv_paths(self, path: pathlib.Path) -> list[pathlib.Path]:
        venv_path = path / self.venv_name
        return list(venv_path.glob("lib/python*/site-packages"))

    def get_server(self, environ: Environ) -> Server:
        host_name = environ["HTTP_HOST"]

        # Lazy load and cache WSGI servers on request
        if host_name not in self.servers:
            path = self.get_server_path(host_name)
            server = Server(
                host_name=host_name,
                script_name=environ["mod_wsgi.script_name"],
                path=path,
                venv_paths=self.get_venv_paths(path),
                wsgi_dir=self.wsgi_dir,
                module_name=self.module_name,
                object_name=self.object_name,
            )
            server.load()
            self.servers[host_name] = server

        return self.servers[host_name]

    def application(self, environ: Environ, start_response: StartResponse):
        start_time = time.perf_counter()
        server = self.get_server(environ)
        with server.time("serve", start_time):
            # Drain the generator to time the response
            yield from server.serve(environ, start_response)
