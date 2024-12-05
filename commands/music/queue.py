from utils.database import get_config, get_embed_color
import asyncio
import discord
from discord.ext import commands
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

    def create_embed(self, title, description, color=get_embed_color()):
        """
        Cria um embed padronizado com título, descrição e cor.
        """
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text=get_config("LEMA"))
        return embed

    @commands.command(name="queue", aliases=["fila", "lista", "q"])
    async def queue(self, ctx, *args):
        """
        Exibe ou gerencia a fila de músicas. Suporta paginação, limpeza e outras ações.
        """
        # Verifica se o autor está no mesmo canal que o bot
        if not ctx.author.voice or self.music_manager.voice_client is None or ctx.author.voice.channel != self.music_manager.voice_client.channel:
            await ctx.send(embed=self.create_embed(
                "Erro", "⚠️ Você precisa estar no mesmo canal de voz do bot para usar este comando.", get_embed_color()
            ))
            return

        # Subcomando: limpar fila
        if args and args[0].lower() in ["limpar", "clear", "clean"]:
            self.music_manager.clear_queue()
            await ctx.send(embed=self.create_embed(
                "Fila Limpa", "✅ A fila de músicas foi limpa com sucesso.", get_embed_color()
            ))
            return

        # Exibição da fila com paginação
        try:
            page = int(args[0]) if args else 1
        except ValueError:
            await ctx.send(embed=self.create_embed(
                "Erro", "⚠️ O argumento fornecido não é um número válido ou um comando reconhecido.", get_embed_color()
            ))
            return

        music_queue = self.music_manager.music_queue

        if not music_queue:
            await ctx.send(embed=self.create_embed(
                "Fila de Músicas", "⚠️ A fila está vazia.", get_embed_color()
            ))
            return

        # Configurações de paginação
        items_per_page = 10
        total_pages = math.ceil(len(music_queue) / items_per_page)
        if page < 1 or page > total_pages:
            await ctx.send(embed=self.create_embed(
                "Erro", f"⚠️ Página inválida. Escolha um número entre 1 e {total_pages}.", get_embed_color()
            ))
            return

        # Gerar a descrição da fila para a página solicitada
        def generate_page_description(page_number):
            start_index = (page_number - 1) * items_per_page
            end_index = start_index + items_per_page
            description = ""
            for index, song in enumerate(music_queue[start_index:end_index], start=start_index + 1):
                duration_formatted = (
                    f"{song.get('duration', 0) // 60}:{song.get('duration', 0) % 60:02d}" if 'duration' in song else "Desconhecido"
                )
                description += (
                    f"**{index}.** [{song.get('title', 'Título Desconhecido')}]({song.get('url', '#')})\n"
                    f" 🎵 **Adicionado por:** {song.get('added_by', 'Desconhecido')} | ⏱️ **Duração:** {duration_formatted}\n"
                )
            return description

        # Criar embed inicial
        embed = self.create_embed(
            title="🎶 Fila de Reprodução",
            description=generate_page_description(page),
            color=get_embed_color()
        )
        embed.set_footer(text=f"Página {page}/{total_pages} | {get_config("LEMA")}")
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
                embed.description = generate_page_description(page)
                embed.set_footer(text=f"Página {page}/{total_pages} | {get_config("LEMA")}")
                await message.edit(embed=embed)

                # Remove a reação do usuário
                await message.remove_reaction(reaction, user)

            except asyncio.TimeoutError:
                await message.clear_reactions()
                break


async def setup(bot, music_manager):
    """
    Adiciona o cog ao bot.

    :param bot: O bot do Discord.
    :param music_manager: O gerenciador de música compartilhado.
    """
    await bot.add_cog(QueueCommand(bot, music_manager))
