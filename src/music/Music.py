import asyncio
import io
import math
import re

import discord
from discord.ext import commands, tasks, bridge
from spotipy.exceptions import SpotifyException

from music import spotify_yt_bridge, voice_state_manager, youtube_dl_source


class Music(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.voice_states = {}

    def get_voice_state(
        self, ctx: bridge.BridgeContext
    ) -> voice_state_manager.VoiceState:
        state = self.voice_states.get(ctx.guild.id)
        if not state or state.has_timed_out:
            state = voice_state_manager.VoiceState(self.client, ctx)
            self.voice_states[ctx.guild.id] = state

        return state

    def cog_command_error(self, ctx, error):
        if error is AttributeError or error is commands.errors.MissingRequiredArgument:
            return ctx.respond(
                f"There was an error processing your request (Perhaps checks your command?) \n Details:{error}"
            )
        else:
            print(error)
            return ctx.respond(f"There was an error processing your request :(")

    def cog_unload(self):
        for state in self.voice_states.values():
            self.client.loop.create_task(state.stop())

    async def cog_check(self, ctx):
        if not ctx.guild:
            await ctx.respond("This command group is not supported in DMs")
            return False
        return True

    async def cog_before_invoke(self, ctx):
        ctx.voice_state = self.get_voice_state(ctx)

    @bridge.bridge_command()
    async def summon(self, ctx: bridge.BridgeContext):
        """
        Connects to the user's voice channel
        """
        if not ctx.author.voice:
            return await ctx.respond("Hmm? What should I join here?")

        destination = ctx.author.voice.channel

        if ctx.voice_state.voice:
            return await ctx.voice_state.voice.move_to(destination)

        ctx.voice_state.voice = await destination.connect()
        # Automatically deafen the bot (We don't use voice features, save bandwidth)
        await ctx.voice_state.voice.guild.change_voice_state(
            channel=destination, self_mute=False, self_deaf=True
        )
        ctx.voice_state.voice_channel = destination
        ctx.voice_state.summon_user = ctx.author

    @bridge.bridge_command(aliases=["dc"])
    async def disconnect(self, ctx: bridge.BridgeContext):
        """
        Disconnect and clear queue
        """
        if not ctx.voice_state.voice:
            return await ctx.respond("Not currently connected to any channel!")
        else:
            if ctx.author.guild_permissions.manage_channels:
                await ctx.voice_state.stop()
                del self.voice_states[ctx.guild.id]
                await ctx.respond("Disconnected and cleared queue")
            else:
                if ctx.author.voice:
                    if ctx.author.voice.channel != ctx.voice_state.voice_channel:
                        return await ctx.respond(
                            "You are not in the voice channel that I am currently in."
                        )
                    else:
                        if (
                            ctx.voice_state.summon_user != ctx.author
                            and ctx.voice_state.voice_channel.members.__len__() > 2
                        ):
                            return await ctx.respond(
                                "There are others using this channel right now. \nOnly an admin or the user who summoned the bot can disconnect"
                            )
                        await ctx.voice_state.stop()
                        del self.voice_states[ctx.guild.id]
                        await ctx.respond("Disconnected and cleared queue")

    @bridge.bridge_command()
    async def play(
        self,
        ctx: bridge.BridgeContext,
        *,
        url: str,
        silent_mesg: bool = False,
        isurl: bool = False,
        hidden: bool = False,
    ):
        """
        Play **from URL**
        """
        if not ctx.voice_state.voice:
            await ctx.invoke(self.summon)
        await ctx.defer()
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
                if not isurl:
                    status = await ctx.respond(
                        f"Added {source.title} - {source.uploader} to the queue!"
                    )
                else:
                    status = await ctx.respond(
                        f"Added {source.title} - {source.uploader} ({source.webpage}) to the queue!"
                    )
                if silent_mesg:
                    await asyncio.sleep(8)
                    await status.delete()
            else:
                await asyncio.sleep(8)

    @bridge.bridge_command(name="pause")
    async def _pause(self, ctx: bridge.BridgeContext):
        """
        Pause the current song
        """
        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_playing():
            ctx.voice_state.voice.pause()
            if isinstance(ctx, bridge.BridgeExtContext):
                await ctx.message.add_reaction("🆗")

    @bridge.bridge_command(name="resume")
    async def _resume(self, ctx: bridge.BridgeContext):
        """
        Resume the current song
        """
        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_paused():
            ctx.voice_state.voice.resume()
            if isinstance(ctx, bridge.BridgeExtContext):
                await ctx.message.add_reaction("🆗")

    @bridge.bridge_command()
    async def remove(self, ctx, index: int):
        """
        Remove a song from the queue
        """
        if len(ctx.voice_state.play_queue) == 0:
            return await ctx.respond("Empty queue.")

        ctx.voice_state.play_queue.remove(index - 1)
        if isinstance(ctx, bridge.BridgeExtContext):
            await ctx.message.add_reaction("🆗")
            await ctx.invoke(self.queue)

    @bridge.bridge_command()
    async def volume(self, ctx: bridge.BridgeContext, volume: float):
        """
        Adjust volume (0-100)
        """
        if not ctx.voice_client:
            return await ctx.respond("Hmm? Do I even have a voice?")
        elif 0 > volume > 100:
            return await ctx.respond("What kind of silly volume is that???")
        else:
            ctx.voice_client.source.volume = volume / 100
            return await ctx.respond(f"Done! The volume is now {volume}%")

    @bridge.bridge_command()
    async def queue(self, ctx, page: int = 1):
        """
        Show the playback queue
        """
        await ctx.defer()
        if len(ctx.voice_state.play_queue) == 0:
            await ctx.respond("Oh no queue is empty :(")

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

            await ctx.respond(embed=this_embed)

    @bridge.bridge_command()
    async def search(self, ctx: bridge.BridgeContext, *, query: str):
        print(
            f"@{ctx.author.name}#{ctx.author.discriminator} searches something on YouTube"
        )
        """
        Use youtube-dl to look up videos
        """

        def check_requester_msg(message: discord.Message):
            return message.author == ctx.author

        await ctx.defer()
        result = await youtube_dl_source.YouTubeDLSingleSource.list_from_query(
            query, loop=self.client.loop
        )
        result = result["entries"]
        this_embed = discord.Embed(title=f"Search result for {query}")
        res_str = ""
        for number, data in enumerate(result):
            res_str += f"**{number+1}**. {data['title']} - {data['uploader']}" + "\n"
        this_embed.description = res_str
        this_embed.color = int(0x0062FF)
        search_res = await ctx.respond(embed=this_embed)
        try:
            msg = await self.client.wait_for(
                "message", timeout=15, check=check_requester_msg
            )
        except asyncio.TimeoutError:
            await search_res.delete()
            return await ctx.respond("Timeout!")
        else:
            if msg.content.isdigit():
                await search_res.delete()
                return await ctx.invoke(
                    self.play,
                    url=result[int(msg.content) - 1]["webpage_url"],
                    silent_mesg=True,
                    isurl=True,
                )
            else:
                return await ctx.respond("That was not a valid selection!")

    @bridge.bridge_command(aliases=["np"])
    async def nowplaying(self, ctx):
        """
        Show the currently playing song
        """
        await ctx.respond(embed=ctx.voice_state.current.create_embed())

    @bridge.bridge_command(name="loop")
    async def _loop(self, ctx: bridge.BridgeContext):
        """Loops/Unloops whatever is currently being played

        Args:
            ctx (bridge.BridgeContext): Context
        """
        if not ctx.voice_state.is_playing:
            return await ctx.respond("Nothing being played at the moment.")
        ctx.voice_state.loop = not ctx.voice_state.loop
        if ctx.voice_state.loop:
            msg = await ctx.respond("Looping this track")
        else:
            msg = await ctx.respond("Unlooped")
        if isinstance(ctx, bridge.BridgeExtContext):
            await asyncio.sleep(5)
            await msg.delete()
            await ctx.message.add_reaction("✅")

    @bridge.bridge_command(name="queueloop")
    async def _queueloop(self, ctx: bridge.BridgeContext):
        """
        Loops/Unloops the entire queue
        """
        if not ctx.voice_state.is_playing:
            return await ctx.respond("Nothing being played at the moment")
        ctx.voice_state.queueloop = not ctx.voice_state.queueloop
        if ctx.voice_state.queueloop:
            msg = await ctx.respond("Looping this queue")
        else:
            msg = await ctx.respond("Unlooped")
        if isinstance(ctx, bridge.BridgeExtContext):
            await asyncio.sleep(5)
            await msg.delete()
            return await ctx.message.add_reaction("✅")

    @bridge.bridge_command()
    async def skip(self, ctx, n: int = 1):
        """
        Skip n items
        """
        if not ctx.voice_state.is_playing:
            return await ctx.respond("Not playing any music right now...")
        else:
            if n > len(ctx.voice_state.play_queue):
                await ctx.invoke(self.disconnect)
            await ctx.respond(f"Skipping {n} track...")
            ctx.voice_state.skip(n)

    @bridge.bridge_command()
    async def seek(self, ctx, timestamp: str):
        """Skips to part of song
        timestamp (str): Where to jumps to. Format mm:ss.
        """
        parts = timestamp.split(":")
        if len(parts) < 1:
            return await ctx.respond("Heeeeey! That is not a valid timestamp")

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
        if isinstance(ctx, bridge.BridgeExtContext):
            return await ctx.message.add_reaction("✅")

    @bridge.bridge_command()
    async def spotify(self, ctx, url: str, silent: bool = None):
        print(
            f"@{ctx.author.name}#{ctx.author.discriminator} played a Spotify Playlist"
        )
        """
        Plays a Spotify Playlist
        """
        if not ctx.voice_state.voice:
            await ctx.invoke(self.summon)
        await ctx.defer()
        if re.match(
            r"https?://open\.spotify\.com/(playlist|album)/(?P<id>[^/?&#]+)", url
        ):
            await ctx.respond(
                "Please wait, converting your playlist. This could take a while!"
            )
            try:
                if re.match(r"https?://open\.spotify\.com/album/(?P<id>[^/?&#]+)", url):
                    track_list = (
                        await spotify_yt_bridge.async_spotify_album_to_track_names(
                            url, self.client.loop
                        )
                    )
                elif re.match(
                    r"https?://open\.spotify\.com/playlist/(?P<id>[^/?&#]+)", url
                ):
                    track_list = (
                        await spotify_yt_bridge.async_spotify_playlist_to_track_list(
                            url, self.client.loop
                        )
                    )
            except SpotifyException as e:
                await ctx.respond(f"Something funky happened: {e}")
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
                        await ctx.respond(f"Something funky happened. Stopping")
                        break
                    else:
                        if not silent:
                            await ctx.invoke(
                                self.play,
                                url=track_link,
                                silent_mesg=True,
                                isurl=True,
                            )
                        else:
                            await ctx.invoke(self.play, url=track_link, hidden=True)
                        await asyncio.sleep(2)

                await ctx.invoke(self.queue)
                await ctx.respond(
                    "Done! Tip: You can also use `exportqueue` to get the queue exported and use it with other bots!"
                )
        elif re.match(r"https?://open\.spotify\.com/track/(?P<id>[^/?&#]+)", url):
            yt_url = await spotify_yt_bridge.async_single_spotify_track_to_yt(
                url, loop=self.client.loop
            )
            return await ctx.invoke(
                self.play, url=yt_url, silent_mesg=False, isurl=True
            )

    @bridge.bridge_command()
    async def exportqueue(self, ctx: bridge.BridgeContext):
        """
        Export the current queue to file
        """
        await ctx.defer()
        with io.StringIO() as tmp_queue:
            for i, item in enumerate(ctx.voice_state.play_queue):
                tmp_queue.write(
                    f"{i+1}. {item.source.webpage} - {item.source.title} - {item.source.uploader}\n"
                )
            tmp_queue.seek(0)
            file = discord.File(tmp_queue, filename=f"queue-{ctx.guild}.txt")
            await ctx.respond("Here's the current queue!", file=file)

    @play.before_invoke
    async def ensure_voice(self, ctx):
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.respond("You are not connected to any voice channel.")
            raise bridge.bridge_commandError(
                "User is not connected to any voice channel."
            )

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                await ctx.respond("I am already in another channel")
                raise bridge.bridge_commandError("Bot is already in a voice channel.")

    @tasks.loop(seconds=180.0)
    async def check_alone(self):
        for client in self.client.voice_clients:
            if client.channel.members.__len__() == 1:
                await client.disconnect()


def setup(client: commands.Bot):
    client.add_cog(Music(client))
