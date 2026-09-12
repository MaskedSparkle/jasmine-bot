import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
import json
import traceback
import feedparser
from flask import Flask
import threading

app_web = Flask(__name__)
@app_web.route('/')
def home():
    return "Jasmine is alive! 🌸 WORKING Multi-Server + Slash"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host='0.0.0.0', port=port)

threading.Thread(target=run_web, daemon=True).start()

DATA_FILE = "jasmine_data.json"
CONFIG_FILE = "jasmine_config.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {}

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Save error: {e}")

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {}

def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Config save error: {e}")

def format_message(template: str, member: discord.Member = None, author: discord.Member = None, guild: discord.Guild = None):
    """{member.mention}, {member.name}, {author.mention}, {guild.name}, {member_count} cseréje"""
    if not template:
        return ""
    result = template
    try:
        if member:
            result = result.replace("{member.mention}", member.mention)
            result = result.replace("{member.name}", member.name)
            result = result.replace("{member.id}", str(member.id))
            if member.display_avatar:
                result = result.replace("{member.avatar}", member.display_avatar.url)
        if author:
            result = result.replace("{author.mention}", author.mention)
            result = result.replace("{author.name}", author.name)
        if guild:
            result = result.replace("{guild.name}", guild.name)
            result = result.replace("{member_count}", str(guild.member_count))
            result = result.replace("{guild.id}", str(guild.id))
    except: pass
    return result

