# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# TruckersMP

import os, asyncio
import discord
from discord.ext import commands
from discord.ui import Button, View
from discord.enums import ButtonStyle
from discord.ext.commands import CooldownMapping, Cooldown, BucketType
import time
from datetime import datetime
import requests
import json, io

from bot import bot
from settings import *
from functions import *
from db import newconn
from truckersmp.tmp import *

PNF = """Player not found or not cached.
Gecko caches all the players it found on the map, and if the player is not cached, it will not show up in the name search.
Please use TruckersMP ID instead, and bot will cache the player.

**NOTE** Player profile & VTC infomration updates each 3 hours, map data is realtime."""

async def PlayerAutocomplete(ctx: discord.AutocompleteContext):
    if ctx.value.replace(" ", "") == "":
        return []
    return SearchName(ctx.value)

async def ServerAutocomplete(ctx: discord.AutocompleteContext):
    return SearchServer(ctx.value)

async def LocationAutocomplete(ctx: discord.AutocompleteContext):
    server = ctx.options["server"]
    if server is None:
        return ["You must specify a server"]
    server = SearchServer(server)[0]
    if ctx.value.replace(" ","") == "":
        return location[server][:10]
    return SearchLocation(server, ctx.value)

async def CountryAutocomplete(ctx: discord.AutocompleteContext):
    server = ctx.options["server"]
    if server is None:
        return ["You must specify a server"]
    server = SearchServer(server)[0]
    if ctx.value.replace(" ","") == "":
        return country[server][:10]
    return SearchCountry(server, ctx.value)

