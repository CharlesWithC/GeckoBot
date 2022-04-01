# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Staff Functions of Gecko Bot

import os, asyncio
import discord
from discord.commands import CommandPermission, SlashCommandGroup
from discord.ext import commands
from base64 import b64encode, b64decode

from bot import bot
from settings import *
from functions import *
from db import newconn

class ManageStaff(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    staff = SlashCommandGroup("staff", "Staff")

    @staff.command(name = "list", description="List all staff in this guild.")
    async def show(self, ctx, 
        showid: discord.Option(str, "Show user id attached to username?", required = False, choices = ["Yes", "No"])):
            
        conn = newconn()
        cur = conn.cursor()
        await ctx.trigger_typing()
        
        guild = ctx.guild

        if guild is None:
            await ctx.respond("You can only use this command in guilds, not in DMs.")
            return

        # ADMINISTRATIVE STAFF
        cur.execute(f"SELECT roleid FROM staffrole WHERE guildid = {ctx.guild.id}")
        troleids = cur.fetchall()
        roleids = []
        for r in ctx.guild.roles:
            if (r.id,) in troleids:
                roleids.append((r.id,)) # to sort roles based on their guild role level
        roleids.reverse()
        cur.execute(f"SELECT userid FROM staffuser WHERE guildid = {ctx.guild.id}")
        userids = cur.fetchall()
        msg = "**Administrative Staff**\n"
        msg += "**Server Owner**\n"
        msg += f"<@!{ctx.guild.owner.id}> "
        if showid == "Yes":
            msg += f"(`{ctx.guild.owner.id}`)"
        msg += "\n\n"
        for d in roleids:
            roleid = d[0]
            msg += f"<@&{roleid}>\n"
            found = False
            role = discord.utils.get(guild.roles, id=roleid)
            for member in guild.members:
                for r in member.roles:
                    if r.id == roleid:
                        found = True
                        msg += f"<@!{member.id}> "
                        if showid == "Yes":
                            msg += f"(`{member.id}`)\n"
                        if userids.count((member.id,)) > 0:
                            userids.remove((member.id,))
            if not found:
                msg += "No staff with this title.\n"
            else:
                msg += "\n"
            if showid != "Yes":
                msg += "\n"
        
        if len(userids) > 0:
            msg += "**Additional staff**\n"
            msg += "*They are staff but they don't have any role above.*\n"
            for d in userids:
                userid = d[0]
                msg += f"<@!{userid}> "
                if showid == "Yes":
                    msg += f"(`{member.id}`)\n"
            msg += "\n\n"
        
        # NON-ADMINISTRATIVE STAFF
        cnt = 0
        cur.execute(f"SELECT roleid FROM nastaffrole WHERE guildid = {ctx.guild.id}")
        troleids = cur.fetchall()
        roleids = []
        for r in ctx.guild.roles:
            if (r.id,) in troleids:
                roleids.append((r.id,)) # to sort roles based on their guild role level
        roleids.reverse()
        cur.execute(f"SELECT userid FROM nastaffuser WHERE guildid = {ctx.guild.id}")
        userids = cur.fetchall()
        tmsg = "**Non-Administrative Staff**\n"
        for d in roleids:
            roleid = d[0]
            tmsg += f"<@&{roleid}>\n"
            found = False
            role = discord.utils.get(guild.roles, id=roleid)
            for member in guild.members:
                for r in member.roles:
                    if r.id == roleid:
                        cnt += 1
                        found = True
                        tmsg += f"<@!{member.id}> "
                        if showid == "Yes":
                            tmsg += f"(`{member.id}`)\n"
                        if userids.count((member.id,)) > 0:
                            userids.remove((member.id,))
            if not found:
                tmsg += "No staff with this title.\n"
            else:
                tmsg += "\n"
            if showid != "Yes":
                tmsg += "\n"
        
        if len(userids) > 0:
            tmsg += "**Additional staff**\n"
            tmsg += "*They are staff but they don't have any role above.*\n"
            for d in userids:
                cnt += 1
                userid = d[0]
                tmsg += f"<@!{userid}> "
                if showid == "Yes":
                    tmsg += f"(`{member.id}`)\n"
            tmsg += "\n\n"
        
        if cnt > 0:
            msg += "\n" + tmsg
        
        # EMBED
        embed = discord.Embed(title=f"{ctx.guild.name} Staff", description=msg)
        embed.set_thumbnail(url = ctx.guild.icon.url)
        embed.set_footer(text=f"{ctx.guild.name}", icon_url = ctx.guild.icon.url)
        await ctx.respond(embed = embed)
    
    @staff.command(name = "manage", description = "Server Owner - Manage staff in this guild.")
    async def manage(self, ctx, operation: discord.Option(str, "Operation", required = True, choices = ["add", "remove"]),
        target: discord.Option(str, "Target", required = True, choices = ["role", "user"]),
        administrative: discord.Option(str, "Is administrative? (Only administrative staff are able to use staff commands)", \
            required = True, choices = ["Yes", "No"]),
        obj: discord.Option(str, "All the roles / users you want to add / remove", required = True)):

        guild = ctx.guild
        if guild is None:
            await ctx.respond("You can only use this command in guilds, not in DMs.")
            return
            
        if ctx.author.id != ctx.guild.owner.id and ctx.author.id != BOTOWNER:
            await ctx.respond(f"{ctx.author.name}, only the server owner {ctx.guild.owner.nick} can use this command!", ephemeral = True)
            return

        conn = newconn()
        cur = conn.cursor()
        
        obj = obj.split()
        d = []
        if target == "role":
            for ob in obj:
                if not ob.startswith("<@&") or not ob.endswith(">"):
                    await ctx.respond(f"{ctx.author.name}, {ob} is not a valid role! You should tag the role, e.g. @Admin", ephemeral = True)
                    return
                d.append(int(ob[3:-1]))
        elif target == "user":
            for ob in obj:
                if not ob.startswith("<@!") or not ob.endswith(">"):
                    await ctx.respond(f"{ctx.author.name}, {ob} is not a valid user! You should tag the user, e.g. <@{ctx.author.id}>", ephemeral = True)
                    return
                d.append(int(ob[3:-1]))
        else:
            await ctx.respond(f"{ctx.author.name}, {target} is not a valid target!", ephemeral = True)
            return
        
        await ctx.trigger_typing()

        dbprefix = "na"
        resprefix = "non-administrative "
        if administrative == "Yes":
            dbprefix = ""
            resprefix = ""

        if operation == "add":
            for dd in d:
                cur.execute(f"SELECT * FROM {dbprefix}staff{target} WHERE guildid = {ctx.guild.id} AND {target}id = {dd}")
                t = cur.fetchall()
                if len(t) > 0:
                    continue
                cur.execute(f"INSERT INTO {dbprefix}staff{target} VALUES ({ctx.guild.id}, {dd})")
            conn.commit()

            if len(d) > 1:
                await ctx.respond(f"{ctx.author.name}, {resprefix}staff {target}s {' '.join(obj)} added!")
            else:
                await ctx.respond(f"{ctx.author.name}, {resprefix}staff {target} {' '.join(obj)} added!")
            await log("Staff", f"[Guild {ctx.guild} ({ctx.guild.id})] {ctx.author} added {resprefix}staff {target}s {obj}", ctx.guild.id)
        
        elif operation == "remove":
            for dd in d:
                cur.execute(f"DELETE FROM {dbprefix}staff{target} WHERE guildid = {ctx.guild.id} AND {target}id = {dd}")
            conn.commit()

            if len(d) > 1:
                await ctx.respond(f"{ctx.author.name}, {resprefix}staff {target}s {' '.join(obj)} removed!")
            else:
                await ctx.respond(f"{ctx.author.name}, {resprefix}staff {target} {' '.join(obj)} removed!")
            await log("Staff", f"[Guild {ctx.guild} ({ctx.guild.id})] {ctx.author} removed {resprefix}staff {target}s {obj}", ctx.guild.id)

bot.add_cog(ManageStaff(bot))