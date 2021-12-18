from PIL import Image, ImageDraw, ImageFont, ImageOps
import asyncio
import aiohttp
import io

async def test_avatar():
        AVATAR_SIZE = 192
        server_msg = "Welcome to DemoHouse !"
        member_msg = "@Buzzle#5646"

        background = Image.open("runtime/assets/bg.jpg", "r").convert("RGBA")
        bg_w, bg_h = background.size

        timeout = aiohttp.ClientTimeout(total=15)
        # print(member.avatar_url)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            raw_icon = await session.get(str("https://cdn.discordapp.com/avatars/169257697345011712/fa1ff14e7510ea22f1cd72baeaa1bbb0.webp"))
            buffer = io.BytesIO(await raw_icon.read())
            buffer.seek(0)

            icon = Image.open(buffer, "r").convert("RGBA")
            icon = icon.resize((AVATAR_SIZE, AVATAR_SIZE))
            icon_w, icon_h = icon.size

            text_font = ImageFont.truetype("runtime/assets/font.ttf", 40)

            # mask pfp ->
            mask = Image.new("L", icon.size, 255)
            draw = ImageDraw.Draw(mask)
            draw.rectangle((0, 0) + icon.size, fill=0)

            icon = ImageOps.fit(icon, mask.size, centering=(0.5, 0.5))
            icon.paste(0, (0, 0), mask)
            offset = ((bg_w - icon_w) // 2, (bg_h - icon_h) // 2)

            blurple = Image.new("RGBA", (background.size), (54, 57, 63, 255))
            blurple.paste(icon, offset)
            blurple.paste(background, (0, 0), background)
            #draw = ImageDraw.Draw(blurple)
            #draw.rectangle(
            #    (
            #        offset[0] - 2,
            #        offset[1] - 2,
            #        (offset[0]) + icon_w + 2,
            #        (offset[1]) + icon_h + 2,
            #    ),
            #    fill="#36393f",
            #    outline="#ffffff",
            #    width=2,
            #)
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

            final_img.show()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_avatar())