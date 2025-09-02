# orcamento_pro/data_services.py
"""
Módulo para carregar e processar dados de fontes externas (GitHub).
Cada função de carregamento principal é individualmente cacheada para otimização,
evitando recargas desnecessárias de dados.
"""
import pandas as pd
import streamlit as st
import re
import config

# --- FUNÇÕES DE LIMPEZA AUXILIARES ---
def _clean_paper_name(name: str) -> str:
    """
    Normaliza os nomes dos papéis removendo prefixos, sufixos e espaços extras.
    Esta função é interna ao módulo (indicado pelo _ no início).
    """
    if pd.isna(name):
        return ""
    name = re.sub(r'^(MP\d{3}|COUCHE|CARTAO|PAPEL|20\d{3}|COLOR|SCRITURA|Papel|Cartão)\s*', '', str(name), flags=re.IGNORECASE)
    name = re.sub(r'\s*UNICA-\w+', '', name)
    name = re.sub(r'\s*-\s*SEM\s*LINER', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s*-\s*CHAMBRIL', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+', ' ', name).strip()
    return name.title()

# --- FUNÇÕES DE CARREGAMENTO COM CACHE ---
@st.cache_data
def load_paper_purchases():
    """Carrega e processa os dados de compra de papel."""
    df = pd.read_csv(config.URL_COMPRAS, encoding='utf-8')
    df.columns = [
        'Demanda', 'Quantidade', 'DataSolicitacao', 'PrazoDesejado', 'DataAprovacao',
        'DataEmissaoNF', 'PrevisaoEntrega', 'NumeroNF', 'Fornecedor', 'ValorTotal',
        'ValorFrete', 'CreditoICMS', 'CNPJ', 'FormaPagamento', 'Parcelas', 'ValorUnitarioStr'
    ]
    date_cols = ['DataSolicitacao', 'PrazoDesejado', 'DataAprovacao', 'DataEmissaoNF', 'PrevisaoEntrega']
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], format='%d/%m/%Y', errors='coerce')

    df['ValorUnitario'] = (df['ValorUnitarioStr']
                          .astype(str)
                          .str.replace('R\\$', '', regex=True)
                          .str.replace(',', '.')
                          .str.strip())
    df['ValorUnitario'] = pd.to_numeric(df['ValorUnitario'], errors='coerce')
    df['PapelLimpo'] = df['Demanda'].apply(_clean_paper_name)

    df = df.dropna(subset=['ValorUnitario', 'PapelLimpo'])
    df = df[df['PapelLimpo'] != ""]
    df = df.sort_values('DataEmissaoNF', ascending=False)
    return df

@st.cache_data
def load_component_data(url: str, columns: list):
    """Função genérica para carregar dados de componentes (miolo, bolsa, etc.)."""
    df = pd.read_csv(url, encoding='utf-8')
    df.columns = columns
    # A primeira coluna é o nome do item (ex: 'Miolo', 'Bolsa')
    item_col = columns[0]
    df[item_col] = df[item_col].astype(str).str.strip()
    df['Papel'] = df['Papel'].apply(_clean_paper_name)

    numeric_cols = ['QuantidadePapel', 'ValorImpressao', 'UnitImpressao', 'QuantidadeAprovada']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

