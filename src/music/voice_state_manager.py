from discord.ext import commands
import asyncio, async_timeout
import itertools

from discord.ext.commands.core import Command
from music import youtube_dl_source

class VoiceError(Exception):
    pass

class PlayQueue(asyncio.Queue):
    def __getitem__(self, item):
        if isinstance(item, slice):
            return list(itertools.islice(self._queue, item.start, item.stop, item.step))
        else:
            return self._queue[item]

    def __iter__(self): # pylint: disable=non-iterator-returned
        return self._queue.__iter__()
    
    def __len__(self):
        return self.qsize()

    def clear(self):
        self._queue.clear()
    
    def remove(self, index):
        del self._queue[index]

class PlaybackItem():
    __slots__ = ('source', 'requester')

    def __init__(self, source: youtube_dl_source.YouTubeDLSingleSource):
        self.source = source
        self.requester = source.requester

    def __str__(self) -> str:
        return f"{self.source.title} - {self.source.uploader}"

class VoiceState:
    def __init__(self, client:commands.Bot, ctx: commands.Context) -> None:
        self.client = client
        self._ctx = ctx

        self.current = None
        self.voice = None
        self.next = asyncio.Event()
        self.play_queue = PlayQueue()

        self._loop = False
        self._volume = 0.5

        self.audio_player = client.loop.create_task(self.audio_player_task())
        
    def __del__(self):
        self.audio_player.cancel()

    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value: bool):
        self._loop = value


    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = value

    @property
    def is_playing(self):
        return self.voice and self.current
    
    async def audio_player_task(self):
        while True:
            self.next.clear()

            if not self.loop:
                # Try to get the next song within 3 minutes.
                # If no song will be added to the queue in time,
                # the player will disconnect due to performance
                # reasons.
                try:
                    async with async_timeout.timeout(180):  # 3 minutes
                        self.current = await self.play_queue.get()
                except asyncio.TimeoutError:
                    self.client.loop.create_task(self.stop())
                    return

            self.current.source.volume = self._volume
            self.voice.play(self.current.source, after=self.play_next_song)
            await self.current.source.channel.send(embed=self.current.create_embed())

            await self.next.wait()

    def play_next_song(self, error=None):
        if error:
            raise VoiceError(str(error))

        self.next.set()

    async def stop(self):
        self.play_queue.clear()

        if self.voice:
            await self.voice.disconnect()
            self.voice = None



