import asyncio
import discord
from discord.ext import commands
from utils.database import execute_query, fetchone, get_config, get_embed_color


class SampCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def update_listener_status(self, status):
        """
        Atualiza o status do `SampListener` e força uma atualização inicial.
        """
        listener = self.bot.get_cog("SampListener")
        if listener:
            listener.status = status
            print(f"[SAMP COMMAND] Listener atualizado para: {status}")
            if status == "on":
                await self.update_channels(listener)  # Atualiza canais ao ligar
        else:
            print("[SAMP COMMAND] SampListener não encontrado.")

    async def update_channels(self, listener):
        """
        Atualiza os canais com informações do SampListener.
        """
        try:
            server_info = listener.get_server_info()
            player_info = listener.get_player_info()

            if not server_info:
                print("[SAMP COMMAND] Nenhuma informação do servidor disponível.")
                return

            # Obter IDs dos canais
            status_channel_id = fetchone("SELECT id FROM canais WHERE tipodecanal = ?", ("samp_status",))
            players_channel_id = fetchone("SELECT id FROM canais WHERE tipodecanal = ?", ("samp_jogadores",))

            if not (status_channel_id and players_channel_id):
                print("[SAMP COMMAND] Canais necessários não encontrados no banco de dados.")
                return

            # Obter os canais
            status_channel = self.bot.get_channel(status_channel_id[0])
            players_channel = self.bot.get_channel(players_channel_id[0])

            if not (status_channel and players_channel):
                print("[SAMP COMMAND] Um ou mais canais não foram encontrados no servidor.")
                return

            # Atualizar os canais
            status = "🟢 Online" if server_info else "🔴 Offline"
            await status_channel.edit(name=f"Status: {status}")
            await asyncio.sleep(2)  # Pausa para evitar rate limits
            await players_channel.edit(
                name=f"Jogadores: {player_info.get('online', 0)}/{player_info.get('max', 0)}"
            )
            print("[SAMP COMMAND] Canais atualizados com sucesso.")
        except Exception as e:
            print(f"[SAMP COMMAND] Erro ao atualizar canais: {e}")

    @commands.command(name="samp")
    async def samp_command(self, ctx):
        """
        Comando principal para gerenciar o SAMP.
        Apenas o dono pode executar este comando.
        """
        lema = get_config("LEMA") or "Bot oficial"

        # Verificar se o usuário é o dono
        dono_id = get_config("DONO")
        if not dono_id or str(ctx.author.id) != dono_id:
            embed = discord.Embed(
                title="🔒 Acesso Negado",
                description="Você não tem permissão para usar este comando.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=lema)
            await ctx.send(embed=embed)
            return

        # Enviar as opções
        embed = discord.Embed(
            title="⚙️ Gerenciar SA-MP",
            description="1️⃣ **Criar categoria**\n2️⃣ **Apagar categoria**",
            color=get_embed_color()
        )
        embed.set_footer(text=lema)
        await ctx.send(embed=embed)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            # Esperar a resposta do usuário
            msg = await self.bot.wait_for("message", check=check, timeout=30.0)
            option = int(msg.content)
        except (ValueError, asyncio.TimeoutError):
            embed = discord.Embed(
                title="❌ Comando Cancelado",
                description="Entrada inválida ou tempo esgotado.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=lema)
            await ctx.send(embed=embed)
            return

        if option == 1:
            await self.create_category(ctx)
        elif option == 2:
            await self.delete_category(ctx)
        else:
            embed = discord.Embed(
                title="❌ Opção Inválida",
                description="Você digitou uma opção inválida. Tente novamente.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=lema)
            await ctx.send(embed=embed)

    async def create_category(self, ctx):
        """
        Cria a categoria e canais relacionados ao servidor SA-MP ou sincroniza os IDs se já existir.
        """
        lema = get_config("LEMA") or "Bot oficial"
        category_name = "Brasil Cidade Vida Real"

        # Consultar informações do SampListener
        listener = self.bot.get_cog("SampListener")
        if not listener:
            embed = discord.Embed(
                title="❌ Listener Indisponível",
                description="O Listener não está disponível no momento.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=lema)
            await ctx.send(embed=embed)
            return

        server_info = listener.get_server_info()
        player_info = listener.get_player_info()
        status = "🟢 Online" if server_info else "🔴 Offline"
        players_name = f"Jogadores: {player_info.get('online', 0)}/{player_info.get('max', 0)}"

        existing_category = discord.utils.get(ctx.guild.categories, name=category_name)
        if existing_category:
            await ctx.send("🔄 A categoria já existe. Sincronizando IDs...")
            for channel in existing_category.channels:
                if "Status" in channel.name:
                    execute_query(
                        "UPDATE canais SET id = ? WHERE tipodecanal = ?", (channel.id, "samp_status")
                    )
                elif "Jogadores" in channel.name:
                    execute_query(
                        "UPDATE canais SET id = ? WHERE tipodecanal = ?", (channel.id, "samp_jogadores")
                    )
            execute_query(
                "UPDATE canais SET id = ? WHERE tipodecanal = ?", (existing_category.id, "samp_categoria")
            )
            await self.update_listener_status("on")
            embed = discord.Embed(
                title="✅ Categoria Sincronizada",
                description="Os IDs foram sincronizados com sucesso.",
                color=get_embed_color()
            )
            embed.set_footer(text=lema)
            await ctx.send(embed=embed)
            return

        try:
            category = await ctx.guild.create_category(category_name)
            await category.edit(position=0)

            status_channel = await category.create_voice_channel(f"Status: {status}")
            players_channel = await category.create_voice_channel(players_name)

            execute_query(
                "INSERT INTO canais (tipodecanal, id) VALUES (?, ?) ON CONFLICT(tipodecanal) DO UPDATE SET id=excluded.id",
                ("samp_status", status_channel.id)
            )
            execute_query(
                "INSERT INTO canais (tipodecanal, id) VALUES (?, ?) ON CONFLICT(tipodecanal) DO UPDATE SET id=excluded.id",
                ("samp_jogadores", players_channel.id)
            )
            execute_query(
                "INSERT INTO canais (tipodecanal, id) VALUES (?, ?) ON CONFLICT(tipodecanal) DO UPDATE SET id=excluded.id",
                ("samp_categoria", category.id)
            )

            await self.update_listener_status("on")
            embed = discord.Embed(
                title="✅ Categoria Criada",
                description=f"A categoria '{category_name}' foi criada com sucesso.",
                color=get_embed_color()
            )
            embed.set_footer(text=lema)
            await ctx.send(embed=embed)
        except Exception as e:
            print(f"[SAMP COMMAND] Erro ao criar a categoria: {e}")
            embed = discord.Embed(
                title="❌ Erro",
                description="Ocorreu um erro ao criar a categoria. Verifique os logs para mais detalhes.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=lema)
            await ctx.send(embed=embed)

    async def delete_category(self, ctx):
        """
        Remove a categoria e os canais associados.
        """
        lema = get_config("LEMA") or "Bot oficial"
        try:
            category_id = fetchone("SELECT id FROM canais WHERE tipodecanal = ?", ("samp_categoria",))
            if not category_id:
                embed = discord.Embed(
                    title="❌ Categoria Não Encontrada",
                    description="Nenhuma categoria foi registrada no banco de dados.",
                    color=discord.Colour.red()
                )
                embed.set_footer(text=lema)
                await ctx.send(embed=embed)
                return

            category = discord.utils.get(ctx.guild.categories, id=category_id[0])
            if category:
                for channel in category.channels:
                    await channel.delete()
                await category.delete()

            execute_query("UPDATE canais SET id = NULL WHERE tipodecanal LIKE 'samp_%'")
            await self.update_listener_status("off")
            embed = discord.Embed(
                title="✅ Categoria Removida",
                description="A categoria e os canais foram removidos com sucesso.",
                color=get_embed_color()
            )
            embed.set_footer(text=lema)
            await ctx.send(embed=embed)
        except Exception as e:
            print(f"[SAMP COMMAND] Erro ao remover a categoria: {e}")
            embed = discord.Embed(
                title="❌ Erro",
                description="Ocorreu um erro ao remover a categoria. Verifique os logs para mais detalhes.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=lema)
            await ctx.send(embed=embed)


# Adicionar o cog ao bot
async def setup(bot):
    await bot.add_cog(SampCommand(bot))
