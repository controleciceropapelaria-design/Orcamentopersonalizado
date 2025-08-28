import streamlit as st
import pandas as pd
import numpy as np
import re

# ================== URLs dos CSVs no GitHub ==================
URL_COMPRAS = "https://raw.githubusercontent.com/K1NGOD-RJ/projeto_orcamento/main/compradepapel.csv"
URL_USO_PAPEL_MIOLO = "https://raw.githubusercontent.com/K1NGOD-RJ/projeto_orcamento/main/usodepapelmiolos.csv"
URL_USO_PAPEL_BOLSA = "https://raw.githubusercontent.com/K1NGOD-RJ/projeto_orcamento/main/usodepapelbolsa.csv"
URL_USO_PAPEL_DIVISORIA = "https://raw.githubusercontent.com/K1NGOD-RJ/projeto_orcamento/main/usodepapeldivisoria.csv"
URL_USO_PAPEL_ADESIVO = "https://raw.githubusercontent.com/K1NGOD-RJ/projeto_orcamento/main/usodepapeladesivo.csv"
URL_TABELA_IMPRESSAO = "https://raw.githubusercontent.com/controleciceropapelaria-design/Orcamentoperosnalizado/ccff6ceeb6416b82c73928052f2aba3eea6ab3a7/tabelaimpressao.csv"

# ================== CONFIGURAÇÃO DA PÁGINA ==================
st.set_page_config(page_title="📦 Cálculo de Custo", layout="centered")
st.title("📐 Análise de Custo: Miolo + Bolsa + Divisória + Adesivo + Capa")

