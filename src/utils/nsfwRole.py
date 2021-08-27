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
        db.execute('''CREATE TABLE IF NOT EXISTS `NSFWBans` ([GuildID] INTEGER, [MemberID] INTEGER, [BanReason] TIMESTAMP, PRIMARY KEY ("GuildID", "MemberID"))''')
        db.commit()
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setNSFWRole(self, ctx: commands.Context):
        """
        Set NSFW Role and enable NSFW support features on this server
        """
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
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def delNSFWRole(self, ctx: commands.Context):
        """
        Remove NSFW role and clear all bans from this server
        """
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
                await db.execute('''DELETE FROM NSFWBans WHERE GuildID = :guildID''', 
                {'guildID': ctx.guild.id})
                await db.commit()
                await ctx.send("Done")

    @commands.command
    async def requestNSFW(self, ctx):
        """
        Request NSFW features
        """
        def validate_opt_in(msg: discord.Message):
            return (msg.author == ctx.author and msg.content == "I agree" and msg.channel.type == discord.ChannelType.private)

        async with aiosqlite.connect(self.RT_DATABASE) as db:
            async with db.execute('''SELECT * FROM NSFWBans WHERE GuildID=:guildID AND MemberID=:memberID''',
            {'guildID': ctx.guild.id, 'memberID': ctx.author.id}) as query:
                rows = await query.fetchall()
                if rows.__len__() != 0:
                    return await ctx.send(f"You have been banned from getting NSFW on this server due to: {rows[0][2]}")

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
        """
        Remove NSFW features
        """
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

    @commands.command()
    async def nsfwban(self, ctx: commands.Context, *, reason:str):
        """
        Ban member from getting NSFW roles
        """
        async with aiosqlite.connect(self.RT_DATABASE) as db:
            await db.execute('''INSERT INTO NSFWBans (GuildID, MemberID, BanReason) VALUES(:guildID, :memberID, :banReason)''', 
                {'guildID': ctx.guild.id, 'memberID': ctx.message.mentions[0].id, 'banReason': reason})

            async with db.execute('''SELECT GuildID, RoleID from NSFWRoles WHERE GuildID = :guildID''', {'guildID': ctx.guild.id}) as cursor:
                rows = await cursor.fetchall()
                if rows.__len__() == 0:
                    await ctx.send("This server does not have a NSFW role set up.")
                    return
                else:
                    role_id = rows[0][1]
                    nsfw_role = discord.utils.get(ctx.guild.roles, id=role_id)
                    await ctx.message.mentions[0].remove_roles(nsfw_role)
            await ctx.send("User have been banned from NSFW")

    @commands.command()
    async def nsfwunban(self, ctx: commands.Context):
        """
        Unban member from NSFW
        """
        async with aiosqlite.connect(self.RT_DATABASE) as db:
            await db.execute('''DELETE FROM NSFWBans WHERE GuildID = :guildID AND MemberID = :memberID''', 
                {'guildID': ctx.guild.id, 'memberID': ctx.message.mentions[0].id})
            await ctx.send("Done.")
        

def setup(client: commands.Bot):
    client.add_cog(NSFWRoleManagement(client))