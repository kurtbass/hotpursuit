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
        logger.info(f"{member} entrou no servidor.")
        
        # Buscar ID do canal de boas-vindas na tabela 'canais'
        channel_data = fetchone("SELECT id FROM canais WHERE tipodecanal = 'boas_vindas'")
        if not channel_data:
            logger.warning("Nenhum canal de boas-vindas configurado na tabela 'canais'.")
            return

        # Obter o ID do canal e buscar o canal no Discord
        welcome_channel_id = channel_data[0]
        channel = bot.get_channel(int(welcome_channel_id))
        if not channel:
            logger.error(f"Canal de boas-vindas com ID {welcome_channel_id} não encontrado.")
            return

        # Enviar mensagem de boas-vindas
        await channel.send(f"Bem-vindo(a), {member.mention}! Aproveite o servidor! 🎉")
