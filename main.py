import discord
from discord.ext import commands
import datetime

class Jasmine(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        intents.moderation = True  # Szükséges a kitiltások (bans) ellenőrzéséhez
        super().__init__(command_prefix='!', intents=intents)

    async def on_member_join(self, member):
        # Ellenőrizzük, hogy a tag ki van-e tiltva (bannolva)
        try:
            async for entry in member.guild.audit_logs(limit=5, action=discord.AuditLogAction.ban):
                if entry.target.id == member.id:
                    # Ha friss ban van érvényben, csendben kilépünk (nem köszönjük meg)
                    return
        except discord.Forbidden:
            pass
        
        # Másodlagos biztonság: lekérdezzük a szerver tiltásait is
        try:
            bans = [ban_entry.user.id async for ban_entry in member.guild.bans()]
            if member.id in bans:
                return
        except (discord.Forbidden, discord.HTTPException):
            pass

        # 1. Nyilvános köszöntő üzenet a szerveren
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

        # 2. Privát (DM) üzenet küldése az új tagnak
        try:
            dm_embed = discord.Embed(
                title="💌 Szia kedves Túlélő!",
                description=f"Csak be akartam köszönni így privátban is! 😊 Örülök, hogy csatlakoztál a **Never SMP**-hez.\n\nHa bármi kérdésed van, vagy szeretsz elakadni, nyugodtan keress minket a szerveren. Érezd nagyon jól magad nálunk! 🌸✨",
                color=discord.Color.pink()
            )
            dm_embed.set_footer(text="Szeretettel: Jasmine 🐾")
            
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            # Ha a tagnak le vannak tiltva a DM-ek, a bot csendben átugorja
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
    bot.run("MTUzOTc4ODk0NTU0MDUxMzgzMg.G8d4EK.r-hDF_4X8twdVj89MgdCW4-Ovlig1acUSf1gvg")
