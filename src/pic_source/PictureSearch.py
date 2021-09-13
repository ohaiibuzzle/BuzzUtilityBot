import re
from discord.ext import commands
import discord
from .safebooru import safebooru_random_img
from .zerochan import search_zerochan
from .pixiv import construct_pixiv_embed, get_image_by_id
from .danbooru import search_danbooru
import aioredis, asyncio

class PictureSearch(commands.Cog, name='Random image finder'):
    def __init__(self, client):
        self.client = client
        self.redis_pool = aioredis.from_url('redis://localhost', decode_responses=True)

    def cog_command_error(self, ctx, error):
        if error is AttributeError or error is commands.errors.MissingRequiredArgument:
            return ctx.send(f"There was an error processing your request (Perhaps checks your command?) \n Details:{error}")
        else:
            return ctx.send(f"There was an error processing your request \nDetails: {error}")
    
    @commands.command(brief='Random image from SafeBooru',
                      description='Look for a random image on SafeBooru, input can be any of SafeBooru\'s tag query\n\
                          Combine tags using "+"',
                          aliases=['sbr'])
    async def sbrandom(self, ctx, *, tags):
        print ('@' + ctx.message.author.name + '#' + ctx.message.author.discriminator + ' wants something random (SafeBooru)!')
        async with ctx.channel.typing():
            try:
                target = await safebooru_random_img(tags.split('+'), ctx.channel)
            except ConnectionError:
                await ctx.send("Buzzle's Internet broke :(\n(Try again in a few minutes, server is under high load)")
            else:
                if target:
                    await ctx.send(embed=target)
                    try:
                        await self.redis_pool.set(f'{ctx.channel.id}:{ctx.author.id}', f'SAFEBOORU {tags}', ex=15)
                    except:
                        msg = await ctx.send("Buzzle forgot to start Redis, so I won't remember your command :(")
                        await asyncio.sleep(5)
                        await msg.delete()
                else:
                    await ctx.send("Your search returned no result :(")           
    
    @commands.command(brief='Random image from ZeroChan',
                      description='Look for a random image on ZeroChan, input can be any of ZeroChan\'s tag query\n\
                          Combine tags using "+"',
                          aliases=['zcr'])
    async def zcrandom(self, ctx, *, tags):
        async with ctx.channel.typing():
            print ('@' + ctx.message.author.name + '#' + ctx.message.author.discriminator + ' wants something random (zerochan)!')
            tags = tags.replace('+', ',')
            try:
                res = await self.construct_zerochan_embed(ctx.channel, tags)
            except TypeError as e:
                print(e)
                await ctx.send('Your search string was too wide, or it included NSFW tags.\nNarrow the query to try again')
                return
            except ConnectionError:
                await ctx.send("Buzzle's Internet broke :(\n(Try again in a few minutes, server is under high load)")
            else:
                if res != None:
                    await ctx.send(embed=res)
                    try:
                        await self.redis_pool.set(f'{ctx.channel.id}:{ctx.author.id}', f'ZEROCHAN {tags}', ex=15)
                    except:
                        msg = await ctx.send("Buzzle forgot to start Redis, so I won't remember your command :(")
                        await asyncio.sleep(5)
                        await msg.delete()
                else:
                    await ctx.send("Sorry, I can't find you anything :( \nEither check your search, or Buzzle banned a tag in the result")
                
    @commands.command(brief='Look for a random image on Pixiv',
                      description='Look for a random image on Pixiv',
                      aliases=['pxr'])
    async def pixivrandom(self, ctx, *, tags):
        async with ctx.channel.typing():
            print ('@' + ctx.message.author.name + '#' + ctx.message.author.discriminator + ' wants something random (Pixiv)!')
            try:
                target, file = await construct_pixiv_embed(tags, ctx.channel)
            except ConnectionError:
                await ctx.send("Buzzle's Internet broke :(\n(Try again in a few minutes, server is under high load)")
            except ValueError:
                await ctx.send("Nothing found :(\nCheck your query")
            else:
                if target:
                    await ctx.send(embed=target, file=file)
                    try:
                        await self.redis_pool.set(f'{ctx.channel.id}:{ctx.author.id}', f'PIXIV {tags}', ex=15)
                    except:
                        msg = await ctx.send("Buzzle forgot to start Redis, so I won't remember your command :(")
                        await asyncio.sleep(5)
                        await msg.delete()
                else:
                    await ctx.send("Your search returned no result :(")
    
    @commands.command(brief='Display a Pixiv post in bot\'s format',
                      aliases=['pxs'])
    async def pixivshow(self, ctx, *, url):
        async with ctx.channel.typing():
            print ('@' + ctx.message.author.name + '#' + ctx.message.author.discriminator + ' wants to display Pixiv art!')
            #print(args[0])
            illust_id = re.findall(r'\d+', url[0])[0]
            try:
                target, file = await get_image_by_id(illust_id)
            except ConnectionError:
                await ctx.send("Buzzle's Internet broke :(\n(Try again in a few minutes, server is under high load)")
            except ValueError:
                await ctx.send("Nothing found :(\nCheck your query")
            else:
                if target:
                    await ctx.send(embed=target, file=file)
                else:
                    await ctx.send("Your search returned no result :(") 
        pass

    @commands.command(brief="Danbooru (NSFW) search",
                        description="Search for a random image on Danbooru.", aliases=['dbr'])
    async def danboorurandom(self, ctx: commands.Context, *, tags):
        async with ctx.channel.typing():
            print ('@' + ctx.message.author.name + '#' + ctx.message.author.discriminator + ' wants to search danbooru!')
            try:
                if not ctx.channel.is_nsfw():
                    await ctx.send("This command cannot be ran on channels that aren't marked NSFW!")
                    return
            except AttributeError:
                await ctx.send("This command cannot be ran on channels that aren't marked NSFW!")
                return
            try:
                embed = await PictureSearch.construct_danbooru_embed(tags)
            except ConnectionError:
                await ctx.send("Buzzle's Internet broke :(\n(Try again in a few minutes, server is under high load)")
            else:
                await ctx.send(embed=embed)
                try:
                    await self.redis_pool.set(f'{ctx.channel.id}:{ctx.author.id}', f'DANBOORU {tags}', ex=15)
                except:
                    msg = await ctx.send("Buzzle forgot to start Redis, so I won't remember your command :(")
                    await asyncio.sleep(5)
                    await msg.delete()
            
    @commands.command(brief='Execute the last command, again!',
                        description='Run the last command you executed, timeout is 10s\n\
                            Only some commands are supported.')
    async def more(self, ctx:commands.Context):
        last_exec = await self.redis_pool.get(f'{ctx.channel.id}:{ctx.author.id}')
        if last_exec is None:
            await ctx.send("I can't remember what you were doing~~")
            return
        last_exec = str(last_exec)
        if last_exec.startswith('ZEROCHAN'):
            await self.zcrandom(ctx, tags=last_exec[9:])
        elif last_exec.startswith('SAFEBOORU'):
            await self.sbrandom(ctx, tags=last_exec[10:])
        elif last_exec.startswith('PIXIV'):
            await self.pixivrandom(ctx, tags=last_exec[6:])
        elif last_exec.startswith('DANBOORU'):
            await self.danboorurandom(ctx, tags=last_exec[9:])

    @staticmethod
    async def construct_zerochan_embed(ch, query: str) -> discord.Embed:
        """Make a Zerochan embed 

        Args:
            ch (discord.Channel): A Discord channel (to check whether it is NSFW)
            query (str): The query

        Returns:
            discord.Embed: The embed with the picture
        """
        if ch.type is not discord.ChannelType.private:
            res = await search_zerochan(ch.is_nsfw(), query)
        else: 
            res = await search_zerochan(True, query)
        if res == None:
            return None
        else:
            embed = discord.Embed(title=res['title'])
            embed.url = res['link']
            embed.set_image(url=res['content'])
            
            embed.add_field(
                name = 'Source',
                value = embed.url,
                inline= False
            )
            embed.add_field(
                name = 'Tags',
                value = '```\n' + res['keywords'][:1018] + '\n```',
                inline = False
            )
            return embed

    @staticmethod
    async def construct_danbooru_embed(query:str) -> discord.Embed:
        """Make a Danbooru embed with a random image from query

        Args:
            query (str): The query to look for

        Returns:
            discord.Embed: The embed
        """
        res = await search_danbooru(query)
        embed = discord.Embed(title=query)
        embed.url = f"https://danbooru.donmai.us/posts/{res['id']}"
        embed.set_image(url=res['large_file_url'])
        
        embed.add_field(
            name = 'Source',
            value = res['source'],
            inline= False
        )
        embed.add_field(
            name = 'Tags',
            value = '```\n' + res['tag_string'][:1018] + '\n```',
            inline = False
        )
        return embed

    
def setup(client):
    client.add_cog(PictureSearch(client))