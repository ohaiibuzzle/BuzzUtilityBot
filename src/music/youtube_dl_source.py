import asyncio
from os import stat
import re
import youtube_dl
import discord
from youtube_dl import options

YTDL_OPTS = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

FFMPEG_OPTS = {
    'options': '-vn',
}

ytdl_client = youtube_dl.YoutubeDL(YTDL_OPTS)

class YouTubeDLSingleSource(discord.PCMVolumeTransformer):

    def __init__(self, original, *, data, volume: float = 0.5, requester, channel):
        super().__init__(original, volume=volume)

        self.requester = requester
        self.channel = channel

        self.data = data        
        self.webpage = data.get('webpage_url')
        self.title = data.get('title')
        self.uploader = data.get('uploader')
        self.url = data.get('url')
    
    @classmethod
    async def from_url(cls, url, *,loop=None, stream=False, requester, channel):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl_client.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]
        
        filename = data['url'] if stream else ytdl_client.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **FFMPEG_OPTS), data=data, requester=requester, channel=channel)

    @staticmethod
    async def list_from_query(query, loop, amount:int=10):
        """
        Search for songs using youtube-dl
        """
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl_client.extract_info(f"ytsearch{amount}:{query}", download=False))
        if 'entries' in data:
            return data