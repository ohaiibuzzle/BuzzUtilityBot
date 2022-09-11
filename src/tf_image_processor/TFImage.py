import discord
from discord.ext import commands, bridge
from PIL import UnidentifiedImageError

from . import async_process_url
from utils import embed_finder


class TFImage(commands.Cog, name="AI-based image rating"):
    def __init__(self, client):
        self.client = client

    @bridge.bridge_command(brief="Ask Ai-chan to comment about an image")
    async def police(self, ctx: bridge.BridgeContext):
        """
        Ask Ai-chan, Buzzle's highly trained professional to comment on your image!

        Mention an image to use!
        """
        print(
            "@"
            + ctx.author.name
            + "#"
            + ctx.author.discriminator
            + " wants to rate an image!"
        )
        await ctx.defer()
        msg = await embed_finder.find_message_with_embeds(ctx, 10)
        if msg != None:
            if msg.embeds.__len__() > 0:
                for embed in msg.embeds:
                    if embed.image.url is not discord.Embed.Empty:
                        try:
                            res = await self.tensorflow_embed(embed.image.url)
                            return await ctx.respond(embed=res)
                        except UnidentifiedImageError:
                            await ctx.respond("Hey, that is not an image")
                    elif embed.thumbnail.url is not discord.Embed.Empty:
                        try:
                            res = await self.tensorflow_embed(embed.thumbnail.url)
                            return await ctx.respond(embed=res)
                        except UnidentifiedImageError:
                            await ctx.respond("Hey, that is not an image")
                    elif embed.url is not discord.Embed.Empty:
                        try:
                            res = await self.tensorflow_embed(embed.url)
                            return await ctx.respond(embed=res)
                        except UnidentifiedImageError:
                            await ctx.respond("Hey, that is not an image")
            elif msg.attachments.__len__() > 0:
                for attachment in msg.attachments:
                    if attachment.content_type.startswith("image"):
                        try:
                            res = await self.tensorflow_embed(attachment.url)
                            return await ctx.respond(embed=res)
                        except UnidentifiedImageError:
                            print(msg.attachments)
                            await ctx.respond("Hey, that is not an image")
            # Catch if we can't process it at all
            await ctx.respond("Hey, that is not an image")
        else:
            await ctx.respond("Hey, at least give me something to work with!")

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
    try:
        from .tf_process import async_process_url
    except (ValueError, ModuleNotFoundError) as e:
        print("Model Error: " + str(e))
        print("ML features will be disabled")
        return
    else:
        client.add_cog(TFImage(client))
