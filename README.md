# mod-wsgi-van 🚐

Dynamically route [mod_wsgi][0] to [mod_vhost_alias][1].

[0]: https://modwsgi.readthedocs.io/en/latest/
[1]: https://httpd.apache.org/docs/2.4/mod/mod_vhost_alias.html"

## Features

- Isolate virtual environments between vhosts
- Automatically reload deployed vhosts
- Automatically unload deleted vhosts
- Symlinked vhost support

## Overview

The router checks the HTTP_HOST on request to decide which vhosts it should be routed to.
WSGI apps are lazy loaded. WSGI directories are monitored for mtime changes by default.
Symlinks are resolved on access to support deploys that symlink vhosts.

## Concerns

- Modules belonging to different vhosts are loaded into the same mod_wsgi process by default.
- Modules loaded outside of an app are shared between all apps in a process.

## Install

```sh
sudo -H python -m pip install mod-wsgi-van
```

## Example

```apacheconf
# /etc/apache2/sites-available/vhosts.conf

<VirtualHost *:80>
    UseCanonicalName Off
    ServerAlias *.domain.org
    VirtualDocumentRoot "/var/www/%0/static"

    WSGIDaemonProcess example
    WSGIProcessGroup example
    WSGIScriptAlias /example /var/wsgi/example.py
</VirtualHost>
```

```py
# /var/wsgi/example.py

from mod_wsgi_van import Router

application = Router().application
```

```sh
mkdir -p /var/www/example.domain.org/static
mkdir -p /var/www/example.domain.org/wsgi
python -m venv /var/www/example.domain.org/.venv
/var/www/example.domain.org/.venv/bin/python -m pip install Flask
```

```py
# /var/www/example.domain.org/wsgi/app.py

from flask import Flask

app = Flask(__name__)
...
```

## API

- `Router`
  - Attributes
    - `base_path: str = "/var/www"` - The location of the vhosts.
    - `venv_name: str = ".venv"` - The name of the virtual environment directory inside the vhost.
    - `wsgi_dir: str = "wsgi"` - The name of the WSGI directory inside the vhost.
    - `module_name: str = "app"` - The name of the module inside of the WSGI directory.
    - `object_name: str = "app"` - The name of the object inside of the module.
    - `update_interval: float = 1.0` - The interval for polling symlinks in seconds.
  - Methods
    - `get_server_path(host_name: str) -> pathlib.Path` - Override to change the vhost naming scheme.
    - `get_venv_paths(path: pathlib.Path) -> list[pathlib.Path]` - Override to change the venv site packages locations.
    - `get_version(server: Server) -> Any` - Override to customize the change detection strategy.