@bot.slash_command(name="truckersmp", alias=["tmp"], description="TruckersMP (30 attempt / 10 min)", cooldown = CooldownMapping(Cooldown(30, 600), BucketType.user))
async def truckersmp(ctx, name: discord.Option(str, "TruckersMP Name (cache)", required = False, autocomplete = PlayerAutocomplete),
        mpid: discord.Option(int, "TruckersMP ID", required = False),
        mention: discord.Option(discord.User, "Discord Mention (cache / manual bind)", required = False),
        playerid: discord.Option(int, "Player In-game ID, require server argument, this might only work for ETS2 SIM 1", required = False),
        steamid: discord.Option(str, "Steam ID (cache)", required = False),
        server: discord.Option(str, "TruckersMP Server", required = False, autocomplete = ServerAutocomplete),
        location: discord.Option(str, "Get traffic of location, require server argument.", required = False, autocomplete = LocationAutocomplete),
        country: discord.Option(str, "Get traffic of all locations in the country, require server argument.", required = False, autocomplete = CountryAutocomplete),
        hrmode: discord.Option(str, "HR Mode, to get play hour and ban history", required = False, choices = ["Yes", "No"])):
    
    await ctx.defer()
    if name != None or mpid != None or mention != None or playerid != None or steamid != None:
        player = None
        if name != None:
            player = name.replace(" ", "")
            if player == "":
                await ctx.respond(PNF)
                return
            player = SearchName(player)[0]
            mpid = Name2ID(player)
            if mpid is None:
                await ctx.respond(PNF)
                return
        
        elif mention != None:
            discordid = mention.id
            mpid = Discord2Mp(discordid)
            if mpid is None:
                await ctx.respond(f"{mention} has not bound their Discord account with TruckersMP Profile, and Gecko has not cached their profile.")
                return
            d = GetTMPData(mpid)
            if d is None:
                await ctx.respond(f"Player not found.")
                return

        elif playerid != None:
            if server is None:
                await ctx.respond(f"You need to specify a server.")
                return
            server = SearchServer(server)[0]
            mpid = PlayerID2Mp(server, playerid)
            if mpid is None:
                await ctx.respond(f"Player not online or wrong server.")
                return
        
        elif steamid != None:
            mpid = Steam2Mp(steamid)
            if mpid is None:
                await ctx.respond(f"Gecko has not cached the player's steam profile.\nAt least one normal lookup is needed to cache and enable steam ID lookup.")
                return

        embed = None

        d = GetTMPData(mpid)
        if d != None:
            embed = discord.Embed(title = f"{d['name']}", color = TMPCLR)
            patreon = d["patreon"]
            avatar = d["avatar"]
            joinDate = d["joinDate"]
            group = d["group"]
            vtc = f"**[{d['vtc']}](https://truckersmp.com/vtc/{d['vtcid']})**{d['vtcpos']}"

            embed.set_thumbnail(url = avatar)
            if not patreon:
                embed.add_field(name = "TruckersMP ID", value = f'[{d["mpid"]}](https://truckersmp.com/user/{d["mpid"]})', inline = True)
            else:
                embed.add_field(name = "TruckersMP ID", value = f'[{d["mpid"]}](https://truckersmp.com/user/{d["mpid"]})' + " <:patreon:963787835637399602>", inline = True)
            embed.add_field(name = "Join Date", value = joinDate, inline = True)
            embed.add_field(name = "Group", value = group, inline = True)
            steam = GetSteamUser(mpid, d["steamid"])
            if steam != None:
                steamname = steam["personaname"]
                steamurl = steam["profileurl"]
                steamid = d["steamid"]
                embed.add_field(name = "Steam", value = f'[{steamname}]({steamurl}) (`{steamid}`)', inline = False)
            else:
                embed.add_field(name = "Steam ID", value = f"[{steamid}](https://steamcommunity.com/profiles/{steamid})", inline = False)
            
            discordid = d["discordid"]
            if discordid != None:
                user = bot.get_user(int(discordid))
                if user != None:
                    if ctx.guild != None and await ctx.guild.fetch_member(user.id) != None:
                        embed.add_field(name = "Discord", value = f"<@{discordid}> (`{discordid}`)")
                    else:
                        embed.add_field(name = "Discord", value = f"{user.name}#{user.discriminator} (`{discordid}`)")

            if d["vtcid"] != 0:
                embed.add_field(name = "Virtual Trucking Company", value = vtc, inline = False)
        else:
            if embed is None:
                embed = discord.Embed(title = f"{name}", color = TMPCLR)
            embed.add_field(name = "TruckersMP ID", value = f'[{d["mpid"]}](https://truckersmp.com/user/{d["mpid"]})', inline = True)
        
        if hrmode != "Yes":
            player = GetMapLoc(mpid)
            if player != None:
                if embed is None:
                    embed = discord.Embed(title = f"{player['name']}", color = TMPCLR)
                embed.add_field(name = "Server", value = player["server"], inline = True)
                embed.add_field(name = "Player ID", value = player["playerid"], inline = True)
                location = player["city"] + ", " + player["country"]
                if player["distance"] != 0:
                    dis = player['distance']
                    if dis > 10:
                        dis = int(dis)
                    location = f"Near **{location}**"
                embed.add_field(name = "Location", value = location, inline = False)
                embed.timestamp = datetime.fromtimestamp(player["time"])
            else:
                embed.timestamp = datetime.now()

            if player != None:
                embed.set_footer(text = f"TruckersMP • TruckyApp ", icon_url = f"https://forum.truckersmp.com/uploads/monthly_2020_10/android-chrome-256x256.png")
            else:
                embed.set_footer(text = f"TruckersMP ", icon_url = f"https://forum.truckersmp.com/uploads/monthly_2020_10/android-chrome-256x256.png")
            await ctx.respond(embed = embed)

        else:
            data = GetHRData(mpid)
            if data != None:
                ets2hour = data["ets2hour"]
                atshour = data["atshour"]
                if ets2hour == -1 or atshour == -1:
                    embed.add_field(name = "Play hour", value = f"*Steam profile is private*", inline = False)
                else:
                    embed.add_field(name = "ETS2", value = f"{ets2hour} hours", inline = True)
                    embed.add_field(name = "ATS", value = f"{atshour} hours", inline = True)
                    embed.add_field(name = "Total", value = f"{ets2hour + atshour} hours", inline = True)

                embed.add_field(name = "Active bans", value = data["bansCount"], inline = True)
                if data["banned"]:
                    bannedUntil = data["bannedUntil"]
                    if bannedUntil == None:
                        bannedUntil = "Permanently banned"
                    else:
                        bannedUntil = f"Banned until {bannedUntil}"
                    embed.add_field(name = "Status", value = bannedUntil, inline = True)
                else:
                    embed.add_field(name = "Status", value = f"Not banned", inline = True)

                if not data["displayBans"]:
                    embed.add_field(name = "History bans (latest 5)", value = "*Private*", inline = False)
                else:
                    historyban = ""
                    if len(data["bans"]) == 0:
                        historyban = "*Player has not been banned before*"
                    else:
                        for ban in data["bans"]:
                            historyban += f"{ban['timeAdded']} ~ {ban['expiration']}\nFor `{ban['reason']}` by **{ban['adminName']}**\n\n"
                    embed.add_field(name = "History bans (latest 5)", value = historyban, inline = False)
            
            embed.timestamp = datetime.now()
            embed.set_footer(text = f"TruckersMP • HR Mode ", icon_url = f"https://forum.truckersmp.com/uploads/monthly_2020_10/android-chrome-256x256.png")

            await ctx.respond(embed = embed)
    
    elif location != None:
        if server is None:
            await ctx.respond(f"You need to specify a server.")
            return
        server = SearchServer(server)[0]
        servername = server
        server = traffic[server]
        if "offline" in server.keys() and server["offline"]:
            embed = discord.Embed(title = server, description=f"Server offline", color = TMPCLR)
            embed.set_thumbnail(url = "https://forum.truckersmp.com/uploads/monthly_2020_10/android-chrome-256x256.png")
            embed.set_footer(text = f"TruckersMP • traffic.krashnz.com ", icon_url = f"https://forum.truckersmp.com/uploads/monthly_2020_10/android-chrome-256x256.png")
            await ctx.respond(embed = embed)
            return
        players = server["players"]
        lastupd = server["lastupd"]
        embed = discord.Embed(title = servername, description=f"Players Trucking: **{players}**", color = TMPCLR)

        loc = location
        location = SearchLocation(servername, location)[0]
        if not location in server["traffic"].keys():
            await ctx.respond(f"**{location}** is not in server **{servername}**")
            return
        t = server["traffic"][location]
        severity = t["severity"]
        players = t["players"]
        embed.add_field(name = loc, value = f"**{severity}** ({players})", inline = True)

        embed.timestamp = datetime.fromtimestamp(lastupd)
        embed.set_thumbnail(url = "https://forum.truckersmp.com/uploads/monthly_2020_10/android-chrome-256x256.png")
        embed.set_footer(text = f"TruckersMP • traffic.krashnz.com ", icon_url = f"https://forum.truckersmp.com/uploads/monthly_2020_10/android-chrome-256x256.png")

        await ctx.respond(embed = embed)
    
    elif country != None:
        if server is None:
            await ctx.respond(f"You need to specify a server.")
            return
        server = SearchServer(server)[0]
        servername = server
        server = traffic[server]
        if "offline" in server.keys() and server["offline"]:
            embed = discord.Embed(title = server, description=f"Server offline", color = TMPCLR)
            embed.set_thumbnail(url = "https://forum.truckersmp.com/uploads/monthly_2020_10/android-chrome-256x256.png")
            embed.set_footer(text = f"TruckersMP • traffic.krashnz.com ", icon_url = f"https://forum.truckersmp.com/uploads/monthly_2020_10/android-chrome-256x256.png")
            await ctx.respond(embed = embed)
            return
        players = server["players"]
        lastupd = server["lastupd"]
        country = SearchCountry(servername, country)[0]
        totplayer = 0
        for location in server["ctraffic"][country]:
            players = location["players"]
            totplayer += players
        embed = discord.Embed(title = servername + " - " + country, description=f"Players in **{country}**: **{totplayer}**", color = TMPCLR)
        if not country in server["ctraffic"].keys():
            await ctx.respond(f"**{country}** is not in server **{servername}**")
            return
        for location in server["ctraffic"][country]:
            loc = location["location"]
            severity = location["severity"]
            players = location["players"]
            embed.add_field(name = loc, value = f"**{severity}** ({players})", inline = True)

        embed.timestamp = datetime.fromtimestamp(lastupd)
        embed.set_thumbnail(url = "https://forum.truckersmp.com/uploads/monthly_2020_10/android-chrome-256x256.png")
        embed.set_footer(text = f"TruckersMP • traffic.krashnz.com ", icon_url = f"https://forum.truckersmp.com/uploads/monthly_2020_10/android-chrome-256x256.png")

        await ctx.respond(embed = embed)
    
    elif server != None:
        server = SearchServer(server)[0]
        servername = server
        server = traffic[server]
        if "offline" in server.keys() and server["offline"]:
            embed = discord.Embed(title = server, description=f"Server offline", color = TMPCLR)
            embed.set_thumbnail(url = "https://forum.truckersmp.com/uploads/monthly_2020_10/android-chrome-256x256.png")
            embed.set_footer(text = f"TruckersMP • traffic.krashnz.com ", icon_url = f"https://forum.truckersmp.com/uploads/monthly_2020_10/android-chrome-256x256.png")
            await ctx.respond(embed = embed)
            return
        players = server["players"]
        lastupd = server["lastupd"]
        embed = discord.Embed(title = servername, description=f"Players Trucking: **{players}**", color = TMPCLR)
        for location in server["top"]:
            loc = location["name"] + ", " + location["country"]
            severity = location["severity"]
            players = location["players"]
            embed.add_field(name = loc, value = f"**{severity}** ({players})", inline = True)
        
        embed.timestamp = datetime.fromtimestamp(lastupd)
        embed.set_thumbnail(url = "https://forum.truckersmp.com/uploads/monthly_2020_10/android-chrome-256x256.png")
        embed.set_footer(text = f"TruckersMP • traffic.krashnz.com ", icon_url = f"https://forum.truckersmp.com/uploads/monthly_2020_10/android-chrome-256x256.png")

        await ctx.respond(embed = embed)

    else:
        d = traffic
        if d == {} or "offline" in d.keys() and d["offline"]:
            await ctx.respond("TruckersMP Servers are offline.")
            return
        lastupd = 0
        allplayer = d["allplayer"]
        embed = discord.Embed(title = f"TruckersMP Servers", description=f"Players Trucking: **{allplayer}**", color = TMPCLR)
        for dd in d.keys():
            server = d[dd]
            if type(server) != dict:
                continue
            name = dd
            name = name.replace(" ", "\n", 1)
            if "offline" in server.keys() and server["offline"]:
                embed.add_field(name = name, value = "```Offline```", inline = True)
                continue
            players = server["players"]
            embed.add_field(name = name, value = f"```{players} Online```", inline = True)
            lastupd = server["lastupd"]
        
        embed.timestamp = datetime.fromtimestamp(lastupd)
        embed.set_thumbnail(url = "https://forum.truckersmp.com/uploads/monthly_2020_10/android-chrome-256x256.png")
        embed.set_footer(text = f"TruckersMP • traffic.krashnz.com ", icon_url = f"https://forum.truckersmp.com/uploads/monthly_2020_10/android-chrome-256x256.png")

        await ctx.respond(embed = embed)

