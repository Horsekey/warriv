# my_cog.py
import discord
from discord.ext import commands
from discord import app_commands
import json
from typing import Optional
from utils.paginationView import PaginationView

class Weak(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="weak", description="Quickly show monster weaknesses")
    async def weakness(
        interaction: discord.Interaction,
        monster: Optional[str] = None,
        page_size: Optional[int] = 5
    ):
        await interaction.response.defer(ephemeral=True)

        with open('monster_weaknesses.json', 'r') as file:
            mappings = json.load(file)
        
        if monster:
            monster_lower = monster.lower()
            found = False
            embed = discord.Embed(
                title=f"Monster Weakness Guide",
                color=0x0080ff
            )
            
            for k, v in mappings.items():
                if monster_lower in v.lower():
                    embed.add_field(name=v.split(' ')[0], value=f"{k} {v}", inline=False)
                    found = True
                    
            if not found:
                embed.description = f"No monster matching '{monster}' found."
            
            return await interaction.followup.send(embed=embed)

        # Since mappings comes in as a dict, we need a list of tuples
        mapping_list = list(mappings.items())
        total_mappings = len(mapping_list)
        total_pages = (total_mappings + page_size - 1) // page_size
        pages = []
        files = []

        total_mappings = len(mapping_list)
        total_pages = (total_mappings + page_size - 1) // page_size
        
        for page_num in range(total_pages):
            start_idx = page_num * page_size
            end_idx = min(start_idx + page_size, total_mappings)
            page_mappings = mapping_list[start_idx:end_idx]
        
            embed = discord.Embed(
            title=f"Monster Weakness Guide",
            color=0x0080ff
            )

            # Iterate through touples in the page_mappings which is a slice of mapping_list to get the key and value
            for k,v in page_mappings:
                embed.add_field(name=f"{k} {v}", value="", inline=False)

            # Append the embed
            pages.append(embed)
            files.append(None)
        
        # If pages is empty, return
        if not pages:
            return await interaction.followup.send("No monster data available.")

        # Sending files but we don't have any in this case
        view = PaginationView(pages, files, interaction.user.id)
        await interaction.followup.send(embed=pages[0], view=view)

async def setup(bot):
    await bot.add_cog(Weak(bot))




