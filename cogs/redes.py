"""hecho por iker con ayuda de angely"""
import discord
from discord.ext import commands
from discord import Embed

class RedesSociales(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="redes")
    async def mostrar_redes(self, ctx):
        """redes sociales"""
        embed = Embed(
            title="🌐 MIS REDES SOCIALES",
            description="¡Sígueme en todas mis plataformas!",
            color=0xff0000
        )
        
        # YouTube
        embed.add_field(
            name="🎥 **YOUTUBE**",
            value="[ **CLICK AQUÍ PARA YOUTUBE**](https://youtube.com/Aagustina18_)",
            inline=False
        )
        
        # Kick
        embed.add_field(
            name="🎮 **KICK**",
            value="[ **CLICK AQUÍ PARA KICK**](https://kick.com/Agustina_lou18)",
            inline=False
        )
        
        embed.set_footer(text="Usa agus!ayuda para más comandos")
        await ctx.send(embed=embed)

    @commands.command(name="youtube", aliases=["yt"])
    async def youtube(self, ctx):
        """Solo el link de YouTube"""
        await ctx.send(" **YouTube:** https://youtube.com/@Aagustina18_\n¡Suscríbete! ")

    @commands.command(name="kick")
    async def kick(self, ctx):
        """Solo el link de Kick"""
        await ctx.send(" **Mi Kick:** kick.com/Agustina_lou18\n¡Sígueme para mas streams! ")

async def setup(bot):
    await bot.add_cog(RedesSociales(bot))