from discord.ext import commands, bridge
from .saucenao import find_sauce
from .iqdb import get_sauce
from utils import embed_finder
import discord
import configparser
from pysaucenao.saucenao import SauceNaoResults

config = configparser.ConfigParser()
config.read("runtime/config.cfg")


class SauceFinder(commands.Cog, name="Picture Sauce Finding"):
    def __init__(self, client):
        self.client = client

    #    def cog_command_error(self, ctx, error):
    #        if error is AttributeError or error is commands.errors.MissingRequiredArgument:
    #            return ctx.send(
    #                f"There was an error processing your request (Perhaps checks your command?) \n Details:{error}"
    #            )
    #        else:
    #            return ctx.send(
    #                f"There was an error processing your request \nDetails: {error}"
    #            )

    @bridge.bridge_command(
        brief="Search for picture on SauceNAO, using Pixiv Database",
    )
    async def sauceplz(self, ctx):
        """
        Search for a picture in an embed or attachment, using the SauceNAO engine.

        Pixiv only as of now. Twitter is scary
        """
        print(
            "@"
            + ctx.author.name
            + "#"
            + ctx.author.discriminator
            + " try to find sauce!"
        )
        await ctx.defer()
        msg = await embed_finder.find_message_with_embeds(ctx, 10)
        if msg is not None:
            if msg.embeds.__len__() > 0:
                for embed in msg.embeds:
                    if embed.image.url is not discord.Embed.Empty:
                        res = await find_sauce(embed.image.url)
                        if res is not None:
                            return await ctx.send(embed=res)
                        else:
                            return await ctx.send("No sauce found")
                    elif embed.thumbnail.url is not discord.Embed.Empty:
                        res = await find_sauce(embed.thumbnail.url)
                        if res is not None:
                            return await ctx.send(embed=res)
                        else:
                            return await ctx.send("No sauce found")
                    elif embed.url is not discord.Embed.Empty:
                        res = await find_sauce(embed.url)
                        if res is not None:
                            return await ctx.send(embed=res)
                        else:
                            return await ctx.send("No sauce found")
            elif msg.attachments.__len__() > 0:
                for attachment in msg.attachments:
                    if attachment.content_type.startswith("image"):
                        res = await find_sauce(attachment.url)
                        if res is not None:
                            return await ctx.send(embed=res)
                        else:
                            return await ctx.send("No sauce found")
            else:
                return await ctx.send("No sauce found")
        else:
            return await ctx.send("Please mention a message containing pasta!")

    @bridge.bridge_command(
        brief="Search for picture on IQDB",
    )
    async def iqdb(self, ctx):
        """
        Search for a picture in an embed or attachment, using the IQDB engine.

        Slower than SauceNAO, but has a higher search limit
        """
        print(
            "@"
            + ctx.author.name
            + "#"
            + ctx.author.discriminator
            + " try to find sauce on IQDB!"
        )
        await ctx.defer()
        msg = await embed_finder.find_message_with_embeds(ctx, 10)
        if msg is not None:
            if msg.embeds.__len__() > 0:
                for embed in msg.embeds:
                    if embed.image.url is not discord.Embed.Empty:
                        res = await get_sauce(embed.image.url)
                        if res is not None:
                            return await ctx.send(embed=res)
                        else:
                            return await ctx.send("No sauce found")
                    elif embed.thumbnail.url is not discord.Embed.Empty:
                        res = await get_sauce(embed.thumbnail.url)
                        if res is not None:
                            return await ctx.send(embed=res)
                        else:
                            return await ctx.send("No sauce found")
                    elif embed.url is not discord.Embed.Empty:
                        res = await get_sauce(embed.url)
                        if res is not None:
                            return await ctx.send(embed=res)
                        else:
                            return await ctx.send("No sauce found")
            elif msg.attachments.__len__() > 0:
                for attachment in msg.attachments:
                    if attachment.content_type.startswith("image"):
                        res = await get_sauce(attachment.url)
                        if res is not None:
                            return await ctx.send(embed=res)
                        else:
                            return await ctx.send("No sauce found")
            else:
                return await ctx.send("No sauce found")

    @staticmethod
    async def construct_saucenao_embed_pixiv(attachment: SauceNaoResults):
        embed = discord.Embed(title="Sauce found!")
        embed.add_field(
            name="Similarity", value=f"{attachment.similarity}%", inline=False
        )
        if attachment.title:
            embed.add_field(name="Title", value=attachment.title, inline=False)
        if attachment.author_name:
            embed.add_field(
                name="Author",
                value=f"{attachment.author_name} - {attachment.author_url}",
                inline=False,
            )
        if attachment.source_url:
            embed.add_field(name="Source", value=attachment.source_url, inline=False)
        if attachment.index_name:
            embed.add_field(name="Index", value=attachment.index_name, inline=False)
        embed.set_thumbnail(url=attachment.thumbnail)
        if attachment.url:
            embed.url = attachment.url
        if attachment.urls:
            embed.url = attachment.urls[0]
        return embed

    @staticmethod
    async def construct_iqdb_embed(url: str):
        data = await get_sauce(url)
        if not data:
            return None
        embed = discord.Embed(title="Sauce found!")
        embed.url = data["link"]
        embed.set_thumbnail(url=data["thumbnail"])
        embed.add_field(name="Location", value=data["link"], inline=False)

        embed.add_field(name="Alt Text", value=data["alt_text"], inline=False)
        return embed


def setup(client):
    client.add_cog(SauceFinder(client))
