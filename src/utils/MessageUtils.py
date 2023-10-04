from discord.ext import commands, bridge
import discord
import asyncio
import logging


class MessageUtils(commands.Cog, name="Message Utilities"):
    def __init__(self, client):
        self.client = client

    def cog_command_error(self, ctx, error):
        if error is AttributeError or error is commands.errors.MissingRequiredArgument:
            return ctx.send(
                f"There was an error processing your request (Perhaps checks your command?) \n Details:{error}"
            )
        else:
            logging.critical(error)
            return ctx.send(f"There was an error processing your request")

    @bridge.bridge_command(
        brief="Save a message to your DM",
    )
    async def savethis(self, ctx: bridge.BridgeContext):
        """
        Save whatever message you mention when this command is ran.

        If no message is mentioned, save the last message that has an embed in it
        """
        logging.info("@" + ctx.author.name + "#" + ctx.author.discriminator + " try to save!")
        if ctx.message:
            if ctx.message.reference:
                if ctx.message.reference.resolved != None:
                    search_msg = ctx.message.reference.resolved
                    await ctx.message.author.send(
                        embed=self.construct_save_embed_img(search_msg)
                    )
                    if isinstance(ctx, bridge.BridgeApplicationContext):
                        await asyncio.sleep(5)
                        await ctx.message.delete()

        else:
            messages = await ctx.channel.history(limit=20).flatten()
            for mesg in messages:
                if mesg.attachments.__len__() > 0 or mesg.embeds.__len__() > 0:
                    await ctx.author.send(embed=self.construct_save_embed_img(mesg))
                    if isinstance(ctx, bridge.BridgeExtContext):
                        await asyncio.sleep(5)
                        await ctx.message.delete()
                    elif isinstance(ctx, bridge.BridgeApplicationContext):
                        resp = await ctx.reply("Message saved to your DMs")
                        await asyncio.sleep(5)
                        await resp.delete()
                    break

    @bridge.bridge_command(
        brief="Save n messages to your DM",
    )
    async def saveall(self, ctx, amount: int):
        """
        Save up to n messages in the current channel
        """
        if not amount.isnumeric():
            alert = await ctx.respond("You silly, that is not a number!!")
            await asyncio.sleep(3)
            await alert.delete()
            return
        amount = int(amount)
        if amount > 10:
            alert = await ctx.respond(
                "You can only save up to 10 messages back in time!"
            )
            await asyncio.sleep(3)
            await alert.delete()
            return
        messages = await ctx.channel.history(limit=20).flatten()
        for mesg in messages:
            if (
                mesg.attachments.__len__() > 0 or mesg.embeds.__len__() > 0
            ) and amount > 0:
                await ctx.author.send(embed=self.construct_save_embed_img(mesg))
                amount = amount - 1

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.client.user:
            return

        if message.content.startswith(". so I can save"):
            messages = await message.channel.history(limit=10).flatten()
            for mesg in messages:
                if mesg.attachments.__len__() > 0 or mesg.embeds.__len__() > 0:
                    await message.author.send(embed=self.construct_save_embed_img(mesg))
                    break

    @commands.command(
        brief="Delete the last message the bot send",
    )
    async def oofie(self, ctx):
        """
        Use this command to delete the bot's last message.
        Used in case things went wrong
        """
        logging.info(
            "Uh oh, @"
            + ctx.message.author.name
            + "#"
            + ctx.message.author.discriminator
            + " told us we messed up!"
        )
        await ctx.message.delete()
        messages = await ctx.channel.history(limit=10).flatten()
        for mesg in messages:
            if mesg.author == self.client.user:
                await mesg.delete()
                break

    @commands.command(hidden=True)
    @commands.is_owner()
    async def sudo(self, ctx, *args):
        async with ctx.channel.typing():
            phrases = " ".join(args)
            await ctx.message.delete()
            await ctx.send(phrases)

    @staticmethod
    def construct_save_embed_img(message: discord.Message) -> discord.Embed:
        """Creates an embed for the save

        Args:
            message (discord.Message): A Discord message to save

        Returns:
            discord.Embed: The embed
        """
        IMAGE_FORMAT = [".jpg", ".JPG", ".png", ".PNG", ".gif"]

        embed = discord.Embed(title="Saved!")

        embed.add_field(
            name="From",
            value="@"
            + message.author.name
            + "#"
            + message.author.discriminator
            + " in #"
            + message.channel.name
            + " on "
            + message.channel.guild.name,
            inline=False,
        )

        embed.add_field(name="Location", value=message.jump_url, inline=False)
        if message.content != "":
            embed.add_field(name="Content", value=message.content, inline=False)

        if message.embeds.__len__() > 0:
            if message.embeds[0].image:
                embed.set_image(url=message.embeds[0].image.proxy_url)
            elif message.embeds[0].video:
                embed.set_image(url=message.embeds[0].video.url)
            elif (
                message.embeds[0].url.startswith(
                    "https://media.discordapp.net/attachments"
                )
            ) and (message.embeds[0].url[-4:] in IMAGE_FORMAT):
                embed.set_image(url=message.embeds[0].url)
            else:
                try:
                    embedded_contents = ""
                    for _ in message.embeds:
                        embedded_contents += _.url
                        embedded_contents += "\n"
                    if embedded_contents != "":
                        embed.add_field(
                            name="Embedded Content",
                            value=embedded_contents,
                            inline=False,
                        )
                except UnboundLocalError:
                    pass

        if message.attachments.__len__() > 0:
            att_contents = ""
            for _ in message.attachments:
                if _.content_type.startswith("image"):
                    embed.set_image(url=_.url)
                else:
                    att_contents += _.url
                    att_contents += "\n"
            if att_contents != "":
                embed.add_field(
                    name="Attached Content", value=att_contents, inline=False
                )
        return embed


def setup(client):
    client.add_cog(MessageUtils(client))
