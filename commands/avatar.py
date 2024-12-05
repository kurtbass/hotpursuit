from utils.database import get_embed_color
import discord
from discord.ext import commands
import aiohttp
from PIL import Image, ImageSequence
from io import BytesIO
import logging
from utils.database import get_config

# Configuração de logs
logger = logging.getLogger(__name__)

class AvatarCommand(commands.Cog):
    """Comando para alterar o avatar do bot."""

    def __init__(self, bot):
        self.bot = bot
        self.dono_id = None
        self.subdono_id = None
        self.lema = "LEMA NÃO CARREGADO, PROCURE O PROGRAMADOR DO BOT"
        self.timeout = 60.0  # Timeout padrão para respostas

    @commands.Cog.listener()
    async def on_ready(self):
        """Carrega configurações do banco ao iniciar."""
        try:
            self.dono_id = int(get_config('DONO') or 0)
            self.subdono_id = int(get_config('SUBDONO') or 0)
            self.lema = get_config('LEMA') or self.lema
        except Exception as e:
            logger.error(f"Erro ao carregar configurações: {e}")

    @commands.command(name="avatar")
    async def avatar(self, ctx):
        """Solicita imagem e troca o avatar do bot."""
        # Verificar permissões
        if ctx.author.id not in [self.dono_id, self.subdono_id]:
            embed = discord.Embed(
                title="❌ Permissão Negada",
                description="Você não tem permissão para alterar o avatar do bot.",
                color=get_embed_color()
            )
            embed.set_footer(text=self.lema)
            await ctx.send(embed=embed)
            return

        # Solicitar entrada do usuário
        embed = discord.Embed(
            title="🖼️ Atualizar Avatar",
            description="Envie o arquivo da imagem ou um link válido.",
            color=get_embed_color()
        )
        embed.set_footer(text=self.lema)
        await ctx.send(embed=embed)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            # Esperar a mensagem do usuário
            message = await self.bot.wait_for("message", check=check, timeout=self.timeout)

            # Processar a entrada do usuário
            if message.attachments:
                # Usuário enviou uma imagem como arquivo
                file = message.attachments[0]
                image_data = await file.read()
            elif message.content.startswith('http'):
                # Usuário forneceu um link
                image_data = await self.download_image(message.content)
            else:
                raise ValueError("Entrada inválida. Nenhum arquivo ou link válido fornecido.")

            # Processar e definir o avatar
            buffer = await self.process_image(image_data)
            await self.bot.user.edit(avatar=buffer.read())

            embed = discord.Embed(
                title="✅ Avatar Atualizado",
                description="A imagem de perfil do bot foi alterada com sucesso!",
                color=get_embed_color()
            )
            embed.set_footer(text=self.lema)
            await ctx.send(embed=embed)

        except discord.HTTPException:
            embed = discord.Embed(
                title="❌ Erro no Avatar",
                description="Erro ao alterar o avatar. Certifique-se de que a imagem atende aos requisitos de tamanho e formato.",
                color=get_embed_color()
            )
            embed.set_footer(text=self.lema)
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Erro inesperado ao alterar o avatar: {e}")
            embed = discord.Embed(
                title="❌ Erro Inesperado",
                description="Ocorreu um erro inesperado ao tentar alterar o avatar. Tente novamente mais tarde.",
                color=get_embed_color()
            )
            embed.set_footer(text=self.lema)
            await ctx.send(embed=embed)

    async def download_image(self, url):
        """Baixa uma imagem de uma URL."""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise ValueError("Não foi possível baixar a imagem. Verifique o link fornecido.")
                return await response.read()

    async def process_image(self, image_data):
        """Processa uma imagem, incluindo extração do primeiro frame de GIFs."""
        image = Image.open(BytesIO(image_data)).convert('RGB')

        # Verificar se a imagem é um GIF (multiframe)
        if getattr(image, "is_animated", False):
            logger.info("Imagem é um GIF. Extraindo o primeiro frame.")
            image = next(ImageSequence.Iterator(image))  # Extrair o primeiro frame

        # Redimensionar se necessário
        max_size = 1024  # Tamanho máximo permitido
        if image.width > max_size or image.height > max_size:
            image.thumbnail((max_size, max_size))  # Redimensionar imagem

        buffer = BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer


async def setup(bot):
    """Carrega o comando no bot."""
    await bot.add_cog(AvatarCommand(bot))
