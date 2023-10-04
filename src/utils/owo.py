import asyncio
import datetime
import io
import logging
import random
import re
import sqlite3

import aiohttp
import aiosqlite
import discord
from discord.ext import commands, bridge
from PIL import Image, ImageDraw, ImageFont, ImageOps

RT_DATABASE = "runtime/server_data.db"
AVATAR_SIZE = 192


class OwO(commands.Cog, name="Why? I don't even know why these exists!"):
    app_info = None

    def __init__(self, client: discord.ext.commands.Bot):
        self.client = client
        db = sqlite3.connect(
            RT_DATABASE, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        db.execute(
            """CREATE TABLE IF NOT EXISTS Marriage ([ID] INTEGER, [GuildID] INTEGER, 
        [FirstSide] INTEGER, [SecondSide] INTEGER, [StartDate] TIMESTAMP, PRIMARY KEY ([ID] AUTOINCREMENT))"""
        )

    @bridge.bridge_command(brief="Yowouwuw wowowst nyghtmawe, in a cowommand.")
    async def owo(self, ctx: commands.Context, *, words: str):
        """
        Simply terrifying.
        """
        if len(words) == 0:
            return
        else:
            await ctx.respond(OwO.owoify(" ".join(words)))

    @bridge.bridge_command(
        brief="Ships 🛳️",
        help="Ships two people together, syntax: ship @Someone and @Someone",
    )
    async def ship(self, ctx, first: discord.Member, second: discord.Member):
        """
        A shippy ship shipping ships
        """
        ctx.respond(
            f"Oh look {ctx.message.author.mention} ships {ctx.message.mentions[0]} and {ctx.message.mentions[1]} together \nAww... 🛳️"
        )

    @commands.command(
        brief="Marry 💍",
    )
    async def marry(self, ctx: commands.Context):
        """
        Take your ship to the next level. Mention someone to start
        """
        async with ctx.channel.typing():
            if self.app_info == None:
                self.app_info = await self.client.application_info()
            if len(ctx.message.mentions) != 1:
                await ctx.send("What are you trying to do...?")
                return
            else:

                def check_second_side(msg):
                    return (
                        msg.author.id == ctx.message.mentions[0].id
                        and msg.content == "Yes!"
                    )

                async with aiosqlite.connect(
                    RT_DATABASE,
                    detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
                ) as db:
                    async with db.execute(
                        """SELECT GuildID, FirstSide FROM Marriage WHERE `GuildID` = :guildID AND `SecondSide` = :author""",
                        {"guildID": ctx.guild.id, "author": ctx.message.author.id},
                    ) as rows:
                        this_row = await rows.fetchone()
                        if this_row:
                            logging.debug(this_row)
                            second_member = discord.utils.find(
                                lambda m: m.id == this_row[1], ctx.guild.members
                            )
                            await ctx.send(
                                f"You already have your soul attached to {second_member}. What are you doing?"
                            )
                            return

                    async with db.execute(
                        """SELECT GuildID, SecondSide FROM Marriage WHERE `GuildID` = :guildID AND `FirstSide` = :author""",
                        {"guildID": ctx.guild.id, "author": ctx.message.author.id},
                    ) as rows:
                        this_row = await rows.fetchone()
                        if this_row:
                            logging.debug(this_row)
                            second_member = discord.utils.find(
                                lambda m: m.id == this_row[1], ctx.guild.members
                            )
                            await ctx.send(
                                f"You already have your soul attached to {second_member}. What are you doing?"
                            )
                            return

                    async with db.execute(
                        """SELECT GuildID, FirstSide FROM Marriage WHERE GuildID = :guildID AND `SecondSide` = :target""",
                        {"guildID": ctx.guild.id, "target": ctx.message.mentions[0].id},
                    ) as rows:
                        this_row = await rows.fetchone()
                        if this_row:
                            logging.debug(this_row)
                            first_member = discord.utils.find(
                                lambda m: m.id == this_row[1], ctx.guild.members
                            )
                            await ctx.send(
                                f"Sorry, but their soul has already been attached to {first_member}. I am magic, but I can't do anything for you"
                            )
                            return

                    async with db.execute(
                        """SELECT GuildID, SecondSide FROM Marriage WHERE GuildID = :guildID AND `FirstSide` = :target""",
                        {"guildID": ctx.guild.id, "target": ctx.message.mentions[0].id},
                    ) as rows:
                        this_row = await rows.fetchone()
                        if this_row:
                            logging.debug(this_row)
                            first_member = discord.utils.find(
                                lambda m: m.id == this_row[1], ctx.guild.members
                            )
                            await ctx.send(
                                f"Sorry, but their soul has already been attached to {first_member}. I am magic, but I can't do anything for you"
                            )
                            return

                    this_embed = OwO.construct_marriage_proposal(
                        ctx.message.author, ctx.message.mentions[0]
                    )
                    await ctx.send(embed=this_embed)
                    await ctx.send(
                        f"{ctx.message.mentions[0]} has 15 seconds to answer!"
                    )
                    try:
                        await self.client.wait_for(
                            "message", check=check_second_side, timeout=15
                        )
                    except asyncio.TimeoutError:
                        await ctx.send("Oh no! They didn't seem to care :(")
                        return
                    else:
                        await db.execute(
                            """INSERT INTO Marriage (`GuildID`, `FirstSide`, `SecondSide`, `StartDate`) VALUES  
                        (:guildID, :first_member, :second_member, :today)""",
                            {
                                "guildID": ctx.guild.id,
                                "first_member": ctx.message.author.id,
                                "second_member": ctx.message.mentions[0].id,
                                "today": datetime.datetime.now(),
                            },
                        )
                        await db.commit()

                        marriage_photo = await OwO.generate_marry_image(
                            ctx.message.author, ctx.message.mentions[0]
                        )
                        await ctx.send(
                            f"Yay! Congratulations, {ctx.message.author.mention} ❤️ {ctx.message.mentions[0].mention}. We wish they have a sweet time together! 💍",
                            file=marriage_photo,
                        )

    @commands.command(brief="Unmarriage")
    async def divorce(self, ctx):
        def check_divorce(msg: discord.Message):
            return msg.author.id == ctx.author.id and msg.content == "DO IT"

        async with aiosqlite.connect(
            RT_DATABASE, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        ) as db:
            async with db.execute(
                """SELECT GuildID, FirstSide, SecondSide FROM Marriage WHERE `GuildID` = :guildID AND (`FirstSide` = :author OR `SecondSide` = :author)""",
                {"guildID": ctx.guild.id, "author": ctx.message.author.id},
            ) as rows:
                this_row = await rows.fetchone()
                if this_row:
                    first_member = discord.utils.find(
                        lambda m: m.id == this_row[1], ctx.guild.members
                    )
                    second_member = discord.utils.find(
                        lambda m: m.id == this_row[2], ctx.guild.members
                    )
                    await ctx.send(
                        f"You are in a relationship. You know, the one between {first_member} and {second_member}..."
                    )
                    await ctx.send(
                        f"If you are really sure about this, please say 'DO IT' "
                    )

                    try:
                        await self.client.wait_for(
                            "message", check=check_divorce, timeout=15
                        )
                    except asyncio.TimeoutError:
                        await ctx.send("You did not reply to the request")
                        pass
                    else:
                        await db.execute(
                            """DELETE FROM Marriage WHERE GuildID=:guildID AND (`FirstSide`=:author OR `SecondSide`=:author)""",
                            {"guildID": ctx.guild.id, "author": ctx.message.author.id},
                        )
                        await db.commit()
                        await ctx.send("Alright, I deleted your marriage records... 💔")
                    return
                else:
                    await ctx.send("You are not in a marriage with anyone yet...")

    @commands.command(brief="Show your marriage certificate!")
    async def marriagecert(self, ctx):
        async with ctx.channel.typing():
            if len(ctx.message.mentions) == 0:
                async with aiosqlite.connect(
                    RT_DATABASE,
                    detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
                ) as db:
                    async with db.execute(
                        """SELECT GuildID, FirstSide, SecondSide, StartDate FROM Marriage WHERE `GuildID` = :guildID AND (`FirstSide` = :author OR `SecondSide` = :author)""",
                        {"guildID": ctx.guild.id, "author": ctx.message.author.id},
                    ) as rows:
                        this_row = await rows.fetchone()
                        if this_row:
                            first_member = discord.utils.find(
                                lambda m: m.id == this_row[1], ctx.guild.members
                            )
                            second_member = discord.utils.find(
                                lambda m: m.id == this_row[2], ctx.guild.members
                            )
                            marriage_photo = await OwO.generate_marry_image(
                                first_member, second_member
                            )
                            length = datetime.datetime.now() - this_row[3]
                            # day_or_days = "day" if length.days == 1 else "days"
                            await ctx.send(
                                f"Relationship between {first_member} and {second_member}, which is {length} long!",
                                file=marriage_photo,
                            )
                            return
                        else:
                            await ctx.send(
                                "You are not in a marriage with anyone yet..."
                            )
            else:
                async with aiosqlite.connect(
                    RT_DATABASE,
                    detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
                ) as db:
                    async with db.execute(
                        """SELECT GuildID, FirstSide, SecondSide, StartDate FROM Marriage WHERE `GuildID` = :guildID AND (`FirstSide` = :author OR `SecondSide` = :author)""",
                        {"guildID": ctx.guild.id, "author": ctx.message.mentions[0].id},
                    ) as rows:
                        this_row = await rows.fetchone()
                        if this_row:
                            first_member = discord.utils.find(
                                lambda m: m.id == this_row[1], ctx.guild.members
                            )
                            second_member = discord.utils.find(
                                lambda m: m.id == this_row[2], ctx.guild.members
                            )
                            marriage_photo = await OwO.generate_marry_image(
                                first_member, second_member
                            )
                            length = datetime.datetime.now() - this_row[3]
                            # day_or_days = "day" if length.days == 1 else "days"
                            await ctx.send(
                                f"Relationship between {first_member} and {second_member}, which is {length} long!",
                                file=marriage_photo,
                            )
                            return
                        else:
                            await ctx.send(
                                "The person in question is not in a marriage with anyone yet. Go get 'em!"
                            )

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        async with aiosqlite.connect(
            RT_DATABASE, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        ) as db:
            async with db.cursor() as curr:
                await curr.execute(
                    """DELETE FROM Marriage WHERE GuildID=:guildID AND (FirstSide=:memberID OR SecondSide=:memberID)""",
                    {"guildID": member.guild.id, "memberID": member.id},
                )
                await db.commit()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        async with aiosqlite.connect(
            RT_DATABASE, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        ) as db:
            async with db.cursor() as curr:
                await curr.execute(
                    """DELETE FROM Marriage WHERE GuildID=:guildID""",
                    {"guildID": guild.id},
                )
                await db.commit()

    @staticmethod
    def owoify(text: str) -> str:
        # stolen regex from Artemis (https://github.com/UtopicUnicorns/ArtemisV3/blob/master/commands/general/uwu.js)

        kaomojis = [
            "(ᵘʷᵘ)",
            "(ᵘﻌᵘ)",
            "(◡ ω ◡)",
            "(◡ ꒳ ◡)",
            "(◡ w ◡)",
            "(◡ ሠ ◡)",
            "(˘ω˘)",
            "(⑅˘꒳˘)",
            "(˘ᵕ˘)",
            "(˘ሠ˘)",
            "(˘³˘)",
            "(˘ε˘)",
            "(´˘`)",
            "(´꒳`)",
            "(˘ ˘ ˘)⭜",
            "( ᴜ ω ᴜ )",
            "( ´ω` )۶",
            "(„ᵕᴗᵕ„)",
            "(*ฅ́˘ฅ̀*)",
            "(ㅅꈍ ˘ ꈍ)",
            "(⑅˘꒳˘)",
            "( ｡ᵘ ᵕ ᵘ ｡)",
            "( ᵘ ꒳ ᵘ ✼)",
            "( ˘ᴗ˘ )",
            "(˯ ᵘ ꒳ ᵘ ˯)",
            "(ᵘᆸᵘ)⭜",
            "(。U ω U。)",
            "(。U⁄ ⁄ω⁄ ⁄ U。)",
            "(U ᵕ U❁)",
            "(U ﹏ U)",
            "(⁄˘⁄ ⁄ ω⁄ ⁄ ˘⁄)♡",
            "( ͡U ω ͡U )",
            "( ͡o ᵕ ͡o )",
            "( ͡o ꒳ ͡o )",
            "(❀˘꒳˘)♡(˘꒳˘❀)",
            "( ˊ.ᴗˋ )",
        ]

        replacements = {
            r"(?:r|l)": "w",
            r"(?:R|L)/g": "W",
            r"n([aeiou])": "ny",
            r"N([aeiou])": "Ny",
            r"N([AEIOU])": "Ny",
            r"ove": "uv",
            r"o": "owo",
            r"O": "OwO",
            r"u": "uwu",
            r"U": "UwU",
        }

        for pattern, replacements in list(replacements.items()):
            text = re.sub(pattern=pattern, repl=replacements, string=text)

        text += " " + random.choice(kaomojis)

        return text

    @staticmethod
    async def generate_marry_image(
        first_member: discord.Member, second_member: discord.Member
    ) -> discord.File:
        """
        Generates a marriage "certificate" image
        """
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=15)
        ) as session:
            background = Image.open("runtime/assets/bg.png", "r")
            bg_w, bg_h = background.size
            logging.debug(first_member.avatar_url)
            logging.debug(second_member.avatar_url)

            cert_text = f"@{first_member} x @{second_member}"

            first_icon = await session.get(str(first_member.avatar_url))
            first_buffer = io.BytesIO(await first_icon.read())
            first_buffer.seek(0)
            second_icon = await session.get(str(second_member.avatar_url))
            second_buffer = io.BytesIO(await second_icon.read())
            second_buffer.seek(0)

            icon = Image.open(first_buffer, "r").convert("RGBA")
            icon = icon.resize((AVATAR_SIZE, AVATAR_SIZE))
            icon_w, icon_h = icon.size

            icon_2 = Image.open(second_buffer, "r").convert("RGBA")
            icon_2 = icon_2.resize((AVATAR_SIZE, AVATAR_SIZE))
            icon_w_2, icon_h_2 = icon_2.size

            heart_icon = Image.open("runtime/assets/heart.png", "r").convert("RGBA")
            heart_w, heart_h = heart_icon.size
            heart_offset = ((bg_w - heart_w) // 2, (bg_h - heart_h) // 2)

            text_font = ImageFont.truetype("runtime/assets/font.ttf", 40)

            # mask pfp ->
            mask = Image.new("L", icon.size, 255)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0) + icon.size, fill=0)

            icon = ImageOps.fit(icon, mask.size, centering=(0.5, 0.5))
            icon.paste(0, (0, 0), mask)
            offset = ((bg_w - icon_w) // 5, (bg_h - icon_h) // 2)

            mask_2 = Image.new("L", icon_2.size, 255)
            draw_2 = ImageDraw.Draw(mask_2)
            draw_2.ellipse((0, 0) + icon_2.size, fill=0)

            icon_2 = ImageOps.fit(icon_2, mask_2.size, centering=(0.5, 0.5))
            icon_2.paste(0, (0, 0), mask_2)
            offset_2 = ((bg_w - icon_w_2) // 5 * 4, (bg_h - icon_h_2) // 2)

            blurple = Image.new("RGBA", (background.size), (54, 57, 63, 255))
            blurple.paste(icon, offset, icon)
            blurple.paste(icon_2, offset_2, icon_2)
            blurple.paste(background, (0, 0))
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

            draw.ellipse(
                (
                    offset_2[0] - 2,
                    offset_2[1] - 2,
                    (offset_2[0]) + icon_w_2 + 2,
                    (offset_2[1]) + icon_h_2 + 2,
                ),
                fill="#36393f",
                outline="#ffffff",
                width=2,
            )
            blurple.paste(icon_2, offset_2, icon_2)

            blurple.paste(heart_icon, heart_offset, heart_icon)

            text_layer = Image.new("RGBA", (background.size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(text_layer)

            text_w, text_h = draw.textsize(cert_text, font=text_font)

            username_layer = Image.new("RGBA", (text_w, text_h), (0, 0, 0, 200))
            draw = ImageDraw.Draw(username_layer)
            draw.text((0, 0), cert_text, fill="white", font=text_font)

            text_layer.paste(
                username_layer,
                ((bg_w - text_w) // 2, bg_h - 10 - text_h),
                username_layer,
            )

            final_img = Image.alpha_composite(blurple, text_layer)

            with io.BytesIO() as image_bin:
                final_img.save(image_bin, format="PNG")
                image_bin.seek(0)
                file = discord.File(image_bin, filename="welcome.png")
                return file

    @staticmethod
    def construct_marriage_proposal(
        first_member: discord.Member, second_member: discord.Member
    ) -> discord.Embed:
        """
        Create a marriage proposal embed
        """
        embed = discord.Embed(title="Marriage Proposal!")
        embed.set_thumbnail(
            url="https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/twitter/282/ring_1f48d.png"
        )
        embed.add_field(name="Member", value=f"```{first_member}```", inline=False)
        embed.add_field(
            name="Has proposed", value=f"```{second_member}```", inline=False
        )
        embed.add_field(
            name=f"to a relationship! If {second_member} has agreed to the proposal, please type in the chat",
            value="```Yes!```",
            inline=False,
        )
        return embed


def setup(client):
    client.add_cog(OwO(client))


if __name__ == "__main__":
    logging.debug(OwO.owoify("Why would you even want this kind of thing owo"))
