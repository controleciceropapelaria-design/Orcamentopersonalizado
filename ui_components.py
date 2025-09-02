# orcamento_pro/ui_components.py
"""
Módulo para componentes de UI reutilizáveis do Streamlit.
Agora com validação de formulários e busca de CEP por API.
"""
import streamlit as st
import pandas as pd
import storage
import config
import re
import requests # <-- Importamos a nova biblioteca

# ================== CONSTANTES E FUNÇÕES AUXILIARES ==================

UFS_BRASIL = ["", "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"]

def is_valid_email(email):
    """Verifica se um email tem um formato básico válido."""
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(regex, email)

def format_cep(cep):
    """Formata um CEP para XXXXX-XXX, aceitando apenas dígitos."""
    cep_digits = re.sub(r'\D', '', cep)
    if len(cep_digits) == 8:
        return f"{cep_digits[:5]}-{cep_digits[5:]}"
    return cep # Retorna o original se não tiver 8 dígitos

def format_cnpj(cnpj):
    """Formata um CNPJ para XX.XXX.XXX/XXXX-XX, aceitando apenas dígitos."""
    cnpj_digits = re.sub(r'\D', '', cnpj)
    if len(cnpj_digits) == 14:
        return f"{cnpj_digits[:2]}.{cnpj_digits[2:5]}.{cnpj_digits[5:8]}/{cnpj_digits[8:12]}-{cnpj_digits[12:]}"
    return cnpj

def format_telefone(telefone):
    """Formata um telefone para (XX) XXXXX-XXXX, aceitando apenas dígitos."""
    tel_digits = re.sub(r'\D', '', telefone)
    if len(tel_digits) == 11:
        return f"({tel_digits[:2]}) {tel_digits[2:7]}-{tel_digits[7:]}"
    if len(tel_digits) == 10:
        return f"({tel_digits[:2]}) {tel_digits[2:6]}-{tel_digits[6:]}"
    return telefone

def get_address_from_cep(cep):
    """Busca o endereço correspondente a um CEP usando a API ViaCEP."""
    cep_digits = re.sub(r'\D', '', cep)
    if len(cep_digits) != 8:
        return None, "CEP inválido. Deve conter 8 dígitos."
    
    try:
        response = requests.get(f"https://viacep.com.br/ws/{cep_digits}/json/")
        response.raise_for_status() # Lança um erro para status HTTP ruins (4xx ou 5xx)
        data = response.json()
        if data.get("erro"):
            return None, "CEP não encontrado."
        
        return data, None # Retorna os dados do endereço e nenhuma mensagem de erro
    except requests.exceptions.RequestException as e:
        return None, f"Erro de conexão: {e}"

# ================== COMPONENTES DE UI ==================

# ... (as funções display_login_form, display_registration_form, etc., continuam aqui) ...
def display_login_form():
    """Renderiza o formulário de login na barra lateral."""
    st.sidebar.title("🔐 Login")
    with st.sidebar.form("login_form"):
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar")
        return submitted, username, password

def display_registration_form():
    """Renderiza o formulário de cadastro de usuário."""
    st.title("📝 Cadastro de Novo Usuário")
    with st.form("registration_form"):
        new_user = st.text_input("Novo Usuário")
        new_pass = st.text_input("Nova Senha", type="password")
        full_name = st.text_input("Nome Completo")
        submitted = st.form_submit_button("Cadastrar")
        return submitted, new_user, new_pass, full_name

def display_sidebar_logged_in():
    """Renderiza a barra lateral para um usuário logado."""
    # Esta função não precisa mais existir aqui, pois a lógica foi movida para app.py
    pass

# orcamento_pro/ui_components.py

