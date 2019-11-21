# Supported Formats

Following, we show how to use the different data file formats supported
bu j2cli to render an nginx configuration file template, `nginx.j2`:

```jinja2
server {
  listen 80;
  server_name {{ nginx.hostname }};

  root {{ nginx.webroot }};
  index index.htm;
}
```

## JSON

Data file contents:
```json
{
    "nginx":{
        "hostname": "localhost",
        "webroot": "/var/www/project",
        "logs": "/var/log/nginx/"
    }
}
```

Usage:

    $ j2 config.j2 data.json -o config
    $ j2 -f json config.j2 - < data.json > config


## YAML

Data file contents:
```yaml
nginx:
  hostname: localhost
  webroot: /var/www/project
  logs: /var/log/nginx
```

Usage:

    $ j2 config.j2 data.yaml -o config
    $ j2 -f yaml config.j2 - < data.yaml > config


## INI

Data file contents:
```ini
[nginx]
hostname=localhost
webroot=/var/www/project
logs=/var/log/nginx/
```

Usage:

    $ j2 config.j2 data.ini -o config
    $ j2 -f ini config.j2 - < data.ini > config


## env

### From file
Data file contents:
```sh
NGINX_HOSTNAME=localhost
NGINX_WEBROOT=/var/www/project
NGINX_LOGS=/var/log/nginx/
```

Usage:

    $ j2 config.j2 data.env -o config
    $ j2 -f env config.j2 - < data.env > config


### From shell environment variables
Render directly from the current environment variable values:

Usage:

    $ export NGINX_HOSTNAME=localhost NGINX_WEBROOT=/var/www/project NGINX_LOGS=/var/log/nginx/
    $ env | j2 -f env config.j2 - > config

