from discord import Embed, Color
from .tf_process import async_process_url

async def tensorflow_embed(url: str):
    result = await async_process_url(url)
    embed = Embed(title="Ai-chan reply!")
    
    embed.set_thumbnail(url=url)
    
    dict_sorted = {k: v for k, v in sorted(result.items(), key=lambda item: item[1], reverse=True)}
    
    for _ in dict_sorted:
        embed.add_field(
            name = _,
            value = '```'+str(format(dict_sorted[_][0] * 100, '.2f'))+'%' + '```',
            inline = False
        )
    embed.color = int(list(dict_sorted.values())[0][1])
    
    embed.set_footer(text="Powered by advanced Keyboard Cat technologies")
    return embed