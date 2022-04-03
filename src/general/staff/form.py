# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Staff Functions of Gecko Bot

import os, asyncio
import discord
from discord.commands import CommandPermission, SlashCommandGroup
from discord.ext import commands
from discord.ui import Modal, InputText, Button, View
from discord.enums import ButtonStyle
from base64 import b64encode, b64decode
from time import time
from random import randint
import io

from bot import bot
from settings import *
from functions import *
from db import newconn

class FormEditModal(Modal):
    def __init__(self, formid, btnlbl, btnclr, onetime, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.formid = formid
        self.btnlbl = btnlbl
        self.btnclr = btnclr
        self.onetime = onetime

        d = None

        if formid != -1:
            conn = newconn()
            cur = conn.cursor()
            cur.execute(f"SELECT data FROM form WHERE formid = {formid}")
            t = cur.fetchall()
            if len(t) == 0:
                raise Exception("Form not found!")
            t = t[0][0]
            if t.startswith("stopped-"):
                t = t[8:]
            p = t.split("|")[:-1]
            d = []
            for pp in p:
                d.append(b64d(pp))
            for _ in range(5 - len(p)):
                d.append("")
        else:
            d = ["", "", "", "", ""]

        self.add_item(InputText(label="Field 1", placeholder = "[Long / Short] {Label} e.g. [Short] Title", required = True, value = d[0], max_length = 50))
        self.add_item(InputText(label="Field 2", placeholder = "[Long / Short] {Label} e.g. [Long] Description", required = False, value = d[1], max_length = 50))
        self.add_item(InputText(label="Field 3", placeholder = "Field size is short by default if you don't specify.", required = False, value = d[2], max_length = 50))
        self.add_item(InputText(label="Field 4", placeholder = "You must set at least 1 field", required = False, value = d[3], max_length = 50))
        self.add_item(InputText(label="Field 5", placeholder = "You can have at most 5 field", required = False, value = d[4], max_length = 50))

    async def callback(self, interaction: discord.Interaction):
        guildid = interaction.guild_id
        formid = self.formid
        btnlbl = self.btnlbl
        btnclr = self.btnclr
        onetime = self.onetime

        btn = f"{btnclr}|{onetime}|{b64e(btnlbl)}"

        data = ""
        for i in range(5):
            field = self.children[i].value
            if field.replace(" ","") != "":
                if len(field) > 40:
                    await interaction.response.send_message(f"Field label too long (must not be longer than 40 characters)", ephemeral = True)
                    return
                if not field.startswith("[Short]") and not field.startswith("[Long]"):
                    field = f"[Short] {field}"
                data += b64e(field) + "|"

        conn = newconn()
        cur = conn.cursor()
        if formid != -1:
            cur.execute(f"SELECT data FROM form WHERE formid = {formid}")
            t = cur.fetchall()
            if len(t) == 0:
                await interaction.response.send_message(f"Form not found.", ephemeral = True)
                return
            orgdata = t[0][0]
            if orgdata.startswith("stopped-"):
                data = "stopped-" + data
            cur.execute(f"UPDATE form SET btn = '{btn}', data = '{data}' WHERE formid = {formid}")
            conn.commit()
            await interaction.response.send_message(f"Form #{formid} edited.", ephemeral = False)
            await log(f"Form", f"[Guild {interaction.guild} {guildid}] {interaction.user} ({interaction.user.id}) edited form #{formid}", guildid)
        else:
            cur.execute(f"SELECT COUNT(*) FROM form")
            t = cur.fetchall()
            formid = 0
            if len(t) > 0:
                formid = t[0][0]
            cur.execute(f"INSERT INTO form VALUES ({formid}, {guildid}, '{btn}', '{data}')")
            conn.commit()
            await interaction.response.send_message(f"Form created. Form ID: `{formid}`. Use `/form send` to post it.", ephemeral = False)
            await log(f"Form", f"[Guild {interaction.guild} {guildid}] {interaction.user} ({interaction.user.id}) created form #{formid}", guildid)

class FormModal(Modal):
    def __init__(self, formid, fields, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.formid = formid
        for field in fields:
            if field.startswith("[Short]"):
                field = field[7:]
                while field.startswith(" "):
                    field = field[1:]
                self.add_item(InputText(label=field, required = True))
            elif field.startswith("[Long]"):
                field = field[6:]
                while field.startswith(" "):
                    field = field[1:]
                self.add_item(InputText(label=field, required = True, style=discord.InputTextStyle.long))

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        userid = user.id
        guildid = interaction.guild_id
        formid = self.formid

        data = f"Entry of **{user.name}** (`{user.id}`)  \n"

        conn = newconn()
        cur = conn.cursor()
        cur.execute(f"SELECT data FROM form WHERE formid = {formid}")
        t = cur.fetchall()
        if len(t) == 0:
            raise Exception("Form not found!")
        t = t[0][0]
        if t.startswith("stopped-"):
            t = t[8:]
        p = t.split("|")[:-1]
        i = 0
        for pp in p:
            field = b64d(pp)
            if field.startswith("[Short]"):
                field = field[7:]
            elif field.startswith("[Long]"):
                field = field[6:]
            while field.startswith(" "):
                field = field[1:]
            data += f"**{field}**  \n{self.children[i].value}  \n\n"
            i += 1
        
        cur.execute(f"INSERT INTO formentry VALUES ({formid}, {userid}, '{b64e(data)}')")
        conn.commit()

        await interaction.response.send_message(f"Form submitted. You can view your submission by using command `/form entry {formid}` (*it also works in DM*)", ephemeral = True)
        await log(f"Form", f"[Guild {interaction.guild} {guildid}] {user} ({userid}) submitted form #{formid}", guildid)

        cur.execute(f"SELECT channelid FROM channelbind WHERE guildid = {guildid} AND category = 'form'")
        t = cur.fetchall()
        if len(t) > 0:
            channelid = t[0][0]
            channel = bot.get_channel(channelid)
            if channel != None:
                desc = data.replace(f"**{user.name}**", f"<@!{user.id}>")
                if len(desc) <= 2000:
                    embed=discord.Embed(title=f"New form #{formid} submission", description=desc, color=GECKOCLR)
                    await channel.send(embed = embed)
                else:
                    f = io.BytesIO()
                    f.write(data.encode())
                    f.seek(0)
                    await channel.send(f"New form #{formid} submission")
                    await channel.send(file=discord.File(fp=f, filename='Entry.MD'))

class FormButton(Button):
    def __init__(self, label, style, custom_id):
        super().__init__(
            label=label,
            style=style,
            custom_id=custom_id,
        )

    async def callback(self, interaction: discord.Interaction):        
        custom_id = self.custom_id
        if not custom_id.startswith("GeckoForm"):
            return

        userid = interaction.user.id
        formid = int(custom_id.split("-")[1])

        conn = newconn()
        cur = conn.cursor()
        cur.execute(f"SELECT btn, data FROM form WHERE formid = {formid}")
        t = cur.fetchall()
        if len(t) == 0:
            raise Exception("Form not found!")
        t = t[0]
        btn = t[0]
        data = t[1]
        if data.startswith("stopped-"):
            await interaction.response.send_message(f"The form is not accpeting new entries at this moment.", ephemeral = True)
            return
        if btn.split("|")[1] == "1":
            cur.execute(f"SELECT userid FROM formentry WHERE userid = {userid} AND formid = {formid}")
            p = cur.fetchall()
            if len(p) > 0:
                await interaction.response.send_message(f"You can not submit more than once.", ephemeral = True)
                return

        p = data.split("|")[:-1]
        d = []
        for pp in p:
            d.append(b64d(pp))
        
        await interaction.response.send_modal(FormModal(formid, d, "Submit Form"))   

class ManageForm(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        conn = newconn()
        cur = conn.cursor()
        cur.execute(f"SELECT customid FROM formview")
        d = cur.fetchall()
        for dd in d:
            view = View(timeout=None)
            view.add_item(FormButton("", BTNSTYLE["blurple"], dd[0]))
            self.bot.add_view(view)
    
    manage = SlashCommandGroup("form", "Manage form")

    @manage.command(name="create", description="Staff - Create form. Detailed information will be edited in modal.")
    async def create(self, ctx, btnlabel: discord.Option(str, "Button label, or the text to put inside the button", required = True),
        onetime: discord.Option(str, "Allow member to submit form only once?", required = False, choices = ["Yes", "No"]),
        btncolor: discord.Option(str, "Button background color", required = False, choices = ["blurple", "grey", "green", "red"])):
        
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return

        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return
        
        if not btncolor in ["blurple", "grey", "gray", "green", "red"]:
            btncolor = "blurple"
        
        if len(btnlabel) > 75:
            await ctx.respond("Button label can contain at most 75 characters!", ephemeral = True)
            return

        ot = 0
        if onetime == "Yes":
            ot = 1

        await ctx.send_modal(FormEditModal(-1, btnlabel, btncolor, ot, "Create form"))

    @manage.command(name="edit", description="Staff - Edit form. Detailed information will be edited in modal.")
    async def edit(self, ctx, formid: discord.Option(str, "Form ID, provided when form was created. Use '/form get' to see a list of forms and IDs.", required = True),
        btnlabel: discord.Option(str, "Button label, or the text to put inside the button", required = True),
        onetime: discord.Option(str, "Allow member to submit form only once?", required = False, choices = ["Yes", "No"]),
        btncolor: discord.Option(str, "Button background color", required = False, choices = ["blurple", "grey", "green", "red"])):
        
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return

        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return
        
        if len(btnlabel) > 75:
            await ctx.respond("Button label can contain at most 75 characters!", ephemeral = True)
            return

        try:
            formid = abs(int(formid))
        except:
            await ctx.respond(f"Form ID {formid} is invalid.", ephemeral = True)
            return

        conn = newconn()
        cur = conn.cursor()
        
        cur.execute(f"SELECT btn FROM form WHERE formid = {formid} AND guildid = {ctx.guild.id}")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond(f"Form not found.", ephemeral = True)
            return
        btn = t[0][0]
        orgclr = btn.split("|")[0]
        
        if not btncolor in ["blurple", "grey", "gray", "green", "red"]:
            btncolor = orgclr

        ot = int(btn.split("|")[1])
        if onetime == "Yes":
            ot = 1

        await ctx.send_modal(FormEditModal(formid, btnlabel, btncolor, ot, "Edit form"))

    @manage.command(name="delete", description="Staff - Delete a form and all submitted entries.")
    async def delete(self, ctx, formid: discord.Option(str, "Form ID", required = True)):
        
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return

        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return

        try:
            formid = abs(int(formid))
        except:
            await ctx.respond(f"Form ID {formid} is invalid.", ephemeral = True)
            return

        conn = newconn()
        cur = conn.cursor()
        guildid = ctx.guild.id
        cur.execute(f"SELECT formid FROM form WHERE formid = {formid} AND guildid = {guildid}")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond("The form does not exist or does not belong to this guild.", ephemeral = True)
            return

        cur.execute(f"UPDATE form SET formid = -formid WHERE formid = {formid} AND guildid = {guildid}")
        cur.execute(f"UPDATE formentry SET formid = -formid WHERE formid = {formid}")
        cur.execute(f"DELETE FROM formview WHERE formid = {formid}")
        conn.commit()

        await ctx.respond(f"Form #{formid} and entries are deleted.")
        await log(f"Form", f"[Guild {ctx.guild} {ctx.guild.id}] {ctx.author} ({ctx.author.id}) deleted form #{formid}", ctx.guild.id)

    @manage.command(name="send", description="Staff - Send form submit buttons.")
    async def sendmul(self, ctx, channel: discord.Option(str, "Channel to send the button", required = True),
        formids: discord.Option(str, "Form IDs, separate with space, e.g. '1 2 3'", required = True)):
        
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return

        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return
        
        if not channel.startswith("<#") or not channel.endswith(">"):
            await ctx.respond(f"{channel} is not a valid channel!", ephemeral = True)
            return

        conn = newconn()
        cur = conn.cursor()
        
        formids = formids.split(" ")
        
        view = View(timeout = None)

        if len(formids) > 25:
            await ctx.respond(f"One message can contain at most 25 buttons.", ephemeral = True)
            return

        for i in range(len(formids)):
            try:
                formids[i] = int(formids[i])
                formid = formids[i]
                cur.execute(f"SELECT btn FROM form WHERE formid = {formid} AND guildid = {ctx.guild.id}")
                t = cur.fetchall()
                if len(t) == 0:
                    await ctx.respond(f"Form with ID {formid} not found.", ephemeral = True)
                    return

                btn = t[0][0].split("|")
                color = btn[0]
                label = b64d(btn[2])
                style = BTNSTYLE[color]
                uniq = f"{randint(1,100000)}{int(time()*100000)}"
                custom_id = "GeckoForm-"+str(formid)+"-"+uniq
                button = FormButton(label, style, custom_id)
                view.add_item(button)
                cur.execute(f"INSERT INTO formview VALUES ({formid}, '{custom_id}')")
                conn.commit()
            except:
                await ctx.respond(f"Form ID {formids[i]} is invalid.", ephemeral = True)
                return
                
        channelid = int(channel[2:-1])
        try:
            channel = bot.get_channel(channelid)
            if channel is None:
                raise Exception("No access to channel.")
            
            message = await channel.send(view = view)

            await ctx.respond(f"Form submit buttons sent at <#{channelid}>.", ephemeral = True)
            await log(f"Form", f"[Guild {ctx.guild} {ctx.guild.id}] {ctx.author} ({ctx.author.id}) posted forms {' '.join(formids)} at {channel} ({channelid})", ctx.guild.id)

        except:
            import traceback
            traceback.print_exc()
            await ctx.respond(f"I cannot send message at <#{channelid}>.", ephemeral = True)
            return
    
    @manage.command(name="attach", description = "Staff - Attach form submit button to an existing message sent by Gecko (Text / Embed)")
    async def attach(self, ctx, msglink: discord.Option(str, "Link to the message", required = True),
            formids: discord.Option(str, "Form IDs, separate with space, e.g. '1 2 3'", required = True)):
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return

        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return

        if not msglink.endswith("/"):
            msglink = msglink + "/"
        msglink = msglink.split("/")
        msgid = int(msglink[-2])
        channelid = int(msglink[-3])
        guildid = int(msglink[-4])
        message = None
        try:
            channel = bot.get_channel(channelid)
            message = await channel.fetch_message(msgid)
            if message is None:
                await ctx.respond("I cannot fetch the message!", ephemeral = True)
                return
        except:
            await ctx.respond("I cannot fetch the message!", ephemeral = True)
            return
        if message.author.id != BOTID:
            await ctx.respond("The message isn't sent by Gecko", ephemeral = True)
            return

        conn = newconn()
        cur = conn.cursor()
        view = View.from_message(message, timeout = None)
        
        formids = formids.split(" ")
        if len(view.children) + len(formids) > 25:
            await ctx.respond(f"One message can contain at most 25 buttons (Existing buttons are counted, use `/button clear` to remove existing buttons)", ephemeral = True)
            return

        for i in range(len(formids)):
            try:
                formids[i] = int(formids[i])
                formid = formids[i]
                cur.execute(f"SELECT btn FROM form WHERE formid = {formid} AND guildid = {ctx.guild.id}")
                t = cur.fetchall()
                if len(t) == 0:
                    await ctx.respond(f"Form with ID {formid} not found.", ephemeral = True)
                    return

                btn = t[0][0].split("|")
                color = btn[0]
                label = b64d(btn[2])
                style = BTNSTYLE[color]
                uniq = f"{randint(1,100000)}{int(time()*100000)}"
                custom_id = "GeckoForm-"+str(formid)+"-"+uniq
                button = FormButton(label, style, custom_id)
                view.add_item(button)
                cur.execute(f"INSERT INTO formview VALUES ({formid}, '{custom_id}')")
                conn.commit()
            except:
                await ctx.respond(f"Form ID {formids[i]} is invalid.", ephemeral = True)
                return

        await message.edit(content = message.content, embeds = message.embeds, view = view)
        await ctx.respond(f"Form submit buttons attached to [message]({'/'.join(msglink)[-1]}).")
    
    @manage.command(name="update", description = "Staff - Update the labels of submit buttons to the latest ones.")
    async def attach(self, ctx, msglink: discord.Option(str, "Link to the message", required = True)):
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return

        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return

        if not msglink.endswith("/"):
            msglink = msglink + "/"
        msglink = msglink.split("/")
        msgid = int(msglink[-2])
        channelid = int(msglink[-3])
        guildid = int(msglink[-4])
        message = None
        try:
            channel = bot.get_channel(channelid)
            message = await channel.fetch_message(msgid)
            if message is None:
                await ctx.respond("I cannot fetch the message!", ephemeral = True)
                return
        except:
            await ctx.respond("I cannot fetch the message!", ephemeral = True)
            return
        if message.author.id != BOTID:
            await ctx.respond("The message isn't sent by Gecko", ephemeral = True)
            return
        
        conn = newconn()
        cur = conn.cursor()
        
        view = View.from_message(message, timeout = None)
        newview = View(timeout = None)
        for child in view.children:
            if not child.custom_id.startswith("GeckoForm"):
                newview.add_item(child)
                continue
            formid = -1
            try:
                formid = int(child.custom_id.split("-")[1])
            except:
                newview.add_item(child)
                continue
            cur.execute(f"SELECT btn FROM form WHERE formid = {formid} AND guildid = {ctx.guild.id}")
            t = cur.fetchall()
            if len(t) == 0:
                continue
            btn = t[0][0].split("|")
            color = btn[0]
            label = b64d(btn[2])
            style = BTNSTYLE[color]
            uniq = f"{randint(1,100000)}{int(time()*100000)}"
            custom_id = "GeckoForm-"+str(formid)+"-"+uniq
            button = FormButton(label, style, custom_id)
            newview.add_item(button)
            cur.execute(f"DELETE FROM formview WHERE formid = {formid} AND customid = '{child.custom_id}'")
            cur.execute(f"INSERT INTO formview VALUES ({formid}, '{custom_id}')")
            conn.commit()

        await message.edit(content = message.content, embeds = message.embeds, view = newview)
        await ctx.respond(f"Form submit buttons in [message]({'/'.join(msglink)[-1]}) are updated.")  

    @manage.command(name="list", description="Staff - List all forms in this guild.")
    async def show(self, ctx):
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return

        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return

        conn = newconn()
        cur = conn.cursor()
        
        cur.execute(f"SELECT formid, btn FROM form WHERE guildid = {ctx.guild.id}")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond("There's no form created in this guild. Use `/form create` to create one.")
            return
        
        msg = f"Below are all forms created using Gecko in {ctx.guild}.\nOnly button label is shown and you can use `/form edit` to see details.\n"
        for tt in t:
            msg += f"Form *#{tt[0]}*: **{b64d(tt[1].split('|')[2])}**\n"
        
        if len(msg) > 2000:
            f = io.BytesIO()
            f.write(msg.encode())
            f.seek(0)
            await ctx.respond(file=discord.File(fp=f, filename='Forms.MD'))
        else:
            embed=discord.Embed(title=f"Forms in {ctx.guild}", description=msg, color=GECKOCLR)
            await ctx.respond(embed = embed)     
        
    @manage.command(name="get", description="Staff - Get form ID of form submit button(s) in a message.")
    async def get(self, ctx, msglink: discord.Option(str, "Link to the message", required = True)):
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return

        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return
        
        if not msglink.endswith("/"):
            msglink = msglink + "/"
        msglink = msglink.split("/")
        msgid = int(msglink[-2])
        channelid = int(msglink[-3])
        guildid = int(msglink[-4])
        if guildid != ctx.guild.id:
            await ctx.respond(f"The message isn't sent in the guild you are sending this command.", ephemeral = True)
            return
        view = None
        try:
            channel = ctx.guild.get_channel(channelid)
            if channel is None:
                await ctx.respond(f"I cannot fetch the message as I cannot access the channel.", ephemeral = True)
                return
            message = await channel.fetch_message(msgid)
            if message is None:
                await ctx.respond(f"I cannot fetch the message.", ephemeral = True)
                return
            if message.author.id != BOTID:
                await ctx.respond(f"The message isn't sent by Gecko.", ephemeral = True)
                return
            view = View.from_message(message, timeout = None)
            
            if view is None or len(view.children) == 0:
                await ctx.respond(f"No button is included in the message.", ephemeral = True)
                return
        except:
            await ctx.respond(f"Something wrong occurred.", ephemeral = True)
            return
            
        msg = ""
        conn = newconn()
        cur = conn.cursor()
        for d in view.children:
            if not d.custom_id.startswith("GeckoForm"):
                continue
            formid = -1
            try:
                formid = int(d.custom_id.split("-")[1])
            except:
                continue
            cur.execute(f"SELECT btn FROM form WHERE formid = {formid} AND guildid = {ctx.guild.id}")
            t = cur.fetchall()
            if len(t) == 0:
                continue
            label = b64d(t[0][0].split("|")[2])
            if label != d.label:
                continue
            msg += f"`{label}` -> #{formid}\n"
        if msg == "":
            await ctx.respond(f"No form submit button is included in the message.", ephemeral = True)
            return

        embed=discord.Embed(title="Button -> Form", description=msg, color=GECKOCLR)
        await ctx.respond(embed = embed)

    @manage.command(name="toggle", description="Staff - Toggle form status, whether it accepts new entries.")
    async def toggle(self, ctx, formid: discord.Option(str, "Form ID, provided when form was created. Use '/form get' to see a list of forms and IDs.", required = True)):
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return

        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return

        try:
            formid = abs(int(formid))
        except:
            await ctx.respond(f"Form ID {formid} is invalid.", ephemeral = True)
            return

        conn = newconn()
        cur = conn.cursor()

        cur.execute(f"SELECT data FROM form WHERE formid = {formid} AND guildid = {ctx.guild.id}")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond(f"Form not found.", ephemeral = True)
            return
        
        data = t[0][0]
        if data.startswith("stopped-"):
            cur.execute(f"UPDATE form SET data = '{data[8:]}' WHERE formid = {formid}")
            conn.commit()
            await ctx.respond(f"Form #{formid} is now accepting new entries.")
            await log(f"Form", f"[Guild {ctx.guild} {ctx.guild.id}] {ctx.author} ({ctx.author.id}) stopped form #{formid}", ctx.guild.id)

        else:
            cur.execute(f"UPDATE form SET data = 'stopped-{data}' WHERE formid = {formid}")
            conn.commit()
            await ctx.respond(f"Form #{formid} is no longer accepting new entries.")
            await log(f"Form", f"[Guild {ctx.guild} {ctx.guild.id}] {ctx.author} ({ctx.author.id}) started form #{formid}", ctx.guild.id)

    @manage.command(name="entry", description="View your entry.")
    async def entry(self, ctx, formid: discord.Option(str, "Form ID", required = True),
        user: discord.Option(str, "User Tag, e.g. @Gecko (Staff can use this to view the entry of a specific user)", required = False)):
        try:
            formid = abs(int(formid))
        except:
            await ctx.respond(f"Form ID {formid} is invalid.", ephemeral = True)
            return
            
        conn = newconn()
        cur = conn.cursor()
        
        if user != None:
            if not user.startswith("<@!") or not user.endswith(">"):
                await ctx.respond(f"User Tag {user} is invalid.", ephemeral = True)
                return
            
            userid = int(user[3:-1])

            if ctx.guild is None:
                await ctx.respond("You can only run this command in guilds!")
                return

            if not isStaff(ctx.guild, ctx.author):
                await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
                return
            
            guildid = ctx.guild.id
            cur.execute(f"SELECT formid FROM form WHERE formid = {formid} AND guildid = {guildid}")
            t = cur.fetchall()
            if len(t) == 0:
                await ctx.respond("The form does not exist or does not belong to this guild.", ephemeral = True)
                return
            
            username = ""
            user = bot.get_user(userid)
            if user != None:
                username = user.name
                
            cnt = 0
            cur.execute(f"SELECT data FROM formentry WHERE formid = {formid} AND userid = {userid}")
            t = cur.fetchall()
            for tt in t:
                data = tt[0]
                desc = b64d(data).replace(f"**{username}**", f"<@!{userid}>")
                if len(desc) <= 2000:
                    embed=discord.Embed(title=f"Form #{formid} submission record", description=desc, color=GECKOCLR)
                    await ctx.respond(embed = embed)
                else:
                    f = io.BytesIO()
                    f.write(desc.encode())
                    f.seek(0)
                    await ctx.respond(f"Form #{formid} submission record")
                    await ctx.respond(file=discord.File(fp=f, filename='Entry.MD'))
                cnt += 1
            if cnt == 0:
                await ctx.respond(f"<@!{userid}> hasn't submitted this form before.", ephemeral = True)

        else:
            user = ctx.author
            cur.execute(f"SELECT data FROM formentry WHERE formid = {formid} AND userid = {ctx.user.id}")
            t = cur.fetchall()
            cnt = 0
            for tt in t:
                cnt += 1
                data = tt[0]
                desc = b64d(data).replace(f"**{user.name}**", f"<@!{user.id}>")
                if ctx.guild != None:
                    if len(desc) <= 2000:
                        embed=discord.Embed(title=f"Form #{formid} submission record", description=desc, color=GECKOCLR)
                        await ctx.respond(embed = embed, ephemeral = True)
                    else:
                        f = io.BytesIO()
                        f.write(desc.encode())
                        f.seek(0)
                        await ctx.respond(f"Form #{formid} submission record", ephemeral = True)
                        await ctx.respond(file=discord.File(fp=f, filename='Entry.MD'), ephemeral = True)
                else:
                    if len(desc) <= 2000:
                        embed=discord.Embed(title=f"Form #{formid} submission record", description=desc, color=GECKOCLR)
                        await ctx.respond(embed = embed, ephemeral = False)
                    else:
                        f = io.BytesIO()
                        f.write(desc.encode())
                        f.seek(0)
                        await ctx.respond(f"Form #{formid} submission record", ephemeral = False)
                        await ctx.respond(file=discord.File(fp=f, filename='Entry.MD'), ephemeral = False)
            if cnt == 0:
                await ctx.respond(f"You haven't submitted this form before or the creator deleted the form.", ephemeral = True)

    @manage.command(name="download", description="Staff - Download all entries of a form.")
    async def download(self, ctx, formid: discord.Option(str, "Form ID", required = True)):
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return

        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return

        try:
            formid = abs(int(formid))
        except:
            await ctx.respond(f"Form ID {formid} is invalid.", ephemeral = True)
            return
            
        conn = newconn()
        cur = conn.cursor()
            
        res = ""
        guildid = ctx.guild.id
        cur.execute(f"SELECT formid FROM form WHERE formid = {formid} AND guildid = {guildid}")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond("The form does not exist or does not belong to this guild.", ephemeral = True)
            return
        cur.execute(f"SELECT data FROM formentry WHERE formid = {formid}")
        t = cur.fetchall()
        for tt in t:
            res += b64d(tt[0])+"\n---\n"
        
        try:
            channel = await ctx.author.create_dm()
            if channel is None:
                await ctx.respond(f"For security reasons, Gecko has to send you the data in DM. Please allow Gecko to send you DMs.", ephemeral = True)
                return
            f = io.BytesIO()
            f.write(res.encode())
            f.seek(0)
            await channel.send(f"Here is the file for all entries of form #{formid}\nThe file is in Markdown format and will look great if you have a Markdown viewer.")
            await channel.send(file=discord.File(fp=f, filename='Entries.MD'))
            await ctx.respond(f"I've sent you the entries in DM.", ephemeral = True)
            await log(f"Form", f"[Guild {ctx.guild} {ctx.guild.id}] {ctx.author} ({ctx.author.id}) downloaded all entries of form #{formid}", ctx.guild.id)
        except:
            import traceback
            traceback.print_exc()
            await ctx.respond(f"For security reasons, Gecko has to send you the data in DM. Please allow Gecko to send you DMs.", ephemeral = True)


bot.add_cog(ManageForm(bot))