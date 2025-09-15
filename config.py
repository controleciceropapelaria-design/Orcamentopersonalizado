# orcamento_pro/config.py
"""
Módulo de configuração centralizado para a aplicação Orçamento Pro.
Armazena constantes, caminhos de arquivo, URLs e mapeamentos para
evitar "valores mágicos" espalhados pelo código.
"""
# ================== CAMINHOS DOS ARQUIVOS LOCAIS ==================
BASE_URL_GITHUB = "https://raw.githubusercontent.com/controleciceropapelaria-design/Orcamentoperosnalizado/main/"
USERS_FILE = "https://raw.githubusercontent.com/controleciceropapelaria-design/Orcamentoperosnalizado/refs/heads/main/data/usuarios.csv"
CLIENTES_FILE = "https://raw.githubusercontent.com/controleciceropapelaria-design/Orcamentoperosnalizado/main/data/clientes.csv"
ORCAMENTOS_FILE = "https://raw.githubusercontent.com/controleciceropapelaria-design/Orcamentoperosnalizado/main/data/orcamentos_novo.csv"
TEMPLATES_FILE = "https://raw.githubusercontent.com/controleciceropapelaria-design/Orcamentoperosnalizado/refs/heads/main/data/templates.csv"

# ================== COLUNAS DOS ARQUIVOS CSV ==================
# Colunas atualizadas para incluir o sistema de aprovação de usuários
COLUNAS_USUARIOS = ["usuario", "senha_hashed", "nome_completo", "role", "status"]
COLUNAS_CLIENTES = [
    "Nome", "Razao Social", "CNPJ", "Endereco", "CEP", "Cidade", "UF",
    "Inscricao Estadual", "Email", "Telefone", "Forma de Pagamento", "Contato", "Status"
]
COLUNAS_ORCAMENTOS = ["ID", "OrcamentoGroupID", "Usuario", "NomeOrcamentista", "Cliente", "Produto", "Quantidade", 
                      "CustoBase", "ComissaoPct", "Markup", "PrecoVenda", "AjustesJSON", 
                      "SelecoesJSON", "StatusOrcamento", "Data", "PropostaPDF"]
COLUNAS_TEMPLATES = ["NomeTemplate", "SelecoesJSON"]

# ================== URLs DOS DADOS EXTERNOS (VERSÃO CORRIGIDA E SIMPLIFICADA) ==================
# Unificamos para uma única fonte de dados, o repositório principal do projeto.
BASE_URL_GITHUB = "https://raw.githubusercontent.com/controleciceropapelaria-design/Orcamentoperosnalizado/main/"

# Todas as URLs agora são construídas a partir da mesma base.
URL_COMPRAS = f"{BASE_URL_GITHUB}compradepapel.csv"
URL_USO_PAPEL_MIOLO = f"{BASE_URL_GITHUB}usodepapelmiolos.csv"
URL_USO_PAPEL_BOLSA = f"{BASE_URL_GITHUB}usodepapelbolsa.csv"
URL_USO_PAPEL_DIVISORIA = f"{BASE_URL_GITHUB}usodepapeldivisoria.csv"
URL_USO_PAPEL_ADESIVO = f"{BASE_URL_GITHUB}usodepapeladesivo.csv"
URL_GUARDA_FORRO = f"{BASE_URL_GITHUB}df_guarda_forro.csv"
URL_GUARDA_VERSO = f"{BASE_URL_GITHUB}df_guarda_verso.csv"
URL_COMPRA_DIRETA = f"{BASE_URL_GITHUB}compradiretav2.csv"
URL_TABELA_WIREO = f"{BASE_URL_GITHUB}tabelawireo.csv"
# URL para a nova tabela de Mão de Obra e Gastos Gerais de Fabricação
URL_MOD_GGF = f"{BASE_URL_GITHUB}df_MOD_GGF.csv"

# ================== MAPEAMENTOS E LISTAS DE PRODUTOS ==================
PRODUTOS_BASE = [
    "CADERNETA 9X13 - POLICROMIA", "CADERNETA 14X21 - POLICROMIA", "REVISTA 9X13 - POLICROMIA",
    "REVISTA 14X21 - POLICROMIA", "REVISTA 19X25 - POLICROMIA", "PLANNER WIRE-O A5 - POLICROMIA",
    "FICHARIO A5 - POLICROMIA", "FICHARIO 17X24 - POLICROMIA", "CADERNO WIRE-O 17X24 - POLICROMIA",
    "CADERNO WIRE-O 20X28 - POLICROMIA", "BLOCO WIRE-O 12X20 - POLICROMIA",
    "CADERNO ORGANIZADOR A5 - POLICROMIA", "CADERNO ORGANIZADOR 17X24 - POLICROMIA", "FICHARIO A6 - POLICROMIA",
    "CADERNETA 9X13 - COURO SINTÉTICO", "CADERNETA 14X21 - COURO SINTÉTICO", "PLANNER WIRE-O A5 - COURO SINTÉTICO",
    "FICHARIO A5 - COURO SINTÉTICO", "FICHARIO 17X24 - COURO SINTÉTICO", "CADERNO WIRE-O 17X24 - COURO SINTÉTICO",
    "CADERNO WIRE-O 20X28 - COURO SINTÉTICO", "CADERNO ORGANIZADOR A5 - COURO SINTÉTICO",
    "CADERNO ORGANIZADOR 17X24 - COURO SINTÉTICO", "FICHARIO A6 - COURO SINTÉTICO"
]

# O mapeamento agora também usa a variável única, tornando o código mais limpo.
CSV_MAP_IMPRESSAO = {
    'CADERNETA 9X13': f'{BASE_URL_GITHUB}tabela_impressao_9x13.csv',
    'CADERNETA 14X21': f'{BASE_URL_GITHUB}tabela_impressao_14x21.csv',
    'REVISTA 9X13': f'{BASE_URL_GITHUB}tabela_impressao_9x13.csv',
    'REVISTA 14X21': f'{BASE_URL_GITHUB}tabela_impressao_14x21.csv',
    'PLANNER WIRE-O A5': f'{BASE_URL_GITHUB}tabelaimpressaoA5.csv',
    'FICHARIO A5': f'{BASE_URL_GITHUB}tabelaimpressaoA5.csv',
    'FICHARIO 17X24': f'{BASE_URL_GITHUB}tabela_impressao_17x24.csv',
    'REVISTA 19X25': f'{BASE_URL_GITHUB}tabelaimpressao19x25.csv',
    'CADERNO WIRE-O 20X28': f'{BASE_URL_GITHUB}tabela_impressao_20x28.csv',
    'BLOCO WIRE-O 12X20': f'{BASE_URL_GITHUB}tabelaimpressao9x13.csv',
    'CADERNO WIRE-O 17X24': f'{BASE_URL_GITHUB}tabela_impressao_17x24.csv',
    'CADERNO ORGANIZADOR A5': f'{BASE_URL_GITHUB}tabelaimpressaoA5.csv',
    'CADERNO ORGANIZADOR 17X24': f'{BASE_URL_GITHUB}tabela_impressao_17x24.csv',
    'FICHARIO A6': f'{BASE_URL_GITHUB}tabelaimpressaoA5.csv'
}





