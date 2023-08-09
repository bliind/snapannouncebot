import discord
import json
import os
import re
from discord.ext import tasks

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

@bot.event
async def on_ready():
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
                    if await output_channel.create_thread(name=title, files=files, content=actual_content):
                        await message.add_reaction("✅")
                else:
                    if await output_channel.send(actual_content, files=files):
                        await message.add_reaction("✅")
            else:
                await message.channel.send('No channel specified')

bot.run(config.token)
