import discord
from discord.ext import commands
import logging

logger = logging.getLogger('discord_api_service')

class BasicCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @discord.app_commands.command(name="test", description="Test if bot is working")
    async def test_command(self, interaction: discord.Interaction):
        logger.info("Received test command")

        await interaction.response.send_message("Slash command is working")

async def setup(bot: commands.Bot):
    await bot.add_cog(BasicCommands(bot))