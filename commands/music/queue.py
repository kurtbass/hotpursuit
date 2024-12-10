import asyncio
import discord
from discord.ext import commands
from commands.music.musicsystem.embeds import embed_queue_page, embed_error, embed_queue_empty, embed_queue_cleared
import logging
import math

logger = logging.getLogger(__name__)

class QueueCommand(commands.Cog):
    """
    Comando para exibir e gerenciar a fila de músicas.
    """

    def __init__(self, bot, music_manager):
        self.bot = bot
        self.music_manager = music_manager  # Gerenciador centralizado de músicas

    @commands.command(name="queue", aliases=["fila", "lista", "q"])
    async def queue(self, ctx, *args):
        """
        Exibe ou gerencia a fila de músicas. Suporta paginação, limpeza e outras ações.
        """
        # Verifica se o autor está no mesmo canal que o bot
        if not ctx.author.voice or self.music_manager.voice_client is None or ctx.author.voice.channel != self.music_manager.voice_client.channel:
            await ctx.send(embed=embed_error("user_not_in_same_channel"))
            return

        # Subcomando: limpar fila
        if args and args[0].lower() in ["limpar", "clear", "clean"]:
            if self.music_manager.loop_mode == "single":
                self.music_manager.loop_mode = "none"
                logger.info("Loop desativado devido à limpeza da fila.")
            self.music_manager.clear_queue()
            await ctx.send(embed=embed_queue_cleared())
            return

        # Exibição da fila com paginação
        try:
            page = int(args[0]) if args else 1
        except ValueError:
            await ctx.send(embed=embed_error("invalid_argument"))
            return

        music_queue = self.music_manager.music_queue

        if not music_queue:
            await ctx.send(embed=embed_queue_empty())
            return

        # Configurações de paginação
        items_per_page = 10
        total_pages = math.ceil(len(music_queue) / items_per_page)
        if page < 1 or page > total_pages:
            await ctx.send(embed=embed_error("invalid_page", total_pages=total_pages))
            return

        # Gerar a descrição da fila para a página solicitada
        def generate_page_description(page_number):
            start_index = (page_number - 1) * items_per_page
            end_index = start_index + items_per_page
            description = "\n\n".join(
                f"**{index}.** [{song.get('title', 'Título Desconhecido')}]({song.get('url', '#')})\n"
                f" 🎵 **Adicionado por:** <@{song.get('added_by', 'Desconhecido')}> | ⏱️ **Duração:** {format_duration(song.get('duration', 0))}"
                for index, song in enumerate(music_queue[start_index:end_index], start=start_index + 1)
            )
            return description

        # Criar embed inicial
        embed = embed_queue_page(
            page=page,
            total_pages=total_pages,
            description=generate_page_description(page)
        )
        message = await ctx.send(embed=embed)

        # Adicionar reações para navegação
        if total_pages > 1:
            await message.add_reaction("⬅️")
            await message.add_reaction("➡️")
        await message.add_reaction("❌")

        # Função para lidar com as reações
        def check(reaction, user):
            return user == ctx.author and reaction.message.id == message.id and str(reaction.emoji) in ["⬅️", "➡️", "❌"]

        # Lidar com navegação por reações
        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)

                if str(reaction.emoji) == "⬅️" and page > 1:
                    page -= 1
                elif str(reaction.emoji) == "➡️" and page < total_pages:
                    page += 1
                elif str(reaction.emoji) == "❌":
                    await message.delete()
                    break

                # Atualizar embed com a nova página
                embed = embed_queue_page(
                    page=page,
                    total_pages=total_pages,
                    description=generate_page_description(page)
                )
                await message.edit(embed=embed)

                # Remove a reação do usuário
                await message.remove_reaction(reaction, user)

            except asyncio.TimeoutError:
                await message.clear_reactions()
                break


def format_duration(seconds):
    """
    Formata a duração em segundos para o formato MM:SS.
    """
    minutes, seconds = divmod(seconds, 60)
    return f"{minutes}:{seconds:02d}"


async def setup(bot, music_manager):
    """
    Adiciona o cog ao bot.

    :param bot: O bot do Discord.
    :param music_manager: O gerenciador de música compartilhado.
    """
    await bot.add_cog(QueueCommand(bot, music_manager))
