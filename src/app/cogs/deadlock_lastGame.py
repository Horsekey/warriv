# my_cog.py
import discord
from discord.ext import commands
from discord import app_commands
import requests
import json
import os
import io
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime,timedelta
from utils.paginationView import PaginationView

class DeadLockStats:
    def __init__(self, api_data, player_index):
        self.match_type = str(api_data['match_info']['game_mode'])
        self.match_time = str(api_data['match_info']['start_time'])
        self.match_id = str(api_data['match_info']['match_id'])
        self.match_result = str(api_data['match_info']['winning_team'])
        self.match_duration = round(api_data['match_info']['duration_s'] / 60)
        self.match_kills = str(api_data['match_info']['players'][player_index]['kills'])
        self.match_deaths = str(api_data['match_info']['players'][player_index]['deaths'])
        self.match_assists = str(api_data['match_info']['players'][player_index]['assists'])
        self.match_cs = str(api_data['match_info']['players'][player_index]['last_hits'])
        self.match_spm = str(round(api_data['match_info']['players'][player_index]['net_worth'] / api_data['match_info']['duration_s']))
        # self.match_kp = api_data['match_info']['players'][player_index]['kills']
        # self.match_total_kills = api_data['match_info']['players'][player_index]['kills']
        self.match_headshot = str(round(api_data['match_info']['players'][player_index]['stats'][-1]['hero_bullets_hit_crit'] / api_data['match_info']['players'][player_index]['stats'][-1]['hero_bullets_hit'] * 100))
        self.match_hero = str(api_data['match_info']['players'][player_index]['hero_id'])

def resolve_hero(hero_id):
    with open('mock_data/json/heroes.json', 'r') as f:
            hero_json = json.load(f)

    for hero_obj in hero_json:
        # print(f'hero_id: {hero_id}\nhero_obj: {hero_obj}\nhero_id: {hero_obj['id']}\nhero_name: {hero_obj['name']}')
        if str(hero_obj['id']) == str(hero_id):
            return hero_obj['name']
        
    return None

def resolve_account_id(discord_id):
    with open('mock_data/json/tracked_players.json', 'r') as f:
            player_json = json.load(f)

    # print(f"PLAYER JSON in resolve_account_id: {player_json}")
    
    for player in player_json:
        # print(player['discord_id'], discord_id)
        if player['discord_id'] == str(discord_id):
            # print(f"player_name: {player['name']}\nplayer_discord: {player['discord_id']}\nplayer_steam: {player['steam_id']}")
            return player
        
    return None

