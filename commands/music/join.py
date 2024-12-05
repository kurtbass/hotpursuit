import discord
from discord.ext import commands

class JoinCommand(commands.Cog):
    """
    Comando para fazer o bot entrar em um canal de voz.
    """

    def __init__(self, bot):
        self.bot = bot

    def create_embed(self, title, description, color=0xFF8000):
        """
        Cria um embed padronizado com título, descrição e cor.
        """
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text=get_config("LEMA"))
        return embed

    @commands.command(name="join", aliases=["entrar"])
    async def join(self, ctx):
        """
        Faz o bot entrar no canal de voz do usuário.
        """
        if ctx.author.voice is None:
            await ctx.send(embed=self.create_embed(
                "Erro",
                "⚠️ Você precisa estar em um canal de voz para usar este comando.",
                0xFF0000
            ))
            return

        user_channel = ctx.author.voice.channel

        if self.bot.voice_clients and any(vc.channel != user_channel for vc in self.bot.voice_clients):
            current_channel = [vc.channel.name for vc in self.bot.voice_clients if vc.is_connected()][0]
            await ctx.send(embed=self.create_embed(
                "Erro",
                f"⚠️ Já estou conectado no canal **{current_channel}**.",
                0xFF0000
            ))
            return

        # Conecta ao canal do usuário
        await user_channel.connect()
        await ctx.send(embed=self.create_embed(
            "Conectado",
            f"✅ Entrei no canal **{user_channel.name}**.",
            0xFF8000
        ))


async def setup(bot):
    """
    Adiciona o cog ao bot.

    :param bot: O bot do Discord.
    """
    await bot.add_cog(JoinCommand(bot))
