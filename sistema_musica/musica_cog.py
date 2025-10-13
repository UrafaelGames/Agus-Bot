import discord
from discord.ext import commands
import yt_dlp
import asyncio

# configuracion
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        
        if 'entries' in data:
            data = data['entries'][0]
        
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class MusicaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.music_channel_id = 1424556878255362058   # channel music
        self.command_channel_id = 1424556917283360798 # channel custom
        
    @commands.Cog.listener()
    async def on_ready(self):
        print("Sistema de música listo!")
        
    def can_use_music_commands(self, ctx):
        return ctx.channel.id == self.command_channel_id
    
    async def connect_to_music_channel(self, guild):
        try:
            music_channel = guild.get_channel(self.music_channel_id)
            if not music_channel:
                print("Canal de musica no encontrado")
                return False
                
            voice_client = guild.voice_client
            
            if voice_client and voice_client.is_connected():
                if voice_client.channel.id != self.music_channel_id:
                    await voice_client.move_to(music_channel)
            else:
                await music_channel.connect()
            
            return True
        except Exception as e:
            print(f"Error conectando al canal de musica: {e}")
            return False
    
    async def send_test_warning(self, ctx):
        warning_embed = discord.Embed(
            title="⚠️ MODO PRUEBAS",
            description="El sistema de música se encuentra en **modo test**. Cualquier error o problema puedes reportarlo en el canal de moderación.",
            color=0xffa500  # naranja
        )
        warning_embed.set_footer(text="Gracias por ayudar a mejorar el bot!")
        await ctx.send(embed=warning_embed)
    
    @commands.command(name='play')
    async def play(self, ctx, *, url):
        if not self.can_use_music_commands(ctx):
            await ctx.send(f"Usa los comandos de música en <#{self.command_channel_id}>")
            return
        
        if not ctx.author.voice:
            await ctx.send("Debes estar en un canal de voz para usar este comando!")
            return
        
        try:
            if not await self.connect_to_music_channel(ctx.guild):
                await ctx.send("No se pudo conectar al canal de musica!")
                return
            
            voice_client = ctx.guild.voice_client
            
            loading_embed = discord.Embed(
                title="🔄 Cargando música...",
                description="Por favor espera mientras se carga la canción",
                color=0xffff00
            )
            loading_msg = await ctx.send(embed=loading_embed)
            
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            voice_client.play(player, after=lambda e: print(f'Error del reproductor: {e}') if e else None)
            
            await loading_msg.delete()
            
            play_embed = discord.Embed(
                title="🎵 Reproduciendo",
                description=f"**[{player.title}]({url})**",
                color=0x00ff00
            )
            play_embed.add_field(
                name="Duración", 
                value="*Información de ducción disponible en próximas actualizaciones*", 
                inline=True
            )
            play_embed.add_field(
                name="Solicitado por", 
                value=ctx.author.mention, 
                inline=True
            )
            play_embed.set_footer(text="Usa Agus!musica para ver todos los comandos disponibles")
            
            await ctx.send(embed=play_embed)
            
            await self.send_test_warning(ctx)
                
        except Exception as e:
            await ctx.send(f"❌ Error al reproducir: {str(e)}")
            print(f"Error en play command: {e}")
    
    @commands.command(name='stop')
    async def stop(self, ctx):
        if not self.can_use_music_commands(ctx):
            await ctx.send(f"❌ Usa los comandos de música en <#{self.command_channel_id}>")
            return
        
        voice_client = ctx.guild.voice_client
        
        if voice_client and voice_client.is_connected():
            if voice_client.is_playing():
                voice_client.stop()
            await voice_client.disconnect()
            
            embed = discord.Embed(
                title="⏹️ Música detenida",
                description="La reproducción ha sido detenida y el bot desconectado",
                color=0xff0000
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ No hay música reproduciéndose!")
    
    @commands.command(name='pause')
    async def pause(self, ctx):
        if not self.can_use_music_commands(ctx):
            await ctx.send(f"❌ Usa los comandos de música en <#{self.command_channel_id}>")
            return
        
        voice_client = ctx.guild.voice_client
        
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            embed = discord.Embed(
                title="⏸️ Música pausada",
                description="La reproducción ha sido pausada",
                color=0xffff00
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ No hay música reproduciéndose!")
    
    @commands.command(name='resume')
    async def resume(self, ctx):
        if not self.can_use_music_commands(ctx):
            await ctx.send(f"❌ Usa los comandos de música en <#{self.command_channel_id}>")
            return
        
        voice_client = ctx.guild.voice_client
        
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            embed = discord.Embed(
                title="▶️ Música reanudada",
                description="La reproducción ha sido reanudada",
                color=0x00ff00
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ La música no está pausada!")
    
    @commands.command(name='skip')
    async def skip(self, ctx):
        if not self.can_use_music_commands(ctx):
            await ctx.send(f"❌ Usa los comandos de música en <#{self.command_channel_id}>")
            return
        
        voice_client = ctx.guild.voice_client
        
        if voice_client and voice_client.is_playing():
            voice_client.stop()
            embed = discord.Embed(
                title="⏭️ Canción saltada",
                description="La canción actual ha sido saltada",
                color=0x00ff00
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ No hay música reproduciéndose!")
    
    @commands.command(name='musica')
    async def musica_help(self, ctx):
        """cuadro de dialogo de ayuda"""
        embed = discord.Embed(
            title="🎵 COMANDOS DE MÚSICA",
            description="Lista de todos los comandos disponibles para el sistema de música",
            color=0x7289da
        )
        
        embed.add_field(
            name="🎶 Reproducir música",
            value="`:play [url/búsqueda]` - Reproduce música desde YouTube\n*Ejemplo: `:play https://youtube.com/watch?v=...`*",
            inline=False
        )
        
        embed.add_field(
            name="⏹️ Detener música",
            value="`:stop` - Detiene la música y desconecta al bot",
            inline=False
        )
        
        embed.add_field(
            name="⏸️ Control de reproducción",
            value="`:pause` - Pausa la música\n`:resume` - Reanuda la música\n`:skip` - Salta la canción actual",
            inline=False
        )
        
        embed.add_field(
            name="ℹ️ Información",
            value="`:musica` - Muestra esta ayuda",
            inline=False
        )
        
        embed.add_field(
            name="📋 Cómo usar",
            value=f"1. Únete a cualquier canal de voz\n2. Usa los comandos en <#{self.command_channel_id}>\n3. El bot se conectará automáticamente al canal de música",
            inline=False
        )
        
        embed.add_field(
            name="⚠️ Importante",
            value="El sistema se encuentra en **modo test**. Cualquier error puedes reportarlo en moderación.",
            inline=False
        )
        
        embed.set_footer(text="Prefijos: :, agus!, Agus!")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(MusicaCog(bot))