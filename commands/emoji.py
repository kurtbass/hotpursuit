from utils.database import get_emoji_from_table, get_fun_emoji, get_music_emoji, get_error_emoji, get_number_emoji, get_clan_management_emoji, get_server_staff_emoji
import discord
from discord.ext import commands
from utils.database import get_config
import io
import requests

class EmojiCommand(commands.Cog):
    """
    Comando para adicionar ou substituir emojis no servidor.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="emoji")
    async def emoji(self, ctx, action: str = None, name: str = None):
        """
        Adiciona ou substitui emojis no servidor.
        Uso: hp!emoji add <nome_do_emoji>
        """
        # Verifica se o comando está sendo usado no servidor correto
        allowed_server_id = 1315754008136384572
        if ctx.guild.id != allowed_server_id:
            await ctx.send("Este comando só pode ser usado no servidor autorizado.")
            return

        # Verifica se o usuário é o dono
        owner_id = int(get_config("DONO"))
        if ctx.author.id != owner_id:
            await ctx.send("Apenas o dono do bot pode usar este comando.")
            return

        # Valida a ação e o nome do emoji
        if action not in ["add", "replace"] or not name:
            await ctx.send("Uso inválido. Exemplo: `hp!emoji add <nome_do_emoji>`.")
            return

        # Verifica se há anexos ou links
        if ctx.message.attachments:
            file_url = ctx.message.attachments[0].url
        elif ctx.message.content.split()[-1].startswith("http"):
            file_url = ctx.message.content.split()[-1]
        else:
            await ctx.send("Nenhum anexo ou link foi encontrado. Por favor, envie a imagem do emoji.")
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
                await ctx.send(f"O emoji existente `{name}` foi removido.")

            # Adiciona o novo emoji
            is_gif = file_url.lower().endswith(".gif")
            new_emoji = await ctx.guild.create_custom_emoji(name=name, image=image_data.read(), roles=None)
            await ctx.send(f"Emoji {'animado' if is_gif else 'estático'} `{name}` adicionado com sucesso: {new_emoji}")

        except discord.Forbidden:
            await ctx.send("Permissões insuficientes para adicionar emojis ao servidor.")
        except requests.exceptions.RequestException as e:
            await ctx.send(f"Erro ao baixar a imagem: {e}")
        except discord.HTTPException as e:
            await ctx.send(f"Erro ao criar o emoji: {e}")
        except Exception as e:
            await ctx.send(f"Ocorreu um erro inesperado: {e}")

async def setup(bot):
    """
    Adiciona o cog EmojiCommand ao bot.
    """
    await bot.add_cog(EmojiCommand(bot))
