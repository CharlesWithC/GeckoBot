# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# TruckersMP


import os, asyncio
import discord
from discord.ext import commands
import time
from datetime import datetime
import requests
import json

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

@bot.slash_command(name="truckersmp", alias=["tmp"], description="TruckersMP")
async def truckersmp(ctx, name: discord.Option(str, "TruckersMP Name (Offline players are cached when they were online and might not update / show up)", required = False, autocomplete = PlayerAutocomplete),
        mpid: discord.Option(int, "TruckersMP ID (This can retrieve all info about the player)", required = False),
        server: discord.Option(str, "TruckersMP Server (To get the top traffic locations)", required = False, autocomplete = ServerAutocomplete),
        location: discord.Option(str, "Traffic of a specific location, require server argument.", required = False, autocomplete = LocationAutocomplete),
        country: discord.Option(str, "Traffic of all locations in a specific country, require server argument.", required = False, autocomplete = CountryAutocomplete),
        hrmode: discord.Option(str, "HR Mode, to get play hour and ban history", required = False, choices = ["Yes", "No"])):
    
    if hrmode == "Yes":
        if name is None and mpid is None:
            await ctx.respond(f"Please specify a player name or TruckersMP ID.")
            return
        if mpid is None:
            name = SearchName(name)[0]
            mpid = Name2ID(name)

        d = GetTMPData(mpid)
        if d is None:
            await ctx.respond(f"Player not found.")
            return

        embed = discord.Embed(title = f"{d['name']}", color = TMPCLR)
        patreon = d["patreon"]
        avatar = d["avatar"]
        joinDate = d["joinDate"]
        group = d["group"]
        vtc = f"**{d['vtc']}**{d['vtcpos']}"

        embed.set_thumbnail(url = avatar)
        if not patreon:
            embed.add_field(name = "TruckersMP ID", value = f'[{d["mpid"]}](https://truckersmp.com/user/{d["mpid"]})', inline = True)
        else:
            embed.add_field(name = "TruckersMP ID", value = f'[{d["mpid"]}](https://truckersmp.com/user/{d["mpid"]})' + " <:patreon:963787835637399602>", inline = True)
        embed.add_field(name = "Join Date", value = joinDate, inline = True)
        embed.add_field(name = "Group", value = group, inline = True)
        steam = GetSteamUser(d["steamid"])
        if steam != None:
            steamname = steam["personaname"]
            steamurl = steam["profileurl"]
            steamid = d["steamid"]
            embed.add_field(name = "Steam", value = f'[{steamname}]({steamurl}) (`{steamid}`)', inline = False)
        else:
            embed.add_field(name = "Steam ID", value = f"[{steamid}](https://steamcommunity.com/profiles/{steamid})", inline = False)
        if d["vtcid"] != 0:
            embed.add_field(name = "Virtual Trucking Company", value = vtc, inline = False)
        else:
            embed.add_field(name = "Virtual Trucking Company", value = "*Not in any VTC*", inline = False)
        
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
    
    elif name != None:
        player = name.replace(" ", "")
        if player == "":
            await ctx.respond(PNF)
            return
        player = SearchName(player)[0]
        mpid = Name2ID(player)
        if mpid is None:
            await ctx.respond(PNF)
            return
        player = GetMapLoc(mpid)

        embed = None

        d = GetTMPData(mpid)
        if d != None:
            embed = discord.Embed(title = f"{d['name']}", color = TMPCLR)
            patreon = d["patreon"]
            avatar = d["avatar"]
            joinDate = d["joinDate"]
            group = d["group"]
            vtc = f"**{d['vtc']}**{d['vtcpos']}"

            embed.set_thumbnail(url = avatar)
            if not patreon:
                embed.add_field(name = "TruckersMP ID", value = f'[{d["mpid"]}](https://truckersmp.com/user/{d["mpid"]})', inline = True)
            else:
                embed.add_field(name = "TruckersMP ID", value = f'[{d["mpid"]}](https://truckersmp.com/user/{d["mpid"]})' + " <:patreon:963787835637399602>", inline = True)
            embed.add_field(name = "Join Date", value = joinDate, inline = True)
            embed.add_field(name = "Group", value = group, inline = True)
            steam = GetSteamUser(d["steamid"])
            if steam != None:
                steamname = steam["personaname"]
                steamurl = steam["profileurl"]
                steamid = d["steamid"]
                embed.add_field(name = "Steam", value = f'[{steamname}]({steamurl}) (`{steamid}`)', inline = False)
            else:
                embed.add_field(name = "Steam ID", value = f"[{steamid}](https://steamcommunity.com/profiles/{steamid})", inline = False)
            if d["vtcid"] != 0:
                embed.add_field(name = "Virtual Trucking Company", value = vtc, inline = False)
        else:
            if embed is None:
                embed = discord.Embed(title = f"{name}", color = TMPCLR)
            embed.add_field(name = "TruckersMP ID", value = f'[{d["mpid"]}](https://truckersmp.com/user/{d["mpid"]})', inline = True)

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

    elif mpid != None:
        d = GetTMPData(mpid)
        if d is None:
            await ctx.respond(f"Player not found.")
            return

        embed = discord.Embed(title = f"{d['name']}", color = TMPCLR)
        patreon = d["patreon"]
        avatar = d["avatar"]
        joinDate = d["joinDate"]
        group = d["group"]
        vtc = f"**{d['vtc']}**{d['vtcpos']}"

        embed.set_thumbnail(url = avatar)
        if not patreon:
            embed.add_field(name = "TruckersMP ID", value = f'[{d["mpid"]}](https://truckersmp.com/user/{d["mpid"]})', inline = True)
        else:
            embed.add_field(name = "TruckersMP ID", value = f'[{d["mpid"]}](https://truckersmp.com/user/{d["mpid"]})' + " <:patreon:963787835637399602>", inline = True)
        embed.add_field(name = "Join Date", value = joinDate, inline = True)
        embed.add_field(name = "Group", value = group, inline = True)
        steam = GetSteamUser(d["steamid"])
        if steam != None:
            steamname = steam["personaname"]
            steamurl = steam["profileurl"]
            steamid = d["steamid"]
            embed.add_field(name = "Steam", value = f'[{steamname}]({steamurl}) (`{steamid}`)', inline = False)
        else:
            embed.add_field(name = "Steam ID", value = f"[{steamid}](https://steamcommunity.com/profiles/{steamid})", inline = False)
        if d["vtcid"] != 0:
            embed.add_field(name = "Virtual Trucking Company", value = vtc, inline = False)
            
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

        embed.timestamp = datetime.fromtimestamp(d["lastupd"])
        embed.set_footer(text = f"TruckersMP ", icon_url = f"https://forum.truckersmp.com/uploads/monthly_2020_10/android-chrome-256x256.png")

        await ctx.respond(embed = embed)
    
    elif location != None:
        if server is None:
            await ctx.respond(f"Server is required.")
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
            await ctx.respond(f"Server is required.")
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
            if "offline" in server.keys() and server["offline"]:
                embed.add_field(name = dd, value = "```Offline```", inline = True)
                continue
            players = server["players"]
            embed.add_field(name = dd, value = f"```{players} Online```", inline = True)
            lastupd = server["lastupd"]
        
        embed.timestamp = datetime.fromtimestamp(lastupd)
        embed.set_thumbnail(url = "https://forum.truckersmp.com/uploads/monthly_2020_10/android-chrome-256x256.png")
        embed.set_footer(text = f"TruckersMP • traffic.krashnz.com ", icon_url = f"https://forum.truckersmp.com/uploads/monthly_2020_10/android-chrome-256x256.png")

        await ctx.respond(embed = embed)