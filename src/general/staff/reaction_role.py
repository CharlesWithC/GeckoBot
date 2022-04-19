# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Staff - Reaction Role Management

import os, asyncio
import discord
from discord.commands import CommandPermission, SlashCommandGroup
from discord.ext import commands
import validators

from bot import bot
from settings import *
from functions import *
from db import newconn

class ReactionRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    rr = SlashCommandGroup("reaction_role", "Reaction Role")

    @rr.command(name = "create", description = "Staff - Let users get role by reacting emojis to a message.")
    async def create(self, ctx, 
        msglink: discord.Option(str, "Link to message where members will react. You can use /embed to create one.", required = True), 
        rolebind: discord.Option(str, "Role => Emoji bind (format {@role1} {emoji1} {@role2} {emoji2}, e.g. @Admin :manager:)", required = True)):
        
        await ctx.defer()    
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return
        guild = ctx.guild
        guildid = guild.id
        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return
        botuser = ctx.guild.get_member(BOTID)
        if not botuser.guild_permissions.add_reactions:
            await ctx.respond("I don't have permission to add reactions.", ephemeral = True)
            return
        conn = newconn()
        cur = conn.cursor()
            
        cur.execute(f"SELECT COUNT(*) FROM reactionrole WHERE guildid = {guildid}")
        c = cur.fetchall()
        if len(c) > 0:
            premium = GetPremium(ctx.guild)
            cnt = c[0][0]
            if cnt >= 50 and premium >= 2:
                await ctx.respond("Max reaction role messages: 50.\n\nIf you are looking for more reaction role messages, contact Gecko Moderator in support server", ephemeral = True)
                return
            elif cnt >= 30 and premium == 1:
                await ctx.respond("Premium Tier 1: 30 reaction role messages.\nPremium Tier 2: 50 reaction role messages.\n\nFind out more by using `/premium`", ephemeral = True)
                return
            elif cnt >= 10 and premium == 0:
                await ctx.respond("Free guilds: 10 reaction role messages.\nPremium Tier 1: 30 reaction role messages.\nPremium Tier 2: 50 reaction role messages.\n\nFind out more by using `/premium`", ephemeral = True)
                return
        
        rolebindtxt = rolebind.split()
        i = 0
        rolebind = []
        roles = []
        emojis = []
        r = -1
        e = ""
        for data in rolebindtxt:
            if i%2 == 0: # role
                if not data.startswith("<@&") or not data.endswith(">"):
                    await ctx.respond(f"{ctx.author.name}, invalid role {data}. Make sure the role exists each role has a emoji following.", ephemeral = True)
                    return
                r = int(data[3:-1])
            else:
                if roles.count(r) > 0 or emojis.count(e) > 0:
                    await ctx.respond(f"{ctx.author.name}, each role can only be bound to one unique emoji.", ephemeral = True)
                    return
                roles.append(r)
                e = data.replace(" ", "")
                emojis.append(e)
                rolebind.append((r, e))
                cur.execute(f"SELECT emoji FROM rolebind WHERE guildid = {guildid} AND role = {r}")
                t = cur.fetchall()
                if len(t) != 0:
                    emoji = b64d(t[0][0])
                    await ctx.respond(f"{ctx.author.name}, role <@&{r}> already bound to {emoji} in another post.", ephemeral = True)
                    return
            i += 1
        
        if len(rolebind) > 20:
            await ctx.respond(f"There could be at most 20 reaction roles for a single message.", ephemeral = True)
            return
        
        channel = ctx.channel
        message = await channel.send("Reaction test")
        for t in rolebind:
            emoji = t[1]
            try:
                await message.add_reaction(emoji)
            except:
                await ctx.respond(f"I cannot add reaction {emoji}. Make sure it's a valid emoji.", ephemeral = True)
                await message.delete()
                return
        await message.delete()
        
        if not msglink.endswith("/"):
            msglink = msglink + "/"
        l = msglink.split("/")
        messageid = int(l[-2])
        channelid = int(l[-3])
        
        message = None
        try:
            channel = bot.get_channel(channelid)
            message = await channel.fetch_message(messageid)
            for data in rolebind:
                await message.add_reaction(data[1])
            await ctx.respond(f"{ctx.author.name}, reaction-role message posted at <#{channelid}>!")

            msgid = message.id
            cur.execute(f"INSERT INTO reactionrole VALUES ({guildid}, {channelid}, {msgid})")
            for data in rolebind:
                cur.execute(f"INSERT INTO rolebind VALUES ({guildid}, {channelid}, {msgid}, {data[0]}, '{b64e(data[1])}')")
            conn.commit()

            await log("Staff", f"[Guild {ctx.guild} ({ctx.guild.id})] {ctx.author} created a reaction-role post at {channel} ({channelid}), with role-binding: {rolebindtxt}", ctx.guild.id)
        except Exception as e:
            await ctx.respond(f"{ctx.author.name}, it seems I cannot send message at <#{channelid}>. Make sure the channel exist and I have access to it!", ephemeral = True)

            await log("Staff", f"[Guild {ctx.guild} ({ctx.guild.id})] '/reaction_role create' command executed by {ctx.author} failed due to {str(e)}", ctx.guild.id)

    @rr.command(name = "append", description = "Staff - Add more selection of roles. (You cannot remove existing roles)")
    async def append(self, ctx, 
        msglink: discord.Option(str, "Link to message to edit reaction role.", required = True), 
        rolebind: discord.Option(str, "[Append] Role => Emoji bind (format {@role1} {emoji1} {@role2} {emoji2}, e.g. @Admin :manager:)", required = True)):
        
        await ctx.defer()    
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return
        guild = ctx.guild
        guildid = guild.id
        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return
        botuser = ctx.guild.get_member(BOTID)
        if not botuser.guild_permissions.add_reactions:
            await ctx.respond("I don't have permission to add reactions.", ephemeral = True)
            return
        conn = newconn()
        cur = conn.cursor()
        
        

        if msglink.endswith("/"):
            msglink = msglink[:-1]
        msglink = msglink.split("/")
        guildid = int(msglink[-3])
        channelid = int(msglink[-2])
        msgid = int(msglink[-1])
        message = None
        channel = None
        
        try:
            channel = bot.get_channel(channelid)
            message = await channel.fetch_message(msgid)
        except:
            await ctx.respond(f"{ctx.author.name}, I cannot fetch that message.", ephemeral = True)
            return

        cur.execute(f"SELECT * FROM reactionrole WHERE guildid = {guildid} AND channelid = {channelid} AND msgid = {msgid}")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond(f"{ctx.author.name}, message is not bound to any reaction-role post.", ephemeral = True)
            return

        rolebindtxt = rolebind.split()
        i = 0
        rolebind = []
        roles = []
        emojis = []
        r = -1
        e = ""
        for data in rolebindtxt:
            if i%2 == 0: # role
                if not data.startswith("<@&") or not data.endswith(">"):
                    await ctx.respond(f"{ctx.author.name}, invalid role {data}. Make sure the role exists each role has a emoji following.", ephemeral = True)
                    return
                r = int(data[3:-1])
            else:
                if roles.count(r) > 0 or emojis.count(e) > 0:
                    await ctx.respond(f"{ctx.author.name}, each role can only be bound to one unique emoji.", ephemeral = True)
                    return
                roles.append(r)
                e = data.replace(" ", "")
                emojis.append(e)
                rolebind.append((r, e))
            i += 1
        
        cur.execute(f"SELECT * FROM rolebind WHERE msgid = {msgid}")
        org = cur.fetchall()
        if len(org) + len(rolebind) > 20:
            await ctx.respond(f"There could be at most 20 reaction roles for a single message.", ephemeral = True)
            return
        
        channel = ctx.channel
        tmessage = await channel.send("Reaction test")
        for t in rolebind:
            emoji = t[1]
            try:
                await tmessage.add_reaction(emoji)
            except:
                await ctx.respond(f"I cannot add reaction {emoji}. Make sure it's a valid emoji.", ephemeral = True)
                await tmessage.delete()
                return
        await tmessage.delete()
        
        updates = ""
        updateslog = ""
        for data in rolebind:
            roleid = data[0]
            emoji = data[1]
            cur.execute(f"SELECT roleid, emoji FROM rolebind WHERE guildid = {guildid} AND channelid = {channelid} AND msgid = {msgid}")
            t = cur.fetchall()
            ok = True
            for tt in t:
                if tt[0] == roleid:
                    updates += f"<@&{roleid}> already bound, you cannot have multiple emojis representing it.\n"
                    ok = False
                    break
                elif tt[1] == b64e(emoji):
                    updates += f"{emoji} already bound, you cannot have multiple emojis representing it.\n"
                    ok = False
                    break
            if ok:
                updates += f"Added role {roleid} => {emoji}.\n"
                updateslog += f"Added role {roleid} => {emoji}. "
                await message.add_reaction(emoji)
                emoji = b64e(emoji)
                cur.execute(f"INSERT INTO rolebind VALUES ({guildid}, {channelid}, {msgid}, {roleid}, '{emoji}')")
                conn.commit()
            
        await ctx.respond(f"{ctx.author.name}, reaction-role post updated!\n{updates}")
        await log("Staff", f"{ctx.author} updated reaction-role post {msglink} rolebind. {updateslog}", ctx.guild.id)

    @rr.command(name = "list", description = "Staff - List all reaction role posts in this guild.")
    async def show(self, ctx):
        await ctx.defer()    
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return
        guild = ctx.guild
        guildid = guild.id
        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return
        conn = newconn()
        cur = conn.cursor()
            
        
        msg = ""
        cur.execute(f"SELECT channelid, msgid FROM reactionrole WHERE guildid = {guildid}")
        t = cur.fetchall()
        for tt in t:
            msg += f"<#{tt[0]}> https://discord.com/channels/{guildid}/{tt[0]}/{tt[1]}\n"
        
        embed = discord.Embed(title="Reaction role posts in this guild", description=msg, color = GECKOCLR)
        await ctx.respond(embed=embed)

