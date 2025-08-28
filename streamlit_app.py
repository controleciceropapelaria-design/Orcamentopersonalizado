# streamlit_app.py
import streamlit as st
import pandas as pd
from utils import *

# Configuração da página
st.set_page_config(page_title="📝 Configurador de Cadernetas", layout="wide")
st.markdown("<h1 style='text-align: center;'>🔧 Configurador de Produtos Personalizados</h1>", unsafe_allow_html=True)

# Carregar dados
@st.cache_data
def carregar_csv(caminho):
    try:
        return pd.read_csv(caminho, encoding='utf-8')
    except:
        return pd.read_csv(caminho, encoding='latin1')

clientes = carregar_csv("data/clientes.csv")
vendedores = carregar_csv("data/vendedores.csv")
quantidades = carregar_csv("data/quantidades.csv")
tabela_offset = carregar_csv("data/tabela_impressao.csv")
papeis_df = carregar_csv("data/catalogo_papeis.csv")

miolo_df = carregar_csv("data/produtos/miolo.csv")
laminas_df = carregar_csv("data/produtos/laminas.csv")
guardas_df = carregar_csv("data/produtos/guardas.csv")
divisorias_df = carregar_csv("data/produtos/divisorias.csv")
bolsa_df = carregar_csv("data/produtos/bolsa.csv")
adesivo_df = carregar_csv("data/produtos/adesivo.csv")

# Estado
if 'produto' not in st.session_state:
    st.session_state.update({'produto': '', 'quantidade': 25})

# === 1. Cliente ===
st.subheader("👤 Cliente")
cliente_nome = st.selectbox("Selecione o cliente", options=[""] + clientes["Nome"].tolist(), key="cliente")

if cliente_nome:
    cliente = clientes[clientes["Nome"] == cliente_nome].iloc[0]
    col1, col2, col3 = st.columns(3)
    col1.text_input("Contato", value=cliente["Contato"], disabled=True)
    col2.text_input("Email", value=cliente["Email"], disabled=True)
    col3.text_input("Pagamento", value=cliente["Pagamento"], disabled=True)

# === 2. Dados do Pedido ===
st.subheader("📦 Pedido")
col1, col2, col3 = st.columns(3)

produto = col1.selectbox(
    "Produto",
    options=[""] + [
        "CADERNETA 9X13 - POLICROMIA",
        "CADERNETA 14X21 - POLICROMIA",
        "CADERNETA 9X13 - COURO SINTÉTICO",
        "CADERNETA 14X21 - COURO SINTÉTICO",
        "REVISTA 9X13 - POLICROMIA",
        "PLANNER WIRE-O A5 - POLICROMIA",
        "FICHARIO A5 - POLICROMIA",
        "CADERNO WIRE-O 20X28 - POLICROMIA"
    ],
    key="produto"
)

vendedor = col2.selectbox("Vendedor", options=[""] + vendedores["Vendedor"].dropna().tolist())
quantidade = col3.selectbox("Quantidade", options=quantidades["Quantidade"].dropna().astype(int).tolist(), index=0)

st.session_state.produto = produto
st.session_state.quantidade = quantidade

if not produto:
    st.stop()

base_produto = produto.replace(" - COURO SINTÉTICO", "").replace(" - POLICROMIA", "").strip()
acabamento = "COURO" if "COURO SINTÉTICO" in produto else "POLICROMIA"

# === 4. Capa ===
st.subheader("🎨 Capa")

papeis = papeis_df[papeis_df["Tipo"] == "Couros"]["Item"].tolist() if acabamento == "COURO" \
    else papeis_df[papeis_df["Tipo"] == "Papeis Capa"]["Item"].tolist()

papel_capa = st.selectbox("Papel da Capa", options=[""] + papeis, key="papel_capa")

impressao_capa = None
if acabamento == "POLICROMIA":
    if "Couro Sintético" in produto:
        st.warning("🚫 Impressão não aplicável.")
    else:
        impressao_capa = st.selectbox(
            "Impressão da Capa",
            ["Digital 4/0", "Digital 4/1", "Digital 1/0", "Digital 1/1", "Offset 4/0", "Offset 4/1"],
            key="impressao_capa"
        )
else:
    st.write("🔹 Impressão: Não aplicável para Couro Sintético")

