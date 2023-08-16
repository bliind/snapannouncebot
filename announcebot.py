import discord
import json
import os
import datetime
import announcedb
from discord import app_commands

##
class PostView(discord.ui.View):
    def __init__(self, timeout):
        super().__init__(timeout=timeout)
        self.value = None
        self.channel = None

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True

    @discord.ui.select(cls=discord.ui.ChannelSelect, custom_id='channel', channel_types=[discord.ChannelType.text, discord.ChannelType.forum])
    async def _channel(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        self.channel = select.values[0].name
        await interaction.response.defer()

    @discord.ui.button(label='Post it!', style=discord.ButtonStyle.green)
    async def _yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.value = True
        await self.on_timeout()
        self.stop()

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.red)
    async def _no(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.value = False
        await self.on_timeout()
        self.stop()

### EDIT VIEW
class EditSelect(discord.ui.Select):
    def __init__(self, posts):
        self.selected = None
        options = []
        for post in posts:
            dt = datetime.datetime.fromtimestamp(int(post.datestamp))
            datestamp = dt.strftime('%Y-%m-%d %I:%M %p')
            content = post.content.replace('\n', ' ')[:60]
            options.append(discord.SelectOption(
                label=f'{content}...',
                description=f'to #{post.channel} on {datestamp}',
                value=post.link
            ))

        super().__init__(placeholder='Select post to edit', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        self.selected = self.values[0]
        await interaction.response.defer()

class EditButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label='Edit Post',
            style=discord.ButtonStyle.green
        )

    async def callback(self, interaction: discord.Interaction):
        self.view.value = True
        await interaction.response.defer()
        self.view.stop()

class CancelButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label='Cancel',
            style=discord.ButtonStyle.red
        )

    async def callback(self, interaction: discord.Interaction):
        self.view.value = False
        await interaction.response.defer()
        self.view.stop()

class EditView(discord.ui.View):
    def __init__(self, posts, timeout):
        super().__init__(timeout=timeout)
        self.value = None
        self.post = None
        self.select = EditSelect(posts)

        self.add_item(self.select)
        self.add_item(EditButton())
        self.add_item(CancelButton())

###
##

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

class MyClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.synced = False
    
    async def on_ready(self):
        print(f"{config.env.upper()} ANNOUNCEBOT is ready for duty")
        if not self.synced:
            await tree.sync(guild=discord.Object(id=config.server))
            self.synced = True

bot = MyClient()
tree = app_commands.CommandTree(bot)

@tree.context_menu(name='Post Announcement', guild=discord.Object(id=config.server))
async def post_announcement_command(interaction, message: discord.Message):
    view = PostView(timeout=30)
    await interaction.response.send_message(message.content.splitlines()[0] + '...', view=view)
    await view.wait()
    if view.value:
        # Post it! was chosen
        guild = [g for g in bot.guilds if g.id == config.server][0]
        channel = discord.utils.get(guild.channels, name=view.channel)
        if channel:
            files = []
            for file in message.attachments:
                files.append(await file.to_file())

            if channel.type == discord.ChannelType.forum:
                title = message.content.splitlines()[0]
                actual_content = message.content.replace(title, '').strip()
                thread = await channel.create_thread(name=title, files=files, content=actual_content)
                if thread:
                    announcedb.add_post(channel.name, actual_content, thread.message.jump_url, int(round(thread.message.created_at.timestamp())))
                    await interaction.edit_original_response(content=None, view=None, embed=discord.Embed(description=thread.message.jump_url))
                    await message.add_reaction("✅")
            else:
                sent = await channel.send(message.content, files=files)
                if sent:
                    announcedb.add_post(channel.name, message.content, sent.jump_url, int(round(sent.created_at.timestamp())))
                    await interaction.edit_original_response(content=None, view=None, embed=discord.Embed(description=sent.jump_url))
                    await message.add_reaction("✅")
        else:
            await interaction.edit_original_response(content=None, view=None, embed=discord.Embed(description='No channel selected'))
    else:
        await interaction.edit_original_response(content=None, view=None, embed=discord.Embed(description='Cancelled'))

@tree.context_menu(name='Edit Announcement', guild=discord.Object(id=config.server))
async def edit_announcement_command(interaction: discord.Interaction, message: discord.Message):
    options = []
    for post in announcedb.get_last_posts():
        options.append(dotdict(post))
    view = EditView(options, timeout=30)
    await interaction.response.send_message(view=view)
    await view.wait()
    if view.value:
        if view.select.selected:
            our_post = [o for o in options if o.link == view.select.selected][0]
            announcedb.update_content(our_post.id, message.content)
            link = view.select.selected.split('/')
            message_id = int(link.pop())
            channel_id = int(link.pop())
            chan = bot.get_channel(channel_id)
            msg = await chan.fetch_message(message_id)
            await msg.edit(content=message.content)
            await interaction.edit_original_response(view=None, embed=discord.Embed(description=f'Edited {view.select.selected}'))
        else:
            await interaction.edit_original_response(view=None, embed=discord.Embed(description=f'No post selected'))
    else:
        await interaction.edit_original_response(view=None, embed=discord.Embed(description=f'Cancelled'))

bot.run(config.token)
