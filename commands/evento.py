from utils.database import get_embed_color
import discord
from discord.ext import commands
import logging
from utils.database import get_config
from commands.evento.perguntas import PerguntasHelper  # type: ignore
from commands.evento.permissoes import PermissoesHelper  # type: ignore
from commands.evento.logicadeenvio import LogicaEnvioHelper  # type: ignore

# Configuração de logs
logger = logging.getLogger(__name__)

class Evento(commands.Cog):
    """Comando para criar e divulgar eventos no servidor."""

    def __init__(self, bot):
        self.bot = bot
        self.lema = get_config("LEMA") or "LEMA NÃO CARREGADO, PROCURE O PROGRAMADOR DO BOT"
        self.tag_staff = self.safe_get_config("TAG_STAFF", is_int=True)
        self.tag_membro = self.safe_get_config("TAG_MEMBRO", is_int=True)
        self.em_execucao = False

        # Inicializar os auxiliares
        self.perguntas_helper = PerguntasHelper(bot, self.lema)
        self.permissoes_helper = PermissoesHelper(bot, self.tag_staff, self.tag_membro, self.lema)
        self.logicadeenvio_helper = LogicaEnvioHelper(bot, self.lema)

    def safe_get_config(self, key, is_int=False):
        """
        Obtém uma configuração do banco de forma segura.

        :param key: Nome da chave a ser buscada.
        :param is_int: Converte o valor para int, se necessário.
        :return: Valor da configuração ou None.
        """
        try:
            value = get_config(key)
            if not value:
                logger.warning(f"Configuração '{key}' não encontrada no banco.")
                return None
            return int(value) if is_int else value
        except Exception as e:
            logger.error(f"Erro ao carregar configuração '{key}': {e}")
            return None

    @commands.command(name="evento")
    async def evento(self, ctx):
        """Comando principal para criar e enviar um evento."""
        if self.em_execucao:
            await ctx.send(embed=self.perguntas_helper.create_embed(
                "Erro", "⚠️ Já existe um evento em execução. Aguarde até que finalize.", get_embed_color()
            ))
            return

        if not await self.permissoes_helper.check_permissions(ctx):
            return

        self.em_execucao = True
        try:
            # Coletar informações do evento
            event_data = await self.perguntas_helper.collect_event_details(ctx)
            if not event_data:
                return  # Comando cancelado ou falhou

            # Criar embed do evento
            embed = self.perguntas_helper.create_embed(
                title=f"📢 {event_data['titulo']}",
                description=f"{event_data['descricao']}\n\n📅 **Data:** {event_data['data']}\n⏰ **Horário:** {event_data['horario']}",
                color=event_data["cor"],
                image_url=event_data["banner_url"]
            )

            # Enviar preview do embed
            await ctx.send(embed=embed)

            # Confirmar envio
            if not await self.perguntas_helper.confirm_action(ctx, "A mensagem está correta?"):
                await ctx.send(embed=self.perguntas_helper.create_embed(
                    "Cancelado", "⚠️ Cancelando o comando. Corrija as informações e tente novamente.", get_embed_color()
                ))
                return

            # Selecionar destinatários
            destinatarios = await self.logicadeenvio_helper.select_recipients(ctx, self.tag_staff, self.tag_membro)
            if not destinatarios:
                await ctx.send(embed=self.perguntas_helper.create_embed(
                    "Cancelado", "⚠️ Nenhum destinatário foi selecionado. Comando cancelado.", get_embed_color()
                ))
                return

            # Enviar evento
            enviadas, erros = await self.logicadeenvio_helper.send_event(destinatarios, embed)
            await ctx.send(embed=self.perguntas_helper.create_embed(
                "Sucesso", f"✅ Evento enviado para {enviadas} membros. Erros: {erros}.", get_embed_color()
            ))
        finally:
            self.em_execucao = False


async def setup(bot):
    """Carrega o cog no bot."""
    await bot.add_cog(Evento(bot))
