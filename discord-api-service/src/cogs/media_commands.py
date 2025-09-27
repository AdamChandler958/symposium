import discord
from discord.ext import commands
import logging
from collections import deque
import asyncio

logger = logging.getLogger('discord-api-service')
STREAMING_SERVICE = "http://processing-service:3020/retrieve-audio_stream"

class MediaCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.song_queue = deque()

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

    def play_next_in_queue(self, interaction:discord.Interaction):
        voice_client = interaction.guild.voice_client
        if not voice_client:
            return
        
        if self.song_queue:
            next_url = self.song_queue.popleft()
            logger.info(f"Playing next song from queue: {next_url}")

            try:
                import urllib.parse
                encoded_url = urllib.parse.quote_plus(next_url)
                full_url = f"{STREAMING_SERVICE}?url={encoded_url}"
                source = discord.FFmpegPCMAudio(
                full_url,
                before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
                )
                source = discord.PCMVolumeTransformer(source, volume=0.5) 

                voice_client.play(source, after=lambda e: self.play_next_in_queue(interaction))

                asyncio.run_coroutine_threadsafe(
                    interaction.channel.send(f"Now playing next: **{next_url}**"), 
                    self.bot.loop
                )
            except Exception as e:
                logger.error(f"Error playing next song from queue: {e}")
                self.play_next_in_queue(interaction)


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

        if voice_client.is_playing() or voice_client.is_paused():
            self.song_queue.append(input_url)
            logger.info(f"Added to queue: {input_url}. Queue length: {len(self.song_queue)}")
            await interaction.followup.send(f"Queued **{input_url}** at position **#{len(self.song_queue)}**.")
        else:
            try:
                import urllib.parse
                encoded_url =  urllib.parse.quote_plus(input_url)
                full_url = f"{STREAMING_SERVICE}?url={encoded_url}"
                logger.info(f"Attempting to stream audio from URL: {full_url}")
                source = discord.FFmpegPCMAudio(
                    full_url,
                    before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
                )
                source = discord.PCMVolumeTransformer(source, volume=0.5) 

                voice_client.play(source, after=lambda e: self.play_next_in_queue(interaction))

                logger.info(f"Starting playback: {input_url}")

                await interaction.followup.send(f"Now playing audio for: **{input_url}**")

            except Exception as e:
                logger.error(f"Error during /play command: {e}")
                await interaction.followup.send(
                    f"An error occurred while trying to play the audio. Check logs for details. ({e})",
                    ephemeral=True
                )

    @discord.app_commands.command(name="pause", description="Pauses the current track.")
    async def pause_command(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if not voice_client:
            return await interaction.response.send_message(
                "Not currently connected to a voice channel",
                ephemeral=True
            )
        
        if voice_client.is_playing():
            voice_client.pause()
            logger.info(f"Audio paused in guild: {interaction.guild_id}")
            await interaction.response.send_message("Audio paused.")

        elif voice_client.is_paused():
            await interaction.response.send_message("The audio player is already paused.", ephemeral=True)

        else:
            await interaction.response.send_message("Not currently playing any media.", ephemeral=True)

    @discord.app_commands.command(name="resume", description="Resumes the currently paused audio.")
    async def resume_command(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client

        if not voice_client:
            return await interaction.response.send_message("I'm not connected to a voice channel.", ephemeral=True)

        if voice_client.is_paused():
            voice_client.resume()
            logger.info(f"Audio resumed in guild: {interaction.guild.id}")
            await interaction.response.send_message("Audio resumed.")
            
        elif voice_client.is_playing():
            await interaction.response.send_message("The audio is already playing.", ephemeral=True)
            

        else:
            await interaction.response.send_message("No audio is currently paused to resume.", ephemeral=True)
        

async def setup(bot: commands.Bot):
    await bot.add_cog(MediaCommands(bot))