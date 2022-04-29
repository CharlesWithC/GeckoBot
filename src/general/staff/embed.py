# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Staff - Embed Management

import os, asyncio
import discord
from discord.commands import CommandPermission, SlashCommandGroup
from discord.ext import commands
from discord.ui import Modal, InputText
import validators
from datetime import datetime

from bot import bot
from settings import *
from functions import *
from db import newconn

class EmbedModal(Modal):
    def __init__(self, embedid, guildid, color, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.embedid = embedid
        self.guildid = guildid
        self.color = color
        
        conn = newconn()
        cur = conn.cursor()

        orgdata = ["", "", "", "", ""]
        if embedid != -1:
            cur.execute(f"SELECT data FROM embed WHERE embedid = {embedid} AND guildid = {guildid}")
            t = cur.fetchall()
            if len(t) == 0:
                raise Exception("Embed not found!")
            d = t[0][0].split("|")
            title = b64d(d[0])
            url = b64d(d[1])
            description = b64d(d[2])
            footer = b64d(d[3])
            thumbnail_url = b64d(d[4]) + " | " + b64d(d[5])
            orgdata = [title, url, description, footer, thumbnail_url]

        self.add_item(InputText(label="Title", placeholder = "(Required)", value = orgdata[0]))
        self.add_item(InputText(label="URL", placeholder = "(Optional)", value = orgdata[1], required = False))
        self.add_item(InputText(label="Description", style=discord.InputTextStyle.long, placeholder = "(Required)", value = orgdata[2]))
        self.add_item(InputText(label="Footer", placeholder = "(Optional, add [URL] for icon, e.g. [icon url] footer)", value = orgdata[3], required = False))
        self.add_item(InputText(label="Thumbnail | Image URL", placeholder = "(Optional, use | to split, you can leave either empty)", value = orgdata[4], required = False))

    async def callback(self, interaction: discord.Interaction):
        conn = newconn()
        cur = conn.cursor()

        guildid = self.guildid
        embedid = self.embedid
        color = self.color
        title = self.children[0].value
        url = self.children[1].value.replace(" ","")
        description = self.children[2].value
        footer = self.children[3].value
        thumbnail_url = self.children[4].value.replace(" ","")

        l = len(title) + len(description)
        # if l > 2000:
        #     await interaction.response.send_message(f"The maximum length of title + description is 2000, current {l}", ephemeral = True)
        #     return

        if "|" in thumbnail_url:
            thumbnail_url = thumbnail_url.split("|")
        else:
            thumbnail_url = [thumbnail_url, ""]

        footer_icon_url = ""

        if footer.startswith("["):
            footer_icon_url = footer[footer.find("[") + 1: footer.find("]")].replace(" ","")
        
        if url != "" and validators.url(url) != True:
            await interaction.response.send_message(f"URL {url} is not a valid url.", ephemeral = True)
            return
        if thumbnail_url[0] != "" and  validators.url(thumbnail_url[0]) != True:
            await interaction.response.send_message(f"Thumbnail URL {thumbnail_url[0]} is not a valid url.", ephemeral = True)
            return
        if thumbnail_url[1] != "" and  validators.url(thumbnail_url[1]) != True:
            await interaction.response.send_message(f"Image URL {thumbnail_url[1]} is not a valid url.", ephemeral = True)
            return
        if footer_icon_url != "" and  validators.url(footer_icon_url) != True:
            await interaction.response.send_message(f"Footer Icon URL {footer_icon_url} is not a valid url.", ephemeral = True)
            return

        if embedid != -1:
            cur.execute(f"SELECT data FROM embed WHERE embedid = {embedid} AND guildid = {guildid}")
            t = cur.fetchall()
            if len(t) == 0:
                await interaction.response.send_message(f"Embed not found.", ephemeral = True)
                return
            data = b64e(title) + "|" + b64e(url) + "|" + b64e(description) + "|" + b64e(footer) + "|" + b64e(thumbnail_url[0]) + "|" + b64e(thumbnail_url[1])
            data += "|" + color
            cur.execute(f"UPDATE embed SET data = '{data}' WHERE embedid = {embedid} AND guildid = {guildid}")
            cur.execute(f"UPDATE alias SET label = '{b64e(title)}' WHERE elementid = {embedid} AND elementtype = 'embed' AND guildid = {guildid}")
            conn.commit()
            
            await interaction.response.send_message(f"Embed #{embedid} updated.", ephemeral = False)
            await log(f"Embed", f"[Guild {interaction.guild} {guildid}] {interaction.user} ({interaction.user.id}) updated embed #{embedid}", guildid)

        else:
            cur.execute(f"SELECT COUNT(*) FROM embed")
            t = cur.fetchall()
            embedid = 0
            if len(t) > 0:
                embedid = t[0][0]
            
            data = b64e(title) + "|" + b64e(url) + "|" + b64e(description) + "|" + b64e(footer) + "|" + b64e(thumbnail_url[0]) + "|" + b64e(thumbnail_url[1])
            data += "|" + color
            cur.execute(f"INSERT INTO embed VALUES ({embedid}, {guildid}, '{data}')")
            cur.execute(f"INSERT INTO alias VALUES ({guildid}, 'embed', {embedid}, '{b64e(title)}')")
            conn.commit()

            await interaction.response.send_message(f"Embed created. Embed ID: `{embedid}`. Use `/embed send` to post it.", ephemeral = False)
            await log(f"Embed", f"[Guild {interaction.guild} {guildid}] {interaction.user} ({interaction.user.id}) created embed #{embedid}", guildid)

class ManageEmbed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    manage = SlashCommandGroup("embed", "Manage embed")

    @manage.command(name="create", description="Staff - Create embed. Detailed information will be edited in modal.")
    async def create(self, ctx, color: discord.Option(str, "Color in RGB (default 158 132 46)", required = False)):
        
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return

        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return

        conn = newconn()
        cur = conn.cursor()

        guildid = ctx.guild.id

        cur.execute(f"SELECT COUNT(*) FROM embed WHERE guildid = {guildid} AND embedid > 0")
        c = cur.fetchall()
        if len(c) > 0:
            premium = GetPremium(ctx.guild)
            cnt = c[0][0]
            if cnt >= 100 and premium >= 2:
                await ctx.respond("Max embeds: 100.\n\nIf you are looking for more embeds, contact Gecko Moderator in support server", ephemeral = True)
                return
            elif cnt >= 30 and premium == 1:
                await ctx.respond("Premium Tier 1: 30 embeds.\nPremium Tier 2: 100 embeds.\n\nFind out more by using `/premium`", ephemeral = True)
                return
            elif cnt >= 10 and premium == 0:
                await ctx.respond("Free guilds: 10 embeds.\nPremium Tier 1: 30 embeds.\nPremium Tier 2: 100 embeds.\n\nFind out more by using `/premium`", ephemeral = True)
                return
        
        if color is None:
            color = "158 132 46"
        else:
            t = color.split(" ")
            if len(t) != 3:
                await ctx.respond(f"{color} is not a valid RGB color code.", ephemeral = True)
                return
            for tt in t:
                try:
                    p = int(tt)
                    if p < 0 or p > 255:
                        await ctx.respond(f"{color} is not a valid RGB color code.", ephemeral = True)
                        return
                except:
                    await ctx.respond(f"{color} is not a valid RGB color code.", ephemeral = True)
                    return

        await ctx.send_modal(EmbedModal(-1, ctx.guild.id, color, "Create embed"))
    
    def AliasSearch(self, guildid, value):
        if value is None:
            return []
        value = value.lower()
        conn = newconn()
        cur = conn.cursor()
        cur.execute(f"SELECT elementid, label FROM alias WHERE guildid = {guildid} AND elementtype = 'embed'")
        t = cur.fetchall()
        alias = {}
        for tt in t:
            alias[f"{b64d(tt[1])} ({tt[0]})"] = tt[0]
        if value.replace(" ", "") == "":
            return list(alias.keys())[:10]
        res = process.extract(value, alias.keys(), score_cutoff = 60, limit = 10)
        ret = []
        for t in res:
            ret.append(t[0])
        return ret

    async def AliasAutocomplete(self, ctx: discord.AutocompleteContext):
        return self.AliasSearch(ctx.interaction.guild_id, ctx.value)

    @manage.command(name="edit", description="Staff - Edit embed. Detailed information will be edited in modal.")
    async def edit(self, ctx, embedid: discord.Option(str, "Embed id, provided when the it's created. Use /embed list to see all embeds in this guild.", required = False),
        title: discord.Option(str, "Embed title, alias to embed id", required = False, autocomplete = AliasAutocomplete),
        color: discord.Option(str, "Color in RGB. Leave empty to remain unchanged.", required = False)):
         
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return

        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return

        if embedid is None:
            embedid = self.AliasSearch(ctx.guild.id, title)
            if len(embedid) == 0:
                await ctx.respond("Failed to get embed ID by title.\nPlease use embedid instead.\nOr use `/embed list` to list all embeds in this guild.", ephemeral = True)
                return
            embedid = embedid[0][embedid[0].rfind("(") + 1 : embedid[0].rfind(")")]
        else:
            try:
                embedid = abs(int(embedid))
            except:
                await ctx.respond("Invalid embed ID!", ephemeral = True)
                return

        conn = newconn()
        cur = conn.cursor()

        cur.execute(f"SELECT data FROM embed WHERE guildid = {ctx.guild.id} AND embedid = {embedid}")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond("Embed not found.", ephemeral = True)
            return

        if color is None:
            color = t[0][0].split("|")[-1]
        else:
            t = color.split(" ")
            if len(t) != 3:
                await ctx.respond(f"{color} is not a valid RGB color code.", ephemeral = True)
                return
            for tt in t:
                try:
                    p = int(tt)
                    if p < 0 or p > 255:
                        await ctx.respond(f"{color} is not a valid RGB color code.", ephemeral = True)
                        return
                except:
                    await ctx.respond(f"{color} is not a valid RGB color code.", ephemeral = True)
                    return

        await ctx.send_modal(EmbedModal(embedid, ctx.guild.id, color, "Edit embed"))
    
    @manage.command(name="delete", description="Staff - Delete embed from database. This will not delete messages already sent.")
    async def delete(self, ctx, embedid: discord.Option(int, "Embed id, provided when the it's created. Use /embed list to see all embeds in this guild.", required = False),
            title: discord.Option(str, "Embed title, alias to embed id", required = False, autocomplete = AliasAutocomplete)):
        
        await ctx.defer()    
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return

        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return

        if embedid is None:
            embedid = self.AliasSearch(ctx.guild.id, title)
            if len(embedid) == 0:
                await ctx.respond("Failed to get embed ID by title.\nPlease use embedid instead.\nOr use `/embed list` to list all embeds in this guild.", ephemeral = True)
                return
            embedid = embedid[0][embedid[0].rfind("(") + 1 : embedid[0].rfind(")")]
        else:
            try:
                embedid = abs(int(embedid))
            except:
                await ctx.respond("Invalid embed ID!", ephemeral = True)
                return

        conn = newconn()
        cur = conn.cursor()

        cur.execute(f"SELECT data FROM embed WHERE guildid = {ctx.guild.id} AND embedid = {embedid}")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond("Embed not found.", ephemeral = True)
            return

        cur.execute(f"UPDATE embed SET embedid = -embedid WHERE guildid = {ctx.guild.id} AND embedid = {embedid}")
        cur.execute(F"DELETE FROM alias WHERE guildid = {ctx.guild.id} AND elementtype = 'embed' AND elementid = {embedid}")
        conn.commit()

        await ctx.respond(f"Embed #{embedid} deleted from database. Note that messages sent in guilds are not affected.")
        await log(f"Embed", f"[Guild {ctx.guild} {ctx.guild.id}] {ctx.author} ({ctx.author.id}) updated embed #{embedid}", ctx.guild.id)
    
    @manage.command(name="preview", description="Staff - Preview an embed privately before posting it in public.")
    async def preview(self, ctx, embedid: discord.Option(int, "Embed id, provided when the it's created. Use /embed list to see all embeds in this guild.", required = False),
            title: discord.Option(str, "Embed title, alias to embed id", required = False, autocomplete = AliasAutocomplete),
            showauthor: discord.Option(str, "Show author? (Your avatar and name will be displayed)", required = False, choices = ["Yes", "No"]),
            timestamp: discord.Option(str, "Add timestamp?", required = False, choices = ["Yes", "No"])):
        
        await ctx.defer()    
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return

        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return

        if embedid is None:
            embedid = self.AliasSearch(ctx.guild.id, title)
            if len(embedid) == 0:
                await ctx.respond("Failed to get embed ID by title.\nPlease use embedid instead.\nOr use `/embed list` to list all embeds in this guild.", ephemeral = True)
                return
            embedid = embedid[0][embedid[0].rfind("(") + 1 : embedid[0].rfind(")")]
        else:
            try:
                embedid = abs(int(embedid))
            except:
                await ctx.respond("Invalid embed ID!", ephemeral = True)
                return

        conn = newconn()
        cur = conn.cursor()

        cur.execute(f"SELECT data FROM embed WHERE guildid = {ctx.guild.id} AND embedid = {embedid}")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond("Embed not found.", ephemeral = True)
            return
            
        d = t[0][0].split("|")
        title = b64d(d[0])
        url = b64d(d[1])
        description = b64d(d[2])
        footer = b64d(d[3])
        thumbnail_url = [b64d(d[4]), b64d(d[5])]
        clr = d[6].split(" ")

        footer_icon_url = ""

        if footer.startswith("["):
            footer_icon_url = footer[footer.find("[") + 1: footer.find("]")].replace(" ","")
            footer = footer[footer.find("]") + 1:]
        
        embed=discord.Embed(title=title, url=url, description=description, color=discord.Colour.from_rgb(int(clr[0]), int(clr[1]), int(clr[2])))
        if showauthor == "Yes":
            icon_url = discord.Embed.Empty
            if not ctx.author.avatar is None:
                icon_url = ctx.author.avatar.url
            embed.set_author(name=ctx.author.name, icon_url=icon_url)
        if timestamp == "Yes":
            embed.timestamp = datetime.now()
        embed.set_footer(text=footer, icon_url=footer_icon_url)
        embed.set_thumbnail(url=thumbnail_url[0])
        embed.set_image(url=thumbnail_url[1])
        await ctx.respond(embed = embed, ephemeral = True)

    @manage.command(name="list", description="Staff - List all embeds in this guild.")
    async def show(self, ctx):
        await ctx.defer()    
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return

        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return

        conn = newconn()
        cur = conn.cursor()
        
        cur.execute(f"SELECT embedid, data FROM embed WHERE guildid = {ctx.guild.id}")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond("There's no embed created in this guild. Use `/embed create` to create one.")
            return
        
        msg = f"Below are all embeds created using Gecko in {ctx.guild}.\nOnly title is shown and you can use `/embed edit` to see details.\n\n"
        for tt in t:
            msg += f"Embed *#{tt[0]}*: **{b64d(tt[1].split('|')[0])}**\n"
        
        if len(msg) > 2000:
            f = io.BytesIO()
            f.write(msg.encode())
            f.seek(0)
            await ctx.respond(file=discord.File(fp=f, filename='Embeds.MD'))
        else:
            embed=discord.Embed(title=f"Embeds in {ctx.guild}", description=msg, color=GECKOCLR)
            embed.set_footer(text = f"Gecko Embed", icon_url = GECKOICON)
            await ctx.respond(embed = embed)
        
    @manage.command(name="send", description="Staff - Send an embed in public.")
    async def send(self, ctx, channel: discord.Option(discord.TextChannel, "Channel to post the embed.", required = True),
            embedid: discord.Option(int, "Embed id, provided when the it's created. Use /embed list to see all embeds in this guild.", required = False),
            title: discord.Option(str, "Embed title, alias to embed id", required = False, autocomplete = AliasAutocomplete),
            showauthor: discord.Option(str, "Show author? (Your avatar and name will be displayed)", required = False, choices = ["Yes", "No"]),
            timestamp: discord.Option(str, "Add timestamp?", required = False, choices = ["Yes", "No"])):
        
        await ctx.defer()    
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return

        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return

        channelid = channel.id

        if embedid is None:
            embedid = self.AliasSearch(ctx.guild.id, title)
            if len(embedid) == 0:
                await ctx.respond("Failed to get embed ID by title.\nPlease use embedid instead.\nOr use `/embed list` to list all embeds in this guild.", ephemeral = True)
                return
            embedid = embedid[0][embedid[0].rfind("(") + 1 : embedid[0].rfind(")")]
        else:
            try:
                embedid = abs(int(embedid))
            except:
                await ctx.respond("Invalid embed ID!", ephemeral = True)
                return

        conn = newconn()
        cur = conn.cursor()

        cur.execute(f"SELECT data FROM embed WHERE guildid = {ctx.guild.id} AND embedid = {embedid}")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond("Embed not found.", ephemeral = True)
            return
            
        d = t[0][0].split("|")
        title = b64d(d[0])
        url = b64d(d[1])
        description = b64d(d[2])
        footer = b64d(d[3])
        thumbnail_url = [b64d(d[4]), b64d(d[5])]
        clr = d[6].split(" ")

        footer_icon_url = ""

        if footer.startswith("["):
            footer_icon_url = footer[footer.find("[") + 1: footer.find("]")].replace(" ","")
            footer = footer[footer.find("]") + 1:]
        
        embed=discord.Embed(title=title, url=url, description=description, color=discord.Colour.from_rgb(int(clr[0]), int(clr[1]), int(clr[2])))
        if showauthor == "Yes":
            icon_url = discord.Embed.Empty
            if not ctx.author.avatar is None:
                icon_url = ctx.author.avatar.url
            embed.set_author(name=ctx.author.name, icon_url=icon_url)
        if timestamp == "Yes":
            embed.timestamp = datetime.now()
        embed.set_footer(text=footer, icon_url=footer_icon_url)
        embed.set_thumbnail(url=thumbnail_url[0])
        embed.set_image(url=thumbnail_url[1])

        try:
            await channel.send(embed = embed)
            await ctx.respond(f"Embed #{embedid} posted at <#{channelid}>")
        except:
            await ctx.respond(f"Failed to post embed at <#{channelid}>. Make sure I have access to the channel!")
        
    @manage.command(name="update", description="Staff - Update an embed in a message. The message must be sent by Gecko.")
    async def update(self, ctx, msglink: discord.Option(str, "Link to the message to update.", required = True),
            embedid: discord.Option(int, "Embed id, provided when the it's created. Use /embed list to see all embeds in this guild.", required = False),
            title: discord.Option(str, "Embed title, alias to embed id", required = False, autocomplete = AliasAutocomplete),
            showauthor: discord.Option(str, "Show author? (Your avatar and name will be displayed)", required = False, choices = ["Yes", "No"]),
            timestamp: discord.Option(str, "Add timestamp?", required = False, choices = ["Yes", "No"])):
        
        await ctx.defer()    
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return

        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return

        if not msglink.endswith("/"):
            msglink = msglink + "/"
        msglink = msglink.split("/")
        messageid = int(msglink[-2])
        channelid = int(msglink[-3])

        if embedid is None:
            embedid = self.AliasSearch(ctx.guild.id, title)
            if len(embedid) == 0:
                await ctx.respond("Failed to get embed ID by title.\nPlease use embedid instead.\nOr use `/embed list` to list all embeds in this guild.", ephemeral = True)
                return
            embedid = embedid[0][embedid[0].rfind("(") + 1 : embedid[0].rfind(")")]
        else:
            try:
                embedid = abs(int(embedid))
            except:
                await ctx.respond("Invalid embed ID!", ephemeral = True)
                return

        conn = newconn()
        cur = conn.cursor()

        cur.execute(f"SELECT data FROM embed WHERE guildid = {ctx.guild.id} AND embedid = {embedid}")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond("Embed not found.", ephemeral = True)
            return
            
        d = t[0][0].split("|")
        title = b64d(d[0])
        url = b64d(d[1])
        description = b64d(d[2])
        footer = b64d(d[3])
        thumbnail_url = [b64d(d[4]), b64d(d[5])]
        clr = d[6].split(" ")

        footer_icon_url = ""

        if footer.startswith("["):
            footer_icon_url = footer[footer.find("[") + 1: footer.find("]")].replace(" ","")
            footer = footer[footer.find("]") + 1:]
        
        embed=discord.Embed(title=title, url=url, description=description, color=discord.Colour.from_rgb(int(clr[0]), int(clr[1]), int(clr[2])))
        if showauthor == "Yes":
            icon_url = discord.Embed.Empty
            if not ctx.author.avatar is None:
                icon_url = ctx.author.avatar.url
            embed.set_author(name=ctx.author.name, icon_url=icon_url)
        if timestamp == "Yes":
            embed.timestamp = datetime.now()
        embed.set_footer(text=footer, icon_url=footer_icon_url)
        embed.set_thumbnail(url=thumbnail_url[0])
        embed.set_image(url=thumbnail_url[1])

        try:
            channel = bot.get_channel(channelid)
            message = await channel.fetch_message(messageid)
            await message.edit(embed = embed)
            await ctx.respond(f"Embed in [message]({'/'.join(msglink)[:-1]}) updated.")
        except:
            await ctx.respond(f"Failed to update [message]({'/'.join(msglink)[:-1]}). Make sure it exists and is sent by Gecko!")

bot.add_cog(ManageEmbed(bot))