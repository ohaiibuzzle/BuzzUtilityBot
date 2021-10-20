from discord.ext import commands
import discord
from PIL import UnidentifiedImageError
from .tf_process import async_process_url


class TFImage(commands.Cog, name="AI-based image rating"):
    def __init__(self, client):
        self.client = client

    @commands.command(
        brief="Ask Ai-chan to comment about an image",
        description="Ask Ai-chan, Buzzle's highly trained professional to comment on your image!\n\
                          Mention an image to use!",
    )
    async def police(self, ctx):
        print(
            "@"
            + ctx.message.author.name
            + "#"
            + ctx.message.author.discriminator
            + " wants to rate an image!"
        )
        async with ctx.channel.typing():
            if ctx.message.reference:
                if ctx.message.reference.resolved != None:
                    search_msg = ctx.message.reference.resolved
                    if search_msg.embeds.__len__() > 0:
                        for attachment in search_msg.embeds:
                            try:
                                res = await self.tensorflow_embed(attachment.url)
                                await ctx.send(embed=res)
                            except UnidentifiedImageError:
                                await ctx.send("Hey, that is not an image")
                            pass
                    elif search_msg.attachments.__len__() > 0:
                        for attachment in search_msg.attachments:
                            if attachment.content_type.startswith("image"):
                                try:
                                    res = await self.tensorflow_embed(attachment.url)
                                    await ctx.send(embed=res)
                                except UnidentifiedImageError:
                                    await ctx.send("Hey, that is not an image")
                                pass
            else:
                await ctx.send("Hey, at least send me something! :(")

    @staticmethod
    async def tensorflow_embed(url: str) -> discord.Embed:
        """Creates an embed representing the TensorFlow result

        Args:
            url (str): The URL of an image

        Returns:
            discord.Embed: The embed describing the TensorFlow result
        """
        result = await async_process_url(url)
        embed = discord.Embed(title="Ai-chan reply!")

        embed.set_thumbnail(url=url)

        dict_sorted = {
            k: v
            for k, v in sorted(result.items(), key=lambda item: item[1], reverse=True)
        }

        for _ in dict_sorted:
            embed.add_field(
                name=_,
                value="```" + str(format(dict_sorted[_][0] * 100, ".2f")) + "%" + "```",
                inline=False,
            )
        embed.color = int(list(dict_sorted.values())[0][1])

        embed.set_footer(text="Powered by advanced Keyboard Cat technologies")
        return embed


def setup(client):
    client.add_cog(TFImage(client))
