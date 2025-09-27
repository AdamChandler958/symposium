import discord
from discord.ext import commands
import logging
from collections import deque
import asyncio
import requests
import urllib
import urllib.parse

logger = logging.getLogger('discord-api-service')
STREAMING_SERVICE = "http://processing-service:3020/retrieve-audio-stream"
FETCHING_SERVICE = "http://fetching-service:3000/stream-metadata"

class MediaCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.song_queue = deque()
        self.current_track_playing = None
        self.last_interaction_info = {}

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

    def play_next_in_queue(self, error, guild_id: int):
        async def _play_next():
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return

            voice_client = guild.voice_client
            if not voice_client:
                return
            
            channel = self.last_interaction_info.get(guild_id)
            
            if error:
                logger.error(f"Playback error in guild {guild_id}: {error}")
                if channel:
                    await channel.send(f"An error occurred during playback: {error}")
            
            if self.song_queue:
                next_url, next_track, next_duration = self.song_queue.popleft()
                logger.info(f"Playing next song from queue in guild {guild_id}: {next_track}")

                try:
                    encoded_url = urllib.parse.quote_plus(next_url)
                    full_url = f"{STREAMING_SERVICE}?url={encoded_url}"
                    source = discord.FFmpegPCMAudio(
                        full_url,
                        before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
                    )
                    source = discord.PCMVolumeTransformer(source, volume=0.5) 

                    # Correctly set the after callback to pass the error and guild_id
                    voice_client.play(source, after=lambda e: self.play_next_in_queue(e, guild_id))
                    self.current_track_playing = next_track

                    if channel:
                        await channel.send(f"Now playing next: **{next_track}**: `{next_duration}`")
                except Exception as e:
                    logger.error(f"Error playing next song from queue in guild {guild_id}: {e}")
                    await _play_next()
            else:
                self.current_track_playing = None 
                if channel:
                    await channel.send("Queue finished. Disconnecting in a moment if idle.")

        asyncio.run_coroutine_threadsafe(_play_next(), self.bot.loop)


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

        self.last_interaction_info[interaction.guild_id] = interaction.channel

        response = requests.get(FETCHING_SERVICE, params={"url_query": input_url})
        if response.status_code == 200:
            data = response.json()

        if voice_client.is_playing() or voice_client.is_paused():
            self.song_queue.append((data.get('url'), data.get('title'), data.get('duration')))
            logger.info(f"Added to queue: {data.get('title')}. Queue length: {len(self.song_queue)}")
            await interaction.followup.send(f"Queued **{data.get('title')}** at position **#{len(self.song_queue)}**.")
        else:
            try:
                import urllib.parse
                encoded_url =  urllib.parse.quote_plus(data.get('url'))
                full_url = f"{STREAMING_SERVICE}?url={encoded_url}"
                logger.info(f"Attempting to stream audio from URL: {full_url}")
                source = discord.FFmpegPCMAudio(
                    full_url,
                    before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
                )
                source = discord.PCMVolumeTransformer(source, volume=0.5) 

                voice_client.play(source, after=lambda e: self.play_next_in_queue(e, interaction.guild_id))

                logger.info(f"Starting playback: {data.get('title')}")
                self.current_track_playing = data.get('title')

                await interaction.followup.send(f"Now playing audio for: **{data.get('title')}**")

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

    @discord.app_commands.command(name="queue", description="Displays the next tracks in the queue.")
    async def queue_command(self, interaction: discord.Interaction):
        await interaction.response.defer() 

        voice_client = interaction.guild.voice_client
        
        is_playing = voice_client.is_playing() if voice_client else False
        is_paused = voice_client.is_paused() if voice_client else False
        
        
        if is_playing or is_paused:
            current_track_url = self.current_track_playing 
            
        if not self.song_queue:
            embed = discord.Embed(
                title="Playback Queue",
                description="The queue is empty! Use `/play` to add a song.",
                color=discord.Color.blue()
            )
            embed.add_field(name="Current Track", value=current_track_url, inline=False)
            return await interaction.followup.send(embed=embed)

        tracks = []
        for index, (_, track, duration) in enumerate(list(self.song_queue)[:20]): 
            
            tracks.append(f"**{index + 1}.** {track} : `{duration}`")

        embed = discord.Embed(
            title="Playback Queue",
            description=f"Showing **{len(tracks)}** tracks out of **{len(self.song_queue)}** total.",
            color=discord.Color.green()
        )

        embed.add_field(name="Now Playing", value=self.current_track_playing, inline=False)
        
        embed.add_field(name="Up Next", value="\n".join(tracks), inline=False)
        
        if len(self.song_queue) > 20:
            embed.set_footer(text=f"Showing the first 20 tracks. Total tracks: {len(self.song_queue)}")

        logger.info(f"Displayed queue for guild {interaction.guild.id} with {len(self.song_queue)} tracks.")
        await interaction.followup.send(embed=embed)
        
    @discord.app_commands.command(name="skip", description="Skips the current track and plays the next in the queue.")
    async def skip_command(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client

        if not voice_client:
            return await interaction.response.send_message("I'm not connected to a voice channel.", ephemeral=True)
        
        if voice_client.is_playing() or voice_client.is_paused():
            current_track = self.current_track_playing
            voice_client.stop()
            logger.info(f"Skipped track: {current_track}")
            await interaction.response.send_message(f"Skipped **{current_track}**.")
        else:
            await interaction.response.send_message("Not currently playing any track to skip.", ephemeral=True)
            
async def setup(bot: commands.Bot):
    await bot.add_cog(MediaCommands(bot))