import discord
from discord.ext import commands
from discord import Embed
import os
import asyncio

# ajustes
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # esto es necesario para el sistema de rango

bot = commands.Bot(command_prefix='agus!', intents=intents)
bot = commands.Bot(command_prefix='Agus!', intents=intents)
bot = commands.Bot(command_prefix=':', intents=intents)

# discord token key (dueño de la app : angely_.12)
DISCORD_TOKEN = "MTQwNjI3MzcxNjcxODkyNzk4NA.G11zFR.D4MZViXC38vTEx9QVF2Rw1yHQ99DO7nWUxSXX4"

# modulos
async def cargar_modulos():    
    # sistema de rangos
    try:
        await bot.load_extension("sistema_rangos.rangos_cog")
        print(" Sistema de rangos cargado")
    except Exception as e:
        print(f" Error cargando sistema de rangos: {e}")
    
    # cogs - redes sociales
    if os.path.exists("./cogs"):
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py") and filename != "__init__.py":
                try:
                    await bot.load_extension(f"cogs.{filename[:-3]}")
                    print(f" Cog cargado: {filename[:-3]}")
                except Exception as e:
                    print(f" Error cargando {filename}: {e}")
    else:
        print(" Carpeta 'cogs' no encontrada")

# info
@bot.event
async def on_ready():
    print(f'{bot.user} se ha conectado a discord')
    print(f'Conectado a {len(bot.guilds)} servidores')

@bot.command()
async def hola(ctx):
    await ctx.send(f'¡Hola {ctx.author.mention}!')

@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f'🏓 Pong! Latencia: {latency}ms')

# mensaje de error
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Amigo eres Pelotudo? Di Los Comandos bien Imbecil")
    else:
        print(f"Error: {error}")

# comando de ayuda hecho con ia
@bot.command()
async def ayuda(ctx):

    embed = Embed(
        title="🤖 COMANDOS DEL BOT",
        description="Lista de todos los comandos disponibles",
        color=0x00ff00
    )
    embed.add_field(name="🔗 Redes Sociales", value="agus!redes - Mis redes sociales\nagus!youtube - Mi YouTube\nagus!kick - Mi Kick", inline=False)
    embed.add_field(name="📊 Sistema de Rangos", value="agus!rango - Ver tu rango\nagus!toprangos - Top usuarios", inline=False)
    embed.add_field(name="🛠️ Utilidades", value="agus!ping - Ver latencia\nagus!hola - Saludo del bot", inline=False)
    embed.add_field(name="ℹ️ Información", value="agus!ayuda - Esta ayuda", inline=False)
    embed.set_footer(text="Prefijo: agus!")
    
    await ctx.send(embed=embed)

# run
async def main():
    await cargar_modulos()
    
    await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    print("[Agus-bot] Iniciando...")
    asyncio.run(main())