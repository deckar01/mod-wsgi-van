# mod-wsgi-van 🚐

Dynamically route [mod_wsgi][0] to [mod_vhost_alias][1].

[0]: https://modwsgi.readthedocs.io/en/latest/
[1]: https://httpd.apache.org/docs/2.4/mod/mod_vhost_alias.html"

## Features

- Isolate virtual environments between vhosts
- Automatically reload deployed vhosts
- Automatically unload deleted vhosts

## Requirements

- Vhosts must be symlinks, which change on deploy.
- Apps must perform all `import`s and `sys.path` dependent operations during setup.

## Concerns

- Modules belonging to different vhosts are loaded into the same mod_wsgi process / thread by default.
- Built-in modules loaded by `mod_wsgi` remain shared between all apps in a process / thread.

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
mkdir -p /var/www/.builds/example.domain.org/1/static
mkdir -p /var/www/.builds/example.domain.org/1/wsgi
python -m venv /var/www/.builds/example.domain.org/1/.venv
/var/www/.builds/example.domain.org/1/.venv/bin/python -m pip install Flask
```

```py
# /var/www/.builds/example.domain.org/1/wsgi/app.py

from flask import Flask

app = Flask(__name__)
...
```

```sh
ln -sf /var/www/.builds/example.domain.org/1 /var/www/example.domain.org
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
