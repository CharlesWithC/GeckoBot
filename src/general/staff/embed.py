# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Staff Functions of Gecko Bot

import os, asyncio
import discord
from discord.commands import CommandPermission, SlashCommandGroup
from discord.ext import commands
from discord.ui import Modal, InputText
from base64 import b64encode, b64decode
import validators

from bot import bot
from settings import *
from functions import *
from db import newconn

class EmbedModal(Modal):
    def __init__(self, channel, message, showauthor, color, author, orgdata, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.channel = channel
        self.message = message
        self.showauthor = showauthor
        self.author = author
        self.color = color

        self.add_item(InputText(label="Title", placeholder = "(Required)", value = orgdata[0]))
        self.add_item(InputText(label="URL", placeholder = "(Optional)", value = orgdata[1], required = False))
        self.add_item(InputText(label="Description", style=discord.InputTextStyle.long, placeholder = "(Required)", value = orgdata[2]))
        self.add_item(InputText(label="Footer", placeholder = "(Optional, add [URL] for icon, e.g. [icon url] footer)", value = orgdata[3], required = False))
        self.add_item(InputText(label="Thumbnail | Image URL", placeholder = "(Optional, use | to split, you can leave either empty)", value = orgdata[4], required = False))

    async def callback(self, interaction: discord.Interaction):
        title = self.children[0].value
        url = self.children[1].value.replace(" ","")
        description = self.children[2].value
        footer = self.children[3].value
        thumbnail_url = self.children[4].value.replace(" ","")

        if "|" in thumbnail_url:
            thumbnail_url = thumbnail_url.split("|")
        else:
            thumbnail_url = [thumbnail_url, ""]

        footer_icon_url = ""

        if footer.startswith("["):
            footer_icon_url = footer[footer.find("[") + 1: footer.find("]")].replace(" ","")
            footer = footer[footer.find("]") + 1:]
        
        clr = self.color.split()

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

        message = self.message
        if message is None:
            try:
                channel = bot.get_channel(self.channel)
                embed=discord.Embed(title=title, url=url, description=description, color=discord.Colour.from_rgb(int(clr[0]), int(clr[1]), int(clr[2])))
                if self.showauthor:
                    embed.set_author(name=self.author.name, icon_url=self.author.avatar.url)
                embed.set_footer(text=footer, icon_url=footer_icon_url)
                embed.set_thumbnail(url=thumbnail_url[0])
                embed.set_image(url=thumbnail_url[1])
                await channel.send(embed = embed)
                await interaction.response.send_message(f"The embed has been posted at <#{self.channel}>", ephemeral = True)
            except:
                await interaction.response.send_message(f"I cannot post the embed at <#{self.channel}>", ephemeral = True)
        else:
            try:
                embed=discord.Embed(title=title, url=url, description=description, color=discord.Colour.from_rgb(int(clr[0]), int(clr[1]), int(clr[2])))
                if self.showauthor:
                    embed.set_author(name=self.author.name, icon_url=self.author.avatar.url)
                embed.set_footer(text=footer, icon_url=footer_icon_url)
                embed.set_thumbnail(url=thumbnail_url[0])
                embed.set_image(url=thumbnail_url[1])
                await message.edit(embed = embed)
                await interaction.response.send_message(f"The embed has been updated.", ephemeral = True)
            except:
                import traceback
                traceback.print_exc()
                await interaction.response.send_message(f"I cannot edit the message.", ephemeral = True)

class ManageEmbed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    manage = SlashCommandGroup("embed", "Manage embed")

    @manage.command(name="create", description="Staff - Create embed. Detailed information will be edited in modal.")
    async def create(self, ctx, channel: discord.Option(str, "Channel to post the embed", required = True),
        showauthor: discord.Option(str, "Show author? (Your avatar and name will be displayed)", required = True, choices = ["Yes", "No"]),
        color: discord.Option(str, "Color in RGB (e.g. 135 206 235 for skyblue)", required = False)):
        
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return

        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return
        
        if not channel.startswith("<#") or not channel.endswith(">"):
            await ctx.respond(f"{channel} is not a valid channel!", ephemeral = True)
            return
        
        if color is None:
            color = "135 206 235"

        if showauthor == "Yes":
            showauthor = True
        elif showauthor == "No":
            showauthor = False

        channel = int(channel[2:-1])

        orgdata = ["", "", "", "", ""]

        await ctx.send_modal(EmbedModal(channel, None, showauthor, color, ctx.author, orgdata, "Create embed"))
    
    @manage.command(name="edit", description="Staff - Edit embed. Detailed information will be edited in modal.")
    async def edit(self, ctx, msglink: discord.Option(str, "The message link to the original embed", required = True),
        showauthor: discord.Option(str, "Show author? (Your avatar and name will be displayed)", required = True, choices = ["Yes", "No"]),
        color: discord.Option(str, "Color in RGB (e.g. 135 206 235 for skyblue)", required = False)):
        
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return

        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return

        if not validators.url(msglink):
            await ctx.respond(f"{msglink} was an invalid message link.", ephemeral = True)
            return
        
        if not msglink.endswith("/"):
            msglink = msglink + "/"
        msglink = msglink.split("/")
        messageid = int(msglink[-2])
        channelid = int(msglink[-3])
        
        channel = None
        orgmsg = None
        try:
            channel = bot.get_channel(channelid)
            orgmsg = await channel.fetch_message(messageid)
            if orgmsg is None or len(orgmsg.embeds) == 0:
                await ctx.respond(f"The link does not refer to an existing message or a message containing embed.", ephemeral = True)
                return
        except:
            import traceback
            traceback.print_exc()
            await ctx.respond(f"The link does not refer to an existing message or a message containing embed.", ephemeral = True)
            return

        if orgmsg.author.id != BOTID:
            await ctx.respond(f"The message wasn't sent by me so I can not edit it.", ephemeral = True)
            return

        embed = orgmsg.embeds[0]
        fu = ""
        if not embed.footer.icon_url == discord.Embed.Empty:
            fu = embed.footer.icon_url
        ft = ""
        if not embed.footer.text == discord.Embed.Empty:
            ft = embed.footer.text
        tu = ""
        if not embed.thumbnail.url == discord.Embed.Empty:
            tu = embed.thumbnail.url
        tt = ""
        if not embed.image.url == discord.Embed.Empty:
            tt = embed.image.url
        orgdata = [embed.title, embed.url, embed.description, f"[{fu}] {ft}", f"{tu} | {tt}"]
        
        if color is None:
            color = "135 206 235"

        if showauthor == "Yes":
            showauthor = True
        elif showauthor == "No":
            showauthor = False

        await ctx.send_modal(EmbedModal(channel, orgmsg, showauthor, color, ctx.author, orgdata, "Edit embed"))

bot.add_cog(ManageEmbed(bot))