from utils.database import get_emoji_from_table, get_fun_emoji, get_music_emoji, get_error_emoji, get_number_emoji, get_clan_management_emoji, get_server_staff_emoji
import discord
from discord.ext import commands
import logging

# Configuração de logger
logger = logging.getLogger(__name__)

class OnMessageEvent(commands.Cog):
    """Cog para gerenciar o evento on_message."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        Evento disparado toda vez que uma mensagem é enviada em um canal visível para o bot.
        O bot responderá a menções com informações ou processará comandos.
        """

        # Ignorar mensagens enviadas pelo próprio bot
        if message.author == self.bot.user:
            logger.debug("Mensagem enviada pelo próprio bot, ignorando.")
            return

        # Ignorar mensagens de outros bots
        if message.author.bot:
            logger.debug("Mensagem enviada por outro bot, ignorando.")
            return

        # Verificar se o bot foi mencionado
        if self.bot.user in message.mentions:
            logger.info(f"Menção detectada de {message.author} no canal {message.channel}.")

            # Substituir a menção para verificar o restante do texto
            mention_as_prefix = f"<@{self.bot.user.id}>"
            content_after_mention = message.content.replace(mention_as_prefix, "").strip()

            if content_after_mention:  # Processar comando após a menção
                logger.debug(f"Processando comando: {content_after_mention}")

                # Alterar o conteúdo da mensagem para processar o comando
                message.content = f"{self.bot.command_prefix}{content_after_mention}"

                try:
                    await self.bot.process_commands(message)
                except Exception as e:
                    logger.error(f"Erro ao processar comando: {e}")
            else:  # Apenas menção, sem texto adicional
                try:
                    bot_info = (
                        f"Olá, {message.author.mention}! 🤖\n"
                        f"Meu nome é **{self.bot.user.name}**.\n"
                        f"Você pode me mencionar seguido de um comando ou "
                        f"usar comandos configurados diretamente."
                    )
                    await message.channel.send(bot_info)
                    logger.info(f"Enviou informações do bot para {message.author}.")
                except discord.DiscordException as e:
                    logger.error(f"Erro ao responder menção: {e}")
            return

        # Ignorar todas as outras mensagens
        logger.debug(f"Ignorando mensagem: {message.content} de {message.author}")

async def setup(bot):
    """Função necessária para carregar o cog."""
    await bot.add_cog(OnMessageEvent(bot))
