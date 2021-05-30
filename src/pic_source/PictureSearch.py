import re
from discord.ext import commands
from .safebooru import safebooru_random_img
from .zerochan import construct_zerochan_embed
from .pixiv import construct_pixiv_embed, get_image_by_id
from requests.exceptions import ConnectionError

class PictureSearch(commands.Cog, name='Random image finder'):
    def __init__(self, client):
        self.client = client
    
    @commands.command(brief='Random image from SafeBooru',
                      description='Look for a random image on SafeBooru, input can be any of SafeBooru\'s tag query\n\
                          Combine tags using "+"',
                          aliases=['sbr'])
    async def sbrandom(self, ctx, *args):
        print ('@' + ctx.message.author.name + '#' + ctx.message.author.discriminator + ' wants something random (SafeBooru)!')
        async with ctx.channel.typing():
            tags = ' '.join(args)
            try:
                target = safebooru_random_img(tags.split('+'), ctx.channel)
            except ConnectionError:
                await ctx.send("Buzzle's Internet broke :(\n(Try again in a few minutes, server is under high load)")
            else:
                if target:
                    await ctx.send(embed=target)
                else:
                    await ctx.send("Your search returned no result :(")           
    
    @commands.command(brief='Random image from ZeroChan',
                      description='Look for a random image on ZeroChan, input can be any of ZeroChan\'s tag query\n\
                          Combine tags using "+"',
                          aliases=['zcr'])
    async def zcrandom(self, ctx, *args):
        async with ctx.channel.typing():
            print ('@' + ctx.message.author.name + '#' + ctx.message.author.discriminator + ' wants something random (zerochan)!')
            tags = ' '.join(args).strip()
            tags = tags.replace('+', ',')
            try:
                res = construct_zerochan_embed(ctx.channel, tags)
            except TypeError as e:
                print(e)
                await ctx.send('Your search string was too wide, or it included NSFW tags.\nNarrow the query to try again')
                return
            except ConnectionError:
                await ctx.send("Buzzle's Internet broke :(\n(Try again in a few minutes, server is under high load)")
            else:
                if res != None:
                    await ctx.send(embed=res)
                else:
                    await ctx.send("Sorry, I can't find you anything :( \nEither check your search, or Buzzle banned a tag in the result")
                
    @commands.command(brief='Look for a random image on Pixiv',
                      description='Look for a random image on Pixiv',
                      aliases=['pxr'])
    async def pixivrandom(self, ctx, *args):
        async with ctx.channel.typing():
            print ('@' + ctx.message.author.name + '#' + ctx.message.author.discriminator + ' wants something random (Pixiv)!')
            tags = ' '.join(args).strip()
            try:
                target, file = construct_pixiv_embed(tags, ctx.channel)
            except ConnectionError:
                await ctx.send("Buzzle's Internet broke :(\n(Try again in a few minutes, server is under high load)")
            else:
                if target:
                    await ctx.send(embed=target, file=file)
                else:
                    await ctx.send("Your search returned no result :(")
    
    @commands.command(brief='Display a Pixiv post in bot\'s format',
                      aliases=['pxs'])
    async def pixivshow(self, ctx, *args):
        async with ctx.channel.typing():
            print ('@' + ctx.message.author.name + '#' + ctx.message.author.discriminator + ' wants to display Pixiv art!')
            #print(args[0])
            illust_id = re.findall(r'\d+', args[0])[0]
            try:
                target, file = get_image_by_id(illust_id)
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
    
def setup(client):
    client.add_cog(PictureSearch(client))