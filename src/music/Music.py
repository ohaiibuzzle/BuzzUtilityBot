import asyncio
import discord
from discord.ext import commands, tasks
from music import youtube_dl_source, voice_state_manager, spotify_yt_bridge
import math
from spotipy.exceptions import SpotifyException
import io
import re


class Music(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.voice_states = {}
        # self.check_alone.start() #pylint: disable=no-member

    def get_voice_state(self, ctx: commands.Context) -> voice_state_manager.VoiceState:
        state = self.voice_states.get(ctx.guild.id)
        if not state or state.has_timed_out:
            state = voice_state_manager.VoiceState(self.client, ctx)
            self.voice_states[ctx.guild.id] = state

        return state

    def cog_command_error(self, ctx, error):
        if error is AttributeError or error is commands.errors.MissingRequiredArgument:
            return ctx.send(
                f"There was an error processing your request (Perhaps checks your command?) \n Details:{error}"
            )
        else:
            print(error)
            return ctx.send(f"There was an error processing your request :(")

    def cog_unload(self):
        for state in self.voice_states.values():
            self.client.loop.create_task(state.stop())

    async def cog_check(self, ctx):
        if not ctx.guild:
            await ctx.send("This command group is not supported in DMs")
            return False
        return True

    async def cog_before_invoke(self, ctx):
        ctx.voice_state = self.get_voice_state(ctx)

    @commands.command()
    async def summon(self, ctx: commands.Context):
        """
        Connects to the user's voice channel
        """
        if not ctx.author.voice:
            return await ctx.send("Hmm? What should I join here?")

        destination = ctx.author.voice.channel

        if ctx.voice_state.voice:
            return await ctx.voice_state.voice.move_to(destination)

        ctx.voice_state.voice = await destination.connect()

    @commands.command(aliases=["dc"])
    async def disconnect(self, ctx: commands.Context):
        """
        Disconnect and clear queue
        """
        if not ctx.voice_state.voice:
            return await ctx.send("Not currently connected to any channel!")
        else:
            await ctx.voice_state.stop()
            del self.voice_states[ctx.guild.id]

    @commands.command()
    async def play(
        self,
        ctx: commands.Context,
        *,
        url,
        silent_mesg=False,
        has_URL=False,
        hidden=False,
    ):
        """
        Play **from URL**
        """
        if not ctx.voice_state.voice:
            await ctx.invoke(self.summon)
        async with ctx.typing():
            # Handle Spotify stuff separately
            if re.match(
                r"https?://open\.spotify\.com/(track|album|playlist)/(?P<id>[^/?&#]+)",
                url,
            ):
                # Regex stolen from youtube-dl. Not dealing with that haha.
                return await ctx.invoke(self.spotify, url=url)
            try:
                source = await youtube_dl_source.YouTubeDLSingleSource.from_url(
                    url,
                    loop=self.client.loop,
                    stream=True,
                    requester=ctx.author,
                    channel=ctx.channel,
                )
            except Exception as e:
                raise e
            else:
                item = voice_state_manager.PlaybackItem(source=source)

                await ctx.voice_state.play_queue.put(item)
                if not hidden:
                    if not has_URL:
                        status = await ctx.send(
                            f"Added {source.title} - {source.uploader} to the queue!"
                        )
                    else:
                        status = await ctx.send(
                            f"Added {source.title} - {source.uploader} ({source.webpage}) to the queue!"
                        )
                    if silent_mesg:
                        await asyncio.sleep(8)
                        await status.delete()
                else:
                    await asyncio.sleep(8)

    @commands.command(name="pause")
    async def _pause(self, ctx: commands.Context):
        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_playing():
            ctx.voice_state.voice.pause()
            await ctx.message.add_reaction("🆗")

    @commands.command(name="resume")
    async def _resume(self, ctx: commands.Context):
        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_paused():
            ctx.voice_state.voice.resume()
            await ctx.message.add_reaction("🆗")

    @commands.command()
    async def remove(self, ctx, *, index: int):
        if len(ctx.voice_state.play_queue) == 0:
            return await ctx.send("Empty queue.")

        ctx.voice_state.play_queue.remove(index - 1)
        await ctx.message.add_reaction("🆗")
        await ctx.invoke(self.queue)

    @commands.command()
    async def volume(self, ctx: commands.Context, volume: float):
        """
        Adjust volume (0-100)
        """
        if not ctx.voice_client:
            return await ctx.send("Hmm? Do I even have a voice?")
        elif 0 > volume > 100:
            return await ctx.send("What kind of silly volume is that???")
        else:
            ctx.voice_client.source.volume = volume / 100
            return await ctx.send(f"Done! The volume is now {volume}%")

    @commands.command()
    async def queue(self, ctx, *, page: int = 1):
        """
        Show the playback queue
        """
        async with ctx.typing():
            if len(ctx.voice_state.play_queue) == 0:
                await ctx.send("Oh no queue is empty :(")

            else:
                pages = math.ceil(len(ctx.voice_state.play_queue) / 10)
                first_item = (page - 1) * 10

                queue_str = ""
                for number, entry in enumerate(
                    ctx.voice_state.play_queue[first_item : first_item + 10],
                    start=first_item,
                ):
                    queue_str += f"**{number + 1}**. {entry.source.title} - {entry.source.uploader}\n"

                this_embed = discord.Embed(
                    title=f"Queue page {page}/{pages}", description=queue_str
                )

                await ctx.send(embed=this_embed)

    @commands.command()
    async def search(self, ctx: commands.Context, *, query):
        print(
            f"@{ctx.author.name}#{ctx.author.discriminator} searches something on YouTube"
        )
        """
        Use youtube-dl to look up videos
        """

        def check_requester_msg(message: discord.Message):
            return message.author == ctx.author

        async with ctx.typing():
            result = await youtube_dl_source.YouTubeDLSingleSource.list_from_query(
                query, loop=self.client.loop
            )
            result = result["entries"]
            this_embed = discord.Embed(title=f"Search result for {query}")
            res_str = ""
            for number, data in enumerate(result):
                res_str += (
                    f"**{number+1}**. {data['title']} - {data['uploader']}" + "\n"
                )
            this_embed.description = res_str
            this_embed.color = int(0x0062FF)
            search_res = await ctx.send(embed=this_embed)
            try:
                msg = await self.client.wait_for(
                    "message", timeout=15, check=check_requester_msg
                )
            except asyncio.TimeoutError:
                await search_res.delete()
                return await ctx.send("Timeout!")
            else:
                if msg.content.isdigit():
                    await search_res.delete()
                    return await ctx.invoke(
                        self.play,
                        url=result[int(msg.content) - 1]["webpage_url"],
                        silent_mesg=True,
                        has_URL=True,
                    )
                else:
                    return await ctx.send("That was not a valid selection!")

    @commands.command(aliases=["np"])
    async def nowplaying(self, ctx):
        await ctx.send(embed=ctx.voice_state.current.create_embed())

    @commands.command(name="loop")
    async def _loop(self, ctx: commands.Context):
        """Loops/Unloops whatever is currently being played

        Args:
            ctx (commands.Context): Context
        """
        if not ctx.voice_state.is_playing:
            return await ctx.send("Nothing being played at the moment.")
        ctx.voice_state.loop = not ctx.voice_state.loop
        if ctx.voice_state.loop:
            msg = await ctx.send("Looping this track")
        else:
            msg = await ctx.send("Unlooped")
        await asyncio.sleep(5)
        await msg.delete()
        await ctx.message.add_reaction("✅")

    @commands.command(name="queueloop")
    async def _queueloop(self, ctx: commands.Context):
        if not ctx.voice_state.is_playing:
            return await ctx.send("Nothing being played at the moment")
        ctx.voice_state.queueloop = not ctx.voice_state.queueloop
        if ctx.voice_state.queueloop:
            msg = await ctx.send("Looping this queue")
        else:
            msg = await ctx.send("Unlooped")
        await asyncio.sleep(5)
        await msg.delete()
        return await ctx.message.add_reaction("✅")

    @commands.command()
    async def skip(self, ctx, *, n: int = 1):
        """
        Skip n items
        """
        if not ctx.voice_state.is_playing:
            return await ctx.send("Not playing any music right now...")
        else:
            if n > len(ctx.voice_state.play_queue):
                await ctx.invoke(self.disconnect)
            await ctx.send(f"Skipping {n} track...")
            ctx.voice_state.skip(n)

    @commands.command()
    async def seek(self, ctx, *, timestamp: str):
        """Skips to part of song
        timestamp (str): Where to jumps to. Format mm:ss.
        """
        parts = timestamp.split(":")
        if len(parts) < 1:
            return await ctx.send("Heeeeey! That is not a valid timestamp")

        time_convert = (1, 60, 60 * 60, 60 * 60 * 24)
        seconds = 0
        for i in range(len(parts)):
            try:
                v = int(parts[i])
            except:
                continue

            j = len(parts) - i - 1
            if j >= len(time_convert):
                continue

            seconds += v * time_convert[j]
        ctx.voice_state.seek(seconds)
        return await ctx.message.add_reaction("✅")

    @commands.command()
    async def spotify(self, ctx, *, url: str, silent: bool = None):
        print(
            f"@{ctx.author.name}#{ctx.author.discriminator} played a Spotify Playlist"
        )
        """
        Plays a Spotify Playlist
        """
        if not ctx.voice_state.voice:
            await ctx.invoke(self.summon)
        async with ctx.typing():
            if re.match(
                r"https?://open\.spotify\.com/(playlist|album)/(?P<id>[^/?&#]+)", url
            ):
                await ctx.send(
                    "Please wait, converting your playlist. This could take a while!"
                )
                try:
                    if re.match(
                        r"https?://open\.spotify\.com/album/(?P<id>[^/?&#]+)", url
                    ):
                        track_list = (
                            await spotify_yt_bridge.async_spotify_album_to_track_names(
                                url, self.client.loop
                            )
                        )
                    elif re.match(
                        r"https?://open\.spotify\.com/playlist/(?P<id>[^/?&#]+)", url
                    ):
                        track_list = await spotify_yt_bridge.async_spotify_playlist_to_track_list(
                            url, self.client.loop
                        )
                except SpotifyException as e:
                    await ctx.send(f"Something funky happened: {e}")
                else:
                    for track in track_list:
                        if not self.voice_states[ctx.guild.id]:
                            return
                        try:
                            track_link = (
                                await spotify_yt_bridge.async_single_track_to_yt_alt(
                                    track, self.client.loop
                                )
                            )
                        except:
                            await ctx.send(f"Something funky happened. Stopping")
                            break
                        else:
                            if not silent:
                                await ctx.invoke(
                                    self.play,
                                    url=track_link,
                                    silent_mesg=True,
                                    has_URL=True,
                                )
                            else:
                                await ctx.invoke(self.play, url=track_link, hidden=True)
                            await asyncio.sleep(2)

                    await ctx.invoke(self.queue)
                    await ctx.send(
                        "Done! Tip: You can also use `exportqueue` to get the queue exported and use it with other bots!"
                    )
            elif re.match(r"https?://open\.spotify\.com/track/(?P<id>[^/?&#]+)", url):
                yt_url = await spotify_yt_bridge.async_single_spotify_track_to_yt(
                    url, loop=self.client.loop
                )
                return await ctx.invoke(
                    self.play, url=yt_url, silent_mesg=False, has_URL=True
                )

    @commands.command()
    async def exportqueue(self, ctx: commands.Context):
        """
        Export the current queue to file
        """
        async with ctx.typing():
            with io.StringIO() as tmp_queue:
                for i, item in enumerate(ctx.voice_state.play_queue):
                    tmp_queue.write(
                        f"{i+1}. {item.source.webpage} - {item.source.title} - {item.source.uploader}\n"
                    )
                tmp_queue.seek(0)
                file = discord.File(tmp_queue, filename=f"queue-{ctx.guild}.txt")
                await ctx.send("Here's the current queue!", file=file)

    @play.before_invoke
    async def ensure_voice(self, ctx):
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("You are not connected to any voice channel.")
            raise commands.CommandError("User is not connected to any voice channel.")

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                await ctx.send("I am already in another channel")
                raise commands.CommandError("Bot is already in a voice channel.")

    @tasks.loop(seconds=180.0)
    async def check_alone(self):
        for client in self.client.voice_clients:
            if client.channel.members.__len__() == 1:
                await client.disconnect()


def setup(client: commands.Bot):
    client.add_cog(Music(client))