@bot.slash_command(name="tmpbind", description="Bind your TruckersMP profile to your Discord account (3 attempt / 10 min)", cooldown = CooldownMapping(Cooldown(3, 600), BucketType.user))
async def tmpbind(ctx, mpid: discord.Option(int, "Your TruckersMP User ID"),
        unbind: discord.Option(str, "Unbind your TruckersMP profile", required = False, choices = ["Yes", "No"])):
    await ctx.defer()
    conn = newconn()
    cur = conn.cursor()
    if unbind == "Yes":
        cur.execute(f"SELECT * FROM tmpbind WHERE discordid = {discordid}")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond("You are not bound to any TruckersMP profile.")
            return
        cur.execute(f"DELETE FROM tmpbind WHERE discordid = {discordid}")
        conn.commit()
        await ctx.respond("You have successfully unbound your TruckersMP profile.")
        return

    d = GetTMPData(mpid, clearcache = True)
    if d is None:
        await ctx.respond("TruckersMP user not found.")
        return
    if d["discordid"] is None:
        await ctx.respond("Please bind your Discord account on TruckersMP, and make it public visible.")
        return

    discordid = int(d["discordid"])
    if discordid == ctx.author.id:
        cur.execute(f"SELECT * FROM tmpbind WHERE discordid = {discordid}")
        t = cur.fetchall()
        if len(t) > 0:
            await ctx.respond("You are already bound to a TruckersMP profile.")
            return
        cur.execute(f"INSERT INTO tmpbind VALUES ({mpid}, {discordid})")
        conn.commit()
        await ctx.respond(f"Successfully bound to [{d['name']}](https://truckersmp.com/user/{mpid})")
    else:
        await ctx.respond(f"[{d['name']}](https://truckersmp.com/user/{mpid})'s Discord is not you!")

