import discord
from discord import app_commands
from discord.ext import commands
import datetime
from SurveyView import SurveyView
from SurveySelectView import SurveySelectView
import SurveyDatabase as db

def timestamp():
    now = datetime.datetime.now()
    return int(round(now.timestamp()))

def humantime(timestamp):
    date = datetime.datetime.fromtimestamp(timestamp)
    return date.strftime('%Y-%m-%d %H:%M:%S')

class Survey(commands.Cog):
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.server = discord.Object(id=config.server)
        self.bot.tree.add_command(self.create_survey, guild=self.server)
        self.bot.tree.add_command(self.survey_results, guild=self.server)
        self.bot.tree.add_command(self.last_survey_results, guild=self.server)

    def cog_unload(self):
        self.bot.tree.remove_command('create_survey', guild=self.server)
        self.bot.tree.remove_command('survey_results', guild=self.server)
        self.bot.tree.remove_command('last_survey_results', guild=self.server)

    def make_embed(self, color, description=None, title=None):
        # get the color function
        try: color = getattr(discord.Color, color)
        except: color = discord.Color.blue

        # make the embed
        embed = discord.Embed(
            color=color(),
            timestamp=datetime.datetime.now(),
            title=title,
            description=description
        )

        return embed

    @commands.Cog.listener()
    async def on_ready(self):
        latest = await db.get_latest_survey()
        if latest:
            view = SurveyView(timeout=None, channel_id=latest['channel_id'])
            view.message_id = latest['message_id']
            self.bot.add_view(view, message_id=latest['message_id'])

    @app_commands.command(name='create_survey', description='Create a satisfaction survey')
    async def create_survey(self, interaction: discord.Interaction, subject: str='MARVEL SNAP', color: str='blue'):
        # defer response
        await interaction.response.defer(ephemeral=True)
        await interaction.delete_original_response()

        description = f'# Overall, how satisfied are you with {subject}?\n\n'
        description += '😍  Very Satisfied\n\n'
        description += '🙂  Somewhat Satisfied\n\n'
        description += '😐  Neither Satisfied Nor Dissatisfied\n\n'
        description += '🙁  Somewhat Dissatisfied\n\n'
        description += '😣  Very Dissatisfied\n\n'
        embed = self.make_embed(color, description=description)

        view = SurveyView(timeout=None, channel_id=interaction.channel.id)
        survey_msg = await interaction.channel.send(embed=embed, view=view)
        view.message_id = survey_msg.id

        await db.create_survey(timestamp(), interaction.channel.id, survey_msg.id, 0, subject)

        # update buttons to disabled when finished
        await view.wait()
        for child in view.children:
            child.disabled = True
        await survey_msg.edit(embed=embed, view=view)

    @create_survey.autocomplete('color')
    async def autocomplete_survey_color(self, interaction: discord.Interaction, current: str):
        colors = [
            'blue',
            'blurple',
            'brand_green',
            'brand_red',
            'dark_blue',
            'dark_gold',
            'dark_gray',
            'dark_magenta',
            'dark_orange',
            'dark_purple',
            'dark_red',
            'dark_teal',
            'fuchsia',
            'gold',
            'green',
            'greyple',
            'light_grey',
            'magenta',
            'orange',
            'pink',
            'purple',
            'red',
            'teal',
            'yellow',
        ]

        return [
            app_commands.Choice(name=color, value=color) for color in colors if color.startswith(current)
        ]

    @app_commands.command(name='last_survey_results', description='Get the results for the most recent survey')
    async def last_survey_results(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        latest = await db.get_latest_survey()
        if not latest: return

        embed = await self.gather_survey_results(latest)

        await interaction.edit_original_response(embed=embed)

    async def gather_survey_results(self, survey):
        subject = survey['subject']
        if not subject: subject = 'MARVEL SNAP'

        message = f'Survey for {subject} posted <t:{survey["datestamp"]}>:\n\n'

        results = await db.get_results(survey['message_id'])

        responses = {
            'Very Satisfied': 0,
            'Somewhat Satisfied': 0,
            'Neither': 0,
            'Somewhat Dissatisfied': 0,
            'Very Dissatisfied': 0,
        }
        for result in results:
            responses[result['response']] = result['count']

        message += '```\n'
        for response, count in responses.items():
            message += f'{(response + ":").ljust(22)} {count}\n'
        message += '```'

        return self.make_embed('blurple', message, 'Survey Results')

    @app_commands.command(name='survey_results', description='Select which survey results to see')
    async def survey_results(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        all_surveys = await db.list_surveys()

        surveys = []
        for survey in all_surveys:
            surveys.append({
                "date": humantime(survey['datestamp']),
                "subject": survey['subject'],
                "message_id": survey['message_id']
            })

        # create the fancy dropdown View to send
        view = SurveySelectView(interaction, surveys, 30)
        embed = discord.Embed(description='Select a survey to view the results for')
        await interaction.edit_original_response(embed=embed, view=view)

        # wait for interaction with the dropdown (or timeout)
        await view.wait()
        if view.value:
            # they picked something, gather info
            selected = view.select.selected
            message_id = selected['id']

            survey_to_display = [s for s in all_surveys if s['message_id'] == message_id][0]

            results_embed = await self.gather_survey_results(survey_to_display)

            await interaction.edit_original_response(embed=results_embed, view=None)

