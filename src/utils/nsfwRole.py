from discord.ext import commands
import discord
import asyncio
import aiosqlite, sqlite3

class NSFWRoleManagement(commands.Cog):
    RT_DATABASE = 'runtime/server_data.db'

    def __init__(self, client):
        self.client = client
        db = sqlite3.connect(self.RT_DATABASE)
        db.execute('''CREATE TABLE IF NOT EXISTS `NSFWRoles` ([GuildID] INTEGER PRIMARY KEY, [RoleID] INTEGER)''')
        db.commit()
    
    @commands.command(brief='Set NSFW role.')
    @commands.has_permissions(administrator=True)
    async def setNSFWRole(self, ctx: commands.Context):
        def verify_nsfw_set(msg):
            return (msg.author.id == ctx.author.id and msg.content == 'Yes')
        if not ctx.message.role_mentions:
            await ctx.send("You must mention a role here")
            return
        if (ctx.message.role_mentions.__len__() == 1):
            role = ctx.message.role_mentions[0]
            await ctx.send(f"I am going to set the {role.mention} as the server's NSFW role. Confirm? [Yes/No]")
            try:
                await self.client.wait_for('message', check=verify_nsfw_set, timeout=15)
            except asyncio.TimeoutError:
                await ctx.send("Setup aborted.")
                return
            else:
                async with aiosqlite.connect(self.RT_DATABASE) as db:
                    await db.execute('''DELETE FROM NSFWRoles WHERE GuildID = :guildID''', {'guildID': ctx.guild.id})
                    await db.execute('''INSERT INTO NSFWRoles (GuildID, RoleID) VALUES (:guildID, :roleID)''', 
                    {'guildID': ctx.guild.id, 'roleID': role.id})
                    await db.commit()
                    await ctx.send("Done")
    
    @commands.command(brief='Remove NSFW role.')
    @commands.has_permissions(administrator=True)
    async def delNSFWRole(self, ctx: commands.Context):
        def verify_nsfw_set(msg):
            return (msg.author.id == ctx.author.id and msg.content == 'Yes')
        await ctx.send(f"I am going to remove the server's NSFW role. Confirm? [Yes/No]")
        try:
            await self.client.wait_for('message', check=verify_nsfw_set, timeout=15)
        except asyncio.TimeoutError:
            await ctx.send("Removal aborted.")
            return
        else:
            async with aiosqlite.connect(self.RT_DATABASE) as db:
                await db.execute('''DELETE FROM NSFWRoles WHERE GuildID = :guildID''', 
                {'guildID': ctx.guild.id})
                await db.commit()
                await ctx.send("Done")

    @commands.command(brief='Request NSFW role')
    async def requestNSFW(self, ctx):
        def validate_opt_in(msg: discord.Message):
            return (msg.author == ctx.author and msg.content == "I agree" and msg.channel.type == discord.ChannelType.private)

        async with aiosqlite.connect(self.RT_DATABASE) as db:
            async with db.execute('''SELECT GuildID, RoleID from NSFWRoles WHERE GuildID = :guildID''', {'guildID': ctx.guild.id}) as cursor:
                rows = await cursor.fetchall()
                if rows.__len__() == 0:
                    await ctx.send("This server does not have a NSFW role set up.")
                    return
                else:
                    await ctx.send("Please check your DM for instructions.")
                    role_id = rows[0][1]
                    nsfw_role = discord.utils.get(ctx.guild.roles, id=role_id)
                    await ctx.author.send(f"You are requesting NSFW access to {ctx.guild.name}")
                    await ctx.author.send(f"By replying `I agree` to this message, you agree that:\n"+
                    f"1. You are over the age of consent and are willing to be exposed to NSFW content.\n"+
                    f"2. You are going have full responsibility for the content you send on {ctx.guild.name}.\n" +
                    f"3. You are going to follow Discord's guidelines for NSFW content.\n" + 
                    f"4. If you are caught violating these rules, {ctx.guild.name} moderators reserves the right to punish you.")
                    await ctx.author.send("You have 20s to reply to this request or it will be aborted automatically")
                try:
                    await self.client.wait_for('message', check=validate_opt_in, timeout=20)
                except asyncio.TimeoutError:
                    await ctx.author.send("This request has been aborted automatically")
                else:
                    await ctx.author.add_roles(nsfw_role)
                    await ctx.author.send("Done.")

    @commands.command(brief='Request NSFW role')
    async def unNSFW(self, ctx):
        async with aiosqlite.connect(self.RT_DATABASE) as db:
            async with db.execute('''SELECT GuildID, RoleID from NSFWRoles WHERE GuildID = :guildID''', {'guildID': ctx.guild.id}) as cursor:
                rows = await cursor.fetchall()
                if rows.__len__() == 0:
                    await ctx.send("This server does not have a NSFW role set up.")
                    return
                else:
                    role_id = rows[0][1]
                    nsfw_role = discord.utils.get(ctx.guild.roles, id=role_id)
                    await ctx.author.remove_roles(nsfw_role)
                    await ctx.author.send("Done.")

def setup(client: commands.Bot):
    client.add_cog(NSFWRoleManagement(client))