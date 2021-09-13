from importlib.util import source_from_cache
import discord
from discord.ext import commands
import asyncio, async_timeout
import itertools

from music import youtube_dl_source

# Most of these is stolen from here lol
# https://gist.github.com/vbe0201/ade9b80f2d3b64643d854938d40a0a2d
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

    def chop(self, amount: int):
        for _ in range(amount-1):
            self.remove(0)

class PlaybackItem():
    __slots__ = ('source', 'requester')

    def __init__(self, source: youtube_dl_source.YouTubeDLSingleSource):
        self.source = source
        self.requester = source.requester

    def __str__(self) -> str:
        return f"{self.source.title} - {self.source.uploader}"
    
    def create_embed(self) -> discord.Embed:
        return discord.Embed(title="Now Playing").add_field(name='Title', value=self.source.title, inline=False)\
            .add_field(name='Requested By', value=self.requester, inline=False)\
            .add_field(name='Duration', value=self.source.duration, inline=False)\
            .set_thumbnail(url=self.source.thumbnail)

class VoiceState:
    def __init__(self, client:commands.Bot, ctx: commands.Context) -> None:
        self.client = client
        self._ctx = ctx

        self.current = None
        self.voice = None
        self.next = asyncio.Event()
        self.play_queue = PlayQueue()

        self._loop = False
        self._queueloop = False
        self._volume = 0.5

        self.has_timed_out = False

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
    def queueloop(self):
        return self._queueloop

    @queueloop.setter
    def queueloop(self, value: bool):
        self._queueloop = value

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
                if self.queueloop:
                    await self.play_queue.put(PlaybackItem(await youtube_dl_source.YouTubeDLSingleSource.from_url(self.current.source.webpage, stream=True,\
                        requester=self.current.source.requester, channel=self.current.source.channel)))

                # Try to get the next song within 3 minutes.
                # If no song will be added to the queue in time,
                # the player will disconnect due to performance
                # reasons.
                try:
                    async with async_timeout.timeout(180):  # 3 minutes
                        self.current = await self.play_queue.get()
                except asyncio.TimeoutError:
                    self.client.loop.create_task(self.stop())
                    self.has_timed_out = True
                    return

                self.current.source.volume = self._volume
                self.voice.play(self.current.source, after=self.play_next_song)
                await self.current.source.channel.send(embed=self.current.create_embed())
            elif self.loop:
                looped = discord.FFmpegPCMAudio(self.current.source.url, options=youtube_dl_source.FFMPEG_OPTS)
                self.voice.play(looped, after=self.play_next_song)

            await self.next.wait()

    def play_next_song(self, error=None):
        if error:
            print(error)
            raise VoiceError(str(error))
        self.next.set()

    def skip(self, amount: int = 1):
        if amount != 1:
            self.play_queue.chop(amount)
        if self.is_playing:
            self.voice.stop()


    async def stop(self):
        self.play_queue.clear()
        if self.voice:
            await self.voice.disconnect()
            self.voice = None



