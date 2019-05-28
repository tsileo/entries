import binascii
import os
import pkg_resources
import urllib
import tempfile
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

import click
import mf2py
import requests
import yaml

VERSION = pkg_resources.get_distribution("entries").version

CLIENT_ID = "https://hexa.ninja/5ce9a178def3b70a/entries-cli"
REDIRECT_URI = "http://localhost:7881/"


class IndieAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTPServer handler for intercepting the IndieAuth callback."""

    def __init__(self, request, address, server, me, token_endpoint):
        self.me = me
        self.token_endpoint = token_endpoint
        super().__init__(request, address, server)

    def log_message(self, format, *args):
        return

    def do_GET(self):
        data = urllib.parse.parse_qs(self.path[2:])
        # data contains
        # - code
        # - state
        # - me
        tok = requests.post(
            self.token_endpoint,
            data={
                "grant_type": "authorization_code",
                "code": data["code"][0],
                "client_id": CLIENT_ID,
                "redirect_uri": REDIRECT_URI,
                "me": self.me,
            },
            headers={"Accept": "application/json"},
        )
        tok.raise_for_status()

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(
            b'<body style="background:#111;color:#ddd"><h1>Done, you can close this tab now.</h1></body>'
        )

        self.server.access_token = tok.json()["access_token"]


def _wait_for_access_token(me, tok_endpoint):
    """Spawn a HTTPServer and wait for the IndieAuth callback to get executed."""
    server = HTTPServer(
        ("localhost", 7881),
        lambda request, address, server: IndieAuthCallbackHandler(
            request, address, server, me, tok_endpoint
        ),
    )
    server.handle_request()
    return server.access_token


def get_access_token(u, scopes):
    """Initiate an IndieAuth Authorization flow to get an acess token (for talking to the Miropub endpoint)."""
    # Guess the identity from the URL
    me = urllib.parse.urlparse(u)._replace(path="/").geturl()

    # Fetch the 3 endpoints needed:
    # TODO(tsileo): clean error if missing
    dat = mf2py.parse(url=u)
    auth_endpoint = dat["rels"]["authorization_endpoint"][0]
    tok_endpoint = dat["rels"]["token_endpoint"][0]
    micropub_endpoint = dat["rels"]["micropub"][0]

    # Generate a random state
    state = binascii.hexlify(os.urandom(6)).decode()

    # Actually initiate the Authorization flow
    auth_url = (
        auth_endpoint
        + "?"
        + urllib.parse.urlencode(
            {
                "me": me,
                "response_type": "code",
                "state": state,
                "redirect_uri": REDIRECT_URI,
                "scope": " ".join(scopes),
                "client_id": CLIENT_ID,
            }
        )
    )

    # Open the URL in a tab
    webbrowser.open_new_tab(auth_url)

    click.echo("waiting for the IndieAuth callback...")
    tok = _wait_for_access_token(me, tok_endpoint)
    click.echo("success")

    # And wait for the callback via the redirect_uri
    return (me, micropub_endpoint, tok)


def micropub_create(micropub_endpoint, access_token, content, meta):
    props = {"content": [content]}
    if meta["name"]:
        props["name"] = [meta["name"]]
    if meta["category"]:
        props["category"] = meta["category"]
    for k in ["mp-slug", "mp-extra-head", "mp-extra-body"]:
        if k in meta:
            props[k] = [meta[k]]

    resp = requests.post(
        micropub_endpoint,
        headers={"Authorization": f"Bearer {access_token}"},
        json={"type": ["h-entry"], "properties": props},
    )
    resp.raise_for_status()
    webbrowser.open_new_tab(resp.headers.get("Location"))


def micropub_update(micropub_endpoint, access_token, url, content, meta):
    replace = {"content": [content]}
    if meta["name"]:
        replace["name"] = [meta["name"]]
    if meta["category"]:
        replace["category"] = meta["category"]
    # XXX no mp-slug update
    for k in ["mp-extra-head", "mp-extra-body"]:
        if meta[k]:
            replace[k] = [meta[k]]
    resp = requests.post(
        micropub_endpoint,
        headers={"Authorization": f"Bearer {access_token}"},
        json={"action": "update", "url": url, "replace": replace},
    )
    resp.raise_for_status()
    webbrowser.open_new_tab(resp.headers.get("Location"))


def micropub_delete(micropub_endpoint, access_token, url):
    resp = requests.post(
        micropub_endpoint,
        headers={"Authorization": f"Bearer {access_token}"},
        json={"action": "delete", "url": url},
    )
    resp.raise_for_status()
    webbrowser.open_new_tab(url)


def micropub_source(micropub_endpoint, access_token, url):
    resp = requests.get(
        micropub_endpoint,
        {"q": "source", "url": url},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    resp.raise_for_status()
    return resp.json()


@click.group()
@click.version_option(VERSION)
def cli():
    pass


@click.command()
@click.argument("url", required=True)
def get_token(url):
    _, _, tok = get_access_token(url, ["create", "update", "delete"])
    click.echo(tok)


header = """name: title
mp-slug: slug
category: []
---
"""


def edit(header):
    """`click.edit` wrapper that keeps a copy of the edited content in a file."""
    dat = click.edit(header)
    if dat is None:
        raise ValueError("cancelled, no data saved")
    raw_meta, message = dat.split("---", 1)

    # Keep the data in case the server fails
    # TODO(tsileo): clean it
    with tempfile.NamedTemporaryFile("w", delete=False) as cache:
        cache.write(dat)

    click.echo(f"data will be available at {cache.name} in case of crash")
    return message, yaml.safe_load(raw_meta), cache.name


def done(t):
    os.remove(t)
    click.echo("success 🐢")


@click.command()
@click.argument("url", required=True)
def create(url):
    _, micropub_endpoint, tok = get_access_token(url, ["create"])

    message, meta, t = edit(header)

    micropub_create(micropub_endpoint, tok, message, meta)
    done(t)


def _get(source, k, default):
    if k in source["properties"] and len(source["properties"][k]):
        vs = source["properties"][k]
        if k in ["category"]:
            return vs
        else:
            return vs[0]

    return default


def build_header(source):
    name = _get(source, "name", "null")
    slug = _get(source, "mp-slug", "null")
    extra_head = "\n  ".join(_get(source, "mp-extra-head", "").split("\n"))
    extra_body = "\n  ".join(_get(source, "mp-extra-body", "").split("\n"))
    cat = _get(source, "category", [])
    return f"""name: {name}
mp-slug: {slug}
category: {cat!s}
mp-extra-head: |
  {extra_head}
mp-extra-body: |
  {extra_body}
---"""


@click.command()
@click.argument("url", required=True)
def update(url):
    _, micropub_endpoint, tok = get_access_token(url, ["update"])

    # Fetch the source
    source = micropub_source(micropub_endpoint, tok, url)
    existing_content = source["properties"]["content"][0]

    # Edit
    new_content, meta, t = edit(build_header(source) + existing_content)
    micropub_update(micropub_endpoint, tok, url, new_content, meta)
    done(t)


@click.command()
@click.argument("url", required=True)
def source(url):
    _, micropub_endpoint, tok = get_access_token(url, ["update"])

    # Fetch the source
    source = micropub_source(micropub_endpoint, tok, url)
    click.echo(source)


@click.command()
@click.argument("url", required=True)
def delete(url):
    _, micropub_endpoint, tok = get_access_token(url, ["delete"])
    micropub_delete(micropub_endpoint, tok, url)


cli.add_command(get_token)
cli.add_command(create)
cli.add_command(update)
cli.add_command(source)
cli.add_command(delete)


if __name__ == "__main__":
    cli()
