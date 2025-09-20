# my_cog.py
import discord
from discord.ext import commands
from discord import app_commands

class Food(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="food", description="food helper!")
    async def hello(self, interaction: discord.Interaction):
        await interaction.response.send_message("mmmmm food!")

async def setup(bot):
    await bot.add_cog(Food(bot))