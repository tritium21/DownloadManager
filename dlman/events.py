import asyncio
from functools import partial
import weakref
from contextlib import suppress
from functools import partial

STREAMS = 'sse_streams'
WORKER = 'sse_worker'

async def on_startup(app, worker):
    app[STREAMS] = weakref.WeakSet()
    app[WORKER] = app.loop.create_task(worker(app))


async def clean_up(app):
    app[WORKER].cancel()
    with suppress(asyncio.CancelledError):
        await app[WORKER]


async def on_shutdown(app):
    waiters = []
    for stream in app[STREAMS]:
        stream.stop_streaming()
        waiters.append(stream.wait())

    await asyncio.gather(*waiters)
    app[STREAMS].clear()


def install_events(app, worker):
    app.on_startup.append(partial(on_startup, worker=worker))
    app.on_shutdown.append(on_shutdown)
    app.on_cleanup.append(clean_up)