import discord
from discord.ext import commands
import datetime
import os

class Jasmine(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        intents.moderation = True  # Szükséges a kitiltások ellenőrzéséhez
        super().__init__(command_prefix='!', intents=intents)

    async def on_member_join(self, member):
        is_banned = False
        
        # 1. Ellenőrizzük, hogy ki van-e tiltva (bannolva)
        try:
            async for entry in member.guild.audit_logs(limit=5, action=discord.AuditLogAction.ban):
                if entry.target.id == member.id:
                    is_banned = True
                    break
        except discord.Forbidden:
            pass
        
        if not is_banned:
            try:
                bans = [ban_entry.user.id async for ban_entry in member.guild.bans()]
                if member.id in bans:
                    is_banned = True
            except (discord.Forbidden, discord.HTTPException):
                pass

        # Ha ki van bannolva, Jasmine elküldi a DM-et, és megállítjuk a folyamatot
        if is_banned:
            try:
                ban_embed = discord.Embed(
                    title="🚫 Sajnálom, de nem tudsz belépni!",
                    description=f"Szia! Bocsi, de te nem fogsz tudni bejönni a szerverre, ugyanis téged bannoltak. Vagy a hugom, Kamila bannolt, vagy valamelyik staff, esetleg a tulajdonos.\n\nHa a tulaj úgy gondolja, akkor unbannol téged, de én nem tudlak, mert én csak egy bot vagyok, semmi más! 🌸",
                    color=discord.Color.red()
                )
                ban_embed.set_footer(text="Jasmine, a szerver tündérkéje ✨")
                await member.send(embed=ban_embed)
            except discord.Forbidden:
                # Ha le vannak tiltva a DM-ek, csendben átugorjuk
                pass
            return

        # 2. Normál, sikeres belépés (ha NINCS bannolva)
        channel = self.get_channel(1539791346880221196) 
        if channel:
            member_count = member.guild.member_count
            join_date = member.joined_at.strftime("%Y-%m-%d - %H:%M") if member.joined_at else "Ismeretlen"
            
            embed = discord.Embed(
                title="🌸 Új csillag érkezett a Never SMP-re! 🌸",
                description=f"Szia {member.mention}! De örülök, hogy megérkeztél! ✨\nLégy nagyon boldog nálunk, és érezd otthon magad ebben a kis világunkban! 🐾",
                color=discord.Color.pink()
            )
            
            embed.add_field(name="Túlélő ID", value=f"`{member.id}`", inline=False)
            embed.add_field(name="Csatlakozás ideje", value=f"{join_date}", inline=True)
            embed.add_field(name="Túlélők száma", value=f"{member_count}. tag vagy! 💖", inline=True)
            
            if member.display_avatar:
                embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text="Jasmine, a szerver tündérkéje ✨")
            
            await channel.send(embed=embed)

        # Privát (DM) üzenet a normális tagoknak
        try:
            dm_embed = discord.Embed(
                title="💌 Szia kedves Túlélő!",
                description=f"Csak be akartam köszönni így privátban is! 😊 Örülök, hogy csatlakoztál a **Never SMP**-hez.\n\nHa bármi kérdésed van, vagy elakadsz, nyugodtan keress minket a szerveren. Érezd nagyon jól magad nálunk! 🌸✨",
                color=discord.Color.pink()
            )
            dm_embed.set_footer(text="Szeretettel: Jasmine 🐾")
            
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            pass

    async def on_member_remove(self, member):
        # Megható búcsú üzenet
        channel = self.get_channel(1539791383815258172) 
        if channel:
            embed = discord.Embed(
                title="🥀 Egy túlélő elhagyott minket...",
                description=f"Jaj, {member.name} útra kelt... Nagyon fog hiányozni a Never SMP világából! 💔\nRemélem, még viszontlátjuk egymást valamikor... ✨",
                color=discord.Color.dark_gray()
            )
            
            if member.display_avatar:
                embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text="Jasmine, a szerver tündérkéje 🌸")
            
            await channel.send(embed=embed)

if __name__ == "__main__":
    bot = Jasmine()
    token = os.getenv("JASMINE_TOKEN")  # A Railway környezeti változójából olvassa be
    bot.run(token)
