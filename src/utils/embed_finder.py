import discord
from discord.ext import commands


async def find_message_with_embeds(
    ctx: commands.Context, length: int
) -> discord.Message:
    """Finds a message with embeds in the context

    Args:
        ctx (commands.Context): The context

    Returns:
        discord.Message: The message
    """
    found_msg = None
    if ctx.message:
        if ctx.message.reference:
            this_msg = ctx.message.reference.resolved
            if this_msg.embeds.__len__() > 0 or this_msg.attachments.__len__() > 0:
                return this_msg
    messages = await ctx.channel.history(limit=length).flatten()
    for mesg in messages:
        if mesg.attachments.__len__() > 0 or mesg.embeds.__len__() > 0:
            found_msg = mesg
            break
    return found_msg
