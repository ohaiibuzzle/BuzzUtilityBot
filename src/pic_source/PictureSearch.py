from discord.ext import commands
from pic_source.safebooru import safebooru_random_img
from pic_source.zerochan import construct_zerochan_embed

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
            tags = tags.replace('+', ',')
            target = safebooru_random_img(tags.split('+'), ctx.channel)
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
            print ('@' + ctx.message.author.name + '#' + ctx.message.author.discriminator + ' wants something random(zerochan)!')
            tags = ' '.join(args).strip()
            tags = tags.replace('+', ',')
            try:
                res = construct_zerochan_embed(ctx.channel, tags)
            except TypeError:
                await ctx.send('Your search string was too wide, or it included NSFW tags.\nNarrow the query to try again')
                return
            if res != None:
                await ctx.send(embed=res)
            else:
                await ctx.send("Sorry, I can't find you anything :( \nEither check your search, or Buzzle banned a tag in the result")