bot.add_cog(ReactionRole(bot))

async def ReactionRoleUpdate():
    await bot.wait_until_ready()
    
    reactionrole_fail = [] # (channelid, msgid)
    while not bot.is_closed():
        conn = newconn()
        cur = conn.cursor()
        # Self role
        try:
            cur.execute(f"SELECT guildid, channelid, msgid FROM reactionrole")
            t = cur.fetchall()
            reactionroles = []
            for tt in t:
                reactionroles.append((tt[0], tt[1], tt[2]))
            for reactionrole in reactionroles:
                guildid = reactionrole[0]
                guild = bot.get_guild(guildid)
                channelid = reactionrole[1]
                msgid = reactionrole[2]
                
                cur.execute(f"SELECT role, emoji FROM rolebind")
                d = cur.fetchall()
                rolebindtxt = ""
                rolebind = []
                for dd in d:
                    rolebind.append((dd[0], dd[1]))
                    rolebindtxt = f"<@&{dd[0]}> => {b64d(dd[1])} "

                if reactionrole_fail.count((channelid, msgid)) > 3:
                    while reactionrole_fail.count((channelid, msgid)) > 0:
                        reactionrole_fail.remove((channelid, msgid))
                    cur.execute(f"DELETE FROM reactionrole WHERE guildid = {guildid} AND channelid = {channelid} AND msgid = {msgid}")
                    cur.execute(f"DELETE FROM rolebind WHERE guildid = {guildid} AND channelid = {channelid} AND msgid = {msgid}")
                    cur.execute(f"DELETE FROM userrole WHERE guildid = {guildid} AND channelid = {channelid} AND msgid = {msgid}")
                    conn.commit()
                    
                    await log("ReactionRole", f"[{guild} ({guildid})] Self-role post {msgid} expired as bot cannot access the channel.", guildid)
                    try:
                        cur.execute(f"SELECT channelid FROM channelbind WHERE guildid = {guildid} AND category = 'error'")
                        t = cur.fetchall()
                        if len(t) != 0:
                            errchannelid = t[0][0]
                            errchannel = bot.get_channel(errchannelid)
                            embed = discord.Embed(title=f"Error Notification", description=f"A reaction-role post (`{msgid}`) with role-binds {rolebindtxt} sent in <#{channelid}> (`{channelid}`) at guild {guild} (`{guildid}`) has expired because I either cannot view the channel, or cannot find the message. I will no longer assign roles on reactions.", url=f"https://discord.com/channels/{guildid}/{channelid}/{msgid}", color=0x0000DD)
                            await errchannel.send(embed=embed)
                    except Exception as e:
                        pass
                    continue
                
                try:
                    channel = bot.get_channel(channelid)
                    if channel is None:
                        reactionrole_fail.append((channelid, msgid))
                    message = await channel.fetch_message(msgid)
                    if message is None:
                        reactionrole_fail.append((channelid, msgid))
                except:
                    reactionrole_fail.append((channelid, msgid))
                    continue
                while reactionrole_fail.count((channelid, msgid)) > 0:
                    reactionrole_fail.remove((channelid, msgid))

                cur.execute(f"SELECT role, emoji FROM rolebind WHERE channelid = {channelid} AND msgid = {msgid}")
                d = cur.fetchall()
                rolebind = {}
                for dd in d:
                    rolebind[dd[1]] = dd[0]

                reactions = message.reactions
                existing_emojis = []
                for reaction in reactions:
                    emoji = b64e(str(reaction.emoji))
                    existing_emojis.append(emoji)
                    roleid = rolebind[emoji]
                    role = discord.utils.get(guild.roles, id=roleid)
                    inrole = []
                    async for user in reaction.users():
                        if user.id != BOTID:
                            found = False
                            for userrole in user.roles:
                                if userrole.id == roleid:
                                    found = True
                                    break
                            if not found:
                                try:
                                    await user.add_roles(role, reason = "Gecko Reaction Role")
                                except: # cannot assign role to user (maybe user has left server)
                                    await log("ReactionRole", f"[{guild} ({guildid})] Cannot assign {role} ({roleid}) for {user} ({user.id}), user reaction removed.", guildid)
                                    await message.remove_reaction(reaction.emoji, user)
                                    continue
                                cur.execute(f"SELECT * FROM userrole WHERE userid = {user.id} AND roleid = {roleid} AND guildid = {guildid}")
                                p = cur.fetchall()
                                if len(p) == 0:
                                    await log("ReactionRole", f"[{guild} ({guildid})] Added {role} ({roleid}) role to {user} ({user.id}).", guildid)
                                    cur.execute(f"INSERT INTO userrole VALUES ({guildid}, {channelid}, {msgid}, {user.id}, {roleid})")
                            inrole.append(user.id)
                    conn.commit()
                    cur.execute(f"SELECT userid FROM userrole WHERE roleid = {roleid}")
                    preusers = cur.fetchall()
                    for data in preusers:
                        preuser = data[0]
                        if not preuser in inrole:
                            cur.execute(f"DELETE FROM userrole WHERE userid = {preuser} AND roleid = {roleid} AND guildid = {guildid}")
                            try:
                                role = discord.utils.get(guild.roles, id=roleid)
                                user = discord.utils.get(guild.members, id=preuser)
                                await user.remove_roles(role, reason = "Gecko Reaction Role")
                                await log("ReactionRole", f"[{guild} ({guildid})] Removed {role} ({roleid}) role from user {user} ({user.id}).", guildid)
                            except:
                                pass
                    conn.commit()
                    
        except Exception as e:
            try:
                await log("ERROR", f"[Guild {guildid}] Reaction role error {str(e)}")
            except:
                pass

        await asyncio.sleep(60)
        
bot.loop.create_task(ReactionRoleUpdate())