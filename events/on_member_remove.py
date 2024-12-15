from utils.database import get_emoji_from_table, get_fun_emoji, get_music_emoji, get_error_emoji, get_number_emoji, get_clan_management_emoji, get_server_staff_emoji
import logging
from utils.database import fetchone

logger = logging.getLogger(__name__)

async def setup(bot):
    """
    Configura o evento 'on_member_remove'.
    """
    @bot.event
    async def on_member_remove(member):
        """
        Evento acionado quando um membro sai do servidor.
        """
        logger.info(f"❌ Membro saiu: {member} (ID: {member.id})")

        # Buscar ID do canal de saída na tabela 'canais'
        channel_data = fetchone("SELECT id FROM canais WHERE tipodecanal = ?", ("saida",))
        if not channel_data:
            logger.warning("⚠️ Nenhum canal de saída configurado na tabela 'canais'.")
            return

        # Obter o ID do canal e buscar o canal no Discord
        farewell_channel_id = channel_data[0]
        channel = bot.get_channel(int(farewell_channel_id))
        if not channel:
            logger.error(f"❌ Canal de saída com ID {farewell_channel_id} não encontrado.")
            return

        # Enviar mensagem de saída
        try:
            await channel.send(f"😢 {member.mention} deixou o servidor. Sentiremos sua falta.")
            logger.info(f"✅ Mensagem de saída enviada para {member} no canal {channel.name} (ID: {channel.id})")
        except Exception as e:
            logger.error(f"❌ Erro ao enviar mensagem de saída para {member}: {e}")
