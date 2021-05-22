from discord.ext import commands

class AdminTools(commands.Cog, name='Administration Tools'):
    def __init__(self, client):
        self.client = client
        pass
    
    @commands.command(hidden=True)
    async def loadCog(self, ctx, *, module):
        try:
            self.client.load_extension(module)
        except commands.ExtensionError as e:
            await ctx.send('Oh no it didn\'t work :(')
            await ctx.send(f'{e.__class__.__name__}: {e}')
        else:
            await ctx.send('Done!')

    @commands.command(hidden=True)
    async def unloadCog(self, ctx, *, module):
        try:
            self.client.unload_extension(module)
        except commands.ExtensionError as e:
            await ctx.send('Oh no it didn\'t work :(')
            await ctx.send(f'{e.__class__.__name__}: {e}')
        else:
            await ctx.send('Done!')

    @commands.group(hidden=True, invoke_without_command=True)
    async def reloadCog(self, ctx, *, module):
        try:
            self.client.reload_extension(module)
        except commands.ExtensionError as e:
            await ctx.send('Oh no it didn\'t work :(')
            await ctx.send(f'{e.__class__.__name__}: {e}')
        else:
            await ctx.send('Done!')

def setup(client):
    client.add_cog(AdminTools(client))