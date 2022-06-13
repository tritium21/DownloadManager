from asyncio import sleep, create_task, gather
from json import dumps
from pathlib import Path

from aiohttp import web
from aiohttp_jinja2 import template
from aiohttp_sse import sse_response

routes = web.RouteTableDef()
routes.static('/static', (Path(__file__).resolve().parent / 'static'), name='static')

TEST_DATA = [
    {
        'id': 'e699fdbf-eaa3-11ec-9df6-a85e4553818b',
        'name': 'file.zip',
        'size': '69420',
        'complete': '69000',
        'failed': False,
        'finished': False,
    },
]


async def worker(app):
    import random
    while True:
        delay = create_task(sleep(1))
        fs = []
        for stream in app["streams"]:
            com = random.randint(0, 69420)
            fail = bool(random.randint(0, 1))
            TEST_DATA[0]['complete'] = com
            TEST_DATA[0]['failed'] = fail
            fs.append(stream.send(dumps(TEST_DATA), event='update'))
        await gather(*fs)
        await delay


@routes.get('/_sse', name='sse')
async def sse(request):
    # see worker for actual view.  I know.
    stream = await sse_response(request)
    request.app["streams"].add(stream)
    try:
        await stream.wait()
    finally:
        request.app["streams"].discard(stream)
    return stream


@routes.get('/status', name='status')
async def status(request):
    return web.json_response(TEST_DATA)


@routes.post('/cancel', name='cancel')
async def cancel(request):
    data = await request.post()
    if data['id'] in [d['id'] for d in TEST_DATA]:
        return web.json_response({'id': data['id'], 'failed': True})
    raise web.HTTPForbidden()


@routes.post('/remove', name='remove')
async def remove(request):
    data = await request.post()
    if data['id'] in [d['id'] for d in TEST_DATA]:
        return web.json_response({'id': data['id'], 'failed': True})
    raise web.HTTPForbidden()

@routes.post('/add', name='add')
async def remove(request):
    data = await request.post()
    return web.json_response({})

@routes.get('/')
@template('index.html')
async def root(request):
    return {}


