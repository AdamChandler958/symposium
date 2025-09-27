import discord

from discord.ext import commands
from dotenv import load_dotenv
import os
from src.logging import setup_logger
import pathlib
import logging

load_dotenv("dev.env")

API_KEY = os.getenv("API_KEY")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

setup_logger()

logger = logging.getLogger('discord_api_service')

async def load_cogs():
    cogs_path = pathlib.Path("src/cogs/")
    for cog_file in cogs_path.glob("*.py"):
        if cog_file.name != "__init__.py":
            module_name = str(cog_file).replace(os.sep, ".")[:-3]
            try:
                await bot.load_extension(module_name)
                logger.info(f"Successfully loaded extension: {module_name}")
            except commands.ExtensionNotFound as e:
                logger.error(f"Failed to load extension {module_name} with error: {e}")

@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user}")
    await load_cogs()
    synced = await bot.tree.sync()
    logger.info(f"Synced {len(synced)} commands(s)!")
    

bot.run(API_KEY)
