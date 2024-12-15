from utils.database import get_emoji_from_table, get_fun_emoji, get_music_emoji, get_error_emoji, get_number_emoji, get_clan_management_emoji, get_server_staff_emoji
import logging
from utils.database import fetchone

logger = logging.getLogger(__name__)

async def setup(bot):
    """
    Configura o evento 'on_member_join'.
    """
    @bot.event
    async def on_member_join(member):
        """
        Evento acionado quando um novo membro entra no servidor.
        """
        logger.info(f"🎉 Novo membro entrou: {member} (ID: {member.id})")

        # Buscar ID do canal de boas-vindas na tabela 'canais'
        channel_data = fetchone("SELECT id FROM canais WHERE tipodecanal = ?", ("boas_vindas",))
        if not channel_data:
            logger.warning("⚠️ Nenhum canal de boas-vindas configurado na tabela 'canais'.")
            return

        # Obter o ID do canal e buscar o canal no Discord
        welcome_channel_id = channel_data[0]
        channel = bot.get_channel(int(welcome_channel_id))
        if not channel:
            logger.error(f"❌ Canal de boas-vindas com ID {welcome_channel_id} não encontrado.")
            return

        # Enviar mensagem de boas-vindas
        try:
            await channel.send(f"🎉 Bem-vindo(a), {member.mention}! Aproveite o servidor! 🌟")
            logger.info(f"✅ Mensagem de boas-vindas enviada para {member} no canal {channel.name} (ID: {channel.id})")
        except Exception as e:
            logger.error(f"❌ Erro ao enviar mensagem de boas-vindas para {member}: {e}")
