import discord

from discord.ext import commands
from dotenv import load_dotenv
import os
import requests

load_dotenv("dev.env")

API_KEY = os.getenv("API_KEY")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    response = requests.get("http://fetching-service:3000")
    response.raise_for_status()
    data = response.json()
    print(data)



bot.run(API_KEY)
