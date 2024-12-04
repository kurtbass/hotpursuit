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
        self.session_owner = None  # Dono da sessão atual

    def create_embed(self, title, description, color=0xFF8000):
        """
        Cria um embed padronizado com título, descrição e cor.

        :param title: Título do embed.
        :param description: Descrição do embed.
        :param color: Cor do embed.
        :return: Objeto discord.Embed.
        """
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text="Hot Pursuit - Potência e Precisão, Sempre na Frente.")
        return embed

    @commands.command(name="queue", aliases=["fila", "lista"])
    async def queue(self, ctx, page: int = 1):
        """
        Exibe ou gerencia a fila de músicas. Suporta paginação, limpeza e encerramento.

        :param ctx: Contexto do comando.
        :param page: Número da página a ser exibida (opcional, padrão é 1).
        """
        # Verifica se o autor está no mesmo canal que o bot
        if not ctx.author.voice or ctx.author.voice.channel != self.music_manager.voice_client.channel:
            await ctx.send(embed=self.create_embed(
                "Erro", "⚠️ Você precisa estar no mesmo canal de voz do bot para usar este comando.", 0xFF0000
            ))
            return

        # Caso o comando seja `hp!queue limpar`
        if "limpar" in ctx.message.content.lower():
            if ctx.author.id != self.session_owner:
                await ctx.send(embed=self.create_embed(
                    "Erro", "⚠️ Apenas o dono da sessão pode limpar a fila.", 0xFF0000
                ))
                return

            self.music_manager.clear_queue()
            await ctx.send(embed=self.create_embed(
                "🎶 Fila Limpa",
                "Todas as próximas músicas na fila foram removidas.",
                color=0xFF8000
            ))
            return

        # Exibir a fila de músicas
        music_queue = self.music_manager.music_queue

        if not music_queue:
            await ctx.send(embed=self.create_embed(
                "Fila de Músicas", "⚠️ A fila está vazia.", 0xFF0000
            ))
            return

        # Configurações de paginação
        items_per_page = 10
        total_pages = math.ceil(len(music_queue) / items_per_page)

        if page < 1 or page > total_pages:
            await ctx.send(embed=self.create_embed(
                "Erro", f"⚠️ Página inválida. Escolha um número entre 1 e {total_pages}.", 0xFF0000
            ))
            return

        # Gerar a descrição da fila para a página solicitada
        start_index = (page - 1) * items_per_page
        end_index = start_index + items_per_page
        queue_description = ""

        for index, song in enumerate(music_queue[start_index:end_index], start=start_index + 1):
            duration_formatted = (
                f"{song.get('duration', 0) // 60}:{song.get('duration', 0) % 60:02d}"
                if 'duration' in song else "Desconhecido"
            )
            queue_description += (
                f"**{index}.** [{song['title']}]({song['url']})\n"
                f" 🎵 **Adicionado por:** {song['added_by']} | ⏱️ **Duração:** {duration_formatted}\n"
            )

        # Criar embed com informações de paginação
        embed = self.create_embed(
            title="🎶 Fila de Reprodução",
            description=queue_description,
            color=0xFF8000
        )
        embed.set_footer(text=f"Página {page}/{total_pages} | Hot Pursuit - Potência e Precisão, Sempre na Frente.")
        message = await ctx.send(embed=embed)

        # Se houver mais de uma página, adiciona as reações de navegação
        if total_pages > 1:
            await message.add_reaction("⬅️")
            await message.add_reaction("➡️")
        await message.add_reaction("❌")

        # Função para lidar com as reações
        def check(reaction, user):
            return user == ctx.author and reaction.message.id == message.id and str(reaction.emoji) in ["⬅️", "➡️", "❌"]

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
                start_index = (page - 1) * items_per_page
                end_index = start_index + items_per_page
                queue_description = ""

                for index, song in enumerate(music_queue[start_index:end_index], start=start_index + 1):
                    duration_formatted = f"{song['duration'] // 60}:{song['duration'] % 60:02d}"
                    queue_description += (
                        f"**{index}.** [{song['title']}]({song['url']})\n"
                        f" 🎵 **Adicionado por:** {song['added_by']} | ⏱️ **Duração:** {duration_formatted}\n"
                    )

                embed = self.create_embed(
                    title="🎶 Fila de Reprodução",
                    description=queue_description,
                    color=0xFF8000
                )
                embed.set_footer(text=f"Página {page}/{total_pages} | Hot Pursuit - Potência e Precisão, Sempre na Frente.")
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
