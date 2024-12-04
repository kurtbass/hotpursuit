import asyncio
import discord
from discord.ext import commands
import logging

logger = logging.getLogger(__name__)

class SkipCommand(commands.Cog):
    """
    Comando para pular a música atual.
    """

    def __init__(self, bot, music_manager):
        self.bot = bot
        self.music_manager = music_manager  # Gerenciador centralizado de músicas

    def create_embed(self, title, description, color=0xFF8000, banner=None):
        """
        Cria um embed padronizado com título, descrição e cor.

        :param title: Título do embed.
        :param description: Descrição do embed.
        :param color: Cor do embed.
        :param banner: URL do banner para exibir no embed.
        :return: Objeto discord.Embed.
        """
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text="Hot Pursuit - Potência e Precisão, Sempre na Frente.")
        if banner:
            embed.set_image(url=banner)
        return embed

    @commands.command(name="skip", aliases=["pular", "s"])
    async def skip(self, ctx):
        """
        Pula a música atualmente sendo tocada e avança para a próxima na fila.
        """
        voice_client = self.music_manager.voice_client

        if voice_client is None or not voice_client.is_connected():
            await ctx.send(embed=self.create_embed(
                "Erro", "⚠️ O bot não está conectado a nenhum canal de voz.", 0xFF0000
            ))
            return

        if not voice_client.is_playing():
            await ctx.send(embed=self.create_embed(
                "Erro", "⚠️ Nenhuma música está sendo tocada no momento.", 0xFF0000
            ))
            return

        # Obter próxima música
        next_song = self.music_manager.get_next_song()

        if next_song:
            try:
                # Salvar a música atual como anterior (caso necessário para voltar)
                self.music_manager.save_current_to_history()

                # Formatar duração da próxima música
                duration_seconds = next_song.get('duration', 0)
                duration_formatted = f"{duration_seconds // 60}:{duration_seconds % 60:02d}" if duration_seconds else "Desconhecida"

                # Reproduzir próxima música com ajuste de volume
                source = discord.PCMVolumeTransformer(
                    discord.FFmpegPCMAudio(next_song.get('stream_url', ''), **{
                        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                        'options': '-vn'
                    }),
                    volume=self.music_manager.volume  # Ajustar para o volume atual do usuário
                )
                self.music_manager.current_song = next_song  # Atualizar a música atual
                voice_client.stop()
                voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(
                    self.music_manager.play_next(), self.bot.loop
                ))

                # Enviar informações da próxima música
                embed = self.create_embed(
                    title="⏭️ Música Pulada",
                    description=(f"**Agora Tocando:** [{next_song.get('title', 'Desconhecida')}]({next_song.get('url', '')})\n"
                                 f"**Canal do YouTube:** {next_song.get('uploader', 'Desconhecido')}\n"
                                 f"**Duração:** {duration_formatted}\n"
                                 f"**Adicionado por:** {next_song.get('added_by', 'Desconhecido')}"),
                    banner=next_song.get('thumbnail')
                )
                await ctx.send(embed=embed)

            except Exception as e:
                logger.error(f"Erro ao reproduzir a próxima música: {e}")
                await ctx.send(embed=self.create_embed(
                    "Erro", "⚠️ Ocorreu um erro ao tentar reproduzir a próxima música.", 0xFF0000
                ))
        else:
            # Caso não haja próximas músicas na fila, mas ainda há uma atual
            if self.music_manager.current_song:
                self.music_manager.save_current_to_history()  # Salvar a música atual como anterior
                self.music_manager.current_song = None
            voice_client.stop()
            await ctx.send(embed=self.create_embed(
                "Fila Vazia", "⚠️ Não há músicas na fila para reproduzir após esta.", 0xFF8000
            ))


async def setup(bot, music_manager):
    """
    Adiciona o cog ao bot.

    :param bot: O bot do Discord.
    :param music_manager: O gerenciador de música compartilhado.
    """
    await bot.add_cog(SkipCommand(bot, music_manager))