@bot.slash_command(name="vtcbind", description="Bind your VTC to this guild (3 attempt / 60 min)", cooldown = CooldownMapping(Cooldown(3, 3600), BucketType.guild))
async def vtcbind(ctx, vtcid: discord.Option(int, "The ID of your VTC", required = True),
        unbind: discord.Option(str, "Unbind VTC from this guild", required = False, choices = ["Yes", "No"])):
    if ctx.guild is None:
        await ctx.respond("You can only run this command in guilds!")
        return
    guildid = ctx.guild.id
    if not isStaff(ctx.guild, ctx.author):
        await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
        return

    await ctx.defer()

    conn = newconn()
    cur = conn.cursor()
    if unbind == "Yes":
        cur.execute(f"SELECT name FROM vtcbind WHERE guildid = {ctx.guild.id}")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond("This guild is not bound to a VTC!", ephemeral = True)
            return
        name = b64d(t[0][0])
        cur.execute(f"DELETE FROM vtcbind WHERE guildid = {ctx.guild.id}")
        conn.commit()
        await ctx.respond(f"This guild is no longer boung to VTC **{name}**.", ephemeral = True)
        return

    r = requests.get(f"https://api.truckersmp.com/v2/vtc/{vtcid}")
    if r.status_code != 200:
        await ctx.respond(f"TruckersMP API request failed. Please try again later...", ephemeral = True)
        return
    d = json.loads(r.text)
    if d["error"]:
        await ctx.respond(f"TruckersMP API error: {d['response']}", ephemeral = True)
        return
    d = d["response"]
    name = d["name"]
    invitelink = d["socials"]["discord"]
    if invitelink is None:
        await ctx.respond(f"Discord invite link not found for **{name}**. Make sure there's a valid invite link to this guild on TruckersMP.", ephemeral = True)
        return
    try:
        invites = await ctx.guild.invites()
    except:
        await ctx.respond(f"Failed to get invites for this guild. Please make sure I have permission to do that.", ephemeral = True)
        return
    found = False
    for invite in invites:
        if invite.url == invitelink:
            found = True
            break
    if not found:
        await ctx.respond(f"Discord invite link for **{name}** on TruckersMP doesn't link to this guild.", ephemeral = True)
        return
    cur.execute(f"DELETE FROM vtcbind WHERE vtcid = {vtcid}")
    cur.execute(f"INSERT INTO vtcbind VALUES ({ctx.guild.id}, {vtcid}, '{b64e(name)}')")
    conn.commit()
    await ctx.respond(f"Successfully bound the guild to VTC **{name}**!")