@st.cache_data
def load_direct_purchases():
    """Carrega e processa os dados de compras diretas, com tratamento de erro aprimorado."""
    try:
        df = pd.read_csv(config.URL_COMPRA_DIRETA, encoding='utf-8')
        
        # Lista de colunas esperadas
        expected_cols = ['CATEGORIA_MATERIAL_PCP', 'DATA_EMISSAO_NF', 'VALOR_UNITARIO', 'DEMANDA']
        
        # Verifica se todas as colunas esperadas existem
        missing_cols = [col for col in expected_cols if col not in df.columns]
        if missing_cols:
            st.error(f"❌ Erro em 'Compras Diretas': Colunas não encontradas no CSV: {missing_cols}")
            st.info(f"Colunas que foram encontradas: {df.columns.tolist()}")
            return {}

        df['DATA_EMISSAO_NF'] = pd.to_datetime(df['DATA_EMISSAO_NF'], errors='coerce')
        df['VALOR_UNITARIO'] = pd.to_numeric(df['VALOR_UNITARIO'], errors='coerce')
        df = df.dropna(subset=['DATA_EMISSAO_NF', 'VALOR_UNITARIO', 'DEMANDA'])

        df['NomeLimpo'] = df['DEMANDA'].apply(lambda x: re.sub(r'^(MP\d{3}\s*|UNICA-[A-Z0-9\-]+\s*)', '', str(x)).strip())

        categorias_cd = {}
        for cat in df['CATEGORIA_MATERIAL_PCP'].dropna().unique():
            # ... (o resto da lógica de processamento continua igual) ...
            itens_cat = df[df['CATEGORIA_MATERIAL_PCP'] == cat].sort_values('DATA_EMISSAO_NF', ascending=False)
            for nome in itens_cat['NomeLimpo'].unique():
                item_data = itens_cat[itens_cat['NomeLimpo'] == nome]
                ultimas_3 = item_data.head(3)
                preco_medio = ultimas_3['VALOR_UNITARIO'].mean()
                ultima_nf_date = item_data.iloc[0]['DATA_EMISSAO_NF']
                ultima_nf = ultima_nf_date.strftime('%d/%m/%Y') if pd.notna(ultima_nf_date) else 'N/A'

                if cat not in categorias_cd:
                    categorias_cd[cat] = []
                categorias_cd[cat].append({
                    'NomeLimpo': nome,
                    'VALOR_UNITARIO': preco_medio,
                    'ULTIMA_NF': ultima_nf
                })
        return categorias_cd
    except Exception as e:
        # Agora a mensagem de erro será muito mais específica!
        st.error(f"❌ Falha ao processar 'Compras Diretas': {e}")
        st.warning("Verifique se o link está correto e se as colunas do arquivo CSV correspondem ao esperado pelo código.")
        return {}


@st.cache_data
def load_wireo_table():
    """Carrega a tabela de mapeamento de WIRE-O para quantidade por caixa."""
    try:
        df = pd.read_csv(config.URL_TABELA_WIREO, encoding='utf-8')
        df.columns = ['Nome', 'QtdPorCaixa']
        df['Nome'] = df['Nome'].astype(str).str.strip()
        df['QtdPorCaixa'] = pd.to_numeric(df['QtdPorCaixa'], errors='coerce')
        return dict(zip(df['Nome'], df['QtdPorCaixa']))
    except Exception:
        st.warning("⚠️ Não foi possível carregar a tabela de WIRE-O. Usando valor padrão.")
        return {}

@st.cache_data
def load_impression_table(url: str):
    """Carrega uma tabela de custos de impressão/serviço a partir de uma URL."""
    df = pd.read_csv(url, encoding='utf-8')
    # Assume que as colunas relevantes são as 3 primeiras
    df.columns = ['LAMINAS', 'VALOR_ML', 'QTD_FLS'][:len(df.columns)]
    df['LAMINAS'] = pd.to_numeric(df['LAMINAS'], errors='coerce')
    df['QTD_FLS'] = pd.to_numeric(df['QTD_FLS'], errors='coerce')
    df = df.dropna(subset=['LAMINAS', 'QTD_FLS']).sort_values('LAMINAS')
    return df

def load_mod_ggf_data():
    """Carrega a tabela de custos de MOD/GGF com limpeza de dados aprimorada."""
    try:
        df = pd.read_csv(config.URL_MOD_GGF, encoding='utf-8')
        
        # LIMPEZA APRIMORADA:
        # 1. Remove espaços no início e no fim (.str.strip())
        # 2. Converte para maiúsculas para garantir consistência (.str.upper())
        # 3. Substitui múltiplos espaços por um único espaço (.str.replace)
        df['PRODUTO'] = df['PRODUTO'].str.strip().str.upper().str.replace(r'\s+', ' ', regex=True)
        
        return df.set_index('PRODUTO')
        
    except Exception as e:
        st.error(f"❌ Falha ao carregar a tabela de MOD/GGF: {e}")
        return pd.DataFrame()