from asyncio import Future
from aiochannel import Channel, ChannelClosed, ChannelFull

class LeftChannel(Channel):
    async def putleft(self, item):
        """Put an item into the channel.
        If the channel is full, wait until a free
        slot is available before adding item.
        If the channel is closed or closing, raise ChannelClosed.
        This method is a coroutine.
        """
        while self.full() and not self._close.is_set():
            putter = Future(loop=self._loop)
            self._putters.appendleft(putter)
            try:
                await putter
            except ChannelClosed:
                raise
            except BaseException:
                putter.cancel()  # Just in case putter is not done yet.
                if not self.full() and not putter.cancelled():
                    # We were woken up by get_nowait(), but can't take
                    # the call.  Wake up the next in line.
                    self._wakeup_next(self._putters)
                raise
        return self.putleft_nowait(item)

    def putleft_nowait(self, item):
        """Put an item into the channel without blocking.
        If no free slot is immediately available, raise ChannelFull.
        """
        if self.full():
            raise ChannelFull
        if self._close.is_set():
            raise ChannelClosed
        self._put(item)
        self._wakeup_next(self._getters)

    def _put(self, item):
        self._queue.appendleft(item)