# ================== FUNÇÕES AUXILIARES ==================
@st.cache_data
def carregar_dados():
    try:
        # --- 1. Carregar compras de papel ---
        df_compras = pd.read_csv(URL_COMPRAS, encoding='utf-8')
        df_compras.columns = [
            'Demanda', 'Quantidade', 'DataSolicitacao', 'PrazoDesejado', 'DataAprovacao',
            'DataEmissaoNF', 'PrevisaoEntrega', 'NumeroNF', 'Fornecedor', 'ValorTotal',
            'ValorFrete', 'CreditoICMS', 'CNPJ', 'FormaPagamento', 'Parcelas', 'ValorUnitarioStr'
        ]
        date_cols = ['DataSolicitacao', 'PrazoDesejado', 'DataAprovacao', 'DataEmissaoNF', 'PrevisaoEntrega']
        for col in date_cols:
            df_compras[col] = pd.to_datetime(df_compras[col], format='%d/%m/%Y', errors='coerce')
        df_compras['ValorUnitario'] = (df_compras['ValorUnitarioStr']
                                       .astype(str)
                                       .str.replace('R\\$', '', regex=True)
                                       .str.replace(',', '.')
                                       .str.strip())
        df_compras['ValorUnitario'] = pd.to_numeric(df_compras['ValorUnitario'], errors='coerce')

        def limpar_papel(nome):
            if pd.isna(nome): return ""
            nome = re.sub(r'^(MP\d{3}|COUCHE|CARTAO|PAPEL|20\d{3}|COLOR|SCRITURA|Papel|Cartão)\s*', '', str(nome), flags=re.IGNORECASE)
            nome = re.sub(r'\s*UNICA-\w+', '', nome)
            nome = re.sub(r'\s*-\s*SEM\s*LINER', '', nome, flags=re.IGNORECASE)
            nome = re.sub(r'\s*-\s*CHAMBRIL', '', nome, flags=re.IGNORECASE)
            nome = re.sub(r'\s+', ' ', nome).strip()
            return nome.title()

        df_compras['PapelLimpo'] = df_compras['Demanda'].apply(limpar_papel)
        df_compras = df_compras.dropna(subset=['ValorUnitario', 'PapelLimpo'])
        df_compras = df_compras[df_compras['PapelLimpo'] != ""]
        df_compras = df_compras.sort_values('DataEmissaoNF', ascending=False)
        papeis_unicos = sorted(df_compras['PapelLimpo'].dropna().unique())

        # --- 2. Carregar uso de papel por miolo ---
        df_miolos = pd.read_csv(URL_USO_PAPEL_MIOLO, encoding='utf-8')
        df_miolos.columns = ['Miolo', 'Papel', 'QuantidadePapel', 'ValorImpressao', 'UnitImpressao', 'QuantidadeAprovada']
        df_miolos['QuantidadePapel'] = pd.to_numeric(df_miolos['QuantidadePapel'], errors='coerce')
        df_miolos['UnitImpressao'] = pd.to_numeric(df_miolos['UnitImpressao'], errors='coerce')
        df_miolos['QuantidadeAprovada'] = pd.to_numeric(df_miolos['QuantidadeAprovada'], errors='coerce')
        df_miolos['Papel'] = df_miolos['Papel'].apply(limpar_papel)

        # --- 3. Carregar uso de papel por bolsa ---
        df_bolsas = pd.read_csv(URL_USO_PAPEL_BOLSA, encoding='utf-8')
        df_bolsas.columns = ['Bolsa', 'Papel', 'QuantidadePapel', 'ValorImpressao', 'UnitImpressao', 'QuantidadeAprovada']
        df_bolsas['QuantidadePapel'] = pd.to_numeric(df_bolsas['QuantidadePapel'], errors='coerce')
        df_bolsas['UnitImpressao'] = pd.to_numeric(df_bolsas['UnitImpressao'], errors='coerce')
        df_bolsas['QuantidadeAprovada'] = pd.to_numeric(df_bolsas['QuantidadeAprovada'], errors='coerce')
        df_bolsas['Papel'] = df_bolsas['Papel'].apply(limpar_papel)

        # --- 4. Carregar uso de papel por divisória ---
        df_divisorias = pd.read_csv(URL_USO_PAPEL_DIVISORIA, encoding='utf-8')
        df_divisorias.columns = ['Divisoria', 'Papel', 'QuantidadePapel', 'ValorImpressao', 'UnitImpressao', 'QuantidadeAprovada']
        df_divisorias['QuantidadePapel'] = pd.to_numeric(df_divisorias['QuantidadePapel'], errors='coerce')
        df_divisorias['UnitImpressao'] = pd.to_numeric(df_divisorias['UnitImpressao'], errors='coerce')
        df_divisorias['QuantidadeAprovada'] = pd.to_numeric(df_divisorias['QuantidadeAprovada'], errors='coerce')
        df_divisorias['Papel'] = df_divisorias['Papel'].apply(limpar_papel)

        # --- 5. Carregar uso de papel por adesivo ---
        df_adesivos = pd.read_csv(URL_USO_PAPEL_ADESIVO, encoding='utf-8')
        df_adesivos.columns = ['Adesivo', 'Papel', 'QuantidadePapel', 'ValorImpressao', 'UnitImpressao', 'QuantidadeAprovada']
        df_adesivos['QuantidadePapel'] = pd.to_numeric(df_adesivos['QuantidadePapel'], errors='coerce')
        df_adesivos['UnitImpressao'] = pd.to_numeric(df_adesivos['UnitImpressao'], errors='coerce')
        df_adesivos['QuantidadeAprovada'] = pd.to_numeric(df_adesivos['QuantidadeAprovada'], errors='coerce')
        df_adesivos['Papel'] = df_adesivos['Papel'].apply(limpar_papel)

        # --- 6. Carregar tabela de impressão (offset) ---
        try:
            # Forçar leitura SEM cabeçalho, como matriz
            df_tabela_impressao = pd.read_csv(
                URL_TABELA_IMPRESSAO,
                encoding='utf-8',
                sep=',',
                header=None,           # ❌ Sem cabeçalho
                skipinitialspace=True,
                dtype=str              # Ler tudo como string
            )

            # Remover colunas vazias
            df_tabela_impressao = df_tabela_impressao.dropna(axis=1, how='all')

            # Manter apenas as 9 primeiras colunas
            df_tabela_impressao = df_tabela_impressao.iloc[:, :9]

            # Converter todas as colunas para número
            for i in range(9):
                df_tabela_impressao[i] = pd.to_numeric(df_tabela_impressao[i], errors='coerce')

            # Remover linhas com primeira coluna inválida
            df_tabela_impressao = df_tabela_impressao.dropna(subset=[0]).reset_index(drop=True)

            st.success("✅ Tabela de impressão carregada com sucesso!")

        except Exception as e:
            st.error(f"❌ Erro ao carregar tabela de impressão: {e}")
            st.code(f"URL: {URL_TABELA_IMPRESSAO}")
            df_tabela_impressao = pd.DataFrame()

        return df_compras, df_miolos, df_bolsas, df_divisorias, df_adesivos, df_tabela_impressao, papeis_unicos

    except Exception as e:
        st.error(f"❌ Erro ao carregar os dados: {e}")
        return None, None, None, None, None, None, None

# ================== CARREGAR DADOS ==================
df_compras, df_miolos, df_bolsas, df_divisorias, df_adesivos, df_tabela_impressao, papeis_unicos = carregar_dados()
if df_compras is None:
    st.stop()

