# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Staff - Ticket Management

import os, asyncio
import discord
from discord.commands import SlashCommandGroup
from discord.ext import commands
from time import time
from datetime import datetime
import io
from rapidfuzz import process

from bot import bot
from settings import *
from functions import *
from db import newconn

class ManageTicket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    manage = SlashCommandGroup("ticket", "Manage Ticket")

    @manage.command(name="create", description="Staff - Create a new category of ticket.")
    async def create(self, ctx, category: discord.Option(discord.CategoryChannel, "Guild category where tickets will be created"),
            label: discord.Option(str, "A easy-to-remember label, not visible to members, alias of gticketid", required = False),
            channelformat: discord.Option(str, "Channel name format, accept {username} {userid} {ticketid} variables, default 'ticket-{username}'", name="format", default = "ticket-{username}", required = False),
            msg: discord.Option(str, "Message to send after user created ticket", default = "", required = False),
            moderator: discord.Option(str, "Mention Roles or Users who can view the ticket, separate with spaces, default administrative staff", default = "", required = False)):
        
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return

        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return

        conn = newconn()
        cur = conn.cursor()
        guildid = ctx.guild.id
        
        cur.execute(f"SELECT COUNT(*) FROM ticket WHERE guildid = {guildid} AND gticketid > 0")
        c = cur.fetchall()
        if len(c) > 0:
            premium = GetPremium(ctx.guild)
            cnt = c[0][0]
            if cnt >= 50 and premium >= 2:
                await ctx.respond("Max ticket categories: 50.\n\nIf you are looking for more ticket categories, contact Gecko Moderator in support server", ephemeral = True)
                return
            elif cnt >= 15 and premium == 1:
                await ctx.respond("Premium Tier 1: 15 ticket categories.\nPremium Tier 2: 50 ticket categories.\n\nFind out more by using `/premium`", ephemeral = True)
                return
            elif cnt >= 5 and premium == 0:
                await ctx.respond("Free guilds: 3 ticket categories.\nPremium Tier 1: 15 ticket categories.\nPremium Tier 2: 50 ticket categories.\n\nFind out more by using `/premium`", ephemeral = True)
                return
        
        cur.execute(f"SELECT COUNT(*) FROM ticket")
        t = cur.fetchall()
        gticketid = 0
        if len(t) > 0:
            gticketid = t[0][0]
        
        tmoderator = []
        if moderator != "":
            moderator = moderator.split(" ")
            tmoderator = []
            for i in range(len(moderator)):
                moderator[i] = moderator[i].strip()
                if moderator[i].startswith("<@") and moderator[i].endswith(">"):
                    moderator[i] = moderator[i].replace("@!","@")
                    tmoderator.append(moderator[i][1:-1])
        
        cur.execute(f"INSERT INTO ticket VALUES ({gticketid}, {guildid}, {category.id}, '{b64e(channelformat)}', '{b64e(msg)}', '{','.join(tmoderator)}')")

        if label != None:
            cur.execute(f"INSERT INTO alias VALUES ({guildid}, 'ticket', {gticketid}, '{b64e(label)}')")
        
        conn.commit()

        await ctx.respond(f"Guild ticket category created!\nID: g{gticketid}\nTickets will be created under {category.mention}\n\nBind ticket category to button to start receiving tickets! `/button create`")
        await log("Ticket", f"[Guild {ctx.guild} {ctx.guild.id}] {ctx.author} ({ctx.author.id}) created guild ticket category {gticketid}.", ctx.guild.id)

    def AliasSearch(self, guildid, value):
        if value is None:
            return []
        value = value.lower()
        conn = newconn()
        cur = conn.cursor()
        cur.execute(f"SELECT elementid, label FROM alias WHERE guildid = {guildid} AND elementtype = 'ticket'")
        t = cur.fetchall()
        alias = {}
        for tt in t:
            alias[f"{b64d(tt[1])} (g{tt[0]})"] = tt[0]
        if value.replace(" ", "") == "":
            return list(alias.keys())[:10]
        res = process.extract(value, alias.keys(), score_cutoff = 60, limit = 10)
        ret = []
        for t in res:
            ret.append(t[0])
        return ret

    async def AliasAutocomplete(self, ctx: discord.AutocompleteContext):
        return self.AliasSearch(ctx.interaction.guild_id, ctx.value)

    @manage.command(name="edit", description="Staff - Edit a ticket category.")
    async def edit(self, ctx, gticketid: discord.Option(str, "Ticket category id", required = False),
            label: discord.Option(str, "Ticket label, alias of gticketid", required = False, autocomplete = AliasAutocomplete),
            category: discord.Option(discord.CategoryChannel, "Guild category where tickets will be created", required = False),
            newlabel: discord.Option(str, "A easy-to-remember label, not visible to members, used as ticket id only when managing ticket", required = False),
            channelformat: discord.Option(str, "Channel name format, accept {username} {userid} {ticketid} variables, default 'ticket-{username}'", name="format", required = False),
            msg: discord.Option(str, "Message to send after user created ticket", required = False),
            moderator: discord.Option(str, "Mention Roles or Users who can view the ticket, separate with spaces, default administrative staff", required = False)):

        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return

        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return

        conn = newconn()
        cur = conn.cursor()
        guildid = ctx.guild.id
        if gticketid == None and label == None:
            await ctx.respond("You must provide either ticket category id or ticket label!", ephemeral = True)
            return

        if gticketid is None:
            gticketid = self.AliasSearch(ctx.guild.id, label)
            if len(gticketid) == 0:
                await ctx.respond("Failed to get gticketid by label.\nPlease use gticketid instead.\nOr use `/ticket list` to list all ticket categories in this guild.", ephemeral = True)
                return
            gticketid = gticketid[0][gticketid[0].rfind("(") + 2 : gticketid[0].rfind(")")]
        else:
            if gticketid.startswith("g"):
                gticketid = gticketid[1:]
            try:
                gticketid = int(gticketid)
            except:
                await ctx.respond("Invalid gticketid!", ephemeral = True)
                return
        cur.execute(f"SELECT categoryid, channelformat, msg, moderator FROM ticket WHERE guildid = {guildid} AND gticketid = {gticketid}")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond("Ticket category not found!", ephemeral = True)
            return
        
        categoryid = t[0][0]
        if category != None:
            categoryid = category.id

        if channelformat == None:
            channelformat = b64d(t[0][1])
        
        if msg == None:
            msg = b64d(t[0][2])
        
        tmoderator = []
        if moderator != None:
            if moderator != "":
                moderator = moderator.split(" ")
                tmoderator = []
                for i in range(len(moderator)):
                    moderator[i] = moderator[i].strip()
                    if moderator[i].startswith("<@") and moderator[i].endswith(">"):
                        moderator[i] = moderator[i].replace("@!","@")
                        tmoderator.append(moderator[i][1:-1])
        else:
            tmoderator = t[0][3].split(",")
        
        cur.execute(f"UPDATE ticket SET categoryid = {categoryid}, channelformat = '{b64e(channelformat)}', msg = '{b64e(msg)}', moderator = '{','.join(tmoderator)}' WHERE gticketid = {gticketid} AND guildid = {ctx.guild.id}")

        if newlabel != None:
            cur.execute(f"UPDATE alias SET label = '{b64e(newlabel)}' WHERE guildid = {guildid} AND elementtype = 'ticket' AND elementid = {gticketid}")
        
        conn.commit()

        await ctx.respond(f"Guild ticket (g{gticketid}) category updated!")
        await log("Ticket", f"[Guild {ctx.guild} {ctx.guild.id}] {ctx.author} ({ctx.author.id}) edited guild ticket category {gticketid}.", ctx.guild.id)

    @manage.command(name="delete", description="Staff - Delete a ticket category.")
    async def delete(self, ctx, gticketid: discord.Option(str, "Ticket category id (g...)", required = False),
            label: discord.Option(str, "Ticket label, alias of gticketid", required = False, autocomplete = AliasAutocomplete)):
        
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return

        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return

        conn = newconn()
        cur = conn.cursor()
        guildid = ctx.guild.id
        
        if gticketid == None and label == None:
            await ctx.respond("You must provide either ticket category id or ticket label!", ephemeral = True)
            return

        if gticketid is None:
            gticketid = self.AliasSearch(ctx.guild.id, label)
            if len(gticketid) == 0:
                await ctx.respond("Failed to get gticketid by label.\nPlease use gticketid instead.\nOr use `/ticket list` to list all ticket categories in this guild.", ephemeral = True)
                return
            gticketid = gticketid[0][gticketid[0].rfind("(") + 1 : gticketid[0].rfind(")")]
        else:
            if gticketid.startswith("g"):
                gticketid = gticketid[1:]
            try:
                gticketid = int(gticketid)
            except:
                await ctx.respond("Invalid gticketid!", ephemeral = True)
                return
            cur.execute(f"SELECT * FROM ticket WHERE guildid = {guildid} AND gticketid = {gticketid}")
            t = cur.fetchall()
            if len(t) == 0:
                await ctx.respond("Ticket category not found!", ephemeral = True)
                return

        cur.execute(f"UPDATE ticket SET gticketid = -gticketid WHERE guildid = {guildid} AND gticketid = {gticketid}")
        cur.execute(f"DELETE FROM alias WHERE guildid = {guildid} AND elementid = {gticketid} AND elementtype = 'ticket'")
        conn.commit()

        await ctx.respond("Ticket category deleted!\n\nBe aware that ticket records are not deleted.\nYou have to use `/ticket deleterecord` to delete them.")
        await log("Ticket", f"[Guild {ctx.guild} {ctx.guild.id}] {ctx.author} ({ctx.author.id}) deleted guild ticket category {gticketid}.", ctx.guild.id)
    
    @manage.command(name="list", description="Staff - List all ticket categories.")
    async def list(self, ctx):
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return

        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return

        conn = newconn()
        cur = conn.cursor()
        guildid = ctx.guild.id
        cur.execute(f"SELECT gticketid, categoryid, channelformat, msg, moderator FROM ticket WHERE guildid = {guildid}")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond("No ticket categories found!", ephemeral = True)
            return

        res = ""
        for tt in t:
            gticketid = tt[0]
            categoryid = tt[1]
            channelformat = b64d(tt[2])

            msg = b64d(tt[3])
            if msg == "":
                msg = "*None*"

            moderator = tt[4].split(",")
            tmoderator = ""
            if len(moderator) == 0:
                moderator = "*All administrative staff*"
            else:
                tmoderator = []
                for moderatord in moderator:
                    tmoderator.append(f"<{moderatord}>")
                tmoderator = " ".join(tmoderator)

            label = "None"
            cur.execute(f"SELECT label FROM alias WHERE guildid = {guildid} AND elementtype = 'ticket' AND elementid = {gticketid}")
            p = cur.fetchall()
            if len(p) > 0:
                label = b64d(p[0][0])

            cur.execute(f"SELECT COUNT(*) FROM ticketrecord WHERE guildid = {guildid} AND gticketid = {gticketid}")
            p = cur.fetchall()
            cnt = 0
            if len(p) > 0:
                cnt = p[0][0]

            res += f"**ID:** g{gticketid}\n"
            res += f"**Label:** {label}\n"
            res += f"**Guild Category:** <#{categoryid}>\n"
            res += f"**Moderator:** {tmoderator}\n"
            res += f"**Channel Format:** {channelformat}\n"
            res += f"**Message:** {msg}\n\n"
        
        if len(res) <= 5000:
            embed = discord.Embed(title = "Ticket Categories", description = res, color = GECKOCLR)
            embed.set_footer(text = f"Gecko Ticket", icon_url = GECKOICON)
            await ctx.respond(embed = embed)
        
        else:
            f = io.BytesIO()
            f.write(res.encode())
            f.seek(0)
            await ctx.respond(file=discord.File(fp=f, filename='TicketCategories.MD'))

    @manage.command(name="listrecord", description="Staff - List all ticket records")
    async def downloadall(self, ctx, reqstatus: discord.Option(str, "List only ongoing / closed tickets", name="status", required = False, choices = ["All", "Closed", "Ongoing"])):
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return

        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return

        conn = newconn()
        cur = conn.cursor()
        guildid = ctx.guild.id

        cur.execute(f"SELECT ticketid, gticketid, userid, closedBy, closedTs FROM ticketrecord WHERE guildid = {guildid}")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond("No ticket records found!", ephemeral = True)
            return
        res = ""
        for tt in t:
            ticketid = tt[0]
            gticketid = tt[1]
            userid = tt[2]
            closedBy = tt[3]
            closedTs = tt[4]

            if closedBy != 0 and reqstatus == "Ongoing":
                continue
            if closedBy == 0 and reqstatus == "Closed":
                continue

            if closedBy == 0:
                closedBy = "None"
            else:
                closedBy = f"<@{closedBy}>"

            status = "Ongoing"
            if closedBy != 0:
                status = "Closed"

            res += f"ID: {ticketid} ({status})\n"
            res += f"Guild Ticket ID: g{gticketid}\n"
            res += f"Created By: <@{userid}>\n"
            if closedBy != 0:
                res += f"Closed By: {closedBy}\n"
                res += f"Closed At: <t:{closedTs}>\n\n"
        
        if len(res) <= 5000:
            embed = discord.Embed(title = "Ticket Records", description = res, color = GECKOCLR)
            embed.set_footer(text = f"Gecko Ticket", icon_url = GECKOICON)
            await ctx.respond(embed = embed)
        
        else:
            f = io.BytesIO()
            f.write(res.encode())
            f.seek(0)
            await ctx.respond(file=discord.File(fp=f, filename='TicketRecords.MD'))

    @manage.command(name="viewrecord", description="View a ticket record.")
    async def viewrecord(self, ctx, ticketid: discord.Option(int, "Ticket ID")):
        conn = newconn()
        cur = conn.cursor()

        cur.execute(f"SELECT userid, data, closedBy, closedTs FROM ticketrecord WHERE ticketid = {ticketid}")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond("Ticket not found!", ephemeral = True)
            return
        creator = t[0][0]
        data = t[0][1]
        closedBy = t[0][2]
        closedTs = t[0][3]

        if creator != ctx.author.id:
            if ctx.guild is None:
                await ctx.respond("You are not the creator of the ticket! You can only run this command in guild if you are staff.", ephemeral = True)
                return
            guildid = ctx.guild.id
            if not isStaff(ctx.guild, ctx.author):
                await ctx.respond("Only staff / ticket creator are allowed to run the command!", ephemeral = True)
                return

        closedBy = f"<@{closedBy}> (`{closedBy}`)"
        
        embed = discord.Embed(title = "Ticket Record", description = "Conversation record in attached file", color = GECKOCLR)
        embed.add_field(name = "Created By", value = f"<@{creator}> (`{creator}`)", inline = True)
        if closedBy != 0:
            embed.add_field(name = "Closed By", value = closedBy, inline = True)
            embed.add_field(name = "Closed At", value = f"<t:{closedTs}>", inline = True)
        embed.timestamp = datetime.now()
        embed.set_footer(text = f"Gecko Ticket • ID: {ticketid} ", icon_url = GECKOICON)

        await ctx.respond(embed = embed, file=discord.File(io.BytesIO(b64d(data).encode()), filename=f"Ticket-{ticketid}.html"))

    @manage.command(name="deleterecord", description="Delete ticket records. Use '/ticket listrecord' to get a file of all ticket records in this guild.")
    async def deleterecord(self, ctx, ticketid: discord.Option(int, "Ticket record id, displayed when ticket is created, NOT ticket category id")):
        conn = newconn()
        cur = conn.cursor()
        guildid = ctx.guild.id

        cur.execute(f"SELECT userid FROM ticketrecord WHERE ticketid = {ticketid}")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond("Ticket not found!", ephemeral = True)
            return
        creator = t[0][0]

        if creator != ctx.author.id:
            if ctx.guild is None:
                await ctx.respond("You are not the creator of the ticket! You can only run this command in guild if you are staff.", ephemeral = True)
                return
            if not isStaff(ctx.guild, ctx.author):
                await ctx.respond("Only staff / ticket creator are allowed to run the command!", ephemeral = True)
                return

        cur.execute(f"UPDATE ticketrecord SET data = '', ticketid = -ticketid WHERE ticketid = {ticketid}")
        conn.commit()

        await ctx.respond("Ticket record deleted!")
        await log("Ticket", f"[Guild {ctx.guild} {ctx.guild.id}] {ctx.author} ({ctx.author.id}) edited ticket record {ticketid}.", ctx.guild.id)

bot.add_cog(ManageTicket(bot))