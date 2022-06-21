from asyncio import sleep, CancelledError
from contextlib import suppress
from collections import deque
from dataclasses import dataclass, asdict, field
from uuid import uuid5, NAMESPACE_URL

import aiohttp

from .channel import LeftChannel
from yarl import URL

import random

MANAGER = 'manager'
WORKER = 'manager_worker'

UPDATE = 'update'
REMOVE = 'remove'
ADD = 'add'


@dataclass
class DownloadInfo:
    id: str = field(init=False)
    name: str
    url: str
    size: int = 0
    complete: int = field(default=0, init=False)
    rate: int = field(default=0, init=False)
    failed: bool = field(default=False, init=False)
    finished: bool = field(default=False, init=False)

    def __post_init__(self):
        self.id = str(uuid5(NAMESPACE_URL, self.url))

    @classmethod
    async def from_url(cls, url):
        async with aiohttp.request(method='HEAD', url=url) as resp:
            size = resp.content_length
            if (condis := resp.content_disposition) and condis.filename:
                name = condis.filename
            else:
                name = URL(url).name
        return cls(name=name, url=url, size=size)


class Manager:
    def __init__(self):
        self.downloads = {}
        self.channel = None
        self._app = None
        self._cancel = deque()
        self._remove = deque()
        self._add = deque()

        #TEST DATA
        self.add(DownloadInfo('file.zip', 'http://example.com/file.zip', 69420))
        self.add(DownloadInfo('file2.zip', 'http://example.com/file2.zip', 69420))
        self.add(DownloadInfo('file3.zip', 'http://example.com/file3.zip', 69420))

    def add(self, download):
        self._add.append(download)
        self.downloads[download.id] = download

    async def from_url(self, url):
        dl = await DownloadInfo.from_url(url)
        self.add(dl)
        return asdict(dl)

    def status(self):
        return [asdict(x) for x in self.downloads.values()]

    async def worker(self):
        while True:
            while self._add:
                await self.channel.putleft((ADD, [asdict(self._add.popleft())]))
            while self._cancel:
                await self.channel.putleft((UPDATE, [asdict(self._cancel.popleft())]))
            while self._remove:
                await self.channel.putleft((REMOVE, [asdict(self._remove.popleft())]))
            dls = [
                dict(asdict(d), complete=random.randint(0, d.size))
                for d in self.downloads.values()
                if not d.finished and not d.failed
            ]
            for dl in dls:
                self.downloads[dl['id']].complete = dl['complete']
            await self.channel.put((UPDATE, dls))
            while not self.channel.empty():
                await sleep(0.1)


    async def cancel(self, id):
        if id not in self.downloads:
            return
        dl = self.downloads[id]
        dl.failed = True
        self._cancel.append(dl)
        return asdict(dl)


    async def remove(self, id):
        if id not in self.downloads:
            return
        dl = self.downloads[id]
        del self.downloads[id]
        self._remove.append(dl)
        return asdict(dl)


    @classmethod
    def install(cls, app):
        app[MANAGER]  = self = cls()
        self._app = app
        app.on_startup.append(self.on_startup)
        app.on_cleanup.append(self.on_cleanup)
        return self

    async def on_startup(self, app):
        self.channel = LeftChannel(loop=app.loop)
        app[WORKER] = app.loop.create_task(self.worker())

    async def on_cleanup(self, app):
        app[WORKER].cancel()
        with suppress(CancelledError):
            await app[WORKER]