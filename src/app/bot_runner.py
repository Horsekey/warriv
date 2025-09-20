# main.py
import discord
import os
from discord.ext import commands
from dotenv import load_dotenv

# load_dotenv('.env.dev')
load_dotenv(dotenv_path='.env.dev')
token = os.getenv('DISC_TOKEN')

class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def setup_hook(self):
        for filename in os.listdir("./src/app/cogs"):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f"Loaded cog: {filename[:-3]}")
                except Exception as e:
                    print(f"Failed to load cog {filename[:-3]}. {e}")

intents = discord.Intents.default()
bot = MyBot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    print("within sync")
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} command(s).")

bot.run(token)