# ================== SELETOR DE QUANTIDADE (TOP) ==================
st.markdown("### 📦 Quantidade do Orçamento")
quantidade_orcamento = st.number_input(
    "Digite a quantidade total do orçamento:",
    min_value=1,
    value=15000,
    step=1,
    help="Essa quantidade será usada para dividir o valor do serviço no cálculo unitário"
)
st.divider()

# ================== FUNÇÃO PARA CALCULAR CUSTO UNITÁRIO ==================
def calcular_custo(nome_item, df_item, tipo="Item"):
    linha = df_item[df_item[tipo] == nome_item].iloc[0]
    papel_necessario = linha['Papel']
    qtd_papel_total = linha['QuantidadePapel']
    qtd_aprovada = linha['QuantidadeAprovada']
    valor_impressao = linha['ValorImpressao']
    if qtd_aprovada <= 0: qtd_aprovada = 1
    folhas_por_unidade = qtd_papel_total / qtd_aprovada
    df_papel = df_compras[df_compras['PapelLimpo'] == papel_necessario]
    if df_papel.empty:
        st.warning(f"⚠️ Nenhuma compra encontrada para o papel usado no(a) {tipo.lower()}: **{papel_necessario}**")
        return None, None, None, None
    preco_unitario_papel = df_papel.iloc[0]['ValorUnitario']
    custo_papel_por_unidade = preco_unitario_papel * folhas_por_unidade
    custo_servico_por_unidade = valor_impressao / quantidade_orcamento
    custo_total_unitario = custo_papel_por_unidade + custo_servico_por_unidade
    return custo_total_unitario, custo_papel_por_unidade, custo_servico_por_unidade, papel_necessario

# ================== FUNÇÃO: CÁLCULO PERSONALIZADO ==================
def calcular_personalizado(nome, papel_selecionado, aproveitamento, valor_servico, quantidade_orcamento):
    if aproveitamento <= 0: aproveitamento = 1
    df_papel = df_compras[df_compras['PapelLimpo'] == papel_selecionado]
    if df_papel.empty:
        st.error(f"❌ Papel não encontrado: **{papel_selecionado}**")
        return None, None, None, None, None
    preco_unitario_papel = df_papel.iloc[0]['ValorUnitario']
    ultima_data = df_papel.iloc[0]['DataEmissaoNF'].strftime('%d/%m/%Y')
    custo_papel_por_unidade = preco_unitario_papel / aproveitamento
    custo_servico_por_unidade = valor_servico / quantidade_orcamento
    custo_total = custo_papel_por_unidade + custo_servico_por_unidade
    return custo_total, custo_papel_por_unidade, custo_servico_por_unidade, papel_selecionado, ultima_data

