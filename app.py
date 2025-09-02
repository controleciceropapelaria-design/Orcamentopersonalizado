# orcamento_pro/app.py
"""
Ponto de entrada principal da aplicação Streamlit "Orçamento Pro".
Orquestra a UI, o gerenciamento de estado e as chamadas para os outros módulos.
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import re

# Importa os módulos da aplicação
import config
import storage
import auth
import data_services as ds
import ui_components as ui
import calculations as calc

# ================== CONFIGURAÇÃO DA PÁGINA E ESTADO INICIAL ==================
st.set_page_config(page_title="📄 Orçamento Pro", layout="wide")

# orcamento_pro/app.py
# ... (imports e outras funções) ...

def initialize_session_state():
    """Inicializa o estado da sessão para login e DataFrames."""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.full_name = ""
        st.session_state.role = "" # Adiciona role ao estado da sessão

    storage.initialize_session_state_df('df_usuarios', config.USERS_FILE, config.COLUNAS_USUARIOS)
    storage.initialize_session_state_df('df_clientes', config.CLIENTES_FILE, config.COLUNAS_CLIENTES)
    storage.initialize_session_state_df('df_orcamentos', config.ORCAMENTOS_FILE, config.COLUNAS_ORCAMENTOS)

# ... (função budget_page) ...
# ================== LÓGICA DE ORÇAMENTO ==================
def budget_page():
    """Renderiza a página principal de criação de orçamento."""
    st.title("📐 Criação de Orçamento")

    # --- Carregar todos os dados externos ---
    try:
        df_paper = ds.load_paper_purchases()
        df_miolos = ds.load_component_data(config.URL_USO_PAPEL_MIOLO, ['Miolo', 'Papel', 'QuantidadePapel', 'ValorImpressao', 'UnitImpressao', 'QuantidadeAprovada'])
        df_bolsas = ds.load_component_data(config.URL_USO_PAPEL_BOLSA, ['Bolsa', 'Papel', 'QuantidadePapel', 'ValorImpressao', 'UnitImpressao', 'QuantidadeAprovada'])
        df_divisorias = ds.load_component_data(config.URL_USO_PAPEL_DIVISORIA, ['Divisoria', 'Papel', 'QuantidadePapel', 'ValorImpressao', 'UnitImpressao', 'QuantidadeAprovada'])
        df_adesivos = ds.load_component_data(config.URL_USO_PAPEL_ADESIVO, ['Adesivo', 'Papel', 'QuantidadePapel', 'ValorImpressao', 'UnitImpressao', 'QuantidadeAprovada'])
        direct_purchases_cats = ds.load_direct_purchases()
        wireo_map = ds.load_wireo_table()
        df_mod_ggf = ds.load_mod_ggf_data() # <-- NOVO: Carrega os dados de MOD/GGF
        
        paper_options = sorted(df_paper['PapelLimpo'].dropna().unique())
    except Exception as e:
        st.error(f"❌ Erro fatal ao carregar dados externos: {e}")
        st.stop()

    # --- Entradas do Usuário ---
    col1, col2 = st.columns([2,1])
    client_list = [""] + st.session_state.df_clientes["Nome"].tolist()
    selected_client = col1.selectbox("Selecione o Cliente", client_list)
    budget_quantity = col2.number_input("Quantidade total do orçamento:", min_value=1, value=15000, step=100)

    st.divider()
    
    all_costs = []
    
    with st.container(border=True):
        st.markdown("### 📕 Capa")
        selected_product = st.selectbox("Selecione o produto:", options=[""] + sorted(config.PRODUTOS_BASE))

        if selected_product:
            cover_cost_result = None
            if "COURO SINTÉTICO" in selected_product:
                paper_cover_options = [p for p in paper_options if 'couro' in p.lower() or 'percalux' in p.lower()]
                selected_paper_cover = st.selectbox("Material da capa", options=[""] + sorted(paper_cover_options))
                if selected_paper_cover:
                    cover_cost_result = calc.calculate_leather_cover_cost(selected_paper_cover, df_paper)
            else: # POLICROMIA
                paper_cover_options = [p for p in paper_options if 'couche' in p.lower() or 'policromia' in p.lower()]
                selected_paper_cover = st.selectbox("Papel da capa", options=[""] + sorted(paper_cover_options))
                
                if selected_paper_cover:
                    product_base = selected_product.replace(" - POLICROMIA", "")
                    impression_url = config.CSV_MAP_IMPRESSAO.get(product_base)
                    if impression_url:
                        df_impression = ds.load_impression_table(impression_url)
                        cover_cost_result = calc.calculate_offset_cover_cost(budget_quantity, selected_paper_cover, df_paper, df_impression)
                    else:
                        st.warning(f"Tabela de impressão não encontrada para '{product_base}'.")

            # Adiciona custo da capa à lista
            if cover_cost_result and not cover_cost_result.get("error"):
                all_costs.append({"name": "Capa", "cost": cover_cost_result["total_cost_unit"], "details": cover_cost_result["paper_name"]})
            elif cover_cost_result and cover_cost_result.get("error"):
                st.error(f"Capa: {cover_cost_result['error']}")
    
    col_comp, col_cd = st.columns(2)

    with col_comp:
        with st.container(border=True):
            st.markdown("### 📄 Componentes Adicionais")
            component_map = {
                "Miolo": df_miolos, "Bolsa": df_bolsas,
                "Divisória": df_divisorias, "Adesivo": df_adesivos
            }
            for comp_type, df_comp in component_map.items():
                selection = ui.render_component_selector(comp_type, df_comp, paper_options)
                comp_cost_result = None
                if selection["selection"] == "Personalizado" and selection.get("paper"):
                    comp_cost_result = calc.calculate_custom_component_cost(selection["paper"], selection["utilization"], selection["service_cost"], budget_quantity, df_paper)
                elif selection["selection"] != "Nenhum":
                    comp_cost_result = calc.calculate_component_cost(selection["selection"], df_comp, df_paper, budget_quantity, comp_type)

                if comp_cost_result and not comp_cost_result.get("error"):
                    all_costs.append({"name": selection["selection"], "cost": comp_cost_result["total_cost_unit"], "details": f"Papel: {comp_cost_result['paper_name']} (NF: {comp_cost_result.get('last_nf_date', 'N/A')})"})
                elif comp_cost_result and comp_cost_result.get("error"):
                    st.error(f"{comp_type}: {comp_cost_result['error']}")

    with col_cd:
        with st.container(border=True):
            st.markdown("### 🔧 Compras Diretas (Aviamentos)")
            for category, items in sorted(direct_purchases_cats.items()):
                cost_info = ui.render_direct_purchase_selector(category, items, wireo_map)
                if cost_info["cost"] > 0:
                    all_costs.append({"name": category, "cost": cost_info["cost"], "details": cost_info["details"]})

# orcamento_pro/app.py -> DENTRO DE budget_page()

     # --- Lógica de MOD e GGF ---
    if selected_product and not df_mod_ggf.empty:
        try:
            # A padronização continua sendo uma boa prática
            produto_padronizado = re.sub(r'\s+', ' ', selected_product.strip().upper())
            
            # A busca pela linha do produto está correta
            custos_extras = df_mod_ggf.loc[produto_padronizado]
            
            # --- CORREÇÃO PRINCIPAL AQUI ---
            # Acessamos a coluna correta 'MOD+GGF' e a tratamos como um custo único.
            mod_ggf_cost = custos_extras['MOD+GGF']
            
            # Adicionamos o custo combinado à lista de custos
            all_costs.append({
                "name": "MOD + GGF", 
                "cost": mod_ggf_cost, 
                "details": "Custo combinado (Mão de Obra + Gastos Gerais)"
            })

        except KeyError:
            # Este aviso agora só aparecerá se o PRODUTO realmente não estiver na lista
            st.warning(f"⚠️ Produto '{selected_product}' não encontrado na tabela de custos MOD/GGF. Custos não aplicados.")


    # --- Resultados e Cálculo do Preço de Venda ---
    st.divider()
    st.subheader("💰 Resumo Financeiro")
    
    base_total_cost = sum(item['cost'] for item in all_costs)
    
    if base_total_cost > 0:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Custo Base Unitário", f"R$ {base_total_cost:,.4f}".replace('.', ','))
            
            with st.expander("Ver detalhes do custo"):
                cost_df_data = [{"Componente": item['name'], "Custo Unitário (R$)": item['cost'], "Detalhes": item['details']} for item in all_costs]
                cost_df = pd.DataFrame(cost_df_data)
                st.dataframe(cost_df, width='stretch',
                             column_config={"Custo Unitário (R$)": st.column_config.NumberColumn(format="R$ %.4f")})
        
        with col2:
            st.markdown("##### Definição de Preço")
            # --- NOVOS CAMPOS FINANCEIROS ---
            c1, c2 = st.columns(2)
            markup = c1.number_input("Markup", min_value=1.0, value=2.0, step=0.1, help="Fator multiplicador sobre o custo final. Ex: 2.0 para 100% de margem.")
            comissao_vendedor = c2.number_input("Comissão Vendedor (%)", min_value=0.0, value=1.5, step=0.1)
            
            # Adicionei um campo para Promotor conforme solicitado
            comissao_promotor = c2.number_input("Comissão Promotor (%)", min_value=0.0, value=1.7, step=0.1)
            
            # --- CÁLCULOS FINAIS ---
            total_comissao_percent = comissao_vendedor + comissao_promotor
            custo_com_comissao = base_total_cost * (1 + total_comissao_percent / 100)
            preco_venda = custo_com_comissao * markup

            st.metric("Custo Final (com Comissões)", f"R$ {custo_com_comissao:,.4f}".replace('.', ','), help="Custo Base + Comissões")
            st.metric("Preço de Venda Unitário", f"R$ {preco_venda:,.2f}".replace('.', ','), help="Custo Final com Comissões x Markup")

        st.divider()

        if st.button("💾 Salvar Orçamento"):
            if not selected_client or not selected_product:
                st.warning("Selecione um cliente e um produto para salvar o orçamento.")
            else:
                # Lógica de salvamento atualizada no Passo 3
                new_budget = {
                    "ID": f"ORC{int(datetime.now().timestamp())}",
                    "Usuario": st.session_state.username,
                    "Cliente": selected_client,
                    "Produto": selected_product,
                    "Quantidade": budget_quantity,
                    "CustoBase": round(base_total_cost, 4),
                    "ComissaoPct": total_comissao_percent,
                    "Markup": markup,
                    "PrecoVenda": round(preco_venda, 2),
                    "Data": datetime.now().strftime("%d/%m/%Y")
                }
                new_budget_df = pd.DataFrame([new_budget])
                st.session_state.df_orcamentos = pd.concat([st.session_state.df_orcamentos, new_budget_df], ignore_index=True)
                storage.save_csv(st.session_state.df_orcamentos, config.ORCAMENTOS_FILE)
                st.success(f"Orçamento {new_budget['ID']} salvo com sucesso!")
    else:
        st.info("Selecione os componentes para calcular o custo total.")

# ================== FLUXO PRINCIPAL DA APLICAÇÃO ==================
def main():
    """Função principal que controla o fluxo da aplicação."""
    initialize_session_state()

    # --- Bloco de Lógica para usuário NÃO LOGADO ---
    if not st.session_state.logged_in:
        page = st.sidebar.radio("Bem-vindo", ["Login", "Cadastrar Usuário"], label_visibility="collapsed")
        
        if page == "Login":
            submitted, username, password = ui.display_login_form()
            if submitted:
                # Chama a função de login que agora retorna (sucesso, mensagem)
                success, message = auth.login_user(username, password)
                
                # SÓ DÁ O RERUN SE O LOGIN FOR BEM-SUCEDIDO
                if success:
                    st.rerun()
                else:
                    # Se não for, exibe a mensagem de erro retornada
                    st.sidebar.error(message)

        elif page == "Cadastrar Usuário":
            submitted, user, pwd, name = ui.display_registration_form()
            if submitted:
                if user and pwd and name:
                    success, message = auth.register_user(user, pwd, name)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                else:
                    st.warning("Todos os campos são obrigatórios.")

    # --- Bloco de Lógica para usuário LOGADO ---
    else: 
        # Esta lista contém as páginas visíveis para TODOS os usuários logados.
        page_options = ["Orçamento", "Cadastro de Clientes", "Histórico de Orçamentos"]
        
        # A página de admin só é adicionada se o usuário tiver a role correta.
        if st.session_state.get("role") == "admin":
            page_options.append("Painel Admin")

        st.sidebar.success(f"Bem-vindo, {st.session_state.full_name}!")
        page = st.sidebar.radio("Navegação", page_options)
        
        if st.sidebar.button("Sair"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        if page == "Orçamento":
            budget_page()
        elif page == "Cadastro de Clientes":
            ui.display_client_registration_form()
        elif page == "Histórico de Orçamentos":
            ui.display_history_page()
        elif page == "Painel Admin":
            ui.display_admin_panel()

if __name__ == "__main__":
    main()
