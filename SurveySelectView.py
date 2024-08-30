import discord
import math

class SurveySelect(discord.ui.Select):
    def __init__(self, surveys):
        self.selected = None
        options = []
        for survey in surveys:
            subject = survey['subject']
            if not subject: subject = 'MARVEL SNAP'
            options.append(discord.SelectOption(
                label=f'{survey["date"]} - {subject}',
                value=survey['message_id']
            ))

        super().__init__(placeholder=f'Select survey to view results', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected = [f for f in self.options if str(f.value) in self.values][0]
        self.selected = {"name": selected.label, "id": selected.value}
        await interaction.response.defer()
        self.view.value = True
        self.view.stop()

class LeftButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label='◀',
            style=discord.ButtonStyle.primary
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.view.page_down()

class RightButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label='▶',
            style=discord.ButtonStyle.primary
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.view.page_up()

class SurveySelectView(discord.ui.View):
    def __init__(self, interaction, surveys, timeout):
        super().__init__(timeout=timeout)
        self.interaction = interaction
        self.value = None
        self.page = 0
        self.total_pages = 1
        self.surveys = surveys

        if len(surveys) > 25:
            self.page = 1
            self.total_pages = math.ceil(len(surveys) / 25)
            surveys = self.surveys[0:25]

        self.select = SurveySelect(surveys)

        self.add_item(self.select)
        if self.page > 0:
            self.add_item(LeftButton())
            self.add_item(RightButton())

            # disable left button, we're first page at the start
            self.children[1].disabled = True

    async def page_down(self):
        if self.page <= 1:
            return
        self.page -= 1
        await self.change_page()

    async def page_up(self):
        if self.page >= self.total_pages:
            return
        self.page += 1
        await self.change_page()

    async def change_page(self):
        start = (self.page - 1) * 25
        end = start + 25
        surveys = self.surveys[start:end]

        # remove old select, add new select
        self.remove_item(self.select)

        self.select = SurveySelect(surveys)
        self.add_item(self.select)

        # disable buttons if needed
        self.children[0].disabled = self.page == 1
        self.children[1].disabled = self.page == self.total_pages

        await self.interaction.edit_original_response(view=self)