class EventButton(Button):
    def __init__(self, label, vtcid, eid, btntype, style, url = None):
        self.vtcid = vtcid
        self.eid = eid
        self.btntype = btntype
        super().__init__(
            label=label,
            url=url,
            style=style
        )  

    async def callback(self, interaction: discord.Interaction):    
        btntype = self.btntype
        vtcid = self.vtcid
        d = None
        if btntype == "close":
            await interaction.message.delete()
            return
        else:
            t = GetEvents(vtcid)
            if btntype == "next":
                for i in range(len(t)):
                    if t[i]["id"] == self.eid:
                        if i + 1 < len(t):
                            d = t[i+1]
                        else:
                            d = t[0]
                        break
            elif btntype == "previous":
                for i in range(len(t)):
                    if t[i]["id"] == self.eid:
                        if i - 1 >= 0:
                            d = t[i-1]
                        else:
                            d = t[-1]
                        break

        eid = d["id"]
        name = d["name"]
        server = d["server"]
        vtc = d["vtc"]
        creator = d["creator"]

        game = d["game"]
        emap = d["map"]
        departure = d["departure"]
        arrive = d["arrive"]
        ts = d["startat"]

        confirmed = d["confirmed"]
        unsure = d["unsure"]

        dlc = d["dlc"]
        dlcs = "*None*"
        if dlc != []:
            dlcs = ""
            for dd in dlc.keys():
                dlcs += f"{dlc[dd]}, "
            dlcs = dlcs[:-2]

        embed = discord.Embed(title = f"{name}", url=f"https://truckersmp.com{d['url']}", color = TMPCLR)
        embed.add_field(name = "Hosting VTC", value = f"{vtc}", inline = True)
        embed.add_field(name = "Created by", value = f"{creator}", inline = True)

        embed.add_field(name = "Server", value = f"{game} {server}", inline = False)

        embed.add_field(name = "From", value = f"{departure['city']}", inline = True)
        embed.add_field(name = "To", value = f"{arrive['city']}", inline = True)

        embed.add_field(name = "DLC Required", value = dlcs, inline = False)

        embed.add_field(name = "Starting time", value = f"<t:{ts}> (<t:{ts}:R>)", inline = False)

        embed.add_field(name = "Attendance", value = f"**{confirmed}** confirmed, **{unsure}** unsure", inline = False)

        embed.timestamp = datetime.fromtimestamp(ts)
        embed.set_thumbnail(url = "https://forum.truckersmp.com/uploads/monthly_2020_10/android-chrome-256x256.png")
        if emap != None:
            embed.set_image(url = emap)
        embed.set_footer(text = f"TruckersMP • Event #{eid} ", icon_url = f"https://forum.truckersmp.com/uploads/monthly_2020_10/android-chrome-256x256.png")
        
        view = View(timeout = None)
        button1 = EventButton("<< Previous <<", vtcid, eid, "previous", ButtonStyle.blurple)
        button2 = EventButton("Open on TruckersMP", vtcid, eid, "url", ButtonStyle.grey, f"https://truckersmp.com{d['url']}")
        button3 = EventButton(">> Next >>", vtcid, eid, "next", ButtonStyle.blurple)
        button4 = EventButton("X Close X", vtcid, eid, "close", ButtonStyle.red)
        view.add_item(button1)
        view.add_item(button2)
        view.add_item(button3)
        view.add_item(button4)

        await interaction.response.edit_message(embed = embed, view = view)    

