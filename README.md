# Warriv
The discord bot you go to for directions. Who knows what this will entail, but at least it will be fun.

# Setup

### For Discord Setup
Follow https://discordpy.readthedocs.io/en/stable/discord.html

### For Python Dev
pip install -r requirements.txt

** In root directory **

touch .env 
echo 'DISC_TOKEN=$YOUR_APP_DISCORD_TOKEN' >> .env

$YOUR_PYTHON_COMMAND bot_runner.py

### To Run With Docker

docker build -t $TAG .

docker run $TAG

## Log

Adding db functionality
Adding command for upcoming features
Added basic utilities that can be used within every command
Refactored bot runner design to support slash commands

---

## Workflow

To create a new command for the bot, copy the template_mmmFood.py, name it `<game>_<command>`, and change the command name and description to whatever you want. Under the async function, you will be able to put the logic for your new command. Use the utilities in the `util` folder to help speed up development so you can easily add pagination, connect to a database, or get JSON back from an API. 