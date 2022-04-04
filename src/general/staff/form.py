# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Staff - Form Management

import os, asyncio
import discord
from discord.commands import CommandPermission, SlashCommandGroup
from discord.ext import commands
from discord.ui import Modal, InputText
from base64 import b64encode, b64decode
from time import time
from random import randint
import io

from bot import bot
from settings import *
from functions import *
from db import newconn

class FormEditModal(Modal):
    def __init__(self, formid, onetime, cb, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.formid = formid
        self.onetime = onetime
        self.cb = cb

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
        onetime = self.onetime
        cb = self.cb

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
            data += str(onetime)
            cur.execute(f"UPDATE form SET data = '{data}' WHERE formid = {formid}")
            if cb != None:
                cur.execute(f"UPDATE form SET callback = '{b64e(cb)}' WHERE formid = {formid}")
            conn.commit()
            await interaction.response.send_message(f"Form #{formid} edited.", ephemeral = False)
            await log(f"Form", f"[Guild {interaction.guild} {guildid}] {interaction.user} ({interaction.user.id}) edited form #{formid}", guildid)
        else:
            cur.execute(f"SELECT COUNT(*) FROM form")
            t = cur.fetchall()
            formid = 0
            if len(t) > 0:
                formid = t[0][0]
            data += str(onetime)
            cur.execute(f"INSERT INTO form VALUES ({formid}, {guildid}, '{data}', '{b64e(cb)}')")
            conn.commit()
            await interaction.response.send_message(f"Form created. Form ID: `{formid}`. Bind it to a button using `/button create` and post it using `/button send`.", ephemeral = False)
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
        cur.execute(f"SELECT data, callback FROM form WHERE formid = {formid}")
        t = cur.fetchall()
        if len(t) == 0:
            raise Exception("Form not found!")
        cb = b64d(t[0][1])
        t = t[0][0]
        if t.startswith("stopped-"):
            await interaction.response.send_message(f"Form is no longer accepting new entries.", ephemeral = True)
            return
        if t.split("|")[-1] == "1":
            cur.execute(f"SELECT * FROM formentry WHERE formid = {formid} AND userid = {userid}")
            o = cur.fetchall()
            if len(o) > 0:
                await interaction.response.send_message(f"You can only submit this form once.", ephemeral = True)
                return
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

        await interaction.response.send_message(f"{cb}\n\nYou can view your submission by using command `/form entry {formid}` (*it also works in DM*)", ephemeral = True)
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

class ManageForm(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    manage = SlashCommandGroup("form", "Manage form")

    @manage.command(name="create", description="Staff - Create form. Detailed information will be edited in modal.")
    async def create(self, ctx, callback: discord.Option(str, "The message to show after the form is submitted, Markdown is accepted", required = False),
        onetime: discord.Option(str, "Allow member to submit form only once?", required = False, choices = ["Yes", "No"])):
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return

        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return

        ot = 0
        if onetime == "Yes":
            ot = 1

        if len(str(callback)) > 400:
            await ctx.respond("The length of callback message cannot be greater than 400!", ephemeral = True)
            return

        if callback is None:
            callback = "Thanks for submitting the form."

        await ctx.send_modal(FormEditModal(-1, ot, callback, "Create form"))

    @manage.command(name="edit", description="Staff - Edit form. Detailed information will be edited in modal.")
    async def edit(self, ctx, formid: discord.Option(str, "Form ID, provided when form was created. Use '/form list' to see a list of forms and IDs.", required = True),
        callback: discord.Option(str, "The message to show after the form is submitted, leave empty to remain unchanged", required = False),
        onetime: discord.Option(str, "Allow member to submit form only once?", required = False, choices = ["Yes", "No"])):
        
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

        cur.execute(f"SELECT data FROM form WHERE formid = {formid}")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond("The form does not exist or does not belong to this guild.", ephemeral = True)
            return
        data = t[0][0]

        ot = int(data.split("|")[-1])
        if onetime == "Yes":
            ot = 1

        if len(str(callback)) > 400:
            await ctx.respond("The length of callback message cannot be greater than 400!", ephemeral = True)
            return

        await ctx.send_modal(FormEditModal(formid, ot, callback, "Edit form"))

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
        conn.commit()

        await ctx.respond(f"Form #{formid} and entries are deleted.")
        await log(f"Form", f"[Guild {ctx.guild} {ctx.guild.id}] {ctx.author} ({ctx.author.id}) deleted form #{formid}", ctx.guild.id)

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
        
        cur.execute(f"SELECT formid FROM form WHERE guildid = {ctx.guild.id}")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond("There's no form created in this guild. Use `/form create` to create one.")
            return
        
        msg = f"Below are all forms created using Gecko in {ctx.guild}.\nOnly form id is shown and you can use `/form edit` to see details.\n\n"
        for tt in t:
            msg += f"Form **#{tt[0]}**\n"
        
        if len(msg) > 2000:
            f = io.BytesIO()
            f.write(msg.encode())
            f.seek(0)
            await ctx.respond(file=discord.File(fp=f, filename='Forms.MD'))
        else:
            embed=discord.Embed(title=f"Forms in {ctx.guild}", description=msg, color=GECKOCLR)
            await ctx.respond(embed = embed)     

    @manage.command(name="toggle", description="Staff - Toggle form status, whether it accepts new entries.")
    async def toggle(self, ctx, formid: discord.Option(str, "Form ID, provided when form was created. Use '/form list' to see a list of forms and IDs.", required = True)):
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