from utils.database import get_embed_color
from utils.config import get_lema
import discord
from discord.ext import commands
import aiohttp
from PIL import Image, ImageSequence
from io import BytesIO
import logging

# Configuração de logs
logger = logging.getLogger(__name__)

class AvatarCommand(commands.Cog):
    """Comando para alterar o avatar do bot."""

    def __init__(self, bot):
        self.bot = bot
        self.dono_id = None
        self.subdono_id = None
        self.lema, self.lema_img, self.nome_cla = get_lema()
        self.timeout = 60.0  # Timeout padrão para respostas

    @commands.Cog.listener()
    async def on_ready(self):
        """Carrega configurações do banco ao iniciar."""
        try:
            from utils.config import get_config
            self.dono_id = int(get_config('DONO') or 0)
            self.subdono_id = int(get_config('SUBDONO') or 0)
            self.lema, self.lema_img, self.nome_cla = get_lema()
            logger.info("Configurações de dono, lema e clã carregadas com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao carregar configurações iniciais: {e}")

    @commands.command(name="avatar")
    async def avatar(self, ctx):
        """
        Comando que solicita uma imagem ou URL e altera o avatar do bot.
        """
        logger.info(f"Usuário {ctx.author} iniciou o comando de alteração de avatar.")

        # Verificar permissões
        if ctx.author.id not in [self.dono_id, self.subdono_id]:
            await self.send_embed(
                ctx, "❌ Permissão Negada", "Você não tem permissão para alterar o avatar do bot."
            )
            return

        # Solicitar entrada do usuário
        await self.send_embed(
            ctx, "🖼️ Atualizar Avatar", "Envie o arquivo da imagem ou um link válido."
        )

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            # Esperar a mensagem do usuário
            message = await self.bot.wait_for("message", check=check, timeout=self.timeout)
            logger.info(f"Mensagem recebida de {ctx.author}: {message.content}")

            # Processar a entrada do usuário
            image_data = await self.get_image_data(message)

            # Processar e definir o avatar
            buffer = await self.process_image(image_data)
            await self.bot.user.edit(avatar=buffer.read())

            await self.send_embed(
                ctx, "✅ Avatar Atualizado", "A imagem de perfil do bot foi alterada com sucesso!"
            )
            logger.info("Avatar atualizado com sucesso.")

        except discord.HTTPException as e:
            logger.error(f"Erro do Discord ao alterar o avatar: {e}")
            await self.send_embed(
                ctx,
                "❌ Erro no Avatar",
                "Erro ao alterar o avatar. Certifique-se de que a imagem atende aos requisitos de tamanho e formato.",
            )
        except Exception as e:
            logger.error(f"Erro inesperado ao alterar o avatar: {e}")
            await self.send_embed(
                ctx,
                "❌ Erro Inesperado",
                "Ocorreu um erro inesperado ao tentar alterar o avatar. Tente novamente mais tarde.",
            )

    async def get_image_data(self, message):
        """
        Processa a entrada do usuário para obter os dados de uma imagem.
        """
        if message.attachments:
            logger.info("Imagem recebida como anexo.")
            file = message.attachments[0]
            return await file.read()
        elif message.content.startswith('http'):
            logger.info("Imagem recebida como URL.")
            return await self.download_image(message.content)
        else:
            logger.warning("Entrada inválida fornecida.")
            raise ValueError("Entrada inválida. Nenhum arquivo ou link válido fornecido.")

    async def download_image(self, url):
        """
        Baixa uma imagem de uma URL fornecida pelo usuário.
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"Não foi possível baixar a imagem. Código HTTP: {response.status}")
                    raise ValueError("Não foi possível baixar a imagem. Verifique o link fornecido.")
                logger.info("Imagem baixada com sucesso.")
                return await response.read()

    async def process_image(self, image_data):
        """
        Processa uma imagem, incluindo extração do primeiro frame de GIFs.
        """
        try:
            image = Image.open(BytesIO(image_data)).convert('RGB')

            # Verificar se a imagem é um GIF (multiframe)
            if getattr(image, "is_animated", False):
                logger.info("Imagem é um GIF. Extraindo o primeiro frame.")
                image = next(ImageSequence.Iterator(image))

            # Redimensionar se necessário
            max_size = 1024  # Tamanho máximo permitido
            if image.width > max_size or image.height > max_size:
                image.thumbnail((max_size, max_size))
                logger.info(f"Imagem redimensionada para {max_size}x{max_size}.")

            buffer = BytesIO()
            image.save(buffer, format='PNG')
            buffer.seek(0)
            return buffer
        except Exception as e:
            logger.error(f"Erro ao processar a imagem: {e}")
            raise ValueError("Erro ao processar a imagem. Certifique-se de que o formato é compatível.")

    async def send_embed(self, ctx, title, description):
        """
        Envia um embed para o usuário, incluindo o lema e, se disponível, a imagem do lema no rodapé.
        """
        embed = discord.Embed(
            title=title,
            description=description,
            color=get_embed_color()
        )
        footer_text = self.lema
        if self.lema_img:
            footer_text += f" | {self.lema_img}"
        embed.set_footer(text=footer_text)
        await ctx.send(embed=embed)


async def setup(bot):
    """Carrega o comando no bot."""
    await bot.add_cog(AvatarCommand(bot))