class Jasmine(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        intents.bans = True
        intents.guilds = True
        super().__init__(command_prefix='!', intents=intents)
        self.platform_data = load_data()
        self.guild_config = load_config()

    def get_guild_platform_data(self, guild_id):
        gid = str(guild_id)
        if gid not in self.platform_data:
            self.platform_data[gid] = {"last_youtube_link": None, "last_tiktok_link": None, "greeted_users": []}
        if "greeted_users" not in self.platform_data[gid]:
            self.platform_data[gid]["greeted_users"] = []
        return self.platform_data[gid]

    def get_guild_config(self, guild_id):
        gid = str(guild_id)
        if gid not in self.guild_config:
            self.guild_config[gid] = {
                "youtube_channel": None,
                "tiktok_channel": None,
                "welcome_channel": None,
                "leave_channel": None,
                "stream_channel": None,
                "greeting_channel": None,
                "youtube_channel_id": "UCcKLZHpGu8yp8nQi17lwmmg",
                "tiktok_rss": "https://www.tiktok.com/@masked_sparkle/rss",
                "welcome_enabled": True,
                "leave_enabled": True,
                "greeting_enabled": True,
                "greeting_mode": "once",  # once vagy always
                "greeting_trigger": "sziasztok",
                "welcome_message": "Szia {member.mention}! De örülök, hogy megérkeztél a **{guild.name}**-re! ✨\nTe vagy a(z) {member_count}. tag! 🐾",
                "leave_message": "Jaj, **{member.name}** elhagyott minket a **{guild.name}**-ről... 🥀\nMár csak {member_count}-en maradtunk. 💔",
                "greeting_message": "Szia {author.mention}! 🌸"
            }
        # defaultok pótlása ha hiányzik
        defaults = {
            "welcome_enabled": True, "leave_enabled": True, "greeting_enabled": True,
            "greeting_mode": "once", "greeting_trigger": "sziasztok",
            "welcome_message": "Szia {member.mention}! De örülök, hogy megérkeztél a **{guild.name}**-re! ✨",
            "leave_message": "**{member.name}** kilépett... 🥀",
            "greeting_message": "Szia {author.mention}! 🌸"
        }
        for k, v in defaults.items():
            if k not in self.guild_config[gid]:
                self.guild_config[gid][k] = v
        return self.guild_config[gid]

    def find_channel_by_name(self, guild, keywords):
        for ch in guild.text_channels:
            name = ch.name.lower()
            for kw in keywords:
                if kw in name:
                    return ch.id
        return None

    async def setup_hook(self):
        print("🔧 Jasmine setup_hook...")

        # SLASH COMMANDS - 100% működő módszer
        @self.tree.command(name="setwelcome", description="Beállítja az üdvözlő csatornát")
        @app_commands.describe(channel="Melyik csatornába üdvözöljön")
        async def setwelcome(interaction: discord.Interaction, channel: discord.TextChannel):
            try:
                await interaction.response.defer(ephemeral=True)
                if not interaction.user.guild_permissions.administrator:
                    await interaction.followup.send("❌ Nincs jogod!", ephemeral=True); return
                cfg = self.get_guild_config(interaction.guild.id)
                cfg["welcome_channel"] = channel.id
                save_config(self.guild_config)
                await interaction.followup.send(f"✅ Welcome csatorna: {channel.mention}", ephemeral=True)
            except Exception as e:
                print(traceback.format_exc())
                try: await interaction.followup.send(f"❌ {e}", ephemeral=True)
                except: pass

        @self.tree.command(name="setleave", description="Beállítja a kilépő csatornát")
        @app_commands.describe(channel="Melyik csatornába írja ha kilép valaki")
        async def setleave(interaction: discord.Interaction, channel: discord.TextChannel):
            try:
                await interaction.response.defer(ephemeral=True)
                if not interaction.user.guild_permissions.administrator:
                    await interaction.followup.send("❌ Nincs jogod!", ephemeral=True); return
                cfg = self.get_guild_config(interaction.guild.id)
                cfg["leave_channel"] = channel.id
                save_config(self.guild_config)
                await interaction.followup.send(f"✅ Leave csatorna: {channel.mention}", ephemeral=True)
            except Exception as e:
                print(traceback.format_exc())

        @self.tree.command(name="setyoutube", description="Beállítja a YouTube értesítő csatornát")
        @app_commands.describe(channel="Melyik csatornába küldje", channel_id="YouTube channel ID (opcionális)")
        async def setyoutube(interaction: discord.Interaction, channel: discord.TextChannel, channel_id: str = None):
            try:
                await interaction.response.defer(ephemeral=True)
                if not interaction.user.guild_permissions.administrator:
                    await interaction.followup.send("❌ Nincs jogod!", ephemeral=True); return
                cfg = self.get_guild_config(interaction.guild.id)
                cfg["youtube_channel"] = channel.id
                if channel_id:
                    cfg["youtube_channel_id"] = channel_id
                save_config(self.guild_config)
                await interaction.followup.send(f"✅ YouTube: {channel.mention} | ID: {cfg['youtube_channel_id']}", ephemeral=True)
            except Exception as e:
                print(traceback.format_exc())

        @self.tree.command(name="settiktok", description="Beállítja a TikTok értesítő csatornát")
        @app_commands.describe(channel="Melyik csatornába küldje")
        async def settiktok(interaction: discord.Interaction, channel: discord.TextChannel):
            try:
                await interaction.response.defer(ephemeral=True)
                if not interaction.user.guild_permissions.administrator:
                    await interaction.followup.send("❌ Nincs jogod!", ephemeral=True); return
                cfg = self.get_guild_config(interaction.guild.id)
                cfg["tiktok_channel"] = channel.id
                save_config(self.guild_config)
                await interaction.followup.send(f"✅ TikTok: {channel.mention}", ephemeral=True)
            except Exception as e:
                print(traceback.format_exc())

        @self.tree.command(name="setstream", description="Beállítja a Stream/Twitch csatornát")
        @app_commands.describe(channel="Melyik csatornába küldje a live értesítőt")
        async def setstream(interaction: discord.Interaction, channel: discord.TextChannel):
            try:
                await interaction.response.defer(ephemeral=True)
                if not interaction.user.guild_permissions.administrator:
                    await interaction.followup.send("❌ Nincs jogod!", ephemeral=True); return
                cfg = self.get_guild_config(interaction.guild.id)
                cfg["stream_channel"] = channel.id
                save_config(self.guild_config)
                await interaction.followup.send(f"✅ Stream csatorna: {channel.mention}", ephemeral=True)
            except Exception as e:
                print(traceback.format_exc())

        @self.tree.command(name="setwelcomemsg", description="Beállítja az üdvözlő szöveget belépésnél")
        @app_commands.describe(message="Üzenet, használhatsz: {member.mention} {member.name} {guild.name} {member_count}")
        async def setwelcomemsg(interaction: discord.Interaction, message: str):
            try:
                await interaction.response.defer(ephemeral=True)
                if not interaction.user.guild_permissions.administrator:
                    await interaction.followup.send("❌ Nincs jogod!", ephemeral=True); return
                cfg = self.get_guild_config(interaction.guild.id)
                cfg["welcome_message"] = message
                save_config(self.guild_config)
                await interaction.followup.send(f"✅ Welcome üzenet beállítva:\n```{message}```", ephemeral=True)
            except Exception as e:
                print(traceback.format_exc())

        @self.tree.command(name="setleavemsg", description="Beállítja a kilépő szöveget")
        @app_commands.describe(message="Üzenet: {member.name} {guild.name} {member_count}")
        async def setleavemsg(interaction: discord.Interaction, message: str):
            try:
                await interaction.response.defer(ephemeral=True)
                if not interaction.user.guild_permissions.administrator:
                    await interaction.followup.send("❌ Nincs jogod!", ephemeral=True); return
                cfg = self.get_guild_config(interaction.guild.id)
                cfg["leave_message"] = message
                save_config(self.guild_config)
                await interaction.followup.send(f"✅ Leave üzenet:\n```{message}```", ephemeral=True)
            except Exception as e:
                print(traceback.format_exc())

        @self.tree.command(name="setgreeting", description="Köszönés beállítása (sziasztok-ra reagálás)")
        @app_commands.describe(trigger="Milyen szóra reagáljon pl: szia, sziasztok, hello", message="Mit válaszoljon: {author.mention} használható", mode="Egyszer vagy mindig köszöntse ugyanazt az embert")
        @app_commands.choices(mode=[app_commands.Choice(name="Egyszer (ajánlott)", value="once"), app_commands.Choice(name="Mindig", value="always")])
        async def setgreeting(interaction: discord.Interaction, trigger: str, message: str, mode: str = "once"):
            try:
                await interaction.response.defer(ephemeral=True)
                if not interaction.user.guild_permissions.administrator:
                    await interaction.followup.send("❌ Nincs jogod!", ephemeral=True); return
                cfg = self.get_guild_config(interaction.guild.id)
                cfg["greeting_trigger"] = trigger.lower()
                cfg["greeting_message"] = message
                cfg["greeting_mode"] = mode
                save_config(self.guild_config)
                await interaction.followup.send(f"✅ Köszönés: ha valaki írja hogy `{trigger}` -> `{message}` | Mód: {mode}", ephemeral=True)
            except Exception as e:
                print(traceback.format_exc())

        @self.tree.command(name="setgreetingmsg", description="Gyors köszönő szöveg beállítás")
        @app_commands.describe(message="Mit írjon ha köszönnek: {author.mention}")
        async def setgreetingmsg(interaction: discord.Interaction, message: str):
            try:
                await interaction.response.defer(ephemeral=True)
                if not interaction.user.guild_permissions.administrator:
                    await interaction.followup.send("❌ Nincs jogod!", ephemeral=True); return
                cfg = self.get_guild_config(interaction.guild.id)
                cfg["greeting_message"] = message
                save_config(self.guild_config)
                await interaction.followup.send(f"✅ Greeting msg: ```{message}```", ephemeral=True)
            except Exception as e:
                print(traceback.format_exc())

        @self.tree.command(name="togglewelcome", description="Üdvözlés ki/be kapcsolása")
        @app_commands.describe(state="Bekapcsolva legyen?")
        @app_commands.choices(state=[app_commands.Choice(name="Be", value="on"), app_commands.Choice(name="Ki", value="off")])
        async def togglewelcome(interaction: discord.Interaction, state: str):
            try:
                await interaction.response.defer(ephemeral=True)
                if not interaction.user.guild_permissions.administrator:
                    await interaction.followup.send("❌ Nincs jogod!", ephemeral=True); return
                cfg = self.get_guild_config(interaction.guild.id)
                cfg["welcome_enabled"] = state == "on"
                save_config(self.guild_config)
                await interaction.followup.send(f"✅ Welcome: {'BE' if cfg['welcome_enabled'] else 'KI'}", ephemeral=True)
            except: pass

        @self.tree.command(name="toggleleave", description="Kilépő üzenet ki/be")
        @app_commands.choices(state=[app_commands.Choice(name="Be", value="on"), app_commands.Choice(name="Ki", value="off")])
        async def toggleleave(interaction: discord.Interaction, state: str):
            try:
                await interaction.response.defer(ephemeral=True)
                if not interaction.user.guild_permissions.administrator:
                    await interaction.followup.send("❌ Nincs jogod!", ephemeral=True); return
                cfg = self.get_guild_config(interaction.guild.id)
                cfg["leave_enabled"] = state == "on"
                save_config(self.guild_config)
                await interaction.followup.send(f"✅ Leave: {'BE' if cfg['leave_enabled'] else 'KI'}", ephemeral=True)
            except: pass

        @self.tree.command(name="togglegreeting", description="Köszönés (sziasztok) ki/be")
        @app_commands.choices(state=[app_commands.Choice(name="Be", value="on"), app_commands.Choice(name="Ki", value="off")])
        async def togglegreeting(interaction: discord.Interaction, state: str):
            try:
                await interaction.response.defer(ephemeral=True)
                if not interaction.user.guild_permissions.administrator:
                    await interaction.followup.send("❌ Nincs jogod!", ephemeral=True); return
                cfg = self.get_guild_config(interaction.guild.id)
                cfg["greeting_enabled"] = state == "on"
                save_config(self.guild_config)
                await interaction.followup.send(f"✅ Greeting: {'BE' if cfg['greeting_enabled'] else 'KI'}", ephemeral=True)
            except: pass

        @self.tree.command(name="jasmineconfig", description="Jasmine beállítások mutatása")
        async def jasmineconfig(interaction: discord.Interaction):
            try:
                await interaction.response.defer(ephemeral=True)
                cfg = self.get_guild_config(interaction.guild.id)
                embed = discord.Embed(title=f"🌸 Jasmine Config - {interaction.guild.name}", color=discord.Color.pink())
                def ch_mention(cid):
                    if not cid: return "Nincs beállítva"
                    ch = interaction.guild.get_channel(cid)
                    return ch.mention if ch else f"ID:{cid}"
                embed.add_field(name="Welcome", value=f"{ch_mention(cfg.get('welcome_channel'))} - {'BE' if cfg.get('welcome_enabled') else 'KI'}", inline=False)
                embed.add_field(name="Leave", value=f"{ch_mention(cfg.get('leave_channel'))} - {'BE' if cfg.get('leave_enabled') else 'KI'}", inline=False)
                embed.add_field(name="Greeting", value=f"Trigger: `{cfg.get('greeting_trigger')}` | Mód: {cfg.get('greeting_mode')} | {'BE' if cfg.get('greeting_enabled') else 'KI'}", inline=False)
                embed.add_field(name="Welcome msg", value=f"```{cfg.get('welcome_message')[:900]}```", inline=False)
                embed.add_field(name="Leave msg", value=f"```{cfg.get('leave_message')[:900]}```", inline=False)
                embed.add_field(name="Greeting msg", value=f"```{cfg.get('greeting_message')[:900]}```", inline=False)
                embed.add_field(name="YouTube", value=f"{ch_mention(cfg.get('youtube_channel'))} | ID: {cfg.get('youtube_channel_id')}", inline=True)
                embed.add_field(name="TikTok", value=ch_mention(cfg.get('tiktok_channel')), inline=True)
                embed.add_field(name="Stream", value=ch_mention(cfg.get('stream_channel')), inline=True)
                await interaction.followup.send(embed=embed, ephemeral=True)
            except Exception as e:
                print(traceback.format_exc())
                await interaction.followup.send(f"❌ {e}", ephemeral=True)

        @self.tree.command(name="stream", description="Twitch/Stream élő értesítő küldése")
        @app_commands.describe(link="Twitch/YouTube live link")
        async def stream_cmd(interaction: discord.Interaction, link: str = "https://www.twitch.tv/maskedsparkle"):
            try:
                await interaction.response.defer()
                if not interaction.user.guild_permissions.administrator:
                    await interaction.followup.send("❌ Nincs jogod!", ephemeral=True); return
                cfg = self.get_guild_config(interaction.guild.id)
                channel_id = cfg.get("stream_channel")
                channel = interaction.guild.get_channel(channel_id) if channel_id else interaction.channel
                embed = discord.Embed(title="🟣 Új Twitch Élőadás!", description=f"Élőbe mentem! Gyertek! 💖\n\n👉 {link}", color=discord.Color.purple())
                embed.set_footer(text="Jasmine értesítő ✨")
                await channel.send(content="@everyone Élő adás! 🔔", embed=embed)
                await interaction.followup.send(f"✅ Elküldve ide: {channel.mention}", ephemeral=True)
            except Exception as e:
                print(traceback.format_exc())

        @self.tree.command(name="video", description="YouTube videó értesítő")
        @app_commands.describe(link="YouTube link")
        async def video_cmd(interaction: discord.Interaction, link: str = "https://www.youtube.com/@Sparkle_fix"):
            try:
                await interaction.response.defer()
                if not interaction.user.guild_permissions.administrator:
                    await interaction.followup.send("❌ Nincs jogod!", ephemeral=True); return
                cfg = self.get_guild_config(interaction.guild.id)
                channel_id = cfg.get("youtube_channel")
                channel = interaction.guild.get_channel(channel_id) if channel_id else interaction.channel
                embed = discord.Embed(title="🔴 Új YouTube Videó!", description=f"Új videó! ✨\n\n👉 {link}", color=discord.Color.red())
                if "watch?v=" in link:
                    vid = link.split("watch?v=")[1].split("&")[0]
                    embed.set_image(url=f"https://img.youtube.com/vi/{vid}/hqdefault.jpg")
                await channel.send(content="@everyone Új YouTube videó! 🎬", embed=embed)
                await interaction.followup.send(f"✅ Elküldve: {channel.mention}", ephemeral=True)
            except Exception as e:
                print(traceback.format_exc())

        @self.tree.command(name="tiktok", description="TikTok értesítő")
        @app_commands.describe(link="TikTok link")
        async def tiktok_cmd(interaction: discord.Interaction, link: str = "https://www.tiktok.com/@masked_sparkle"):
            try:
                await interaction.response.defer()
                if not interaction.user.guild_permissions.administrator:
                    await interaction.followup.send("❌ Nincs jogod!", ephemeral=True); return
                cfg = self.get_guild_config(interaction.guild.id)
                channel_id = cfg.get("tiktok_channel")
                channel = interaction.guild.get_channel(channel_id) if channel_id else interaction.channel
                embed = discord.Embed(title="📱 Új TikTok!", description=f"Új TikTok! 💖\n\n👉 {link}", color=discord.Color.dark_embed())
                await channel.send(content="@everyone Új TikTok! 🎶", embed=embed)
                await interaction.followup.send(f"✅ Elküldve: {channel.mention}", ephemeral=True)
            except Exception as e:
                print(traceback.format_exc())

        @self.tree.command(name="ping", description="Teszt")
        async def ping(interaction: discord.Interaction):
            await interaction.response.send_message("🌸 Jasmine Pong! Slash működik!", ephemeral=True)

        # Sync
        try:
            synced = await self.tree.sync()
            print(f"✅ Jasmine Global sync: {len(synced)} -> {', '.join([c.name for c in synced])}")
        except Exception as e:
            print(f"❌ Sync hiba: {e}\n{traceback.format_exc()}")

        self.check_platforms.start()

    async def on_ready(self):
        print(f"✨ Jasmine {self.user} | {len(self.guilds)} szerveren")
        for guild in self.guilds:
            cfg = self.get_guild_config(guild.id)
            changed = False
            if not cfg["youtube_channel"]:
                found = self.find_channel_by_name(guild, ["youtube", "video", "yt"])
                if found: cfg["youtube_channel"] = found; changed = True
            if not cfg["tiktok_channel"]:
                found = self.find_channel_by_name(guild, ["tiktok", "tt"])
                if found: cfg["tiktok_channel"] = found; changed = True
            if not cfg["welcome_channel"]:
                found = self.find_channel_by_name(guild, ["welcome", "üdv", "érkezett"])
                if found: cfg["welcome_channel"] = found; changed = True
            if not cfg["leave_channel"]:
                found = self.find_channel_by_name(guild, ["leave", "kilép"])
                if found: cfg["leave_channel"] = found; changed = True
            if not cfg["stream_channel"]:
                found = self.find_channel_by_name(guild, ["stream", "live", "twitch"])
                if found: cfg["stream_channel"] = found; changed = True
            if changed:
                save_config(self.guild_config)
            # Guild sync
            try:
                await self.tree.sync(guild=guild)
                print(f"✅ Guild sync {guild.name}")
            except: pass

    async def on_message(self, message):
        if message.author.bot:  # botokat nem sziazza le
            return
        if not message.guild:
            return

        cfg = self.get_guild_config(message.guild.id)
        pdata = self.get_guild_platform_data(message.guild.id)

        # Köszönés
        if cfg.get("greeting_enabled"):
            trigger = cfg.get("greeting_trigger", "sziasztok").lower()
            content_lower = message.content.lower()
            if trigger in content_lower:
                greeted = pdata["greeted_users"]
                user_id = message.author.id
                mode = cfg.get("greeting_mode", "once")
                should_greet = False
                if mode == "always":
                    should_greet = True
                else:  # once
                    if user_id not in greeted:
                        should_greet = True
                        greeted.append(user_id)
                        if len(greeted) > 1000:
                            greeted = greeted[-500:]
                        pdata["greeted_users"] = greeted
                        save_data(self.platform_data)

                if should_greet:
                    tmpl = cfg.get("greeting_message", "Szia {author.mention}! 🌸")
                    text = format_message(tmpl, author=message.author, guild=message.guild)
                    try:
                        await message.channel.send(text)
                    except: pass

        # tulaj kérdés
        content_lower = message.content.lower()
        owner_keywords = ["ki itt a tulaj", "ki a tulaj", "ki a tulajdonos", "ki csinálta a szervert"]
        if any(k in content_lower for k in owner_keywords):
            await message.channel.send(f"<@{1047920915641548921}> a tulaj ✨")

        await self.process_commands(message)

    @tasks.loop(minutes=5)
    async def check_platforms(self):
        for guild in self.guilds:
            await self.check_youtube_for_guild(guild)
            await self.check_tiktok_for_guild(guild)

    @check_platforms.before_loop
    async def before_check_platforms(self):
        await self.wait_until_ready()

    async def check_youtube_for_guild(self, guild):
        cfg = self.get_guild_config(guild.id)
        pdata = self.get_guild_platform_data(guild.id)
        channel_id = cfg.get("youtube_channel_id", "UCcKLZHpGu8yp8nQi17lwmmg")
        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        try:
            feed = feedparser.parse(rss_url)
            if feed.entries:
                latest = feed.entries[0]
                if pdata["last_youtube_link"] is None:
                    pdata["last_youtube_link"] = latest.link
                    save_data(self.platform_data)
                elif latest.link != pdata["last_youtube_link"]:
                    pdata["last_youtube_link"] = latest.link
                    save_data(self.platform_data)
                    video_id = ""
                    if "watch?v=" in latest.link:
                        video_id = latest.link.split("watch?v=")[1].split("&")[0]
                    elif "/shorts/" in latest.link:
                        video_id = latest.link.split("/shorts/")[1].split("?")[0]
                    target_channel_id = cfg.get("youtube_channel")
                    channel = guild.get_channel(target_channel_id) if target_channel_id else None
                    if not channel:
                        for ch in guild.text_channels:
                            if ch.permissions_for(guild.me).send_messages:
                                channel = ch; break
                    if channel:
                        embed = discord.Embed(title="🔴 Új YouTube Videó!", description=f"**{latest.title}**\n\n{latest.link}", color=discord.Color.red())
                        if video_id:
                            embed.set_image(url=f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg")
                        embed.set_footer(text=f"Jasmine | {guild.name}")
                        await channel.send(content="@everyone Új YouTube videó! 🎬", embed=embed)
        except Exception as e:
            print(f"[{guild.name}] YT hiba: {e}")

    async def check_tiktok_for_guild(self, guild):
        cfg = self.get_guild_config(guild.id)
        pdata = self.get_guild_platform_data(guild.id)
        tiktok_rss = cfg.get("tiktok_rss", "https://www.tiktok.com/@masked_sparkle/rss")
        try:
            feed = feedparser.parse(tiktok_rss)
            if feed.entries:
                latest = feed.entries[0]
                if pdata["last_tiktok_link"] is None:
                    pdata["last_tiktok_link"] = latest.link
                    save_data(self.platform_data)
                elif latest.link != pdata["last_tiktok_link"]:
                    pdata["last_tiktok_link"] = latest.link
                    save_data(self.platform_data)
                    target_channel_id = cfg.get("tiktok_channel")
                    channel = guild.get_channel(target_channel_id) if target_channel_id else None
                    if channel:
                        embed = discord.Embed(title="📱 Új TikTok!", description=f"**{latest.title}**\n\n{latest.link}", color=discord.Color.dark_embed())
                        await channel.send(content="@everyone Új TikTok! 🎶", embed=embed)
        except: pass

    async def on_member_join(self, member):
        cfg = self.get_guild_config(member.guild.id)
        if not cfg.get("welcome_enabled"):
            return
        channel_id = cfg.get("welcome_channel")
        channel = member.guild.get_channel(channel_id) if channel_id else None
        if not channel:
            for ch in member.guild.text_channels:
                if ch.permissions_for(member.guild.me).send_messages:
                    channel = ch; break
        if channel:
            tmpl = cfg.get("welcome_message")
            text = format_message(tmpl, member=member, guild=member.guild)
            embed = discord.Embed(title="🌸 Új csillag érkezett!", description=text, color=discord.Color.pink())
            if member.display_avatar:
                embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"Jasmine | {member.guild.name}")
            try:
                await channel.send(embed=embed)
            except: pass

    async def on_member_remove(self, member):
        cfg = self.get_guild_config(member.guild.id)
        if not cfg.get("leave_enabled"):
            return
        channel_id = cfg.get("leave_channel") or cfg.get("welcome_channel")
        channel = member.guild.get_channel(channel_id) if channel_id else None
        if channel:
            tmpl = cfg.get("leave_message")
            text = format_message(tmpl, member=member, guild=member.guild)
            embed = discord.Embed(title="🥀 Egy túlélő elhagyott...", description=text, color=discord.Color.dark_gray())
            if member.display_avatar:
                embed.set_thumbnail(url=member.display_avatar.url)
            await channel.send(embed=embed)

if __name__ == "__main__":
    token = os.getenv("JASMINE_TOKEN") or os.getenv("DISCORD_TOKEN")
    bot = Jasmine()
    bot.run(token)