@bot.slash_command(name="vtcevents", description="Get events the VTC is attending.")
async def vtcevents(ctx, vtcid: discord.Option(int, "Specify a VTC ID (optional if the guild is bound to a VTC)", required = False),
        listmode: discord.Option(str, "Show all the events in a list (or recent events + markdown file if too many)", required = False, choices = ["Yes", "No"])):
    conn = newconn()
    cur = conn.cursor()
    if vtcid is None:
        cur.execute(f"SELECT vtcid, name FROM vtcbind WHERE guildid = {ctx.guild.id}")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond("This guild is not bound to a VTC!\nUse `/vtcbind` to bind it first.", ephemeral = True)
            return
        vtcid = t[0][0]
        name = b64d(t[0][1])
    
    await ctx.defer()
    d = GetEvents(vtcid)
    if d is None:
        await ctx.respond(f"TruckersMP API request failed, or there's no events the VTC is attending.", ephemeral = True)
        return
    if len(d) == 0:
        await ctx.respond(f"The VTC is not attending any events.", ephemeral = True)
        return
    if listmode == "Yes":
        msg = ""
        tmsg = ""
        for dd in d:
            ts = dd["startat"]
            msg += f"[**{dd['name']}**](https://truckersmp.com{dd['url']}) (<t:{ts}:R>)\n"
            if len(msg) < 2000:
                tmsg = msg

        embed = discord.Embed(title = f"{VTCID2Name(vtcid)} - Events attending", description=tmsg, url=f"https://truckersmp.com/vtc/{vtcid}/events/attending", color = TMPCLR)
        embed.timestamp = datetime.now()
        embed.set_thumbnail(url = "https://forum.truckersmp.com/uploads/monthly_2020_10/android-chrome-256x256.png")
        if len(msg) > len(tmsg):
            f = io.BytesIO()
            f.write(msg.encode())
            f.seek(0)
            embed.set_footer(text = f"TruckersMP • VTC #{vtcid} • Events attending (Partial) ", icon_url = f"https://forum.truckersmp.com/uploads/monthly_2020_10/android-chrome-256x256.png")
            await ctx.respond(embed = embed, file = discord.File(fp=f, filename='AllEvents.MD'))
        else:
            embed.set_footer(text = f"TruckersMP • VTC #{vtcid} • Events attending ", icon_url = f"https://forum.truckersmp.com/uploads/monthly_2020_10/android-chrome-256x256.png")
            await ctx.respond(embed = embed)

        return

    d = d[0]
    eid = d["id"]
    name = d["name"]
    server = d["server"]
    vtc = d["vtc"]
    creator = d["creator"]

    game = d["game"]
    emap = d["map"]
    departure = d["departure"]
    arrive = d["arrive"]
    ts = d["startat"]

    confirmed = d["confirmed"]
    unsure = d["unsure"]

    dlc = d["dlc"]
    dlcs = "*None*"
    if dlc != []:
        dlcs = ""
        for dd in dlc.keys():
            dlcs += f"{dlc[dd]}, "
        dlcs = dlcs[:-2]

    embed = discord.Embed(title = f"{name}", url=f"https://truckersmp.com{d['url']}", color = TMPCLR)
    embed.add_field(name = "Hosting VTC", value = f"{vtc}", inline = True)
    embed.add_field(name = "Created by", value = f"{creator}", inline = True)

    embed.add_field(name = "Server", value = f"{game} {server}", inline = False)

    embed.add_field(name = "From", value = f"{departure['city']}", inline = True)
    embed.add_field(name = "To", value = f"{arrive['city']}", inline = True)

    embed.add_field(name = "DLC Required", value = dlcs, inline = False)

    embed.add_field(name = "Starting time", value = f"<t:{ts}> (<t:{ts}:R>)", inline = False)

    embed.add_field(name = "Attendance", value = f"**{confirmed}** confirmed, **{unsure}** unsure", inline = False)

    embed.timestamp = datetime.fromtimestamp(ts)
    embed.set_thumbnail(url = "https://forum.truckersmp.com/uploads/monthly_2020_10/android-chrome-256x256.png")
    if emap != None:
        embed.set_image(url = emap)
    embed.set_footer(text = f"TruckersMP • Event #{eid} ", icon_url = f"https://forum.truckersmp.com/uploads/monthly_2020_10/android-chrome-256x256.png")

    view = View(timeout = None)
    button1 = EventButton("<< Previous <<", vtcid, eid, "previous", ButtonStyle.blurple)
    button2 = EventButton("Open on TruckersMP", vtcid, eid, "url", ButtonStyle.grey, f"https://truckersmp.com{d['url']}")
    button3 = EventButton(">> Next >>", vtcid, eid, "next", ButtonStyle.blurple)
    button4 = EventButton("X Close X", vtcid, eid, "close", ButtonStyle.red)
    view.add_item(button1)
    view.add_item(button2)
    view.add_item(button3)
    view.add_item(button4)

    await ctx.respond(embed = embed, view = view)

