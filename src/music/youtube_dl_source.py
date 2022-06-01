import asyncio
from collections import deque

import discord
import yt_dlp

YTDL_OPTS = {
    "format": "bestaudio/best",
    "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",
}

FFMPEG_OPTS = {
    "before_options": "-loglevel quiet -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}

ytdl_client = yt_dlp.YoutubeDL(YTDL_OPTS)


class YouTubeDLSingleSource(discord.PCMVolumeTransformer):
    def __init__(self, original, *, data, volume: float = 0.5, requester, channel):
        super().__init__(original, volume=volume)

        self.requester = requester
        self.channel = channel

        self.data = data
        self.webpage = data.get("webpage_url")
        try:
            self.raw_duration = int(data.get("duration"))
            self.duration = self.parse_duration(int(data.get("duration")))
        except TypeError:
            self.raw_duration = 0
            self.duration = "Unavailable"
        self.thumbnail = (
            data.get("thumbnail")
            if data.get("thumbnail")
            else "https://source.boringavatars.com/beam/160/Daisy%20Gatson.svg?colors=A8E6CE,DCEDC2,FFD3B5,FFAAA6,FF8C94"
        )
        self.title = data.get("title")
        self.uploader = data.get("uploader")
        self.url = data.get("url")

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False, requester, channel):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None,
            lambda: ytdl_client.extract_info(
                url,
                download=not stream,
            ),
        )

        if "entries" in data:
            data = data["entries"][0]

        filename = data["url"] if stream else ytdl_client.prepare_filename(data)
        return cls(
            discord.FFmpegPCMAudio(filename, **FFMPEG_OPTS),
            data=data,
            requester=requester,
            channel=channel,
        )

    @staticmethod
    async def list_from_query(query, loop, amount: int = 10):
        """
        Search for songs using youtube-dl
        """
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None,
            lambda: ytdl_client.extract_info(
                f"ytsearch{amount}:{query}", download=False
            ),
        )
        if "entries" in data:
            return data

    @staticmethod
    def parse_duration(duration: int):
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        duration = []
        if days > 0:
            duration.append(str(f"{days}"))
        if hours > 0:
            duration.append(str(f"{hours:02}"))
        if minutes > 0:
            duration.append(str(f"{minutes:02}"))
        if seconds > 0:
            duration.append(str(f"{seconds:02}"))

        return ":".join(duration)
