import asyncio
import itertools
import logging

import async_timeout
import discord
from discord.ext import commands

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

    def __iter__(self):  # pylint: disable=non-iterator-returned
        return self._queue.__iter__()

    def __len__(self):
        return self.qsize()

    def clear(self):
        self._queue.clear()

    def remove(self, index):
        del self._queue[index]

    def chop(self, amount: int):
        for _ in range(amount - 1):
            self.remove(0)


class PlaybackItem:
    __slots__ = ("source", "requester")

    def __init__(self, source: youtube_dl_source.YouTubeDLSingleSource):
        self.source = source
        self.requester = source.requester

    def __str__(self) -> str:
        return f"{self.source.title} - {self.source.uploader}"

    def create_embed(self) -> discord.Embed:
        return (
            discord.Embed(title="Now Playing")
            .add_field(name="Title", value=self.source.title, inline=False)
            .add_field(name="Requested By", value=self.requester, inline=False)
            .add_field(name="Duration", value=self.source.duration, inline=False)
            .set_thumbnail(url=self.source.thumbnail)
        )


class VoiceState:
    def __init__(self, client: commands.Bot, ctx: commands.Context) -> None:
        self.client = client
        self._ctx = ctx

        self.current = None
        self.voice = None
        self.voice_channel = None
        self.summon_user = None
        self.next = asyncio.Event()
        self.play_queue = PlayQueue()

        self._loop = False
        self._queueloop = False
        self._volume = 0.5
        self._seek_to = None

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

    @property
    def seek_to(self):
        return self._seek_to

    @seek_to.setter
    def seek_to(self, value):
        def format_time_ffmpeg(s):
            if s is not None:
                total_seconds = s
                total_minutes = s / 60
                total_hours = s / 3600
                sec = int(total_seconds % 60)
                mins = int(total_minutes % 60 - (sec / 3600))
                hours = int(total_hours - (mins / 60) - (sec / 3600))

                return "{:02d}:{:02d}:{:02d}".format(hours, mins, sec)
            return None

        self._seek_to = format_time_ffmpeg(value)

    async def audio_player_task(self):
        while True:
            self.next.clear()
            if not self.loop and not self.seek_to:
                if self.queueloop:
                    await self.play_queue.put(
                        PlaybackItem(
                            await youtube_dl_source.YouTubeDLSingleSource.from_url(
                                self.current.source.webpage,
                                stream=True,
                                requester=self.current.source.requester,
                                channel=self.current.source.channel,
                            )
                        )
                    )

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
                await self.current.source.channel.send(
                    embed=self.current.create_embed()
                )

            elif self.loop:
                looped = discord.FFmpegPCMAudio(
                    self.current.source.url, **youtube_dl_source.FFMPEG_OPTS
                )
                self.voice.play(looped, after=self.play_next_song)

            elif self.seek_to:
                FFMPEG_SKIP_OPTS = {
                    "before_options": f"-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -ss {self.seek_to}",
                    "options": "-vn -loglevel quiet",
                }
                seeking = discord.FFmpegPCMAudio(
                    self.current.source.url, **FFMPEG_SKIP_OPTS
                )
                self.seek_to = None
                self.voice.play(seeking, after=self.play_next_song)

            await self.next.wait()

    def play_next_song(self, error=None):
        if error:
            logging.critical(error)
            raise VoiceError(str(error))
        self.next.set()

    def skip(self, amount: int = 1):
        if amount != 1:
            self.play_queue.chop(amount)
        if self.is_playing:
            self.voice.stop()

    def seek(self, seconds: int):
        if self.current.source.raw_duration > seconds and self.is_playing:
            self.seek_to = seconds
            self.voice.stop()
        else:
            raise VoiceError("Invalid operation")

    async def stop(self):
        self.play_queue.clear()
        if self.voice:
            await self.voice.disconnect()
            self.voice = None
