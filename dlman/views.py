from asyncio import gather
from json import dumps
from pathlib import Path

from aiohttp import web
from aiohttp_jinja2 import template
from aiohttp_sse import sse_response

from .download import MANAGER
from .events import STREAMS

routes = web.RouteTableDef()
routes.static('/static', (Path(__file__).resolve().parent / 'static'), name='static')


async def sse_worker(app):
    channel = app[MANAGER].channel
    async for event, dl in channel:
        fs = []
        for stream in app[STREAMS]:
            fs.append(stream.send(dumps(dl), event=event))
        await gather(*fs)


@routes.get('/_sse', name='sse')
async def sse(request):
    # see worker for actual view.  I know.
    stream = await sse_response(request)
    request.app[STREAMS].add(stream)
    try:
        await stream.wait()
    finally:
        await stream.send("", event='close')
        request.app[STREAMS].discard(stream)
    return stream


@routes.get('/status', name='status')
async def status(request):
    data = request.app[MANAGER].status()
    return web.json_response(data)


@routes.post('/cancel', name='cancel')
async def cancel(request):
    data = await request.post()
    resp = await request.app[MANAGER].cancel(data['id'])
    return web.json_response(resp)

@routes.post('/remove', name='remove')
async def remove(request):
    data = await request.post()
    resp = await request.app[MANAGER].remove(data['id'])
    return web.json_response(resp)


@routes.post('/add', name='add')
async def add(request):
    data = await request.post()
    resp = await request.app[MANAGER].from_url(data['url'])
    return web.json_response(resp)

@routes.get('/')
@template('index.html')
async def root(request):
    return {}


