## Tutorial

Suppose, you want to have an nginx configuration file template, `nginx.j2`:

```jinja2
server {
  listen 80;
  server_name {{ nginx.hostname }};

  root {{ nginx.webroot }};
  index index.htm;
}
```

And you have a JSON file with the data, `nginx.json`:

```json
{
    "nginx":{
        "hostname": "localhost",
        "webroot": "/var/www/project"
    }
}
```

This is how you render it into a working configuration file:

```bash
$ j2 -f json nginx.j2 nginx.json > nginx.conf
```

The output is saved to `nginx.conf`:

```
server {
  listen 80;
  server_name localhost;

  root /var/www/project;
  index index.htm;
}
```

Alternatively, you can use the `-o nginx.conf` option.

## Tutorial with environment variables

Suppose, you have a very simple template, `person.xml`:

```jinja2
<data><name>{{ name }}</name><age>{{ age }}</age></data>
```

What is the easiest way to use j2 here?
Use environment variables in your bash script:

```bash
$ export name=Andrew
$ export age=31
$ j2 /tmp/person.xml
<data><name>Andrew</name><age>31</age></data>
```

## Using environment variables

Even when you use yaml or json as the data source, you can always access environment variables
using the `env()` function:

```jinja2
Username: {{ login }}
Password: {{ env("APP_PASSWORD") }}
```


## Usage

Compile a template using INI-file data source:

    $ j2 config.j2 data.ini

Compile using JSON data source:

    $ j2 config.j2 data.json

Compile using YAML data source (requires PyYAML):

    $ j2 config.j2 data.yaml

Compile using JSON data on stdin:

    $ curl http://example.com/service.json | j2 --format=json config.j2

Compile using environment variables (hello Docker!):

    $ j2 config.j2

Or even read environment variables from a file:

    $ j2 --format=env config.j2 data.env

Or pipe it: (note that you'll have to use the "-" in this particular case):

    $ j2 --format=env config.j2 - < data.env

