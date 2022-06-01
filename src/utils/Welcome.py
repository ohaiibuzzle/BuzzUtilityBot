import io
import sqlite3

import aiohttp
import aiosqlite
import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageOps


class WelcomeMessage(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.db = sqlite3.connect("runtime/server_data.db")
        self.curr = self.db.cursor()
        self.curr.execute(
            """CREATE TABLE IF NOT EXISTS WelcomeMessage ([GuildID] INTEGER PRIMARY KEY, [ChannelID] Integer)"""
        )

    @commands.Cog.listener()
    async def on_member_join(self, member):
        async with aiosqlite.connect("runtime/server_data.db") as db:
            async with db.cursor() as curr:
                server = await curr.execute(
                    """SELECT GuildID, ChannelID FROM WelcomeMessage WHERE GuildID=:guildid""",
                    {"guildid": member.guild.id},
                )
                server_info = await server.fetchone()
                if server_info != None:
                    channel = discord.utils.get(
                        member.guild.channels, id=server_info[1]
                    )
                    embed, file = await WelcomeMessage.construct_welcome_embed(member)
                    await channel.send(file=file, embed=embed)
                pass

    @commands.command(brief="Use this channel for welcome messages")
    @commands.has_permissions(administrator=True)
    async def setupWelcome(self, ctx):
        if ctx.message.channel.type is discord.ChannelType.text:
            self.curr.execute(
                """DELETE FROM WelcomeMessage WHERE GuildID = :guildid""",
                {"guildid": ctx.guild.id},
            )
            self.curr.execute(
                """INSERT INTO WelcomeMessage (GuildID, ChannelID)
                        VALUES (:guildid, :channelid)""",
                {"guildid": ctx.guild.id, "channelid": ctx.message.channel.id},
            )
            self.db.commit()
            await ctx.send(
                "Success. This channel will now be used for welcome messages!"
            )
        else:
            await ctx.send("Cannot use this channel :<")

    @commands.command(brief="Unset this channel for welcome messages")
    @commands.has_permissions(administrator=True)
    async def clearWelcome(self, ctx):
        self.curr.execute(
            """DELETE FROM WelcomeMessage WHERE GuildID = :guildid""",
            {"guildid": ctx.guild.id},
        )
        self.db.commit()
        await ctx.send("Success. Removed the welcome messages from this channel!")

    @staticmethod
    async def construct_welcome_embed(member: discord.Member):
        """
        Creates a welcome embed for a member
        :param member: A Discord Member
        """
        AVATAR_SIZE = 192
        server_msg = "Welcome to " + member.guild.name + "!"
        member_msg = "@{}#{}".format(member.name, member.discriminator)

        background = Image.open("runtime/assets/bg.png", "r").convert("RGBA")
        bg_w, bg_h = background.size

        timeout = aiohttp.ClientTimeout(total=15)
        # print(member.avatar_url)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            raw_icon = await session.get(str(member.avatar_url))
            buffer = io.BytesIO(await raw_icon.read())
            buffer.seek(0)

            icon = Image.open(buffer, "r").convert("RGBA")
            icon = icon.resize((AVATAR_SIZE, AVATAR_SIZE))
            icon_w, icon_h = icon.size

            text_font = ImageFont.truetype("runtime/assets/font.ttf", 40)

            # mask pfp ->
            mask = Image.new("L", icon.size, 255)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0) + icon.size, fill=0)

            icon = ImageOps.fit(icon, mask.size, centering=(0.5, 0.5))
            icon.paste(0, (0, 0), mask)
            offset = ((bg_w - icon_w) // 2, (bg_h - icon_h) // 2)

            blurple = Image.new("RGBA", (background.size), (54, 57, 63, 255))
            # blurple.paste(icon, offset)
            blurple.paste(background, (0, 0), background)
            draw = ImageDraw.Draw(blurple)

            draw.ellipse(
                (
                    offset[0] - 2,
                    offset[1] - 2,
                    (offset[0]) + icon_w + 2,
                    (offset[1]) + icon_h + 2,
                ),
                fill="#36393f",
                outline="#ffffff",
                width=2,
            )
            blurple.paste(icon, offset, icon)

            text_layer = Image.new("RGBA", (background.size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(text_layer)

            text_w, text_h = draw.textsize(member_msg, font=text_font)
            welc_w, welc_h = draw.textsize(server_msg, font=text_font)

            welc_layer = Image.new("RGBA", (welc_w, welc_h), (0, 0, 0, 200))
            draw = ImageDraw.Draw(welc_layer)
            draw.text((0, 0), server_msg, fill="white", font=text_font)

            username_layer = Image.new("RGBA", (text_w, text_h), (0, 0, 0, 200))
            draw = ImageDraw.Draw(username_layer)
            draw.text((0, 0), member_msg, fill="white", font=text_font)

            text_layer.paste(
                username_layer,
                ((bg_w - text_w) // 2, bg_h - 10 - text_h),
                username_layer,
            )
            text_layer.paste(welc_layer, ((bg_w - welc_w) // 2, 10), welc_layer)

            final_img = Image.alpha_composite(blurple, text_layer)

            embed = discord.Embed(title="Ding dong! 🔔")

            embed.add_field(name="Member", value=member_msg, inline=False)

            embed.add_field(
                name="Account Creation Date", value=member.created_at, inline=False
            )

            embed.add_field(name="Enjoy your stay!", value="👋", inline=False)

            file = None
            with io.BytesIO() as image_bin:
                final_img.save(image_bin, format="PNG")
                image_bin.seek(0)
                file = discord.File(image_bin, filename="welcome.png")
                embed.set_image(url="attachment://welcome.png")

            return embed, file


def setup(client):
    client.add_cog(WelcomeMessage(client))
