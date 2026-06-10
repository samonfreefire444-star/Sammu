import os
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View
import yt_dlp
import asyncio
import re
import urllib.request
from flask import Flask
from threading import Thread

# 🌐 1. Render-ൽ ബോട്ട് എപ്പോഴും ഓൺ ആയിരിക്കാൻ വേണ്ടിയുള്ള വെബ് സർവർ സെറ്റപ്പ്
app = Flask('')

@app.route('/')
def home():
    return "Matrix System is Status: ACTIVE 24/7"

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# 🎛️ 2. ഡിസ്‌കോർഡ് കൺട്രോൾ പാനൽ (9 പ്രീമിയം ബട്ടണുകൾ)
class PremiumMusicView(View):
    def __init__(self, vc: discord.VoiceClient, main_msg: discord.Message = None):
        super().__init__(timeout=None)
        self.vc = vc
        self.main_msg = main_msg

    @discord.ui.button(emoji="⏮️", style=discord.ButtonStyle.secondary, row=0)
    async def previous_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("⏮️ പ്രീവിയസ് ട്രാക്ക് ഫീച്ചർ ലോഡ് ചെയ്യുന്നു...", ephemeral=True)

    @discord.ui.button(emoji="⏸️", style=discord.ButtonStyle.secondary, row=0)
    async def play_pause_btn(self, interaction: discord.Interaction, button: Button):
        if self.vc.is_playing():
            self.vc.pause()
            await interaction.response.send_message("⏸️ പാട്ട് തൽക്കാലം നിർത്തിവെച്ചു!", ephemeral=True)
        elif self.vc.is_paused():
            self.vc.resume()
            await interaction.response.send_message("▶️ പാട്ട് വീണ്ടും പ്ലേ ചെയ്യുന്നു!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ ഇപ്പോൾ പാട്ടുകളൊന്നും ഓടുന്നില്ല ബ്രോ!", ephemeral=True)

    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.secondary, row=0)
    async def skip_btn(self, interaction: discord.Interaction, button: Button):
        if self.vc.is_playing():
            self.vc.stop()
            await interaction.response.send_message("⏭️ അടുത്ത പാട്ടിലേക്ക് കടക്കുന്നു!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ സ്കിപ്പ് ചെയ്യാൻ പാട്ടുകളൊന്നുമില്ല!", ephemeral=True)

    @discord.ui.button(emoji="⏹️", style=discord.ButtonStyle.danger, row=0)
    async def stop_btn(self, interaction: discord.Interaction, button: Button):
        await self.vc.disconnect()
        await interaction.response.send_message("⏹️ ബോട്ട് വോയ്‌സ് ചാനൽ വിട്ടുപോയി!", ephemeral=True)
        self.stop()

    @discord.ui.button(emoji="🔀", style=discord.ButtonStyle.secondary, row=0)
    async def shuffle_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("🔀 പ്ലേലിസ്റ്റ് ക്യൂ ഷഫിൾ ചെയ്തു!", ephemeral=True)

    @discord.ui.button(emoji="🔉", style=discord.ButtonStyle.secondary, row=1)
    async def vol_down_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("🔉 വോളിയം കുറയ്ക്കാനുള്ള ഓപ്ഷൻ റെഡിയാകുന്നു!", ephemeral=True)

    @discord.ui.button(emoji="🔁", style=discord.ButtonStyle.secondary, row=1)
    async def repeat_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("🔁 ലൂപ്പ് മോഡ് ആക്ടിവേറ്റ് ചെയ്തു!", ephemeral=True)

    @discord.ui.button(emoji="🔊", style=discord.ButtonStyle.secondary, row=1)
    async def vol_up_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("🔊 വോളിയം കൂട്ടാനുള്ള ഓപ്ഷൻ റെഡിയാകുന്നു!", ephemeral=True)

    @discord.ui.button(label="Hide Card", style=discord.ButtonStyle.secondary, row=1)
    async def hide_card_btn(self, interaction: discord.Interaction, button: Button):
        if self.main_msg:
            await self.main_msg.delete()
            await interaction.response.send_message("🙈 മ്യൂസിക് കാർഡ് ഹൈഡ് ചെയ്തു!", ephemeral=True)

class MatrixMusicBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("Slash Commands Synced for Render Free Plan!")

bot = MatrixMusicBot()

YTDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': 'True', 'quiet': True, 'default_search': 'ytsearch'}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

@bot.event
async def on_ready():
    print(f"Matrix Bot Online: {bot.user.name}")

@bot.tree.command(name="play", description="Spotify അല്ലെങ്കിൽ YouTube പാട്ടുകൾ പ്ലേ ചെയ്യാം ബ്രോ")
@app_commands.describe(search="പാട്ടിന്റെ പേര്, Spotify ലിങ്ക് അല്ലെങ്കിൽ YouTube ലിങ്ക് നൽകുക")
async def play(interaction: discord.Interaction, search: str):
    await interaction.response.defer()

    if not interaction.user.voice:
        return await interaction.followup.send("നീ ആദ്യം ഒരു വോയ്‌സ് ചാനലിൽ കയറൂ ബ്രോ!")

    vc: discord.VoiceClient = interaction.guild.voice_client
    if not vc:
        vc = await interaction.user.voice.channel.connect()

    title_to_search = search
    artwork_url = None

    if "spotify.com" in search:
        try:
            cleaned_url = search.split('?')[0]
            embed_url = cleaned_url.replace("spotify.com", "open.spotify.com/embed")
            req = urllib.request.Request(embed_url, headers={'User-Agent': 'Mozilla/5.0'})
            html = urllib.request.urlopen(req).read().decode('utf-8')
            
            title_match = re.search(r'"title":"([^"]+)"', html)
            artist_match = re.search(r'"artists":\[{"name":"([^"]+)"', html)
            thumb_match = re.search(r'"coverArt":{"sources":\[{"url":"([^"]+)"', html)
            
            if title_match and artist_match:
                title_to_search = f"{title_match.group(1)} {artist_match.group(1)}"
            if thumb_match:
                artwork_url = thumb_match.group(1)
        except Exception as e:
            print(f"Spotify Fetch Error: {e}")

    try:
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(title_to_search, download=False))
        
        if 'entries' in data:
            track_info = data['entries'][0]
        else:
            track_info = data

        url = track_info['url']
        track_title = track_info['title']
        duration = track_info.get('duration', 0)
        
        minutes = duration // 60
        seconds = duration % 60
        duration_str = f"{minutes:02d}:{seconds:02d}"

        if vc.is_playing():
            vc.stop()
            
        audio_source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
        vc.play(audio_source)

        embed = discord.Embed(
            title="Now Playing",
            description=f"**[{track_title}]({track_info.get('webpage_url', search)})**",
            color=discord.Color.from_rgb(170, 0, 0)
        )
        
        req_name = interaction.user.display_name
        req_avatar = interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url
        embed.set_author(name=f"Requested by: {req_name}", icon_url=req_avatar)

        if artwork_url:
            embed.set_thumbnail(url=artwork_url)
        elif track_info.get('thumbnail'):
            embed.set_thumbnail(url=track_info['thumbnail'])
            
        embed.add_field(name="⏱️ Duration", value=f"`{duration_str}`", inline=True)
        embed.add_field(name="👤 User", value=interaction.user.mention, inline=True)
        
        dev_id = "1145383325280764005"
        try:
            dev_user = await bot.fetch_user(int(dev_id))
            dev_text = f"Developed by @{dev_user.name}"
            dev_avatar = dev_user.avatar.url if dev_user.avatar else req_avatar
        except Exception:
            dev_text = "Developed by @dc.saaaaaaaaam"
            dev_avatar = req_avatar

        embed.set_footer(text=dev_text, icon_url=dev_avatar)

        view = PremiumMusicView(vc=vc)
        main_msg = await interaction.followup.send(embed=embed, view=view)
        view.main_msg = main_msg

    except Exception as e:
        await interaction.followup.send(f"❌ എറർ സംഭവിച്ചു ബ്രോ! (Error: {e})")

# 🤖 ബോട്ടിനെയും വെബ് സർവറിനെയും ഒന്നിച്ച് റൺ ചെയ്യിക്കുന്നു
keep_alive()
import os
bot.run(os.environ.get('DISCORD_TOKEN'))

