import os
import json
import discord
from discord.ui import View, Button
from discord.ext import commands
from pymongo import MongoClient
from typing import Optional
from dotenv import load_dotenv

load_dotenv('.env.dev')

GUILD_ID = os.getenv('GUILD_ID')

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='/', intents=intents)
tree = discord.app_commands.CommandTree(client)

# MongoDB connection
user = os.getenv('MONGO_USER')
passwd = os.getenv('MONGO_PASS')
server = os.getenv('MONGO_IP')

db_client = MongoClient(f"mongodb://{user}:{passwd}@{server}:27017/")
db = db_client['wilds-event-quests']
collection = db['quests']

@bot.event
async def on_ready():
    print(f"=== BOT STARTUP INFORMATION ===")
    print(f"Connected as: {bot.user.name} (ID: {bot.user.id})")
    print(f"Using token starting with: {os.environ['DISC_TOKEN'][:6]}...")
    print(f"Bot is a member of {len(bot.guilds)} servers:")
    for guild in bot.guilds:
        print(f" - {guild.name} (ID: {guild.id})")
    print(f"Looking for GUILD_ID: {os.environ['GUILD_ID']}")
    
    # Force sync commands at startup
    print("Attempting to sync commands...")
    try:
        # Try to sync globally first
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands globally")
        
        # Then sync to each guild the bot is in
        for guild in bot.guilds:
            guild_obj = discord.Object(id=guild.id)
            bot.tree.copy_global_to(guild=guild_obj)
            guild_synced = await bot.tree.sync(guild=guild_obj)
            print(f"Synced {len(guild_synced)} commands to {guild.name}")
    except Exception as e:
        print(f"Error syncing commands: {str(e)}")
    
    print(f"=== END STARTUP INFO ===")

    print("\n=== COMMAND REGISTRATION INFO ===")
    
    # Get global commands
    try:
        global_commands = await bot.tree.fetch_commands()
        print(f"Global commands ({len(global_commands)}):")
        for cmd in global_commands:
            print(f"  - /{cmd.name}")
    except Exception as e:
        print(f"Error fetching global commands: {e}")
    
    # Check guild commands if in any guilds
    if bot.guilds:
        for guild in bot.guilds:
            try:
                guild_commands = await bot.tree.fetch_commands(guild=guild)
                print(f"Commands for guild {guild.name} ({len(guild_commands)}):")
                for cmd in guild_commands:
                    print(f"  - /{cmd.name}")
            except Exception as e:
                print(f"Error fetching commands for guild {guild.name}: {e}")
    else:
        print("Bot is not in any guilds, cannot check guild commands")
    
    print("=== END COMMAND INFO ===")

# Add a command to show available quests in the console for debugging
@bot.tree.command(name="list_quests", description="List all quests in the database (console output only)")
async def list_quests(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
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

class PaginationView(View):
    def __init__(self, pages, image_files, author_id):
        super().__init__(timeout=60)
        self.pages = pages
        self.image_files = image_files
        self.current_page = 0
        self.author_id = author_id
        self.update_buttons()
    
    def update_buttons(self):
        # Clear existing buttons
        self.clear_items()
        
        # Add nav buttons
        if self.current_page > 0:
            prev_button = Button(label="Previous", style=discord.ButtonStyle.primary)
            prev_button.callback = self.prev_page
            self.add_item(prev_button)
        
        # Add page indicator button (disabled, just for display)
        page_indicator = Button(
            label=f"Page {self.current_page + 1}/{len(self.pages)}", 
            style=discord.ButtonStyle.secondary, 
            disabled=True
        )
        self.add_item(page_indicator)
        
        if self.current_page < len(self.pages) - 1:
            next_button = Button(label="Next", style=discord.ButtonStyle.primary)
            next_button.callback = self.next_page
            self.add_item(next_button)
    
    async def prev_page(self, interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Only the command user can navigate pages.", ephemeral=True)
            return
            
        self.current_page -= 1
        self.update_buttons()
        embed = self.pages[self.current_page]

        # Testing to see if there are files for this page
        if self.current_page < len(self.image_files) and self.image_files[self.current_page]:
            image_path = self.image_files[self.current_page]
            file = discord.File(image_path, filename=os.path.basename(image_path))
            embed.set_image(url=f"attachment://{os.path.basename(image_path)}")
            await interaction.response.edit_message(embed=embed, view=self, attachments=[file])
        else:
            # No files? just update the embed
            await interaction.response.edit_message(embed=embed, view=self, attachments=[])
    
    # Make sure only the user who ran the command can navigate the pages
    async def next_page(self, interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Only the command user can navigate pages.", ephemeral=True)
            return
            
        self.current_page += 1
        self.update_buttons()
        embed = self.pages[self.current_page]

        if self.current_page < len(self.image_files) and self.image_files[self.current_page]:
            image_path = self.image_files[self.current_page]
            file = discord.File(image_path, filename=os.path.basename(image_path))
            embed.set_image(url=f"attachment://{os.path.basename(image_path)}")
            await interaction.response.edit_message(embed=embed, view=self, attachments=[file])
        else:
            await interaction.response.edit_message(embed=embed, view=self, attachments=[])

@bot.tree.command(name="interactive_quests", description="Show quests with interactive pagination")
async def interactive_quests(
    interaction: discord.Interaction,
    difficulty: Optional[str] = None,
    show_new_only: Optional[bool] = False,
    page_size: Optional[int] = 1
):
    await interaction.response.defer()
    
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

@bot.tree.command(name="weak", description="Quickly show monster weaknesses")
async def weakness(
    interaction: discord.Interaction,
    monster: Optional[str] = None,
    page_size: Optional[int] = 5
):
    await interaction.response.defer()

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
                embed.add_field(name=v.split(' ')[0], value=v, inline=False)
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
bot.run(os.getenv('DISC_TOKEN'))