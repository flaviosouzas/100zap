import discord
from discord.ext import commands
import requests
import random
import os

# === CONFIGURAÇÕES ===
TOKEN_DISCORD = 'MTQ0OTA5MjQzODA0NzMzMDQwOA.Gv_psJ.a_4Qw6K5Q5PY4nVjzG41g3pSvN_L2RTfiTcO2g' # Substitua pelo token do seu bot
API_URL = 'https://api.flaviosouza.cloud/chat/whatsappNumbers/botVivo'
API_KEY = '925de8b019ca6a020e92eb1b77fc3571'
ARQUIVO_HISTORICO = 'historico_numeros.txt'

# Configuração do Bot com permissão para ler mensagens (necessário para o comando !painel)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# === FUNÇÕES DE LÓGICA (O mesmo princípio anterior, adaptado) ===
def carregar_historico():
    if not os.path.exists(ARQUIVO_HISTORICO):
        return set()
    with open(ARQUIVO_HISTORICO, 'r') as f:
        return set(linha.strip() for linha in f)

def salvar_no_historico(novos_numeros):
    with open(ARQUIVO_HISTORICO, 'a') as f:
        for num in novos_numeros:
            f.write(f"{num}\n")

def gerar_lote_unicos(quantidade, historico):
    lote = []
    while len(lote) < quantidade:
        sufixo = ''.join([str(random.randint(0, 9)) for _ in range(8)])
        numero = f"55219{sufixo}"
        if numero not in historico and numero not in lote:
            lote.append(numero)
            historico.add(numero)
    return lote

def buscar_numeros_sem_whatsapp(numeros):
    headers = {'Content-Type': 'application/json', 'apikey': API_KEY}
    try:
        response = requests.post(API_URL, headers=headers, json={"numbers": numeros})
        response.raise_for_status()
        dados = response.json()
        # Retorna lista de números que NÃO existem no WhatsApp
        return [item['number'] for item in dados if item.get('exists') is False]
    except Exception as e:
        print(f"Erro na API: {e}")
        return []

# === INTERFACE DO DISCORD (Modals e Views) ===

# 2. O Formulário (Modal) que abre quando clica no botão
class QuantidadeModal(discord.ui.Modal, title='Gerador de Números'):
    quantidade_input = discord.ui.TextInput(
        label='Quantos números sem WhatsApp você quer?',
        placeholder='Ex: 10',
        required=True,
        max_length=3
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Avisa o Discord que estamos processando (evita dar erro de "interação falhou")
        await interaction.response.defer(ephemeral=True)
        
        try:
            qtd_desejada = int(self.quantidade_input.value)
            if qtd_desejada <= 0 or qtd_desejada > 50:
                await interaction.followup.send("Por favor, peça entre 1 e 50 números por vez para não travar a API.", ephemeral=True)
                return
        except ValueError:
            await interaction.followup.send("Por favor, digite um número válido.", ephemeral=True)
            return

        historico = carregar_historico()
        numeros_encontrados = []
        
        # Loop: continua gerando e testando até bater a meta exata que o usuário pediu
        while len(numeros_encontrados) < qtd_desejada:
            # Gera um lote um pouco maior que o necessário para compensar os que têm WhatsApp
            lote_gerado = gerar_lote_unicos(qtd_desejada + 5, historico)
            salvar_no_historico(lote_gerado)
            
            # Testa na API
            validos = buscar_numeros_sem_whatsapp(lote_gerado)
            
            # Adiciona os válidos na nossa lista final até bater a cota
            for num in validos:
                if len(numeros_encontrados) < qtd_desejada:
                    numeros_encontrados.append(num)

        # Monta a mensagem final com a lista de números
        mensagem_final = f"**Aqui estão seus {qtd_desejada} números sem WhatsApp (DDD 21):**\n```\n"
        mensagem_final += "\n".join(numeros_encontrados)
        mensagem_final += "\n```"

        await interaction.followup.send(mensagem_final, ephemeral=True)

# 1. O Botão (View) que fica fixo na sala
class PainelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Timeout=None para o botão nunca expirar

    @discord.ui.button(label="Gerar Números", style=discord.ButtonStyle.success, custom_id="btn_gerar_numeros")
    async def botao_gerar(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Abre o formulário (Modal) para o usuário digitar a quantidade
        await interaction.response.send_modal(QuantidadeModal())

# === COMANDOS DO BOT ===

@bot.event
async def on_ready():
    print(f'Bot {bot.user} conectado com sucesso!')
    # Registra a View para que o botão continue funcionando mesmo se o bot reiniciar
    bot.add_view(PainelView())

@bot.command()
async def painel(ctx):
    """
    Comando que você vai digitar na sala: !painel
    Ele envia a mensagem com o botão.
    """
    embed = discord.Embed(
        title="🤖 Painel Gerador de Números",
        description="Clique no botão abaixo para gerar números (DDD 21) que não possuem WhatsApp registrado.",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed, view=PainelView())

# Inicia o bot
bot.run(TOKEN_DISCORD)