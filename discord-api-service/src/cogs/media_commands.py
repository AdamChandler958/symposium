import discord
from discord.ext import commands
import logging

logger = logging.getLogger('discord_api_service')
STREAMING_SERVICE = "http://processing-service:3020/retrieve-audio_stream"

class MediaCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @discord.app_commands.command(name="join", description="Makes the bot join the user's current voice channel.")
    async def join_command(self, interaction: discord.Interaction):
        member = interaction.user
        logger.info(f"Received join command from server: {interaction.guild_id}")

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

    @discord.app_commands.command(name="play", description="Plays a track from YouTube")
    @discord.app_commands.describe(input_url = "The YouTube url to send to the streaming service.")
    async def play_command(self, interaction: discord.Interaction, input_url: str):
        voice_client = interaction.guild.voice_client
        if not voice_client:
            return await interaction.response.send_message(
                "I must be in a voice channel to play audio, use `/join` first.",
                ephemeral=True
            )
        
        await interaction.response.defer()

        full_url = f"{STREAMING_SERVICE}?url={input_url}"
        logger.info(f"Attempting to stream audio from URL: {full_url}")

        try:
            source = discord.FFmpegPCMAudio(
                full_url,
                before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
            )
            source = discord.PCMVolumeTransformer(source, volume=0.5) 

            voice_client.play(source, after=lambda e: logger.error(f"Player error: {e}"))

            await interaction.followup.send(f"Now playing audio for: **{input_url}**")

        except Exception as e:
            logger.error(f"Error during /play command: {e}")
            await interaction.followup.send(
                f"An error occurred while trying to play the audio. Check logs for details. ({e})",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(MediaCommands(bot))