def display_client_registration_form():
    """Renderiza o formulário e a tabela de cadastro de clientes com validação e busca de CEP."""
    st.title("📋 Cadastro de Clientes")

    # Inicializa o estado da sessão para os campos de endereço se não existirem
    if 'cep_data' not in st.session_state:
        st.session_state.cep_data = {}

    st.subheader("1. Buscar Endereço (Opcional)")
    col1, col2 = st.columns([1, 2])
    cep_input = col1.text_input("Digite o CEP")
    
    # MUDANÇA AQUI: O botão de busca agora está FORA do st.form
    if col2.button("Buscar Endereço"):
        address_data, error_message = get_address_from_cep(cep_input)
        if error_message:
            st.warning(error_message)
            st.session_state.cep_data = {}
        else:
            st.session_state.cep_data = address_data
            st.success("Endereço encontrado! Os campos abaixo foram preenchidos.")
    
    st.divider()

    # MUDANÇA AQUI: O st.form começa DEPOIS da lógica do CEP
    with st.form("cadastro_cliente"):
        st.subheader("2. Preencher Dados do Cliente")

        # Campos de endereço usam os valores do session_state
        cep_data = st.session_state.cep_data

        col1, col2 = st.columns(2)
        nome = col1.text_input("Nome*")
        razao_social = col2.text_input("Razão Social")
        cnpj = col1.text_input("CNPJ")
        inscricao_estadual = col2.text_input("Inscrição Estadual")

        email = col1.text_input("Email*")
        telefone = col2.text_input("Telefone")
        
        contato = st.text_input("Nome do Contato")

        # Os campos de endereço agora são preenchidos com base na busca anterior
        endereco = st.text_input("Endereço", value=cep_data.get("logradouro", ""))
        
        col1, col2 = st.columns([2,1])
        cidade = col1.text_input("Cidade", value=cep_data.get("localidade", ""))
        
        uf_index = 0
        if cep_data.get("uf") in UFS_BRASIL:
            uf_index = UFS_BRASIL.index(cep_data.get("uf"))
        uf = col2.selectbox("UF", UFS_BRASIL, index=uf_index)
        
        forma_pagamento = st.text_input("Forma de Pagamento")

        # Este é o único botão permitido dentro de um formulário
        submitted = st.form_submit_button("Cadastrar Cliente")
        if submitted:
            if not nome or not email:
                st.error("Os campos 'Nome' e 'Email' são obrigatórios.")
            elif not is_valid_email(email):
                st.error("Formato de email inválido.")
            else:
                client_data = {
                    "Nome": nome,
                    "Razao Social": razao_social,
                    "CNPJ": format_cnpj(cnpj),
                    "Endereco": endereco,
                    "CEP": format_cep(cep_input), # Usamos o cep_input original
                    "Cidade": cidade,
                    "UF": uf,
                    "Inscriricao Estadual": inscricao_estadual,
                    "Email": email,
                    "Telefone": format_telefone(telefone),
                    "Forma de Pagamento": forma_pagamento,
                    "Contato": contato,
                    "Status": "Ativo"
                }
                new_client_df = pd.DataFrame([client_data])
                st.session_state.df_clientes = pd.concat([st.session_state.df_clientes, new_client_df], ignore_index=True)
                storage.save_csv(st.session_state.df_clientes, config.CLIENTES_FILE)
                st.success(f"Cliente '{nome}' cadastrado com sucesso!")
                st.session_state.cep_data = {} # Limpa o cache do CEP

    st.divider()
    st.write("### Clientes Cadastrados")
    st.dataframe(st.session_state.df_clientes, width='stretch')

def display_history_page():
    """Renderiza a página de histórico de orçamentos para o usuário logado."""
    st.title("📜 Histórico de Orçamentos")
    
    # Filtra o DataFrame de orçamentos para mostrar apenas os do usuário atual
    user_history = st.session_state.df_orcamentos[
        st.session_state.df_orcamentos["Usuario"] == st.session_state.username
    ]
    
    if not user_history.empty:
        st.dataframe(user_history, width='stretch')
    else:
        st.info("Nenhum orçamento salvo para este usuário.")

def render_component_selector(component_type: str, df_items: pd.DataFrame, paper_options: list) -> dict:
    """
    Renderiza um seletor genérico para componentes (Miolo, Bolsa, etc.).
    Retorna um dicionário com as seleções do usuário.
    """
    st.markdown(f"#### {component_type}")
    item_col_name = df_items.columns[0]
    item_list = sorted(df_items[item_col_name].dropna().unique())
    options = ["Nenhum", "Personalizado"] + item_list

    selected_item = st.selectbox(f"Selecione o {component_type}:", options, key=f"sel_{component_type.lower()}")

    result = {"selection": selected_item}
    if selected_item == "Personalizado":
        col1, col2, col3 = st.columns(3)
        result["paper"] = col1.selectbox(f"Papel ({component_type})", paper_options, key=f"paper_{component_type.lower()}")
        result["utilization"] = col2.number_input(f"Aproveitamento", min_value=0.1, value=5.0, step=0.1, key=f"util_{component_type.lower()}")
        result["service_cost"] = col3.number_input(f"Valor do serviço", min_value=0.0, value=1000.0, step=50.0, key=f"serv_{component_type.lower()}")

    return result

