import asyncio
from functools import partial
import weakref
from contextlib import suppress
from datetime import datetime
from functools import partial


async def on_startup(app, worker):
    app["streams"] = weakref.WeakSet()
    app["worker"] = app.loop.create_task(worker(app))


async def clean_up(app):
    app["worker"].cancel()
    with suppress(asyncio.CancelledError):
        await app["worker"]


async def on_shutdown(app):
    waiters = []
    for stream in app["streams"]:
        stream.stop_streaming()
        waiters.append(stream.wait())

    await asyncio.gather(*waiters)
    app["streams"].clear()


def install_events(app, worker):
    app.on_startup.append(partial(on_startup, worker=worker))
    app.on_shutdown.append(on_shutdown)
    app.on_cleanup.append(clean_up)