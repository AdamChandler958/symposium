import discord
from discord.ext import commands
import logging

logger = logging.getLogger(__name__)

class MediaCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @discord.app_commands.command(name="join", description="Makes the bot join the user's current voice channel.")
    async def join_command(self, interaction: discord.Interaction):
        member = interaction.user
        logger.info(f"Received join command from user: {member}")

        if member.voice and member.voice.channel:
            channel = member.voice.channel

            if interaction.guild.voice_client is not None:
                await interaction.guild.voice_client.move_to(channel)
                await interaction.response.send_message(f"Moved to **{channel.name}**")

            else:
                await channel.connect()
                await interaction.response.send_message(f"Joined **{channel.name}**")
        else:
            await interaction.response.send_message("You need to be in a voice channel for me to join", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(MediaCommands(bot))