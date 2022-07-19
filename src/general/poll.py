# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Gecko Poll

import os, json, asyncio
import discord
from discord.commands import SlashCommandGroup
from discord.ext import commands
from discord.ui import Modal, InputText, Button, View
from discord.enums import ButtonStyle
from time import time
from datetime import datetime
from random import randint

from bot import bot
from settings import *
from functions import *
from db import newconn
from general.staff.button import GeckoButton

class PollEditModal(Modal):
    def __init__(self, expire, allowforward, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.expire = expire
        self.allowforward = allowforward
        self.add_item(InputText(label="description", required = True, style=discord.InputTextStyle.long))
        self.add_item(InputText(label="Choice 1", required = True, max_length = 50))
        self.add_item(InputText(label="Choice 2", required = True, max_length = 50))
        self.add_item(InputText(label="Choice 3 (Optional)", required = False, max_length = 50))
        self.add_item(InputText(label="Choice 4 (Optional)", required = False, max_length = 50))

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        userid = user.id
        expire = self.expire
        allowforward = self.allowforward

        description = self.children[0].value
        choice1 = self.children[1].value
        choice2 = self.children[2].value
        choice3 = self.children[3].value
        choice4 = self.children[4].value

        choices = [choice1, choice2]
        if choice3:
            choices.append(choice3)
        if choice4:
            choices.append(choice4)

        data = {"description": description, "choices": choices}
        data = b64e(json.dumps(data))

        channel = interaction.channel

        conn = newconn()
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM poll")
        t = cur.fetchall()
        pollid = 1
        if len(t) > 0:
            pollid = t[0][0] + 1

        view = View(timeout = None)

        embed = discord.Embed(title="Poll (Ongoing)", description=description, color=GECKOCLR)
        i = 0
        for choice in choices:
            embed.add_field(name=choice, value=f"{SPACE * 10} 0.00%", inline=False)
            
            i += 1
            uniq = f"{randint(1,100000)}{int(time()*100000)}"
            custom_id = "GeckoPoll-"+str(pollid)+"-"+str(i)+"-"+uniq
            button = GeckoButton(choice, None, BTNSTYLE["blurple"], False, custom_id)
            view.add_item(button)
            cur.execute(f"INSERT INTO buttonview VALUES ({pollid}, '{custom_id}')")

        # Refresh button
        uniq = f"{randint(1,100000)}{int(time()*100000)}"
        custom_id = "GeckoPoll-"+str(pollid)+"-0-"+uniq
        button = GeckoButton("Refresh", None, BTNSTYLE["red"], False, custom_id)
        view.add_item(button)
        cur.execute(f"INSERT INTO buttonview VALUES ({pollid}, '{custom_id}')")

        embed.add_field(name = "Voted", value = f"0", inline = True)

        if expire != -1:
            embed.add_field(name="End", value = f"<t:{expire}:R>", inline=True)
        else:
            embed.add_field(name="End", value = "Never", inline=True)
        embed.set_footer(text=f"Gecko Poll • ID: {pollid} • Refresh to sync between servers")

        message = await channel.send(embed = embed, view = view)

        cur.execute(f"INSERT INTO poll VALUES ({pollid}, {user.id}, '{data}', {expire}, {int(allowforward)})")
        conn.commit()

        await interaction.response.send_message(f"Poll created. Poll ID: {pollid}\nUse `/poll resend {pollid}` to send it anywhere, even to another server!", ephemeral = True)

class Poll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    poll = SlashCommandGroup("poll", "Poll")

    @poll.command(name="create", description="Create a poll, detailed information will be edited in modal")
    async def create(self, ctx, expire: discord.Option(str, "Leave empty for no end | Format: number + unit (s/m/h/d), e.g. 30m, 3d", required = False),
            allowforward: discord.Option(str, "Allow any user to resend this poll, if no, only you can resend it | default No", required = False, choices = ["Yes", "No"])):
        if expire != None:
            if not expire.endswith("s") and not expire.endswith("m") and not expire.endswith("h") and not expire.endswith("d"):
                await ctx.send("Invalid time unit, please use s/m/h/d")
                return
        
            unit = expire[-1]
            expire = int(expire[:-1])
            if unit == "s":
                expire = expire
            elif unit == "m":
                expire = expire * 60
            elif unit == "h":
                expire = expire * 3600
            elif unit == "d":
                expire = expire * 86400
            expire = int(time()) + expire

        else:
            expire = -1

        if allowforward == "Yes":
            allowforward = True
        else:
            allowforward = False

        modal = PollEditModal(expire, allowforward, "Create Poll")
        await ctx.send_modal(modal)

    @poll.command(name="resend", description="Resend a poll with results preserved, can be used cross-server")
    async def resend(self, ctx, pollid: discord.Option(int, "Poll ID")):
        conn = newconn()
        cur = conn.cursor()
        cur.execute(f"SELECT data, expire, allowforward, userid FROM poll WHERE pollid = {pollid}")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond("Invalid poll ID", ephemeral = True)
            return

        creator = t[0][3]
        allowforward = t[0][2]
        if creator != ctx.author.id and allowforward == 0:
            await ctx.respond("Poll creator disabled forwarding by other users.", ephemeral = True)
            return

        if creator != ctx.author.id:
            cur.execute(f"SELECT * FROM pollvote WHERE pollid = {pollid} AND userid = {ctx.author.id}")
            p = cur.fetchall()
            if len(p) == 0:
                await ctx.respond("Only voted user can resend poll to prevent data leak.", ephemeral = True)
                return

        user = ctx.author
        userid = user.id
        expire = t[0][1]
        data = json.loads(b64d(t[0][0]))

        description = data["description"]
        choices = data["choices"]

        cur.execute(f"SELECT choiceid FROM pollvote WHERE pollid = {pollid}")
        p = cur.fetchall()
        votes = {1: 0, 2: 0, 3: 0, 4: 0}
        tot = 0
        for pp in p:
            votes[pp[0]] += 1
            tot += 1
        
        embed = discord.Embed(title="Poll (Ongoing)", description=description, color=GECKOCLR)
        if expire != -1 and expire < int(time()):
            embed = discord.Embed(title="Poll (Ended)", description=description, color=GECKOCLR)

        view = View(timeout = None)

        i = 0
        for choiceid in range(len(choices)):
            pct = 0
            pctf = 0
            solid = 0
            space = 10
            half = 0
            ot = 0
            to = 0
            if tot != 0: # in case expire
                pct = round(votes[choiceid + 1] / tot * 100)
                pctf = round(votes[choiceid + 1] / tot * 100, 2)
                solid = int(pct / 10)
                k = pct / 10 - int(pct / 10)
                if k >= 0.75:
                    to = 1
                elif k >= 0.5:
                    half = 1
                elif k >= 0.25:
                    ot = 1
                space = (10 - solid - half - ot - to)
            embed.add_field(name=choices[choiceid], value=SOLID * solid + ONETHREE * ot + HALF * half + THREEONE * to + SPACE * space + f" {pctf}%", inline=False)
            
            i += 1
            uniq = f"{randint(1,100000)}{int(time()*100000)}"
            custom_id = "GeckoPoll-"+str(pollid)+"-"+str(i)+"-"+uniq
            button = GeckoButton(choices[choiceid], None, BTNSTYLE["blurple"], False, custom_id)
            view.add_item(button)
            cur.execute(f"INSERT INTO buttonview VALUES ({pollid}, '{custom_id}')")

        # Refresh button
        uniq = f"{randint(1,100000)}{int(time()*100000)}"
        custom_id = "GeckoPoll-"+str(pollid)+"-0-"+uniq
        button = GeckoButton("Refresh", None, BTNSTYLE["red"], False, custom_id)
        view.add_item(button)
        cur.execute(f"INSERT INTO buttonview VALUES ({pollid}, '{custom_id}')")
        conn.commit()

        embed.set_footer(text = f"Gecko Poll • ID: {pollid} • Refresh to sync between servers", icon_url = GECKOICON)

        embed.add_field(name = "Voted", value = f"{tot}", inline = True)

        if expire != -1:
            if expire < int(time()):
                embed.add_field(name="End", value = f"Ended <t:{expire}:R>", inline=True)
                await ctx.send(embed = embed)
            else:
                embed.add_field(name="End", value = f"<t:{expire}:R>", inline=True)
                await ctx.send(embed = embed, view = view)
        else:
            embed.add_field(name="End", value = "Never", inline=True)
            await ctx.send(embed = embed, view = view)

        await ctx.respond(f"Poll resent. Poll ID: {pollid}", ephemeral = True)

    @poll.command(name="result", description="View the results of a poll")
    async def result(self, ctx, pollid: discord.Option(int, "Poll ID")):
        conn = newconn()
        cur = conn.cursor()
        cur.execute(f"SELECT data, expire FROM poll WHERE pollid = {pollid}")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond("Invalid poll ID", ephemeral = True)
            return

        creator = t[0][3]
        if creator != ctx.author.id:
            cur.execute(f"SELECT * FROM pollvote WHERE pollid = {pollid} AND userid = {ctx.author.id}")
            p = cur.fetchall()
            if len(p) == 0:
                await ctx.respond("Only voted user can view poll result to prevent data leak.", ephemeral = True)
                return

        user = ctx.author
        userid = user.id
        expire = t[0][1]
        data = json.loads(b64d(t[0][0]))

        description = data["description"]
        choices = data["choices"]

        cur.execute(f"SELECT choiceid FROM pollvote WHERE pollid = {pollid}")
        p = cur.fetchall()
        votes = {1: 0, 2: 0, 3: 0, 4: 0}
        tot = 0
        for pp in p:
            votes[pp[0]] += 1
            tot += 1
        
        embed = discord.Embed(title="Poll (Ongoing)", description=description, color=GECKOCLR)
        if expire != -1 and expire < int(time()):
            embed = discord.Embed(title="Poll (Ended)", description=description, color=GECKOCLR)

        for choiceid in range(len(choices)):
            pct = 0
            pctf = 0
            solid = 0
            space = 10
            half = 0
            ot = 0
            to = 0
            if tot != 0: # in case expire
                pct = round(votes[choiceid + 1] / tot * 100)
                pctf = round(votes[choiceid + 1] / tot * 100, 2)
                solid = int(pct / 10)
                k = pct / 10 - int(pct / 10)
                if k >= 0.75:
                    to = 1
                elif k >= 0.5:
                    half = 1
                elif k >= 0.25:
                    ot = 1
                space = (10 - solid - half - ot - to)
            embed.add_field(name=choices[choiceid], value=SOLID * solid + ONETHREE * ot + HALF * half + THREEONE * to + SPACE * space + f" {pctf}%", inline=False)
            
        view = View(timeout = None)
        if not (expire != -1 and expire < int(time())):
            # Refresh button
            uniq = f"{randint(1,100000)}{int(time()*100000)}"
            custom_id = "GeckoPoll-"+str(pollid)+"-0-"+uniq
            button = GeckoButton("Refresh", None, BTNSTYLE["red"], False, custom_id)
            view.add_item(button)
            cur.execute(f"INSERT INTO buttonview VALUES ({pollid}, '{custom_id}')")
            conn.commit()

        embed.set_footer(text = f"Gecko Poll • ID: {pollid} • Refresh to sync between servers", icon_url = GECKOICON)

        embed.add_field(name = "Voted", value = f"{tot}", inline = True)

        if expire != -1:
            if expire < int(time()):
                embed.add_field(name="End", value = f"Ended <t:{expire}:R>", inline=True)
                await ctx.respond(embed = embed)
            else:
                embed.add_field(name="End", value = f"<t:{expire}:R>", inline=True)
                await ctx.respond(embed = embed, view = view)
        else:
            embed.add_field(name="End", value = "Never", inline=True)
            await ctx.respond(embed = embed, view = view)

    @poll.command(name="stop", description="Stop a poll")
    async def stop(self, ctx, pollid: discord.Option(int, "Poll ID")):
        conn = newconn()
        cur = conn.cursor()
        cur.execute(f"SELECT userid FROM poll WHERE pollid = {pollid}")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond("Invalid poll ID", ephemeral = True)
            return

        creator = t[0][0]
        if creator != ctx.author.id:
            await ctx.respond("Only creator can stop a poll", ephemeral = True)
            return

        cur.execute(f"UPDATE poll SET expire = {int(time())} WHERE pollid = {pollid}")
        conn.commit()
        await ctx.respond("Poll stopped.", ephemeral = True)

bot.add_cog(Poll(bot))