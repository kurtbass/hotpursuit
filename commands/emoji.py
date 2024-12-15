from utils.database import get_config
from utils.database import get_embed_color
import discord
from discord.ext import commands
import io
import requests
import logging

# Configuração de logs
logger = logging.getLogger(__name__)

class EmojiCommand(commands.Cog):
    """
    Comando para adicionar ou substituir emojis no servidor.
    """

    def __init__(self, bot):
        self.bot = bot
        self.allowed_server_id = int(get_config("EMOJI_SERVER_ID") or 0)
        self.owner_id = int(get_config("DONO") or 0)
        self.default_color = get_embed_color()
        self.lema, self.lema_img, _ = get_config("LEMA"), get_config("LEMA_IMG"), get_config("NOME_DO_CLA")

    @commands.command(name="emoji")
    async def emoji(self, ctx, action: str = None, name: str = None):
        """
        Adiciona ou substitui emojis no servidor.
        Uso: hp!emoji add <nome_do_emoji>
        """
        # Verifica se o comando está sendo usado no servidor autorizado
        if ctx.guild.id != self.allowed_server_id:
            embed = discord.Embed(
                title="🔒 Servidor Não Autorizado",
                description="Este comando só pode ser usado no servidor autorizado.",
                color=discord.Color.red()
            )
            embed.set_footer(text=self.lema, icon_url=self.lema_img)
            await ctx.send(embed=embed)
            return

        # Verifica se o usuário é o dono
        if ctx.author.id != self.owner_id:
            embed = discord.Embed(
                title="🔒 Permissão Negada",
                description="Apenas o dono do bot pode usar este comando.",
                color=discord.Color.red()
            )
            embed.set_footer(text=self.lema, icon_url=self.lema_img)
            await ctx.send(embed=embed)
            return

        # Valida a ação e o nome do emoji
        if action not in ["add", "replace"] or not name:
            embed = discord.Embed(
                title="❌ Uso Incorreto",
                description="Uso correto: `hp!emoji <add|replace> <nome_do_emoji>`.",
                color=discord.Color.red()
            )
            embed.set_footer(text=self.lema, icon_url=self.lema_img)
            await ctx.send(embed=embed)
            return

        # Verifica se há anexos ou links
        if ctx.message.attachments:
            file_url = ctx.message.attachments[0].url
        elif ctx.message.content.split()[-1].startswith("http"):
            file_url = ctx.message.content.split()[-1]
        else:
            embed = discord.Embed(
                title="❌ Nenhuma Imagem Encontrada",
                description="Por favor, envie a imagem do emoji como anexo ou forneça um link válido.",
                color=discord.Color.red()
            )
            embed.set_footer(text=self.lema, icon_url=self.lema_img)
            await ctx.send(embed=embed)
            return

        try:
            # Faz o download do arquivo de imagem
            response = requests.get(file_url)
            response.raise_for_status()
            image_data = io.BytesIO(response.content)

            # Remove o emoji existente com o mesmo nome (se existir)
            existing_emoji = discord.utils.get(ctx.guild.emojis, name=name)
            if existing_emoji:
                await existing_emoji.delete()
                logger.info(f"Emoji existente '{name}' foi removido por {ctx.author}.")
                await ctx.send(embed=discord.Embed(
                    description=f"Emoji existente `{name}` foi removido.",
                    color=self.default_color
                ).set_footer(text=self.lema, icon_url=self.lema_img))

            # Adiciona o novo emoji
            is_gif = file_url.lower().endswith(".gif")
            if is_gif and not ctx.guild.premium_tier:
                raise ValueError("Servidores sem boost não suportam emojis animados (GIFs).")

            new_emoji = await ctx.guild.create_custom_emoji(name=name, image=image_data.read(), roles=None)
            logger.info(f"Emoji '{name}' foi adicionado com sucesso por {ctx.author}.")
            embed = discord.Embed(
                title="✅ Emoji Adicionado",
                description=f"Emoji {'animado' if is_gif else 'estático'} `{name}` adicionado com sucesso: {new_emoji}",
                color=self.default_color
            )
            embed.set_footer(text=self.lema, icon_url=self.lema_img)
            await ctx.send(embed=embed)

        except discord.Forbidden:
            logger.error("Permissões insuficientes para adicionar emojis.")
            embed = discord.Embed(
                title="❌ Permissão Insuficiente",
                description="Não tenho permissões suficientes para adicionar emojis ao servidor.",
                color=discord.Color.red()
            )
            embed.set_footer(text=self.lema, icon_url=self.lema_img)
            await ctx.send(embed=embed)
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao baixar a imagem: {e}")
            embed = discord.Embed(
                title="❌ Erro ao Baixar Imagem",
                description=f"Não foi possível baixar a imagem do link fornecido. Erro: {e}",
                color=discord.Color.red()
            )
            embed.set_footer(text=self.lema, icon_url=self.lema_img)
            await ctx.send(embed=embed)
        except discord.HTTPException as e:
            logger.error(f"Erro ao criar o emoji: {e}")
            embed = discord.Embed(
                title="❌ Erro ao Criar Emoji",
                description=f"Ocorreu um erro ao criar o emoji. Detalhes: {e}",
                color=discord.Color.red()
            )
            embed.set_footer(text=self.lema, icon_url=self.lema_img)
            await ctx.send(embed=embed)
        except ValueError as e:
            logger.warning(f"Erro de validação: {e}")
            embed = discord.Embed(
                title="❌ Requisito Não Atendido",
                description=str(e),
                color=discord.Color.red()
            )
            embed.set_footer(text=self.lema, icon_url=self.lema_img)
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Erro inesperado: {e}")
            embed = discord.Embed(
                title="❌ Erro Inesperado",
                description="Ocorreu um erro inesperado ao tentar adicionar o emoji.",
                color=discord.Color.red()
            )
            embed.set_footer(text=self.lema, icon_url=self.lema_img)
            await ctx.send(embed=embed)


async def setup(bot):
    """
    Adiciona o cog EmojiCommand ao bot.
    """
    await bot.add_cog(EmojiCommand(bot))
