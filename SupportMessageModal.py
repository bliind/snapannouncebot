import discord
from discord import ui

class SupportMessageModal(ui.Modal, title="Update Support Message"):
    new_message = ui.TextInput(label='Message', style=discord.TextStyle.paragraph, min_length=0, required=False)

    def __init__(self, new_message):
        super().__init__()
        self.new_message.default = new_message

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

