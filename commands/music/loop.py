from utils.database import get_emoji_from_table, get_fun_emoji, get_music_emoji, get_error_emoji, get_number_emoji, get_clan_management_emoji, get_server_staff_emoji
import asyncio
import discord
from discord.ext import commands
from commands.music.musicsystem.embeds import (
    embed_dj_error, embed_error, embed_loop_single, embed_loop_all, embed_loop_off, embed_loop_cancel, embed_loop_timeout, create_embed
)
from colorama import Fore, Style
import logging

logger = logging.getLogger(__name__)

class LoopCommand(commands.Cog):
    """
    Comando para gerenciar o loop de reprodução.
    """
    def __init__(self, bot, music_manager):
        self.bot = bot
        self.music_manager = music_manager

    @commands.command(name="loop", aliases=["repetir", "repeat"])
    async def loop(self, ctx):
        """
        Menu para gerenciar o modo de repetição.
        """

        # Verifica se o usuário iniciou a sessão ou tem a tag de DJ
        tag_dj_id = self.music_manager.dj_role_id
        if not (ctx.author.id == self.music_manager.get_session_owner_id() or 
                discord.utils.get(ctx.author.roles, id=int(tag_dj_id))):
            await ctx.send(embed=embed_dj_error())
            return

        # Enviar menu de opções
        options = (
            "1️⃣ Repetir música atual\n"
            "2️⃣ Repetir todas as músicas\n"
            "3️⃣ Desligar repetição\n"
            "❌ Cancelar"
        )
        embed = create_embed(
            "🔁 Configuração de Loop",
            f"Escolha uma opção:\n\n{options}"
        )
        menu_message = await ctx.send(embed=embed)

        # Adicionar reações para o menu
        reactions = ["1️⃣", "2️⃣", "3️⃣", "❌"]
        for reaction in reactions:
            await menu_message.add_reaction(reaction)

        # Função para verificar a reação
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in reactions and reaction.message.id == menu_message.id

        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)

            if str(reaction.emoji) == "1️⃣":
                self.music_manager.set_loop_mode("single")
                await ctx.send(embed=embed_loop_single())

            elif str(reaction.emoji) == "2️⃣":
                self.music_manager.set_loop_mode("all")
                await ctx.send(embed=embed_loop_all())

            elif str(reaction.emoji) == "3️⃣":
                self.music_manager.set_loop_mode("none")
                await ctx.send(embed=embed_loop_off())

            elif str(reaction.emoji) == "❌":
                await ctx.send(embed=embed_loop_cancel())

            logger.info(f"{Fore.GREEN}Loop atualizado para: {self.music_manager.get_loop_mode()} pelo usuário {ctx.author.id}{Style.RESET_ALL}")

        except asyncio.TimeoutError:
            await ctx.send(embed=embed_loop_timeout())

        finally:
            # Apaga a mensagem do menu
            await menu_message.delete()

async def setup(bot, music_manager):
    """
    Adiciona o cog ao bot.

    :param bot: O bot do Discord.
    :param music_manager: O gerenciador de música compartilhado.
    """
    await bot.add_cog(LoopCommand(bot, music_manager))