# ================== FUNÇÃO: CÁLCULO DA CAPA ==================
def calcular_capa(produto, papel, impressao, quantidade):
    if not produto or not papel or not quantidade or quantidade <= 0:
        return None

    # Extrair base e acabamento
    if "COURO SINTÉTICO" in produto:
        base = produto.replace(" - COURO SINTÉTICO", "").strip()
        acabamento = "COURO"
    elif "POLICROMIA" in produto:
        base = produto.replace(" - POLICROMIA", "").strip()
        acabamento = "POLICROMIA"
    else:
        return None

    # Dimensões abertas da capa
    formatos_abertos = {
        'CADERNETA 9X13': {'larg': 22, 'alt': 15.8},
        'CADERNETA 14X21': {'larg': 33.7, 'alt': 24.2},
        'REVISTA 9X13': {'larg': 19, 'alt': 14},
        'REVISTA 14X21': {'larg': 29, 'alt': 22},
        'REVISTA 19X25': {'larg': 40, 'alt': 26},
        'CADERNO WIRE-O 17X24': {'larg': 43.8, 'alt': 27.8},
        'CADERNO WIRE-O 20X28': {'larg': 49.2, 'alt': 31.3},
        'PLANNER WIRE-O A5': {'larg': 41, 'alt': 24.7},
        'BLOCO WIRE-O 12X20': {'larg': 31.4, 'alt': 23},
        'FICHARIO A6': {'larg': 35, 'alt': 19.5},
        'FICHARIO A5': {'larg': 45, 'alt': 26},
        'FICHARIO 17X24': {'larg': 49.2, 'alt': 28.4},
        'CADERNO ORGANIZADOR A5': {'larg': 41.5, 'alt': 24.7},
        'CADERNO ORGANIZADOR 17X24': {'larg': 46, 'alt': 27.7}
    }

    if base not in formatos_abertos:
        return None

    larg_capa, alt_capa = formatos_abertos[base]['larg'], formatos_abertos[base]['alt']

    # Função para calcular máximo de peças por folha
    def max_por_folha(folha_l, folha_a, peca_l, peca_a):
        h1 = (folha_l // peca_l) * (folha_a // peca_a)
        h2 = (folha_l // peca_a) * (folha_a // peca_l)
        return max(h1, h2) if h1 > 0 or h2 > 0 else 0

    # ✅ 1. OFFSET
    if acabamento == "POLICROMIA" and impressao and "Offset" in impressao:
        # Mapeamento: base → URL do CSV específico
        csv_map = {
            'CADERNETA 9X13': 'https://raw.githubusercontent.com/controleciceropapelaria-design/Orcamentoperosnalizado/refs/heads/main/tabelaimpressao9x13.csv',
            'CADERNETA 14X21': 'https://raw.githubusercontent.com/controleciceropapelaria-design/Orcamentoperosnalizado/refs/heads/main/tabelaimpressao14x21.csv',
            'REVISTA 9X13': 'https://raw.githubusercontent.com/controleciceropapelaria-design/Orcamentoperosnalizado/refs/heads/main/tabelaimpressao9x13.csv',
            'REVISTA 14X21': 'https://raw.githubusercontent.com/controleciceropapelaria-design/Orcamentoperosnalizado/refs/heads/main/tabelaimpressao14x21.csv',
            'PLANNER WIRE-O A5': 'https://raw.githubusercontent.com/controleciceropapelaria-design/Orcamentoperosnalizado/refs/heads/main/tabelaimpressaoA5.csv',
            'FICHARIO A5': 'https://raw.githubusercontent.com/controleciceropapelaria-design/Orcamentoperosnalizado/refs/heads/main/tabelaimpressao17x24.csv',
            'FICHARIO 17X24': 'https://raw.githubusercontent.com/controleciceropapelaria-design/Orcamentoperosnalizado/refs/heads/main/tabelaimpressao17x24.csv',
            'REVISTA 19X25': 'https://raw.githubusercontent.com/controleciceropapelaria-design/Orcamentoperosnalizado/refs/heads/main/tabelaimpressao19x25.csv',
            'CADERNO WIRE-O 20X28': 'https://raw.githubusercontent.com/controleciceropapelaria-design/Orcamentoperosnalizado/refs/heads/main/tabelaimpressao20x28.csv',
            'BLOCO WIRE-O 12X20': 'https://raw.githubusercontent.com/controleciceropapelaria-design/Orcamentoperosnalizado/refs/heads/main/tabelaimpressao14x21.csv',
            'CADERNO WIRE-O 17X24': 'https://raw.githubusercontent.com/controleciceropapelaria-design/Orcamentoperosnalizado/refs/heads/main/tabelaimpressao17x24.csv',
            'CADERNO ORGANIZADOR A5': 'https://raw.githubusercontent.com/controleciceropapelaria-design/Orcamentoperosnalizado/refs/heads/main/tabelaimpressao17x24.csv',
            'CADERNO ORGANIZADOR 17X24': 'https://raw.githubusercontent.com/controleciceropapelaria-design/Orcamentoperosnalizado/refs/heads/main/tabelaimpressao17x24.csv',
            'FICHARIO A6': 'https://raw.githubusercontent.com/controleciceropapelaria-design/Orcamentoperosnalizado/refs/heads/main/tabelaimpressaoA5.csv'
        }

        url_csv = csv_map.get(base)
        if not url_csv:
            st.warning(f"⚠️ CSV não encontrado para: {base}")
            return None

        try:
            df_formato = pd.read_csv(url_csv, encoding='utf-8')
            df_formato['Capacidade'] = pd.to_numeric(df_formato['Capacidade'], errors='coerce')
            df_formato['QtdFolhas'] = pd.to_numeric(df_formato['QtdFolhas'], errors='coerce')
            df_formato = df_formato.dropna(subset=['Capacidade', 'QtdFolhas']).reset_index(drop=True)
        except Exception as e:
            st.error(f"❌ Erro ao carregar CSV: {e}")
            return None

        # Buscar a primeira linha onde Capacidade >= quantidade
        for _, row in df_formato.iterrows():
            if quantidade <= row['Capacidade']:
                return {"tipo": "offset", "folhas": int(row['QtdFolhas']), "m2": None}

        # Se não encontrou, usa a última linha
        if len(df_formato) > 0:
            ultima = df_formato.iloc[-1]
            return {"tipo": "offset", "folhas": int(ultima['QtdFolhas']), "m2": None}

        st.error("❌ Nenhuma faixa válida encontrada no CSV.")
        return None
    
    # ✅ 2. DIGITAL
    if acabamento == "POLICROMIA" and impressao and "Digital" in impressao:
        # Extrair dimensões do papel (ex: "Couche Brilho 170G/M2 76X112")
        papel_clean = re.sub(r'g[/]?m2|gsm|g/m²', '', papel, flags=re.IGNORECASE)
        papel_clean = re.sub(r'\s+', ' ', papel_clean).strip()
        match = re.search(r'(\d+)\s*[xX×]\s*(\d+)', papel_clean)
        if not match:
            return None
        papel_l = float(match.group(1))
        papel_a = float(match.group(2))
        if papel_l < papel_a:
            papel_l, papel_a = papel_a, papel_l

        # Formato útil da máquina digital
        if "17X24" in base or "20X28" in base:
            util_l, util_a = 56, 33
        else:
            util_l, util_a = 47, 33

        # Quantidade de pedaços por folha
        pecas_h = int(papel_l // util_l)
        pecas_v = int(papel_a // util_a)
        total_pecas = pecas_h * pecas_v
        if total_pecas == 0:
            return None

        # Capas por pedaço (melhor encaixe)
        capas_por_peca = max_por_folha(util_l, util_a, larg_capa, alt_capa)
        if capas_por_peca == 0:
            return None

        # Capas por folha do papel
        capas_por_folha = total_pecas * capas_por_peca
        folhas = int(np.ceil(quantidade / capas_por_folha))
        return {"tipo": "digital", "folhas": folhas, "m2": None}

    # ✅ 3. COURO SINTÉTICO
    if acabamento == "COURO":
        facas = {
            'CADERNETA 9X13': 40, 'CADERNETA 14X21': 40, 'REVISTA 9X13': 40, 'REVISTA 14X21': 40,
            'REVISTA 19X25': 47, 'CADERNO WIRE-O 17X24': 53, 'CADERNO WIRE-O 20X28': 53,
            'PLANNER WIRE-O A5': 47, 'BLOCO WIRE-O 12X20': 40, 'FICHARIO A6': 40,
            'FICHARIO A5': 50, 'FICHARIO 17X24': 53, 'CADERNO ORGANIZADOR A5': 50,
            'CADERNO ORGANIZADOR 17X24': 53
        }
        altura_faca = facas.get(base)
        if not altura_faca:
            return None
        tira_l, tira_a = 130, altura_faca
        capas_por_tira = max_por_folha(tira_l, tira_a, larg_capa, alt_capa)
        if capas_por_tira == 0:
            return None
        qtd_tiras = np.ceil((quantidade + 5) / capas_por_tira)
        m2_total = qtd_tiras * (altura_faca / 100) * 1.3
        return {"tipo": "couro", "folhas": None, "m2": round(m2_total, 2)}

    return None

# ================== SELETOR DE PRODUTO (CAPA) ==================
st.markdown("### 📕 Seleção de Produto (Capa)")
produtos_base = [
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

produto_selecionado = st.selectbox(
    "Selecione o produto:",
    options=[""] + sorted(produtos_base),
    format_func=lambda x: "Selecione um produto" if x == "" else x
)

if not produto_selecionado:
    st.stop()

# === Capa ===
st.markdown("📘 Capa")
col1, col2, col3 = st.columns(3)

# Papel da capa
if "COURO SINTÉTICO" in produto_selecionado:
    papeis_capa = sorted(df_compras[df_compras['Demanda'].str.contains('Couro', case=False, na=False)]['PapelLimpo'].unique())
else:
    papeis_capa = [p for p in papeis_unicos if 'couche' in p.lower() or 'policromia' in p.lower()]

papel_capa = col1.selectbox("Papel da capa", options=[""] + papeis_capa, index=0)

# Impressão (opcional para couro)
impressao_opcoes = ["Digital 4/0", "Digital 4/1", "Digital 1/0", "Digital 1/1", "Offset 4/0", "Offset 4/1"]
impressao_capa = col2.selectbox("Impressão", options=[""] + impressao_opcoes, index=0) if "POLICROMIA" in produto_selecionado else ""

# Calcular
if col3.button("🧮 Calcular Capa"):
    with st.spinner("Calculando..."):
        resultado = calcular_capa(produto_selecionado, papel_capa, impressao_capa, quantidade_orcamento)
        if resultado:
            st.session_state.capa_resultado = resultado
            st.session_state.papel_capa = papel_capa
            st.session_state.impressao_capa = impressao_capa
            st.success(f"✅ {resultado['folhas'] or resultado['m2']} {'folhas' if resultado['folhas'] else 'm²'}")
        else:
            st.error("Erro no cálculo da capa.")

# ================== INTERFACE DO USUÁRIO (miolo, bolsa, etc) ==================
st.markdown("Selecione um **miolo**, uma **bolsa**, uma **divisória**, um **adesivo** ou use a opção personalizada.")
# === Miolo ===
miolos = sorted(df_miolos['Miolo'].dropna().unique())
miolo_opcoes = ["Personalizado"] + list(miolos)
miolo_selecionado = st.selectbox("📘 Miolo:", options=miolo_opcoes, index=0, key="miolo")
if miolo_selecionado == "Personalizado":
    col1, col2, col3 = st.columns(3)
    papel_miolo = col1.selectbox("Papel utilizado (miolo)", options=papeis_unicos, index=0, key="papel_miolo")
    aproveitamento_miolo = col2.number_input("Aproveitamento (unidades por folha)", min_value=1, value=5, key="aprov_miolo")
    valor_servico_miolo = col3.number_input("Valor total do serviço (impressão)", min_value=0.0, value=13050.0, key="serv_miolo")
else:
    papel_miolo = None

# === Bolsa ===
bolsas = sorted(df_bolsas['Bolsa'].dropna().unique())
bolsa_opcoes = ["Personalizado"] + list(bolsas)
bolsa_selecionada = st.selectbox("👜 Bolsa:", options=bolsa_opcoes, index=0, key="bolsa")
if bolsa_selecionada == "Personalizado":
    col1, col2, col3 = st.columns(3)
    papel_bolsa = col1.selectbox("Papel utilizado (bolsa)", options=papeis_unicos, index=0, key="papel_bolsa")
    aproveitamento_bolsa = col2.number_input("Aproveitamento (unidades por folha)", min_value=1, value=4, key="aprov_bolsa")
    valor_servico_bolsa = col3.number_input("Valor total do serviço (impressão)", min_value=0.0, value=2425.0, key="serv_bolsa")
else:
    papel_bolsa = None

# === Divisória ===
divisorias = sorted(df_divisorias['Divisoria'].dropna().unique())
divisoria_opcoes = ["Personalizado"] + list(divisorias)
divisoria_selecionada = st.selectbox("🔖 Divisória:", options=divisoria_opcoes, index=0, key="divisoria")
if divisoria_selecionada == "Personalizado":
    col1, col2, col3 = st.columns(3)
    papel_divisoria = col1.selectbox("Papel utilizado (divisória)", options=papeis_unicos, index=0, key="papel_divisoria")
    aproveitamento_divisoria = col2.number_input("Aproveitamento (unidades por folha)", min_value=1, value=3, key="aprov_div")
    valor_servico_divisoria = col3.number_input("Valor total do serviço (impressão)", min_value=0.0, value=22986.0, key="serv_div")
else:
    papel_divisoria = None

# === Adesivo ===
adesivos = sorted(df_adesivos['Adesivo'].dropna().unique())
adesivo_opcoes = ["Personalizado"] + list(adesivos)
adesivo_selecionado = st.selectbox("🏷️ Adesivo:", options=adesivo_opcoes, index=0, key="adesivo")
if adesivo_selecionado == "Personalizado":
    col1, col2, col3 = st.columns(3)
    papel_adesivo = col1.selectbox("Papel utilizado (adesivo)", options=papeis_unicos, index=0, key="papel_adesivo")
    aproveitamento_adesivo = col2.number_input("Aproveitamento (unidades por folha)", min_value=1, value=10, key="aprov_adesivo")
    valor_servico_adesivo = col3.number_input("Valor total do serviço (impressão)", min_value=0.0, value=4840.0, key="serv_adesivo")
else:
    papel_adesivo = None

# ================== CALCULAR CUSTOS ==================
custo_miolo = None
custo_bolsa = None
custo_divisoria = None
custo_adesivo = None

# Miolo
if miolo_selecionado and miolo_selecionado != "Personalizado":
    custo_miolo = calcular_custo(miolo_selecionado, df_miolos, "Miolo")
elif miolo_selecionado == "Personalizado":
    custo_miolo = calcular_personalizado("Miolo Personalizado", papel_miolo, aproveitamento_miolo, valor_servico_miolo, quantidade_orcamento)

# Bolsa
if bolsa_selecionada and bolsa_selecionada != "Personalizado":
    custo_bolsa = calcular_custo(bolsa_selecionada, df_bolsas, "Bolsa")
elif bolsa_selecionada == "Personalizado":
    custo_bolsa = calcular_personalizado("Bolsa Personalizada", papel_bolsa, aproveitamento_bolsa, valor_servico_bolsa, quantidade_orcamento)

# Divisória
if divisoria_selecionada and divisoria_selecionada != "Personalizado":
    custo_divisoria = calcular_custo(divisoria_selecionada, df_divisorias, "Divisoria")
elif divisoria_selecionada == "Personalizado":
    custo_divisoria = calcular_personalizado("Divisória Personalizada", papel_divisoria, aproveitamento_divisoria, valor_servico_divisoria, quantidade_orcamento)

# Adesivo
if adesivo_selecionado and adesivo_selecionado != "Personalizado":
    custo_adesivo = calcular_custo(adesivo_selecionado, df_adesivos, "Adesivo")
elif adesivo_selecionado == "Personalizado":
    custo_adesivo = calcular_personalizado("Adesivo Personalizado", papel_adesivo, aproveitamento_adesivo, valor_servico_adesivo, quantidade_orcamento)

# ================== EXIBIR RESULTADOS ==================
st.divider()
st.subheader("📊 Resultados por Componente")
cols = st.columns(5)

# Exibir Capa
if 'capa_resultado' in st.session_state:
    with cols[0]:
        st.markdown("**Capa**")
        valor = st.session_state.capa_resultado
        tipo = valor['tipo']
        texto = f"{valor['folhas']} folhas" if tipo != "couro" else f"{valor['m2']} m²"
        st.metric("Consumo", texto)
        with st.expander("Detalhes"):
            st.markdown(f"**Produto:** {produto_selecionado}")
            st.markdown(f"**Papel:** {st.session_state.papel_capa}")
            if tipo != "couro":
                st.markdown(f"**Impressão:** {st.session_state.impressao_capa}")

# Miolo
if miolo_selecionado != "Personalizado" and custo_miolo:
    with cols[1]:
        st.markdown(f"**{miolo_selecionado}**")
        st.metric("Custo Unit.", f"R$ {custo_miolo[0]:,.2f}".replace('.', ','))
        with st.expander("Detalhes"):
            st.markdown(f"**Papel:** {custo_miolo[3]}")
            st.markdown(f"**Papel/unid:** R$ {custo_miolo[1]:,.2f}".replace('.', ','))
            st.markdown(f"**Serviço/unid:** R$ {custo_miolo[2]:,.2f}".replace('.', ','))
elif miolo_selecionado == "Personalizado" and custo_miolo:
    with cols[1]:
        st.markdown("**Miolo Personalizado**")
        st.metric("Custo Unit.", f"R$ {custo_miolo[0]:,.2f}".replace('.', ','))
        with st.expander("Detalhes"):
            st.markdown(f"**Papel:** {papel_miolo}")
            st.markdown(f"**Última NF:** {custo_miolo[4]}")
            st.markdown(f"**Aproveitamento:** {aproveitamento_miolo} unid/folha")
            st.markdown(f"**Custo papel/unid:** R$ {custo_miolo[1]:,.2f}".replace('.', ','))
            st.markdown(f"**Custo serviço/unid:** R$ {custo_miolo[2]:,.2f}".replace('.', ','))

# Bolsa
if bolsa_selecionada != "Personalizado" and custo_bolsa:
    with cols[2]:
        st.markdown(f"**{bolsa_selecionada}**")
        st.metric("Custo Unit.", f"R$ {custo_bolsa[0]:,.2f}".replace('.', ','))
        with st.expander("Detalhes"):
            st.markdown(f"**Papel:** {custo_bolsa[3]}")
            st.markdown(f"**Papel/unid:** R$ {custo_bolsa[1]:,.2f}".replace('.', ','))
            st.markdown(f"**Serviço/unid:** R$ {custo_bolsa[2]:,.2f}".replace('.', ','))
elif bolsa_selecionada == "Personalizado" and custo_bolsa:
    with cols[2]:
        st.markdown("**Bolsa Personalizada**")
        st.metric("Custo Unit.", f"R$ {custo_bolsa[0]:,.2f}".replace('.', ','))
        with st.expander("Detalhes"):
            st.markdown(f"**Papel:** {papel_bolsa}")
            st.markdown(f"**Última NF:** {custo_bolsa[4]}")
            st.markdown(f"**Aproveitamento:** {aproveitamento_bolsa} unid/folha")
            st.markdown(f"**Custo papel/unid:** R$ {custo_bolsa[1]:,.2f}".replace('.', ','))
            st.markdown(f"**Custo serviço/unid:** R$ {custo_bolsa[2]:,.2f}".replace('.', ','))

# Divisória
if divisoria_selecionada != "Personalizado" and custo_divisoria:
    with cols[3]:
        st.markdown(f"**{divisoria_selecionada}**")
        st.metric("Custo Unit.", f"R$ {custo_divisoria[0]:,.2f}".replace('.', ','))
        with st.expander("Detalhes"):
            st.markdown(f"**Papel:** {custo_divisoria[3]}")
            st.markdown(f"**Papel/unid:** R$ {custo_divisoria[1]:,.2f}".replace('.', ','))
            st.markdown(f"**Serviço/unid:** R$ {custo_divisoria[2]:,.2f}".replace('.', ','))
elif divisoria_selecionada == "Personalizado" and custo_divisoria:
    with cols[3]:
        st.markdown("**Divisória Personalizada**")
        st.metric("Custo Unit.", f"R$ {custo_divisoria[0]:,.2f}".replace('.', ','))
        with st.expander("Detalhes"):
            st.markdown(f"**Papel:** {papel_divisoria}")
            st.markdown(f"**Última NF:** {custo_divisoria[4]}")
            st.markdown(f"**Aproveitamento:** {aproveitamento_divisoria} unid/folha")
            st.markdown(f"**Custo papel/unid:** R$ {custo_divisoria[1]:,.2f}".replace('.', ','))
            st.markdown(f"**Custo serviço/unid:** R$ {custo_divisoria[2]:,.2f}".replace('.', ','))

# Adesivo
if adesivo_selecionado != "Personalizado" and custo_adesivo:
    with cols[4]:
        st.markdown(f"**{adesivo_selecionado}**")
        st.metric("Custo Unit.", f"R$ {custo_adesivo[0]:,.2f}".replace('.', ','))
        with st.expander("Detalhes"):
            st.markdown(f"**Papel:** {custo_adesivo[3]}")
            st.markdown(f"**Papel/unid:** R$ {custo_adesivo[1]:,.2f}".replace('.', ','))
            st.markdown(f"**Serviço/unid:** R$ {custo_adesivo[2]:,.2f}".replace('.', ','))
elif adesivo_selecionado == "Personalizado" and custo_adesivo:
    with cols[4]:
        st.markdown("**Adesivo Personalizado**")
        st.metric("Custo Unit.", f"R$ {custo_adesivo[0]:,.2f}".replace('.', ','))
        with st.expander("Detalhes"):
            st.markdown(f"**Papel:** {papel_adesivo}")
            st.markdown(f"**Última NF:** {custo_adesivo[4]}")
            st.markdown(f"**Aproveitamento:** {aproveitamento_adesivo} unid/folha")
            st.markdown(f"**Custo papel/unid:** R$ {custo_adesivo[1]:,.2f}".replace('.', ','))
            st.markdown(f"**Custo serviço/unid:** R$ {custo_adesivo[2]:,.2f}".replace('.', ','))

# ================== CUSTO TOTAL DO PRODUTO ==================
st.divider()
st.subheader("💰 Custo Total Unitário do Produto")
custo_total = 0.0
itens = []

if 'capa_resultado' in st.session_state:
    custo_total += 0  # Aqui você pode adicionar custo real da capa depois
    itens.append("Capa")

if miolo_selecionado != "Personalizado" and custo_miolo:
    custo_total += custo_miolo[0]
    itens.append("Miolo")
elif miolo_selecionado == "Personalizado" and custo_miolo:
    custo_total += custo_miolo[0]
    itens.append("Miolo (Pers.)")

if bolsa_selecionada != "Personalizado" and custo_bolsa:
    custo_total += custo_bolsa[0]
    itens.append("Bolsa")
elif bolsa_selecionada == "Personalizado" and custo_bolsa:
    custo_total += custo_bolsa[0]
    itens.append("Bolsa (Pers.)")

if divisoria_selecionada != "Personalizado" and custo_divisoria:
    custo_total += custo_divisoria[0]
    itens.append("Divisória")
elif divisoria_selecionada == "Personalizado" and custo_divisoria:
    custo_total += custo_divisoria[0]
    itens.append("Divisória (Pers.)")

if adesivo_selecionado != "Personalizado" and custo_adesivo:
    custo_total += custo_adesivo[0]
    itens.append("Adesivo")
elif adesivo_selecionado == "Personalizado" and custo_adesivo:
    custo_total += custo_adesivo[0]
    itens.append("Adesivo (Pers.)")

if itens:
    st.success(f"**Custo Total Unitário ({' + '.join(itens)}):** R$ {custo_total:,.2f}".replace('.', ','))
else:
    st.warning("Nenhum item selecionado.")

# ================== RODAPÉ ==================
st.markdown("---")
st.caption("✅ Cálculo: `(Preço do Papel / Aproveitamento) + (Valor do Serviço / Quantidade do Orçamento)`")