# === 5. Miolo ===
with st.expander("📘 Miolo", expanded=False):
    opcoes_miolo = get_compativel_items(miolo_df, base_produto) + ["Personalizado"]
    miolo_opcao = st.selectbox("Miolo", opcoes_miolo, key="miolo")

    if miolo_opcao == "Personalizado":
        col1, col2 = st.columns(2)
        papel_miolo = col1.selectbox("Papel do Miolo", [
            'Offset 63g/m2 114x87', 'Offset 75g/m2 66x96', 'Offset 75g/m2 89x117',
            'Offset 90g/m2 66x96', 'Offset 90g/m2 76x112', 'Offset 120g/m2 66x96',
            'Offset 150g/m2 76x112', 'Polen Natural 80g/m2 66x96',
            'Couche Brilho 90g/m2 66x96', 'Couche Brilho 115g/m2 66x96',
            'Couche Brilho 170g/m2 66x96', 'Couche Matte 150g/m2 66x96',
            'Couche Matte 170g/m2 66x96'
        ])
        paginas = col2.number_input("Páginas", min_value=4, step=4, value=32)
        impressao_miolo = st.selectbox("Impressão Miolo", ["4/4", "1/1"])

# === 6. Guarda ===
with st.expander("🧵 Guarda / Forro", expanded=False):
    opcoes_guarda_frente = [g for g in get_compativel_items(guardas_df, base_produto) if "FRENTE" in g.upper() or "FORRO" in g.upper()] + ["Personalizado"]
    guarda_frente = st.selectbox("Guarda Frente", opcoes_guarda_frente)

    opcoes_guarda_verso = [g for g in get_compativel_items(guardas_df, base_produto) if "VERSO" in g.upper()] + ["Personalizado"]
    guarda_verso = st.selectbox("Guarda Verso", opcoes_guarda_verso)

    if guarda_frente == "Personalizado" or guarda_verso == "Personalizado":
        col1, col2 = st.columns(2)
        papel_guarda = col1.selectbox("Papel da Guarda", ["Offset 120g/m2 66x96", "Scritura 130g/m2 66x96"])
        impressao_guarda = col2.selectbox("Impressão Guarda", ["4/4", "1/1"])
        folhas = calcular_folhas(base_produto, quantidade)
        st.metric("Folhas necessárias", folhas)

# === 7. Lâmina ===
with st.expander("✨ Lâmina", expanded=False):
    opcoes_lamina = get_compativel_items(laminas_df, base_produto) + ["Personalizado"]
    lamina_opcao = st.selectbox("Lâmina", opcoes_lamina)

    if lamina_opcao == "Personalizado":
        col1, col2 = st.columns(2)
        papel_lamina = col1.selectbox("Papel da Lâmina", ["Offset 120g/m2 66x96", "Scritura 130g/m2 66x96"])
        impressao_lamina = col2.selectbox("Impressão Lâmina", ["4/4", "1/1"])
        folhas = calcular_folhas(base_produto, quantidade)
        st.metric("Folhas necessárias", folhas)

# === 8. Outros componentes ===
for nome, df in [("🗂️ Divisórias", divisorias_df), ("💼 Bolsa", bolsa_df), ("🏷️ Adesivo", adesivo_df)]:
    with st.expander(nome, expanded=False):
        opcoes = get_compativel_items(df, base_produto)
        st.selectbox(nome.replace(" ", ""), [""] + opcoes)

# === 9. Acabamentos ===
with st.expander("🔧 Acabamentos", expanded=False):
    acabamentos_validos = [
        'Laminação Fosca', 'Hot Stamping Pequeno', 'Hot Stamping Grande',
        'Relevo Pequeno', 'Silk 1/0', 'Silk 2/0', 'Silk 3/0'
    ]
    if "COURO SINTÉTICO" in produto:
        acabamentos_validos = [a for a in acabamentos_validos if a != "Laminação Fosca"]
    st.multiselect("Acabamentos", acabamentos_validos)

# === 10. Cálculo Final ===
st.subheader("🧮 Matéria-Prima da Capa")

if papel_capa and quantidade and produto:
    resultado = calcular_capa(produto, papel_capa, quantidade, impressao_capa, tabela_offset)
    st.success(f"**Resultado:** {resultado}")
else:
    st.info("Preencha produto, papel da capa e quantidade para calcular.")