# def generate_image(match_type, match_time, match_id, match_result, match_duration, match_kills, match_deaths, match_assists, match_cs, match_spm, match_kp, match_total_kills, match_headshot):
def generate_image(match_type, match_time, match_id, match_duration, match_kills, match_deaths, match_assists, match_cs, match_spm, match_headshot, match_hero_name, items):

    image = Image.new("RGBA", (515, 150), "darkslategray")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=12)

    # main stats
    draw.text((25, 25), match_type, fill=(255, 255, 255), font=font)
    draw.text((25, 45), match_time, fill=(255, 255, 255), font=font)
    draw.text((25, 65), match_id, fill=(255, 255, 255), font=font)
    draw.text((25, 100), "WIN/LOSS", fill=(255, 255, 255), font=font)
    draw.text((25, 120), str(match_duration), fill=(255, 255, 255), font=font)
    draw.text((100, 120), "RANK", fill=(255, 255, 255), font=font)

    # divider
    middle_y = image.height // 2 + 13
    draw.line([(20, middle_y), (125, middle_y)], fill="white", width=1)

    # character icon
    avatar = Image.open(f"mock_data/assets/deadlock/{match_hero_name}.png").convert("RGBA")
    avatar.thumbnail((50, 50), Image.Resampling.LANCZOS)

    square_avatar = Image.new("RGBA", (50, 50), (0, 0, 0, 0))
    ax = (50 - avatar.width) // 2
    ay = (50 - avatar.height) // 2
    square_avatar.paste(avatar, (ax, ay))

    mask = Image.new("L", (50, 50), 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.ellipse((0, 0, 50, 50), fill=255)

    image.paste(square_avatar, (115, 20), mask)

    # ellipse border
    draw.ellipse([(115, 20), (165, 70)], outline="white", width=2)

    kda = match_kills + " / " + match_deaths + " / " + match_assists
    kda_percentage = int(match_kills) + int(match_assists) / int(match_deaths)
    draw.text((185, 25), kda, (255, 255, 255), font=font)
    draw.text((185, 40), f"{round(kda_percentage)} KDA", (255, 255, 255), font=font)
    
    # item bounding boxes

    item_slots = [
    (190, 60, 220, 90),
    (225, 60, 255, 90),
    (260, 60, 290, 90),
    (295, 60, 325, 90),
    (330, 60, 360, 90),
    (365, 60, 395, 90),

    (190, 95, 220, 125),
    (225, 95, 255, 125),
    (260, 95, 290, 125),
    (295, 95, 325, 125),
    (330, 95, 360, 125),
    (365, 95, 395, 125),
    ]

    for rect in item_slots:
        draw.rounded_rectangle(rect, radius=5, outline="white", width=2)

    item_urls = items

    for rect, url in zip(item_slots, item_urls):
        try:
            # Download the image
            response = requests.get(url)
            response.raise_for_status()
            item_img = Image.open(io.BytesIO(response.content)).convert("RGBA")

            x1, y1, x2, y2 = rect
            slot_w, slot_h = x2 - x1, y2 - y1

            # resize item image
            item_img.thumbnail((slot_w, slot_h), Image.Resampling.LANCZOS)

            # center position
            paste_x = x1 + (slot_w - item_img.width) // 2
            paste_y = y1 + (slot_h - item_img.height) // 2

            # paste into the slot
            image.paste(item_img, (paste_x, paste_y), item_img)

        except Exception as e:
            print(f"Failed to load {url}: {e}")
    
    # draw.rounded_rectangle([(190, 60), (220, 90)], radius=5, outline="white", width=2)
    # draw.rounded_rectangle([(225, 60), (255, 90)], radius=5, outline="white", width=2)
    # draw.rounded_rectangle([(260, 60), (290, 90)], radius=5, outline="white", width=2)
    # draw.rounded_rectangle([(295, 60), (325, 90)], radius=5, outline="white", width=2)
    # draw.rounded_rectangle([(330, 60), (360, 90)], radius=5, outline="white", width=2)
    # draw.rounded_rectangle([(365, 60), (395, 90)], radius=5, outline="white", width=2)

    # draw.rounded_rectangle([(190, 95), (220, 125)], radius=5, outline="white", width=2)
    # draw.rounded_rectangle([(225, 95), (255, 125)], radius=5, outline="white", width=2)
    # draw.rounded_rectangle([(260, 95), (290, 125)], radius=5, outline="white", width=2)
    # draw.rounded_rectangle([(295, 95), (325, 125)], radius=5, outline="white", width=2)
    # draw.rounded_rectangle([(330, 95), (360, 125)], radius=5, outline="white", width=2)
    # draw.rounded_rectangle([(365, 95), (395, 125)], radius=5, outline="white", width=2)

    draw.text((425, 45), f"CS {match_cs}", (255, 255, 255), font=font)
    draw.text((425, 60), f"SPM {match_spm}", (255, 255, 255), font=font)
    draw.text((425, 75), "KP", (255, 255, 255), font=font)
    draw.text((425, 90), f"HS {match_headshot}%", (255, 255, 255), font=font)
    
    image_binary = io.BytesIO()
    image.save(image_binary, format="PNG")
    image_binary.seek(0)  # rewind so Discord can read it
    return image_binary

class Deadlock(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="deadlock", description="get dedlok thing")
    async def matches(self, interaction: discord.Interaction):

        account_json = resolve_account_id(interaction.user.id)
        # print(f"ACCOUNT JSON: {account_json}")
        await interaction.response.defer()
        
        # get match history
        response = requests.get(
            f"https://api.deadlock-api.com/v1/players/{account_json['steam_id']}/match-history",
        )

        match_history = response.json()
        # print(f"MATCH HISTORY (one): {match_history[0]}")

        # get latest match
        latest_match = match_history[0]
        # print(f"LATEST MATCH: {latest_match}")

        # get match metadata
        match_response = requests.get(
            f"https://api.deadlock-api.com/v1/matches/{latest_match['match_id']}/metadata",
        )

        # print(f"MATCH RESPONSE: {match_response}")

        # resolve account id within match metadata
        match_data = match_response.json()
        
        for index, player in enumerate(match_data['match_info']['players']):
            # print(account_json['deadlock_id'], player['account_id'])
            if str(account_json['deadlock_id']) == str(player['account_id']):
                # get last item in match metadata list which will be ending stats
                stats = player
                # print(f"PLAYER JSON: {stats}")
                # print(index)
                stats = DeadLockStats(match_data, index)
                
                match_hero_name = resolve_hero(stats.match_hero)

                # print(f"PLAYER: {player}")

                # create items array
                items = []
                for item in player['items']:
                    
                    # print(item['item_id'])
                    
                    item_response = requests.get(
                        f"https://assets.deadlock-api.com/v2/items/{item['item_id']}",
                    )

                    # print(item_response)
                    item_data = item_response.json()
                    # print(f"ITEM DATA: {item_data}")
                    if "shop_image" in item_data:
                        items.append(item_data['shop_image'])
                    else:
                        continue

        try:
            image = generate_image(stats.match_type, stats.match_time, stats.match_id, stats.match_duration, stats.match_kills, stats.match_deaths, stats.match_assists, stats.match_cs, stats.match_spm, stats.match_headshot, match_hero_name, items=items)
            await interaction.followup.send(file=discord.File(fp=image, filename="piltestimage.png"))
        except Exception as e:
            print("Image generation failed:", e)
            await interaction.response.send_message("Sorry, something went wrong.")
            return

        ''' --- '''

        # await interaction.response.defer()
        # # for player in tracked_players:
        # response = requests.get(
        #     f"https://api.deadlock-api.com/v1/players/76561198274274999/hero-stats",
        # )

        # data = response.json()

        # pages = []
        # files = []
        
        # for index, item in enumerate(data, start=1):
        #     embed = discord.Embed(
        #     title=f"Deadlock Stats",
        #     color=0x0080ff
        #     )
        #     kda = []

        #     for key, value in item.items():
        #         fields = ["hero_id","wins","matches_played","time_played","kills","deaths","assists","creeps_per_min","damage_per_min","damage_taken_per_min","networth_per_min","obj_damage_per_min","denies_per_match"]

        #         if key in fields:
        #             # resolve hero_id and add the fields
        #             if key == "hero_id":
        #                 field_name = resolve_hero(hero_id=value)
        #                 field_value = f"```{str(round(value))}```"
                        
        #                 script_dir = os.path.dirname(os.path.abspath(__file__))
        #                 file_path = os.path.join(script_dir, f"../../../deadlock/hero_icons/{resolve_hero(hero_id=value)}.png")
        #                 file_path = os.path.normpath(file_path)
        #                 file = discord.File(file_path, filename=str(resolve_hero(hero_id=value)))

        #                 print(f"field name: {field_name}\nfield value: {field_value}")

        #                 embed.add_field(
        #                     name=field_name,
        #                     value=field_value,
        #                     inline=True
        #                 )
                    
        #             # Append value to kda string to be joined
        #             elif key in ["kills", "deaths", "assists"]:
        #                 kda.append(str(value))
        #                 if len(kda) == 3:
        #                     embed.add_field(
        #                         name="K/D/A",
        #                         value=f"```{"/".join(kda)}```",
        #                         inline=True
        #                     )

        #             elif key:
        #                 field_name = str(key)
        #                 field_value = f"```{str(round(value))}```"
                        
        #                 print(f"field name: {field_name}\nfield value: {field_value}")

        #                 embed.add_field(
        #                     name=field_name,
        #                     value=field_value,
        #                     inline=True
        #                 )

        #     pages.append(embed)
        #     files.append(file_path)
                    
        # # patches = response.json()
        # # format_string = "%Y-%m-%dT%H:%M:%SZ"
        # # temp = "2025-08-30"
        # # patch_list = []
        # # for patch in patches:
        # #     norm_date = datetime.strptime(patch['pub_date'], format_string)
        # #     pub_date = norm_date.date()
        # #     today = (datetime.today() - timedelta(days=1)).date()
            
        # #     if pub_date == today:
        # #         patch_list.append(patch)
        # #     else:
        # #         test(patch)
        # #         break
        
        # # print("patch_list:", patch_list)
        # # link_str = str(patch_list[0]['link'])
        # view = PaginationView(pages, files, interaction.user.id)
        # file = discord.File(files[0], filename=os.path.basename(files[0]))
        # pages[0].set_image(url=f"attachment://{os.path.basename(files[0])}")
        # await interaction.followup.send(embed=pages[0], view=view, file=file)
    
async def setup(bot):
    await bot.add_cog(Deadlock(bot))