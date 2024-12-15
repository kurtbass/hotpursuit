from utils.database import get_embed_color
import discord
import asyncio
import logging

logger = logging.getLogger(__name__)

class PerguntasHelper:
    """
    Auxiliar para lidar com perguntas, confirmações e coleta de informações
    para o comando de evento.
    """

    def __init__(self, bot, lema: str):
        """
        Inicializa o PerguntasHelper com o bot e o lema padrão.

        :param bot: Instância do bot do Discord.
        :param lema: Mensagem padrão para o rodapé dos embeds.
        """
        self.bot = bot
        self.lema = lema

    def create_embed(self, title: str, description: str, color=get_embed_color(), image_url=None) -> discord.Embed:
        """
        Cria um embed padronizado com título, descrição, cor e uma imagem opcional.

        :param title: Título do embed.
        :param description: Conteúdo do embed.
        :param color: Cor do embed (padrão: configurada ou aleatória).
        :param image_url: URL da imagem opcional.
        :return: Um objeto discord.Embed.
        """
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text=self.lema)
        if image_url:
            embed.set_image(url=image_url)
        return embed

    async def ask_question(self, ctx, question: str, timeout: int = 300) -> str | None:
        """
        Faz uma pergunta ao usuário e aguarda uma resposta.

        :param ctx: Contexto do comando.
        :param question: Texto da pergunta.
        :param timeout: Tempo limite para responder (padrão: 300 segundos).
        :return: Resposta do usuário ou None em caso de timeout.
        """
        embed = self.create_embed("Pergunta", question)
        await ctx.send(embed=embed)

        try:
            response = await self.bot.wait_for(
                "message",
                timeout=timeout,
                check=lambda m: m.author == ctx.author and m.channel == ctx.channel
            )
            logger.info(f"Resposta recebida: {response.content}")
            return response.content.strip()
        except asyncio.TimeoutError:
            await ctx.send(embed=self.create_embed("Tempo Esgotado", "O comando foi cancelado.", discord.Color.red()))
            logger.warning("Tempo esgotado para resposta do usuário.")
            return None

    async def confirm_action(self, ctx, question: str) -> bool:
        """
        Confirma uma ação com "Sim" ou "Não".

        :param ctx: Contexto do comando.
        :param question: Pergunta de confirmação.
        :return: True se o usuário confirmar, False caso contrário.
        """
        response = await self.ask_question(ctx, f"{question} (Responda com 'Sim' ou 'Não')")
        if response and response.lower() in ["sim", "s"]:
            logger.info("Usuário confirmou a ação.")
            return True
        logger.info("Usuário negou ou não respondeu corretamente.")
        return False

    async def ask_image(self, ctx) -> str | None:
        """
        Solicita ao usuário um link ou anexo de imagem.

        :param ctx: Contexto do comando.
        :return: URL da imagem fornecida ou None em caso de timeout.
        """
        embed = self.create_embed("Imagem", "Envie o link ou anexe a imagem.")
        await ctx.send(embed=embed)

        try:
            response = await self.bot.wait_for(
                "message",
                timeout=300,
                check=lambda m: m.author == ctx.author and m.channel == ctx.channel
            )
            if response.attachments:
                logger.info("Imagem enviada como anexo.")
                return response.attachments[0].url
            if response.content.startswith("http"):
                logger.info("Imagem enviada como link.")
                return response.content
        except asyncio.TimeoutError:
            await ctx.send(embed=self.create_embed("Tempo Esgotado", "O comando foi cancelado.", discord.Color.red()))
            logger.warning("Tempo esgotado para envio de imagem.")
            return None

    async def ask_color(self, ctx) -> int:
        """
        Solicita ao usuário uma cor em formato hexadecimal.

        :param ctx: Contexto do comando.
        :return: Cor em formato inteiro ou cor padrão (get_embed_color()) em caso de erro.
        """
        while True:
            response = await self.ask_question(ctx, "Digite o código hexadecimal da cor (Ex: FF8000 ou #FF8000):")
            if not response:
                logger.info("Nenhuma resposta fornecida. Usando cor padrão.")
                return get_embed_color()

            try:
                color = int(response.lstrip("#"), 16)
                logger.info(f"Cor válida fornecida: {color}")
                return color
            except ValueError:
                await ctx.send(embed=self.create_embed(
                    "Erro", "⚠️ Código de cor inválido. Certifique-se de usar o formato hexadecimal (Ex: FF8000).", discord.Color.red()
                ))

    async def collect_event_details(self, ctx) -> dict | None:
        """
        Coleta todas as informações do evento por meio de interações com o usuário.

        :param ctx: Contexto do comando.
        :return: Dicionário contendo as informações do evento ou None se algo for cancelado.
        """
        event_data = {}

        # Coletar informações básicas
        questions = {
            "titulo": "Qual o título do evento?",
            "descricao": "Qual a descrição do evento?",
            "data": "Qual a data do evento? (Exemplo: 15/12/2023)",
            "horario": "Qual o horário do evento? (Exemplo: 14h00)"
        }

        for key, question in questions.items():
            response = await self.ask_question(ctx, question)
            if not response:
                logger.info(f"Coleta de '{key}' cancelada ou tempo esgotado.")
                return None
            event_data[key] = response

        # Coletar banner
        if await self.confirm_action(ctx, "Deseja incluir um banner na mensagem?"):
            event_data["banner_url"] = await self.ask_image(ctx)
        else:
            event_data["banner_url"] = None

        # Coletar cor do embed
        if await self.confirm_action(ctx, "Deseja mudar a cor da embed?"):
            event_data["cor"] = await self.ask_color(ctx)
        else:
            event_data["cor"] = get_embed_color()

        return event_data
