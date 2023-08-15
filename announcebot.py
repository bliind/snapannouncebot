import discord
import json
import os
import re
from discord import app_commands

class PostModal(discord.ui.Modal, title='Post Where?'):
    def __init__(self, the_message):
        super().__init__()
        self.the_message = the_message

    channel = discord.ui.TextInput(label='Channel')
    async def on_submit(self, interaction: discord.Interaction):
        message = self.the_message

        guild = [g for g in bot.guilds if g.id == config.server][0]
        channel = discord.utils.get(guild.channels, name=self.channel.value.replace('#', ''))

        if channel:
            files = []
            for file in message.attachments:
                files.append(await file.to_file())

            if channel.type == discord.ChannelType.forum:
                title = message.content.splitlines()[0]
                actual_content = message.content.replace(title, '').strip()
                thread = await channel.create_thread(name=title, files=files, content=actual_content)
                if thread:
                    await interaction.response.send_message(thread.message.jump_url, ephemeral=True)
                    await message.add_reaction("✅")
            else:
                sent = await channel.send(message.content, files=files)
                if sent:
                    await interaction.response.send_message(sent.jump_url, ephemeral=True)
                    await message.add_reaction("✅")
        else:
            await interaction.response.send_message('Failed, sorry', ephemeral=True)

class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

def load_config():
    global config
    config_file = 'announcebot_config.json' if env == 'prod' else 'announcebot_config.test.json'
    with open(config_file, encoding='utf8') as stream:
        config = json.load(stream)
    config = dotdict(config)

env = os.getenv('ANNOUNCEBOT_ENV')
load_config()

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

@bot.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=config.server))
    print(f"{config.env.upper()} ANNOUNCEBOT is ready for duty")

@bot.event
async def on_message(message):
    if message.author.id in config.allowed_users:
        if message.content.startswith(config.prompt):
            actual_content = message.content.replace(config.prompt, '')
            chanMatch = re.match(r'<#(?P<chanID>\d+)>', actual_content)
            if chanMatch:
                channelID = int(chanMatch.group('chanID'))
                actual_content = actual_content.replace(f'<#{channelID}>', '').strip()
                output_channel = bot.get_channel(channelID)

                files = []
                for file in message.attachments:
                    files.append(await file.to_file())

                if output_channel.type == discord.ChannelType.forum:
                    title = actual_content.splitlines()[0]
                    actual_content = actual_content.replace(title, '').strip()
                    thread = await output_channel.create_thread(name=title, files=files, content=actual_content)
                    if thread:
                        await message.channel.send(thread.message.jump_url)
                        await message.add_reaction("✅")
                else:
                    sent = await output_channel.send(actual_content, files=files)
                    if sent:
                        await message.channel.send(sent.jump_url)
                        await message.add_reaction("✅")
            else:
                await message.channel.send('No channel specified')

@tree.context_menu(name='Post Announcement', guild=discord.Object(id=config.server))
async def dev_reply_command(interaction, message: discord.Message):
    modal = PostModal(message)
    await interaction.response.send_modal(modal)

bot.run(config.token)
