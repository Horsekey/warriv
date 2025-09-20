# my_cog.py
import discord
from discord.ext import commands
from discord import app_commands
from utils.paginationView import PaginationView
from typing import Optional
from utils.dbHandler import database_connection
import os

class InteractiveQuests(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="interactive_quests", description="Show quests with interactive pagination")
    async def interactive_quests(
        interaction: discord.Interaction,
        difficulty: Optional[str] = None,
        show_new_only: Optional[bool] = False,
        page_size: Optional[int] = 1
    ):
        
        collection = database_connection("wilds-event-quests", "quests")
        await interaction.response.defer(ephemeral=True)
        
        query = {}
        if difficulty:
            query["difficulty"] = f"{difficulty}★"
        if show_new_only:
            query["is_new"] = True
            
        quests = list(collection.find(query))
        
        if not quests:
            await interaction.followup.send("No quests found with the specified criteria.")
            return
        
        pages = []
        files = []

        temp_dir = "./temp_quest_images/"
        os.makedirs(temp_dir, exist_ok=True)

        total_quests = len(quests)
        total_pages = (total_quests + page_size - 1) // page_size

        for page_num in range(total_pages):
            start_idx = page_num * page_size
            end_idx = min(start_idx + page_size, total_quests)
            page_quests = quests[start_idx:end_idx]
            
            embed = discord.Embed(
                title=f"Monster Hunter Quests",
                color=0x0080ff
            )

            for quest in page_quests:
                
                new_badge = "🆕  " if quest.get("is_new", False) else ""
                title = f"{new_badge}{quest.get('title')} ({quest.get('difficulty')})\n\u200B"
                value = (
                    f"**Location:** {quest.get('locale', 'Unknown')}\n"
                    f"**Objective:** {quest.get('completion_conditions', 'Unknown')}\n"
                    f"**Available:** {quest.get('start_datetime', 'Unknown')} to {quest.get('end_datetime', 'Unknown')}\n"
                    f"**Description:** {quest.get('description', 'Unknown')}\n\u200B"
                )
                embed.add_field(name=title, value=value, inline=False)

                page_image_path = None

                if page_quests and 'image_data' in page_quests[0] and page_quests[0]['image_data']:
                    try:
                        quest_title = page_quests[0].get('title', f"quest_{page_num}")
                        safe_title = "".join(c for c in quest_title if c.isalnum() or c in (' ', '_', '-')).replace(' ', '_')
                        image_filename = f"{safe_title}_{page_num}.png"
                        image_path = os.path.join(temp_dir, image_filename)

                        image_data_str = page_quests[0]['image_data']
                        import ast
                        image_bytes = ast.literal_eval(image_data_str) if image_data_str.startswith('b') else ast.literal_eval(f"b'{image_data_str}'")


                        with open(image_path, 'wb') as f:
                            f.write(image_bytes)

                        page_image_path = image_path

                    except Exception as e:
                        print(f"Error extracting image for page {page_num}: {str(e)}")

            filter_info = []
            if difficulty:
                filter_info.append(f"Difficulty: {difficulty}★")
            if show_new_only:
                filter_info.append("New quests only")
                
            if filter_info:
                embed.set_footer(text=f"Filters: {', '.join(filter_info)}")
            
            pages.append(embed)

            files.append(page_image_path)
        
        # Create pagination view
        view = PaginationView(pages, files, interaction.user.id)
        
        if files[0]:
            file = discord.File(files[0], filename=os.path.basename(files[0]))
            pages[0].set_image(url=f"attachment://{os.path.basename(files[0])}")
            await interaction.followup.send(embed=pages[0], view=view, file=file)
        else:
            await interaction.followup.send(embed=pages[0], view=view)

async def setup(bot):
    await bot.add_cog(InteractiveQuests(bot))