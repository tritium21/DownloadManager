DownloadManager
===============

[![Python version](https://img.shields.io/static/v1?label=Python&message=3.10&color=3776AB&style=plastic&logo=python&labelColor=FFDC55 "Python version: 3.10")](https://docs.python.org/3.10/) [![AIOHTTP version](https://img.shields.io/static/v1?label=AIOHTTP&message=3.8.1&style=plastic&logo=aiohttp&labelColor=2C5BB4&color=FFDC55 "AIOHTTP version: 3.8.1")](https://docs.aiohttp.org/en/v3.8.1/) [![Jinja version](https://img.shields.io/static/v1?label=Jinja&message=3.1.2&style=plastic&logo=jinja&labelColor=B41717&color=101010 "Jinja version: 3.1.2")](https://jinja.palletsprojects.com/en/3.1.x/)

An [aiohttp](https://docs.aiohttp.org/) based server for
downloading files to the remote system, without being
horribly slow or obviously insecure -- hopefully.

Probably don't use this in a high volume environment,
but you do you, boo.

> Note: No back end code has been written, look elsewhere