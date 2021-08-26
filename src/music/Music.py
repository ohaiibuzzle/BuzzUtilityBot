import asyncio
from logging import exception
import discord
from discord import embeds
from discord.ext import commands, tasks
from music import youtube_dl_source, voice_state_manager
import math

class Music(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.voice_states = {}
        #self.check_alone.start() #pylint: disable=no-member

    def get_voice_state(self, ctx: commands.Context) -> voice_state_manager.VoiceState:
        state = self.voice_states.get(ctx.guild.id)
        if not state:
            state = voice_state_manager.VoiceState(self.client, ctx)
            self.voice_states[ctx.guild.id] = state

        return state
    
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
        if not ctx.author.voice:
            await ctx.send("Hmm? What should I join here?")

        destination = ctx.author.voice.channel

        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return

        ctx.voice_state.voice = await destination.connect()
        

    @commands.command()
    async def disconnect(self, ctx: commands.Context):
        if not ctx.voice_state.voice:
            return await ctx.send("Not currently connected to any channel!")
        else:
            await ctx.voice_state.stop()
            del self.voice_states[ctx.guild.id]

    @commands.command()
    async def play(self, ctx: commands.Context, *, url):
        if not ctx.voice_state.voice:
            await ctx.invoke(self.summon)
        async with ctx.typing():
            try:
                source = await youtube_dl_source.YouTubeDLSingleSource.from_url(url, loop=self.client.loop, stream=True, requester=ctx.author)
            except Exception as e:
                await ctx.send(f"Something funky happened: {e}")
            else:
                item = voice_state_manager.PlaybackItem(source=source)

                await ctx.voice_state.play_queue.put(item)
                await ctx.send(f"Added {source.title} - {source.uploader} to the queue!")
    
    @commands.command()
    async def pause(self, ctx: commands.Context):
        if not ctx.voice_state.is_playing and ctx.voice_state.voice.is_playing():
            ctx.voice_state.voice.pause()
            await ctx.message.add_reaction('🆗')

    @commands.command()
    async def resume(self, ctx: commands.Context):
        if not ctx.voice_state.is_playing and ctx.voice_state.voice.is_playing():
            ctx.voice_state.voice.resume()
            await ctx.message.add_reaction('🆗')

    @commands.command()
    async def volume(self, ctx: commands.Context, volume: float):
        if not ctx.voice_client:
            return await ctx.send("Hmm? Do I even have a voice?")
        elif 0 > volume > 100:
            return await ctx.send("What kind of silly volume is that???")
        else:
            ctx.voice_client.source.volume = volume / 100
            return await ctx.send(f"Done! The volume is now {volume}%")

    @commands.command()
    async def showqueue(self, ctx, *, page: int = 1):
        async with ctx.typing():
            if len(ctx.voice_state.play_queue) == 0:
                await ctx.send("Oh no queue is empty :(")
            
            else:
                pages = math.ceil(len(ctx.voice_state.play_queue) / 10)
                first_item = (page - 1) * 10

                queue_str = ""
                for number, entry in enumerate(ctx.voice_state.play_queue[first_item:first_item+10], start=first_item):
                    queue_str += f"**{number}**. {entry.source.title} - {entry.source.uploader}"

                this_embed = discord.Embed(title=f"Queue page {page}/{pages}",
                description = queue_str)

                await ctx.send(embed=this_embed)

    @commands.command()
    async def search(self, ctx: commands.Context, *, query):
        def check_requester_msg(message: discord.Message):
            return message.author == ctx.author
        async with ctx.typing():
            result = await youtube_dl_source.YouTubeDLSingleSource.list_from_query(query, loop=self.client.loop)
            result = result['entries']
            this_embed = discord.Embed(title=f"Search result for {query}")
            res_str = ""
            for number, data in enumerate(result):
                res_str += f"**{number+1}**. {data['title']} - {data['uploader']}" + '\n'
            this_embed.description = res_str
            this_embed.color = int(0x0062ff)
            search_res = await ctx.send(embed=this_embed)
            try:
                msg = await self.client.wait_for('message', timeout=15, check=check_requester_msg)
            except asyncio.TimeoutError:
                await search_res.delete()
                return await ctx.send("Timeout!")
            else:
                if msg.content.isdigit():
                    await search_res.delete()
                    return await ctx.invoke(self.play, url=result[int(msg.content)-1]['webpage_url'])
                else:
                    return await ctx.send("That was not a valid selection!")

    @commands.command(alias=['np'])
    async def nowplaying(self, ctx):
        await ctx.send(f"Currently playing {ctx.voice_state.current}")

    @play.before_invoke
    async def ensure_voice(self, ctx):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError('You are not connected to any voice channel.')

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CommandError('Bot is already in a voice channel.')

    @tasks.loop(seconds=180.0)
    async def check_alone(self):
        for client in self.client.voice_clients:
            if client.channel.members.__len__() == 1:
                await client.disconnect()

def setup(client: commands.Bot):
    client.add_cog(Music(client))