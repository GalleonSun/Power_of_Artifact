import discord
from discord import Option
import asyncio
from enkanetwork import EquipmentsType, DigitType
from enkanetwork import EnkaNetworkAPI
from tabulate import tabulate
from PIL import Image, ImageDraw, ImageFont
import io
import json

with open("bot_token.txt") as f:
    TOKEN = f.read()

with open("server_id.txt") as f:
    DISCORD_SERVER_IDS = int(f.read())

client = discord.Bot()
client_enka = EnkaNetworkAPI(lang="jp")

HP_character = ["夜蘭", "胡桃", "ディシア"]

with open('output.json', 'r', encoding='utf-8') as file:
    User_list = json.load(file)
    print(User_list)


@client.event
async def on_ready():
    print(f"{client.user} コマンド待機中...")


@client.slash_command(description="原神スコア計算", guild_ids=[DISCORD_SERVER_IDS])
async def calc(ctx: discord.ApplicationContext):
    senderid = str(ctx.author.id)
    print(user_id)
    if senderid in User_list:
        user_id = User_list[senderid]
    else :
        await ctx.respond(f"原神IDが登録されていません")
    async with client_enka:
        data = await client_enka.fetch_user(user_id)
        character_palams = ""
        for character in data.characters:
            character_palams = calc_each_character(character, character_palams)
    if len(character_palams) >= 2000:
        await ctx.respond(f"文字数が{len(character_palams)}で2000文字を超えているのでダメです")    
    else :
        await ctx.respond(f"{character_palams}")

@client.slash_command(description="原神スコア計算", guild_ids=[DISCORD_SERVER_IDS])
async def choice_calc(ctx: discord.ApplicationContext, user_id: Option(int, required=True, description="UIDを入力してください")):
    async with client_enka:
        data = await client_enka.fetch_user(user_id)
        character_palams = ""
        for character in data.characters:
            character_palams = calc_each_character(character, character_palams)
    if len(character_palams) >= 2000:
        await ctx.respond(f"文字数が{len(character_palams)}で2000文字を超えているのでダメです")    
    else :
        await ctx.respond(f"{character_palams}")

@client.slash_command(description="画像で原神スコア計算", guild_ids=[DISCORD_SERVER_IDS])
async def image_calc(ctx: discord.ApplicationContext):
    senderid = str(ctx.author.id)
    if senderid in User_list:
            user_id = User_list[senderid]
    else :
        await ctx.respond(f"原神IDが登録されていません")
    async with client_enka:
        data = await client_enka.fetch_user(user_id)
        character_palams = ""
        for character in data.characters:
            character_palams = calc_each_character(character, character_palams)
    image_text = character_palams
    img_byte_arr = create_image_with_text(image_text)
    image_file = discord.File(img_byte_arr, filename="result.png")
    await ctx.respond("Here is the result:", file=image_file)




def calc_each_character(character, character_palams):
    character_palams += f"=== Artifacts of {character.name} ===\n"
    if character.name in HP_character:
        character_palams = calc_HP_character(character, character_palams)
        for stat in character.stats:
            if stat[0] == "FIGHT_PROP_MAX_HP":
                print(stat[0],stat[1].value)
                character_palams += f"HP : {round(stat[1].value,0)}\n\n"
            elif stat[0] == "FIGHT_PROP_CRITICAL":
                character_palams += f"会心率 : {round(stat[1].value * 100,1)}\n"
            elif stat[0] == "FIGHT_PROP_CRITICAL_HURT":
                character_palams += f"会心ダメージ : {round(stat[1].value * 100,1)}\n"
    else:
        character_palams = calc_default_character(character, character_palams)
        for stat in character.stats:
            if stat[0] == "FIGHT_PROP_CUR_ATTACK":
                print(stat[0],stat[1].value)
                character_palams += f"攻撃力 : {round(stat[1].value,0)}\n\n"
            elif stat[0] == "FIGHT_PROP_CRITICAL":
                character_palams += f"会心率 : {round(stat[1].value * 100,1)}\n"
            elif stat[0] == "FIGHT_PROP_CRITICAL_HURT":
                character_palams += f"会心ダメージ : {round(stat[1].value * 100,1)}\n"
    return character_palams


def calc_character(character, character_palams, calc_score):
    total_score = 0
    artifacts_table = []
    for artifact in filter(lambda x: x.type == EquipmentsType.ARTIFACT, character.equipments):
        score = 0
        substats = []

        for substate in artifact.detail.substats:
            score = calc_score(score, substate)
            substats.append(f"{substate.name}: {substate.value}{('%' if substate.type == DigitType.PERCENT else '')}")

        artifact_row = [score,', '.join(substats)]
        artifacts_table.append(artifact_row)
        total_score += score

    character_palams += tabulate(artifacts_table, headers=["Score","Sub Stats"]) + "\n"
    total_score = round(total_score,1)
    character_palams += f"Total Score: {total_score}\n"

    return character_palams


def calc_default_character(character, character_palams):
    def calc_score(score, substate):
        if substate.name == "攻撃力" and substate.type == DigitType.PERCENT:
            score += substate.value
        elif substate.name == "会心率":
            score += substate.value * 2
        elif substate.name == "会心ダメージ":
            score += substate.value
        return round(score, 1)

    return calc_character(character, character_palams, calc_score)


def calc_HP_character(character, character_palams):
    def calc_score(score, substate):
        if substate.name == "HP" and substate.type == DigitType.PERCENT:
            score += substate.value
        elif substate.name == "会心率":
            score += substate.value * 2
        elif substate.name == "会心ダメージ":
            score += substate.value
        return round(score, 1)

    return calc_character(character, character_palams, calc_score)

def create_image_with_text(img_text):
    # 画像のサイズやフォントサイズは必要に応じて調整してください
    new_line_count = img_text.count('\n')
    img = Image.new("RGB", (700, new_line_count * 20), color="white")
    
    print(f"escape is  {new_line_count }")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("msmincho.ttc", 16)
    draw.text((10, 10), img_text, font=font, fill="black")

    # 画像をバイナリ形式で一時ファイルに保存
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    return img_byte_arr


client.run(TOKEN)
