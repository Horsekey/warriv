# my_cog.py
import discord
from discord.ext import commands
from discord import app_commands
from utils.dbHandler import database_connection

class ListQuests(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="list_quests", description="List all quests in the database (console output only)")
    async def list_quests(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        collection = database_connection("wilds-event-quests", "quests")

        try:
            quests = list(collection.find())
            print(f"Found {len(quests)} quests:")
            
            for quest in quests:
                print(f"Title: {quest.get('title')}")
                print(f"Difficulty: {quest.get('difficulty')}")
                print(f"Is New: {quest.get('is_new', False)}")
                print(f"Description: {quest.get('description')}")
                print("---")
                
            await interaction.followup.send(f"Listed {len(quests)} quests in the console.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ListQuests(bot))

