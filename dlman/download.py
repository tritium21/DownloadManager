import asyncio
from contextlib import suppress
from dataclasses import dataclass, asdict, field
from uuid import uuid5, NAMESPACE_URL

from aiochannel import Channel
from yarl import URL

import random

MANAGER = 'manager'
WORKER = 'manager_worker'


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

class Manager:
    def __init__(self):
        self.downloads = []
        self.channel = Channel()

        #TEST DATA
        self.add(DownloadInfo('file.zip', 'http://example.com/file.zip', 69420))
        self.add(DownloadInfo('file2.zip', 'http://example.com/file2.zip', 69420))
        self.add(DownloadInfo('file3.zip', 'http://example.com/file3.zip', 69420))

    def add(self, download):
        self.downloads.append(download)

    async def from_url(self, url):
        id = uuid5(NAMESPACE_URL, url)
        url = URL(url)
        name = url.name
        dl = DownloadInfo(id, name, url)
        self.add(dl)
        return dl

    def status(self):
        return [asdict(x) for x in self.downloads]

    async def worker(self):
        while True:
            dl = random.choice(self.downloads)
            dl.complete = random.randint(0, dl.size - 1)
            await self.channel.put([asdict(dl)])
            await asyncio.sleep(1)

    @classmethod
    def install(cls, app):
        app[MANAGER]  = self = cls()
        app.on_startup.append(self.on_startup)
        app.on_cleanup.append(self.on_cleanup)
        return self

    async def on_startup(self, app):
        app[WORKER] = app.loop.create_task(self.worker())

    async def on_cleanup(self, app):
        app[WORKER].cancel()
        with suppress(asyncio.CancelledError):
            await app[WORKER]