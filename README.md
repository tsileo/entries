# entries

<a href="https://d.a4.io/tsileo/entries"><img src="https://d.a4.io/api/badges/tsileo/entries/status.svg" alt="Build Status"></a>
<a href="https://github.com/tsileo/entries/blob/master/LICENSE"><img src="https://img.shields.io/badge/license-ISC-red.svg?style=flat" alt="License"></a>
<a href="https://github.com/ambv/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>

[Micropub](https://www.w3.org/TR/micropub/) client for the CLI.

Designed for [entries.pub](https://github.com/tsileo/entries.pub) but should work with any Micropub server.


## Features

 - Zero configuration (everything is "guessed" from the URI)
 - Create/update posts directly within your favorite `$EDITOR`
 - Support the [mp-slug](https://indieweb.org/Micropub-extensions#Slug) extension


## Install

Requires Python3+.

    $ pip install git+https://github.com/tsileo/entries


## Usage

See the help.

    $ entries -h

    # Create a new article
    $ entries create https://mywebsite.tld

    # Update an article
    $ entries update https://mywebsite.tld/posts/1

    # Delete an article
    $ entries delete https://mywebsite.tld/posts/1