@bot.slash_command(name="vtceventping", description="Send a message one hour before and the time an event starts.")
async def vtceventping(ctx, channel: discord.Option(discord.TextChannel, "Channel to send the message", required = True),
        msg: discord.Option(str, "Message to send, can contain @role pings", required = False),
        disable: discord.Option(str, "Disable event ping", required = False, choices = ["Yes", "No"])):

    if ctx.guild is None:
        await ctx.respond("You can only run this command in guilds!")
        return
    guildid = ctx.guild.id
    if not isStaff(ctx.guild, ctx.author):
        await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
        return
    
    await ctx.defer()

    conn = newconn()
    cur = conn.cursor()

    channelid = channel.id
    if msg is None:
        msg = ""
    
    if disable == "Yes":
        cur.execute(f"SELECT * FROM eventping WHERE guildid = {ctx.guild.id}")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond("Event pings not enabled!")
            return
        cur.execute(f"DELETE FROM eventping WHERE guildid = {ctx.guild.id}")
        conn.commit()

        await ctx.respond("Event pings disabled!")
    else:
        cur.execute(f"SELECT vtcid FROM vtcbind WHERE guildid = {ctx.guild.id}")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond("This guild is not bound to a VTC!\nUse `/vtcbind` to bind it first.", ephemeral = True)
            return
        vtcid = t[0][0]

        cur.execute(f"SELECT * FROM eventping WHERE guildid = {ctx.guild.id}")
        t = cur.fetchall()
        if len(t) == 0:
            cur.execute(f"INSERT INTO eventping VALUES ({ctx.guild.id}, {vtcid}, {channelid}, '{b64e(msg)}')")
        else:
            cur.execute(f"UPDATE eventping SET vtcid = {vtcid}, channelid = {channelid}, msg = '{b64e(msg)}' WHERE guildid = {ctx.guild.id}")
        conn.commit()
        
        await ctx.respond("Event pings enabled!")

