import discord
from discord.ext import commands
from .rangos_manager import RangosManager

class RangosCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.manager = RangosManager(bot)

    @commands.Cog.listener()
    async def on_ready(self):
        print(" Sistema de rangos inicializando...")
        for guild in self.bot.guilds:
            await self.manager.inicializar_servidor(guild)
        print(" Sistema de rangos listo!")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.manager.asignar_rango_novato(member)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild and not message.author.bot:
            await self.manager.procesar_mensaje(message)

    @commands.command(name="rango")
    async def ver_rango(self, ctx, member: discord.Member = None):
        if not member:
            member = ctx.author
        
        stats = self.manager.get_user_stats(member.id)
        requisitos = self.manager.rangos[stats["proximo_rango"]]["requisito"] if stats["proximo_rango"] != "Máximo rango alcanzado" else {}
        
        embed = discord.Embed(
            title=f"📊 Rango de {member.display_name}",
            color=discord.Color(self.manager.rangos[stats["rango_actual"]]["color"])
        )
        
        embed.add_field(name="🎯 Rango Actual", value=f"**{stats['rango_actual']}**", inline=True)
        embed.add_field(name="📅 Días en el servidor", value=f"**{stats['tiempo_dias']} días**", inline=True)
        embed.add_field(name="💬 Mensajes totales", value=f"**{stats['mensajes_totales']}**", inline=True)
        
        if stats["proximo_rango"] != "Máximo rango alcanzado":
            embed.add_field(
                name="⭐ Próximo Rango", 
                value=f"**{stats['proximo_rango']}**\n"
                      f"Requisitos: {requisitos['tiempo']} días + {requisitos['mensajes']} mensajes",
                inline=False
            )
        else:
            embed.add_field(name="🏆 Estado", value="**¡Máximo rango alcanzado!**", inline=False)
        
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        
        await ctx.send(embed=embed)

    @commands.command(name="top")
    @commands.has_permissions(manage_roles=True)
    async def top_rangos(self, ctx):
        sorted_users = sorted(
            [(user_id, data) for user_id, data in self.manager.user_data.items()],
            key=lambda x: x[1]["mensajes"],
            reverse=True
        )[:10]
        
        embed = discord.Embed(
            title="🏆 TOP 10 USUARIOS POR MENSAJES",
            color=0xffd700
        )
        
        for i, (user_id, data) in enumerate(sorted_users, 1):
            try:
                user = await self.bot.fetch_user(int(user_id))
                username = user.name
            except:
                username = f"Usuario {user_id}"
                
            embed.add_field(
                name=f"{i}. {username}",
                value=f"**{data['mensajes']}** mensajes | **{data['rango_actual']}**",
                inline=False
            )
        
        await ctx.send(embed=embed)

    @commands.command(name="forzar_rango")
    @commands.has_permissions(administrator=True)
    async def forzar_rango(self, ctx, member: discord.Member, rango: str):
        if rango not in self.manager.rangos:
            await ctx.send("❌ Rango no válido. Rangos disponibles: " + ", ".join(self.manager.rangos.keys()))
            return
        
        await self.manager.asignar_nuevo_rango(member, ctx.guild, rango, self.manager.get_user_data(member.id))
        await ctx.send(f"✅ {member.mention} ahora es **{rango}**")

async def setup(bot):
    await bot.add_cog(RangosCog(bot))