def render_direct_purchase_selector(category: str, items: list, wireo_map: dict) -> dict:
    """
    Renderiza um seletor genérico para itens de compra direta.
    Retorna um dicionário com o custo calculado e detalhes.
    """
    st.markdown(f"##### {category}")
    item_names = [item['NomeLimpo'] for item in items]
    options = ["Nenhum", "Personalizado"] + sorted(item_names)

    selected_item = st.selectbox(f"Selecione:", options, key=f"cd_{category}", label_visibility="collapsed")

    cost_info = {"cost": 0.0, "details": "Nenhum"}

    if selected_item == "Personalizado":
        val_unit = st.number_input(f"Valor unitário pers.", min_value=0.0, value=1.0, key=f"vu_{category}", step=0.1)
        util = st.number_input(f"Aproveitamento", min_value=0.01, value=1.0, step=0.01, key=f"util_cd_{category}")
        cost_info["cost"] = val_unit * util
        cost_info["details"] = f"Personalizado (R$ {val_unit:.2f} * {util}) = R$ {cost_info['cost']:.4f}"

    elif selected_item != "Nenhum":
        item_data = next((i for i in items if i['NomeLimpo'] == selected_item), None)
        if item_data:
            price = item_data['VALOR_UNITARIO']
            last_nf = item_data['ULTIMA_NF']

            if category == "WIRE-O":
                qty_box = wireo_map.get(selected_item, 6000)
                rings = st.number_input(f"Nº de anéis por unidade", min_value=1, value=30, step=1, key=f"rings_{selected_item}")
                cost_info["cost"] = (price / qty_box) * rings if qty_box > 0 else 0
            else:
                util = st.number_input(f"Aproveitamento ({selected_item})", min_value=0.01, value=1.0, step=0.01, key=f"util_{selected_item}")
                cost_info["cost"] = price * util

            cost_info["details"] = f"{selected_item} (NF: {last_nf})"

    return cost_info

def display_admin_panel():
    """Renderiza a página de gerenciamento de usuários, clientes e orçamentos para o admin."""
    st.title("🔑 Painel de Administração")
    
    tab1, tab2, tab3 = st.tabs(["Gerenciar Usuários", "Visualizar Clientes", "Visualizar Orçamentos"])

    with tab1:
        st.write("### Gerenciamento de Usuários")
        users_df = st.session_state.df_usuarios.copy()
        
        if users_df.empty:
            st.info("Nenhum usuário cadastrado.")
        else:
            # Itera sobre cada usuário para criar um painel de gerenciamento individual
            for index, user in users_df.iterrows():
                st.subheader(f"Usuário: {user['usuario']} ({user['nome_completo']})")
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.write(f"**Status:** {user['status']}")
                    if user['status'] == 'pendente':
                        if st.button("✅ Aprovar", key=f"approve_{user['usuario']}"):
                            st.session_state.df_usuarios.loc[index, 'status'] = 'ativo'
                            storage.save_csv(st.session_state.df_usuarios, config.USERS_FILE)
                            st.success(f"Usuário {user['usuario']} aprovado!")
                            st.rerun()

                with col2:
                    st.write(f"**Role:** {user['role']}")
                    if user['role'] != 'admin':
                        if st.button("⬆️ Promover a Admin", key=f"promote_{user['usuario']}"):
                            st.session_state.df_usuarios.loc[index, 'role'] = 'admin'
                            storage.save_csv(st.session_state.df_usuarios, config.USERS_FILE)
                            st.success(f"Usuário {user['usuario']} promovido a admin!")
                            st.rerun()

                with col3:
                    # Impede que o admin desative a si mesmo
                    if user['status'] == 'ativo' and user['usuario'] != st.session_state.username:
                        if st.button("❌ Desativar", key=f"deactivate_{user['usuario']}"):
                            st.session_state.df_usuarios.loc[index, 'status'] = 'inativo'
                            storage.save_csv(st.session_state.df_usuarios, config.USERS_FILE)
                            st.warning(f"Usuário {user['usuario']} desativado.")
                            st.rerun()
                st.divider()

    with tab2:
        st.write("### Registros de Clientes")
        st.dataframe(st.session_state.df_clientes, width='stretch')

    with tab3:
        st.write("### Registros de Orçamentos")
        st.dataframe(st.session_state.df_orcamentos, width='stretch')