async def EventPing():
    await bot.wait_until_ready()
    await asyncio.sleep(5)
    
    while not bot.is_closed():
        conn = newconn()
        cur = conn.cursor()
        cur.execute(f"SELECT guildid, vtcid, channelid, msg FROM eventping")
        t = cur.fetchall()
        for tt in t:
            try:
                guildid = tt[0]
                vtcid = tt[1]
                channelid = tt[2]
                channel = bot.get_channel(channelid)
                if channel is None:
                    continue
                msg = b64d(tt[3])
                d = GetEvents(vtcid)
                if d is None:
                    continue
                d = d[0]
                eid = d["id"]
                name = d["name"]
                server = d["server"]
                vtc = d["vtc"]
                creator = d["creator"]

                game = d["game"]
                emap = d["map"]
                departure = d["departure"]
                arrive = d["arrive"]
                ts = d["startat"]

                if ts - int(time.time()) <= 300: 
                    cur.execute(f"SELECT * FROM eventpinged WHERE vtcid = {vtcid} AND eventid = {eid}")
                    t = cur.fetchall()
                    if len(t) > 1:
                        continue
                    cur.execute(f"INSERT INTO eventpinged VALUES ({vtcid}, {eid})")
                    conn.commit()
                    msg = f"An event is starting very soon!\n{msg}"
                elif ts - int(time.time()) <= 3600:
                    cur.execute(f"SELECT * FROM eventpinged WHERE vtcid = {vtcid} AND eventid = {eid}")
                    t = cur.fetchall()
                    if len(t) > 0:
                        continue
                    cur.execute(f"INSERT INTO eventpinged VALUES ({vtcid}, {eid})")
                    conn.commit()
                    msg = f"An event is starting in one hour!\n{msg}"
                else:
                    continue

                confirmed = d["confirmed"]
                unsure = d["unsure"]

                dlc = d["dlc"]
                dlcs = "*None*"
                if dlc != []:
                    dlcs = ""
                    for dd in dlc.keys():
                        dlcs += f"{dlc[dd]}, "
                    dlcs = dlcs[:-2]

                embed = discord.Embed(title = f"{name}", url=f"https://truckersmp.com{d['url']}", color = TMPCLR)
                embed.add_field(name = "Hosting VTC", value = f"{vtc}", inline = True)
                embed.add_field(name = "Created by", value = f"{creator}", inline = True)

                embed.add_field(name = "Server", value = f"{game} {server}", inline = False)

                embed.add_field(name = "From", value = f"{departure['city']}", inline = True)
                embed.add_field(name = "To", value = f"{arrive['city']}", inline = True)

                embed.add_field(name = "DLC Required", value = dlcs, inline = False)

                embed.add_field(name = "Starting time", value = f"<t:{ts}> (<t:{ts}:R>)", inline = False)

                embed.add_field(name = "Attendance", value = f"**{confirmed}** confirmed, **{unsure}** unsure", inline = False)

                embed.timestamp = datetime.fromtimestamp(ts)
                embed.set_thumbnail(url = "https://forum.truckersmp.com/uploads/monthly_2020_10/android-chrome-256x256.png")
                if emap != None:
                    embed.set_image(url = emap)
                embed.set_footer(text = f"TruckersMP • Event #{eid} ", icon_url = f"https://forum.truckersmp.com/uploads/monthly_2020_10/android-chrome-256x256.png")

                await channel.send(content = msg, embed = embed)
            
            except:
                import traceback
                traceback.print_exc()
                continue

        await asyncio.sleep(30)

bot.loop.create_task(EventPing())