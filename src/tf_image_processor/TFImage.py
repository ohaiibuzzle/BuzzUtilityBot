from discord.ext import commands
from tf_image_processor.embeds import tensorflow_embed
from PIL import UnidentifiedImageError

class TFImage(commands.Cog, name="AI-based image rating"):
    def __init__(self, client):
        self.client = client
        
    @commands.command(brief="Ask Ai-chan to comment about an image",
                      description="Ask Ai-chan, Buzzle's highly trained professional to comment on your image!\n\
                          Mention an image to use!") 
    async def police(self, ctx):
        print('@' + ctx.message.author.name + '#' + ctx.message.author.discriminator + ' wants to rate an image!')
        async with ctx.channel.typing():
            if (ctx.message.reference):
                if (ctx.message.reference.resolved != None):
                    search_msg = ctx.message.reference.resolved
                    if (search_msg.embeds.__len__() > 0):
                        for attachment in search_msg.embeds:
                            try:
                                res = tensorflow_embed(attachment.url)
                                await ctx.send(embed=res)
                            except UnidentifiedImageError:
                                await ctx.send("Hey, that is not an image")                                
                            pass
                    elif (search_msg.attachments.__len__() > 0):
                        for attachment in search_msg.attachments:
                            if attachment.content_type.startswith('image'):
                                try:
                                    res = tensorflow_embed(attachment.url)
                                    await ctx.send(embed=res)
                                except UnidentifiedImageError:
                                    await ctx.send("Hey, that is not an image")
                                pass                                
            else:
                await ctx.send("Please mention a message containing pasta!")