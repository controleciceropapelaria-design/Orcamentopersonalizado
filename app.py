# orcamento_pro/app.py
"""
Ponto de entrada principal da aplicação Streamlit "Orçamento Pro".
Orquestra a UI, o gerenciamento de estado e as chamadas para os outros módulos.
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import re
import json
import os
import unicodedata

# Importa os módulos da aplicação
import config
import storage
import auth
import data_services as ds
import ui_components as ui
import calculations as calc
from generate_pdf import generate_proposal_pdf
from generate_ordem_prototipo import generate_ordem_prototipo_pdf

# ================== CONFIGURAÇÃO DA PÁGINA E ESTADO INICIAL ==================


st.set_page_config(
    page_title="📄 Orçamento Pro", 
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_session_state():
    """Inicializa o estado da sessão para login e DataFrames."""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.full_name = ""
        st.session_state.role = ""  # Adiciona role ao estado da sessão
        st.session_state.ajustes = []
        storage.initialize_session_state_df('df_orcamentos', config.ORCAMENTOS_FILE, config.COLUNAS_ORCAMENTOS)
        storage.initialize_session_state_df('df_templates', config.TEMPLATES_FILE, config.COLUNAS_TEMPLATES)

    storage.initialize_session_state_df('df_usuarios', config.USERS_FILE, config.COLUNAS_USUARIOS)
    storage.initialize_session_state_df('df_clientes', config.CLIENTES_FILE, config.COLUNAS_CLIENTES)
    storage.initialize_session_state_df('df_orcamentos', config.ORCAMENTOS_FILE, config.COLUNAS_ORCAMENTOS)

# orcamento_pro/app.py

# ================== LÓGICA DE ORÇAMENTO ==================
def budget_page():
    """Renderiza a página principal de criação de orçamento."""
    st.title("📐 Criação de Orçamento")

    # --- Dinâmica de edição: aviso e botão cancelar ---
    editing_id = st.session_state.get('editing_id')
    if editing_id:
        st.info(f"📝 Editando orçamento: {editing_id}")
        if st.button("Cancelar edição"):
            st.session_state.pop('editing_id')
            if 'edit_loaded' in st.session_state:
                st.session_state.pop('edit_loaded')
            st.session_state['page'] = "Histórico de Orçamentos"
            st.rerun()

    # Carrega os dados do orçamento para edição, se houver
    if editing_id and not st.session_state.get('edit_loaded'):
        df = st.session_state.df_orcamentos
        row = df[df['ID'] == editing_id]
        if not row.empty:
            row = row.iloc[0]
            selecoes = json.loads(row.get("SelecoesJSON", "{}"))
            for key, value in selecoes.items():
                st.session_state[key] = value
            # Preenche campos principais do formulário
            st.session_state['selected_client'] = row['Cliente']
            st.session_state['budget_quantity'] = int(row['Quantidade']) if str(row['Quantidade']).isdigit() else 15000
            st.session_state['sel_produto'] = row['Produto']
            # Preenche campos de acabamento
            def busca_acabamento(tipo, opcoes):
                # Prioriza valor salvo explicitamente
                if tipo in selecoes:
                    return selecoes[tipo]
                # Busca valor que bate com as opções
                for v in selecoes.values():
                    if v in opcoes:
                        return v
                return opcoes[0]
            st.session_state['selected_laminacao'] = busca_acabamento('selected_laminacao', ["Nenhum", "Laminação Fosca"])
            st.session_state['selected_hot_stamping'] = busca_acabamento('selected_hot_stamping', ["Nenhum", "Interno (sem custo adicional)", "Externo Pequeno", "Externo Grande"])
            st.session_state['selected_silk'] = busca_acabamento('selected_silk', ["Nenhum", "1/0","2/0","3/0","4/0"])
            st.session_state['edit_loaded'] = True

    # --- Carregar todos os dados externos ---
    try:
        df_paper = ds.load_paper_purchases()
        df_miolos = ds.load_component_data(config.URL_USO_PAPEL_MIOLO, ['Miolo', 'Papel', 'QuantidadePapel', 'ValorImpressao', 'UnitImpressao', 'QuantidadeAprovada'])
        df_bolsas = ds.load_component_data(config.URL_USO_PAPEL_BOLSA, ['Bolsa', 'Papel', 'QuantidadePapel', 'ValorImpressao', 'UnitImpressao', 'QuantidadeAprovada'])
        df_divisorias = ds.load_component_data(config.URL_USO_PAPEL_DIVISORIA, ['Divisoria', 'Papel', 'QuantidadePapel', 'ValorImpressao', 'UnitImpressao', 'QuantidadeAprovada'])
        df_adesivos = ds.load_component_data(config.URL_USO_PAPEL_ADESIVO, ['Adesivo', 'Papel', 'QuantidadePapel', 'ValorImpressao', 'UnitImpressao', 'QuantidadeAprovada'])
        df_guarda_forro = ds.load_component_data(config.URL_GUARDA_FORRO, ['Item', 'Papel', 'QuantidadePapel', 'ValorImpressao', 'UnitImpressao', 'QuantidadeAprovada'])
        df_guarda_verso = ds.load_component_data(config.URL_GUARDA_VERSO, ['GuardaVerso', 'Papel', 'QuantidadePapel', 'ValorImpressao', 'UnitImpressao', 'QuantidadeAprovada'])
        direct_purchases_cats = ds.load_direct_purchases()
        wireo_map = ds.load_wireo_table()
        df_mod_ggf = ds.load_mod_ggf_data()
        paper_options = sorted(df_paper['PapelLimpo'].dropna().unique())
    except Exception as e:
        st.error(f"❌ Erro fatal ao carregar dados externos: {e}")
        st.stop()

    # --- LÓGICA DE TEMPLATES ---
    st.header("Modelo de Orçamento")
    template_list = [""] + st.session_state.df_templates["NomeTemplate"].tolist()
    selected_template_name = st.selectbox("Carregar um modelo de orçamento", template_list, key="load_template_selector")
    if selected_template_name and st.button("Carregar Modelo"):
        template_data = st.session_state.df_templates[st.session_state.df_templates["NomeTemplate"] == selected_template_name].iloc[0]
        selections = json.loads(template_data["SelecoesJSON"])
        for key, value in selections.items():
            st.session_state[key] = value
        st.success(f"Modelo '{selected_template_name}' carregado!")
        st.rerun()

    # --- Entradas do Usuário ---
    col1, col2 = st.columns([2, 1])
    client_list = [""] + st.session_state.df_clientes["Nome"].tolist()
    selected_client = col1.selectbox(
        "Selecione o Cliente",
        client_list,
        index=client_list.index(st.session_state.get('selected_client', "")) if st.session_state.get('selected_client', "") in client_list else 0
    )
    budget_quantity = col2.number_input(
        "Quantidade total do orçamento:",
        min_value=1,
        value=st.session_state.get('budget_quantity', 15000),
        step=100
    )

    st.divider()

    all_costs = []
    direct_purchases_render = direct_purchases_cats.copy()
    direct_purchases_render.pop("COURO", None)

    # --- Lógica da Capa ---
    with st.container(border=True):
        st.markdown("### 📕 Capa")
        # Corrige conflito de Session State e valor default do selectbox
        produto_options = [""] + sorted(config.PRODUTOS_BASE)
        if 'sel_produto' in st.session_state and st.session_state['sel_produto'] in produto_options:
            selected_product = st.selectbox(
                "Selecione o produto:",
                options=produto_options,
                key="sel_produto"
            )
        else:
            selected_product = st.selectbox(
                "Selecione o produto:",
                options=produto_options,
                key="sel_produto",
                index=0
            )
        hot_stamping_options = ["Nenhum", "Interno (sem custo adicional)", "Externo Pequeno", "Externo Grande"]
        selected_hot_stamping = st.selectbox("Acabamento: Hot Stamping", options=hot_stamping_options, key="selected_hot_stamping")
        laminacao_options = ["Nenhum", "Laminação Fosca"]
        selected_laminacao = st.selectbox("Acabamento: Laminação", options=laminacao_options, key="selected_laminacao")
        silk_options = ["Nenhum", "1/0","2/0","3/0","4/0"]
        selected_silk = st.selectbox("Acabamento: SILK", options=silk_options, key="selected_silk")
        cover_cost_result = None
        if selected_product:
            if "COURO SINTÉTICO" in selected_product:
                direct_purchases_render.pop("COURO", None)
                leather_materials = ds.load_leather_materials(direct_purchases_cats)
                if not leather_materials:
                    st.warning("⚠️ Nenhum material 'COURO' encontrado.")
                else:
                    selected_leather = st.selectbox("Material da Capa", options=[""] + leather_materials, key="sel_capa_couro")
                    if selected_leather:
                        # NOVO: cálculo com aproveitamento da faca
                        cover_cost_result = calc.calculate_synthetic_leather_cover_cost(
                            selected_product,
                            selected_leather,
                            budget_quantity,
                            direct_purchases_cats
                        )
            else:
                paper_cover_options = [p for p in paper_options if 'couche' in p.lower() or 'policromia' in p.lower()]
                c1, c2 = st.columns(2)
                selected_paper_cover = c1.selectbox("Papel da capa", options=[""] + sorted(paper_cover_options), key="sel_capa_papel")
                impression_options = ["", "Offset", "Digital 4/0", "Digital 4/1", "Digital 1/0", "Digital 1/1"]
                impression_type = c2.selectbox("Tipo de Impressão", options=impression_options, key="sel_capa_impressao")
                if selected_paper_cover and impression_type:
                    product_base = selected_product.replace(" - POLICROMIA", "")
                    if "Offset" in impression_type:
                        impression_url = config.CSV_MAP_IMPRESSAO.get(product_base)
                        if impression_url:
                            df_impression = ds.load_impression_table(impression_url)
                            cover_cost_result = calc.calculate_offset_cover_cost(product_base, budget_quantity, selected_paper_cover, df_paper, df_impression)
                    elif "Digital" in impression_type:
                        cover_cost_result = calc.calculate_digital_cover_cost(selected_product, selected_paper_cover, impression_type, budget_quantity, df_paper)
            if cover_cost_result and not cover_cost_result.get("error"):
                paper_cost = cover_cost_result.get("paper_cost_unit", 0)
                if paper_cost > 0:
                    all_costs.append({"name": "Capa - Papel/Material", "cost": paper_cost, "details": cover_cost_result.get('paper_name', 'N/A'), "category": "Papel/Material"})
                service_cost = cover_cost_result.get("service_cost_unit", 0)
                if service_cost > 0:
                    all_costs.append({"name": "Capa - Impressão", "cost": service_cost, "details": "Serviço de impressão da capa", "category": "Impressão/Serviços"})
            elif cover_cost_result and cover_cost_result.get("error"):
                st.error(f"Capa: {cover_cost_result['error']}")

    # --- NOVO: Adiciona o custo do Hot Stamping à lista ---
    if selected_hot_stamping != "Nenhum":
        hot_stamping_cost_result = calc.calculate_hot_stamping_cost(selected_hot_stamping, budget_quantity)
        if hot_stamping_cost_result and not hot_stamping_cost_result.get("error"):
            cost = hot_stamping_cost_result.get("total_cost_unit", 0)
            if cost > 0:
                all_costs.append({
                    "name": "Acabamento - Hot Stamping",
                    "cost": cost,
                    "details": hot_stamping_cost_result.get("details", "Acabamento - Hot Stamping"),
                    "category": "Impressão/Serviços"
                })
        elif hot_stamping_cost_result and hot_stamping_cost_result.get("error"):
            st.error(f"Hot Stamping: {hot_stamping_cost_result['error']}")

    # --- NOVO: Adiciona o custo de Laminação à lista ---
    if selected_laminacao != "Nenhum" and cover_cost_result and not cover_cost_result.get("error"):
        if "Digital" in impression_type:
            lamination_cost_result = calc.calculate_lamination_cost(
                impression_type,
                selected_paper_cover,
                budget_quantity,
                df_paper,
                digital_sheets=cover_cost_result.get("folhas_uteis_necessarias"),
                product_name=selected_product
            )
        else:  # Offset
            lamination_cost_result = calc.calculate_lamination_cost(
                impression_type,
                selected_paper_cover,
                budget_quantity,
                df_paper,
                offset_sheets=cover_cost_result.get("quantity"),
                product_name=selected_product
            )
        if lamination_cost_result and not lamination_cost_result.get("error"):
            cost = lamination_cost_result.get("total_cost_unit", 0)
            if cost > 0:
                all_costs.append({
                    "name": "Acabamento - Laminação",
                    "cost": cost,
                    "details": lamination_cost_result.get("details", ""),
                    "category": "Impressão/Serviços"
                })
        elif lamination_cost_result and lamination_cost_result.get("error"):
            st.error(f"Laminação: {lamination_cost_result['error']}")

    # --- NOVO: Adiciona o custo de Silk à lista ---
    if selected_silk != "Nenhum":
        silk_cost_result = calc.calculate_silk_cost(selected_silk, budget_quantity)
        if silk_cost_result and not silk_cost_result.get("error"):
            cost = silk_cost_result.get("total_cost_unit", 0)
            if cost > 0:
                all_costs.append({
                    "name": f"Acabamento - Silk {selected_silk}",
                    "cost": cost,
                    "details": silk_cost_result.get("details", ""),
                    "category": "Impressão/Serviços"
                })
        elif silk_cost_result and silk_cost_result.get("error"):
            st.error(f"Silk: {silk_cost_result['error']}")

    # --- Função Auxiliar para Adicionar Custos ---
    def add_component_costs_to_list(result, selection_dict):
        if result and not result.get("error"):
            paper_cost = result.get("paper_cost_unit", 0)
            if paper_cost > 0:
                paper_name = selection_dict.get("paper", "Material Personalizado") if selection_dict["selection"] == "Personalizado" else result.get('paper_name')
                all_costs.append({"name": f"{selection_dict['selection']} - Material", "cost": paper_cost, "details": f"Papel: {paper_name}", "category": "Papel/Material"})
            service_cost = result.get("service_cost_unit", 0)
            if service_cost > 0:
                all_costs.append({"name": f"{selection_dict['selection']} - Serviço", "cost": service_cost, "details": "Custo de serviço do componente", "category": "Impressão/Serviços"})
        elif result and result.get("error"):
            st.error(f"{selection_dict['selection']}: {result['error']}")

    # --- Renderização dos Componentes e Compras Diretas ---
    col_comp, col_cd = st.columns(2)
    with col_comp:
        with st.container(border=True):
            st.markdown("### 📄 Componentes Adicionais")
            
            component_configs = {
                "Guarda (Frente) ou Forro": {"df": df_guarda_forro, "col": "Item"},
                "Miolo": {"df": df_miolos, "col": "Miolo"},
                "Bolsa": {"df": df_bolsas, "col": "Bolsa"},
                "Divisória": {"df": df_divisorias, "col": "Divisoria"},
                "Adesivo": {"df": df_adesivos, "col": "Adesivo"},
            }

            selection_guarda_frente = None
            for title, config_data in component_configs.items():
                selection = ui.render_component_selector(title, config_data["df"], paper_options)
                if title == "Guarda (Frente) ou Forro":
                    selection_guarda_frente = selection

                comp_cost_result = None
                if selection["selection"] == "Personalizado":
                    if selection.get("total_material_cost", 0) > 0 or selection.get("total_service_cost", 0) > 0:
                        comp_cost_result = calc.calculate_custom_component_cost(total_material_cost=selection["total_material_cost"], total_service_cost=selection["total_service_cost"], budget_quantity=budget_quantity)
                elif selection["selection"] != "Nenhum":
                    comp_cost_result = calc.calculate_component_cost(selection["selection"], config_data["df"], df_paper, budget_quantity, config_data["col"])
                
                add_component_costs_to_list(comp_cost_result, selection)
                st.divider()

            if selection_guarda_frente and "guarda" in selection_guarda_frente["selection"].lower():
                selection_gv = ui.render_component_selector("Guarda (Verso)", df_guarda_verso, paper_options)
                comp_cost_result_gv = None
                if selection_gv["selection"] == "Personalizado":
                    if selection_gv.get("total_material_cost", 0) > 0 or selection_gv.get("total_service_cost", 0) > 0:
                       comp_cost_result_gv = calc.calculate_custom_component_cost(total_material_cost=selection_gv["total_material_cost"], total_service_cost=selection_gv["total_service_cost"], budget_quantity=budget_quantity)
                elif selection_gv["selection"] != "Nenhum":
                    comp_cost_result_gv = calc.calculate_component_cost(selection_gv["selection"], df_guarda_verso, df_paper, budget_quantity, "GuardaVerso")
                
                add_component_costs_to_list(comp_cost_result_gv, selection_gv)

    with col_cd:
        with st.container(border=True):
            st.markdown("### 🔧 Compras Diretas (Aviamentos)")
            for category, items in sorted(direct_purchases_render.items()):
                cost_info = ui.render_direct_purchase_selector(category, items, wireo_map)
                if cost_info["cost"] > 0:
                    all_costs.append({
                        "name": category,
                        "cost": cost_info["cost"],
                        "details": cost_info["details"],
                        "category": "Aviamentos",
                        "aproveitamento": cost_info.get("util", 1)  # Pega o aproveitamento do cost_info
                    })

    # --- Lógica de MOD e GGF ---
    if selected_product and not df_mod_ggf.empty:
        try:
            produto_padronizado = re.sub(r'\s+', ' ', selected_product.strip().upper())
            custos_extras = df_mod_ggf.loc[produto_padronizado]
            mod_ggf_cost = custos_extras['MOD+GGF']
            all_costs.append({"name": "MOD + GGF", "cost": mod_ggf_cost, "details": "Custo combinado", "category": "MOD+GGF"})
        except KeyError:
            st.warning(f"⚠️ Produto '{selected_product}' não encontrado na tabela de custos MOD/GGF.")

 # --- SALVAR TEMPLATE (LÓGICA CORRIGIDA E ROBUSTA) ---
    if not editing_id:
        st.divider()
        with st.container(border=True):
            st.subheader("Salvar como Modelo")
            new_template_name = st.text_input("Nome do novo modelo")
            if st.button("Salvar Configuração Atual como Modelo"):
                if not new_template_name:
                    st.warning("Por favor, dê um nome ao modelo.")
                elif new_template_name in st.session_state.df_templates["NomeTemplate"].values:
                    st.error(f"O nome de modelo '{new_template_name}' já existe.")
                else:
                    current_selections = {}
                    for key, value in st.session_state.items():
                        if key.startswith(('sel_', 'paper_', 'mat_cost_', 'serv_cost_', 'util_', 'rings_', 'vu_', 'cd_')):
                            current_selections[key] = value
                    new_template = {"NomeTemplate": new_template_name, "SelecoesJSON": json.dumps(current_selections)}
                    new_template_df = pd.DataFrame([new_template])
                    st.session_state.df_templates = pd.concat([st.session_state.df_templates, new_template_df], ignore_index=True)
                    storage.save_csv(st.session_state.df_templates, config.TEMPLATES_FILE)
                    # Salva no GitHub após criar template
                    storage.save_templates_to_github(st.session_state.df_templates, st.secrets["github_token"])
                    st.success(f"Modelo '{new_template_name}' salvo com sucesso!")
                    st.rerun()

    # --- Resultados e Cálculo do Preço de Venda ---
    st.divider()
    st.subheader("💰 Resumo Financeiro")

    if all_costs:
        custo_componentes = sum(item['cost'] for item in all_costs)
        
        with st.container(border=True):
            st.markdown("##### Resumo de Custos por Categoria")
            categorias_custo = {
                "Papel/Material": sum(c['cost'] for c in all_costs if c.get("category") == "Papel/Material"),
                "Impressão/Serviços": sum(c['cost'] for c in all_costs if c.get("category") == "Impressão/Serviços"),
                "Aviamentos": sum(c['cost'] for c in all_costs if c.get("category") == "Aviamentos"),
                "MOD+GGF": sum(c['cost'] for c in all_costs if c.get("category") == "MOD+GGF")
            }
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Papel/Material", f"R$ {categorias_custo['Papel/Material']:,.2f}")
            c2.metric("Impressão/Serviços", f"R$ {categorias_custo['Impressão/Serviços']:,.2f}")
            c3.metric("Aviamentos", f"R$ {categorias_custo['Aviamentos']:,.2f}")
            c4.metric("MOD+GGF", f"R$ {categorias_custo['MOD+GGF']:,.2f}")

        # Seção de Ajustes Dinâmicos
        if st.session_state.get("role") in ["admin", "orcamentista"]:
            with st.container(border=True):
                st.markdown("##### Ajustes Manuais de Custo")
                with st.form("add_ajuste_form", clear_on_submit=True):
                    c1, c2 = st.columns(2)
                    new_ajuste_desc = c1.text_input("Componente/Motivo do Novo Ajuste")
                    new_ajuste_valor = c2.number_input("Adicionar/Subtrair Valor (R$)", format="%.2f", step=1.0)
                    add_button = st.form_submit_button("Adicionar Ajuste")
                    if add_button and new_ajuste_desc and new_ajuste_valor != 0:
                        st.session_state.ajustes.append({"descricao": new_ajuste_desc, "valor": new_ajuste_valor})
                        st.experimental_rerun()
                if st.session_state.ajustes:
                    st.write("**Ajustes Adicionados:**")
                    for i, ajuste in enumerate(st.session_state.ajustes):
                        c1, c2, c3 = st.columns([3, 1, 1])
                        c1.write(f"- {ajuste['descricao']}")
                        c2.write(f"R$ {ajuste['valor']:,.2f}")
                        if c3.button("Remover", key=f"remove_ajuste_{i}"):
                            st.session_state.ajustes.pop(i)
                            st.experimental_rerun()
        
        # Detalhes dos Custos
        with st.expander("Ver detalhes do custo"):
            # Adiciona coluna de quantidade
            cost_rows = []
            for item in all_costs:
                quantidade = None
                # CAPA
                if item["name"].startswith("Capa"):
                    if "Impressão" in item["name"]:
                        quantidade = budget_quantity
                    else:
                        quantidade = cover_cost_result.get("quantity", budget_quantity)
                # Componentes Miolo, Guarda, Bolsa, Divisoria, Adesivo
                elif (
                    "Miolo" in item["name"]
                    or "Bolsa" in item["name"]
                    or "Divisória" in item["name"]
                    or "Adesivo" in item["name"]
                    or "GUARDA FRENTE" in item["name"]
                    or "GUARDA VERSO" in item["name"]
                ):
                    # Busca o DataFrame e linha do componente conforme o nome
                    comp_row = None
                    if "Miolo" in item["name"]:
                        df_comp = df_miolos
                        comp_col = "Miolo"
                        comp_nome = "Miolo"
                    elif "Bolsa" in item["name"]:
                        df_comp = df_bolsas
                        comp_col = "Bolsa"
                        comp_nome = "Bolsa"
                    elif "Divisória" in item["name"]:
                        df_comp = df_divisorias
                        comp_col = "Divisoria"
                        comp_nome = "Divisória"
                    elif "Adesivo" in item["name"]:
                        df_comp = df_adesivos
                        comp_col = "Adesivo"
                        comp_nome = "Adesivo"
                    elif "GUARDA FRENTE" in item["name"]:
                        df_comp = df_guarda_forro
                        comp_col = "Item"
                        comp_nome = "Guarda"
                    elif "GUARDA VERSO" in item["name"]:
                        df_comp = df_guarda_verso
                        comp_col = "GuardaVerso"
                        comp_nome = "Guarda"
                    else:
                        df_comp = None
                        comp_col = None
                        comp_nome = None

                    if df_comp is not None and comp_col is not None and comp_nome is not None:
                        try:
                            comp_row = df_comp[df_comp[comp_col].str.lower().str.contains(comp_nome.lower())].iloc[0]
                        except Exception:
                            comp_row = None

                    # Se for material, calcula a quantidade de folhas
                    if "Material" in item["name"] and comp_row is not None:
                        qtd_papel = comp_row["QuantidadePapel"]
                        qtd_aprovada = comp_row["QuantidadeAprovada"]
                        quantidade = (qtd_papel / qtd_aprovada) * budget_quantity if qtd_aprovada else budget_quantity
                    else:
                        quantidade = budget_quantity
                # ELÁSTICO, FITA DE CETIM, PAPELÃO (Aviamentos)
                else:
                    # --- NOVO: Verificação robusta para aviamentos ---
                    def normalize(s):
                        return unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('ASCII').lower()
                    aviamentos = [
                        "elastico", "fita de cetim", "papelao", "ilhos", "ferragem",
                        "rebites", "pendente", "saco adesivado", "wire-o"
                    ]
                    name_norm = normalize(item["name"])
                    if any(av in name_norm for av in aviamentos):
                        aproveitamento = item.get("aproveitamento", 1)
                        quantidade = aproveitamento * budget_quantity
                    # MOD+GGF
                    elif "MOD + GGF" in item["name"]:
                        quantidade = budget_quantity    
                    # ACABAMENTO HOT STAMPING
                    elif "Acabamento - Hot Stamping" in item["name"]:
                        quantidade = budget_quantity    
                    # ACABAMENTO LAMINAÇÃO
                    elif "Acabamento - Laminação" in item["name"]:
                        quantidade = budget_quantity
                    # ACABAMENTO SILK
                    elif "Acabamento - Silk" in item["name"]:   
                        quantidade = budget_quantity
                    else:
                        quantidade = ""
                row = item.copy()
                row["Quantidade"] = quantidade
                cost_rows.append(row)
            # Reordena colunas: name, Quantidade, cost, details
            cost_df = pd.DataFrame(cost_rows)
            cols = ["name", "Quantidade", "cost", "details"]
            cost_df = cost_df[[c for c in cols if c in cost_df.columns]]
            if "cost" in cost_df.columns:
                cost_df["cost"] = cost_df["cost"].round(2)
            if "Quantidade" in cost_df.columns:
                # NOVO: mostra casas decimais para Couro Sintético, inteiro para os demais
                def round_quantidade(row):
                    try:
                        val = row["Quantidade"]
                        # Se for None, vazio ou não numérico, retorna como está
                        if val is None or (isinstance(val, str) and not val.replace('.', '', 1).isdigit()):
                            return val
                        val = float(val)
                        if "Capa - Papel/Material" in row["name"] and cover_cost_result and "COURO SINTÉTICO" in str(cover_cost_result.get("details", "")):
                            return round(val, 2)
                        if cover_cost_result and "COURO SINTÉTICO" in str(cover_cost_result.get("details", "")) and row["name"].startswith("Capa"):
                            return round(val, 2)
                        return round(val, 0)
                    except Exception:
                        return row["Quantidade"]
                cost_df["Quantidade"] = cost_df.apply(round_quantidade, axis=1)
            cost_df = cost_df.copy()
            for col in cost_df.columns:
                # Se a coluna for object, tenta converter para número, senão converte para string
                if cost_df[col].dtype == "object":
                    try:
                        cost_df[col] = pd.to_numeric(cost_df[col])
                    except Exception:
                        cost_df[col] = cost_df[col].astype(str)
            st.dataframe(
                cost_df.drop(columns=['category'], errors='ignore'),
                width='stretch',
                column_config={
                    "cost": st.column_config.NumberColumn("Custo Unitário (R$)", format="R$ %.2f"),
                    "Quantidade": st.column_config.NumberColumn("Quantidade", format="%.0f")
                }
            )

        # Cálculos Finais e Exibição de Métricas
        ajuste_total_valor = sum(item['valor'] for item in st.session_state.ajustes)
        st.metric("Custo Base (Componentes + MOD/GGF)", f"R$ {custo_componentes:,.2f}".replace('.', ','))
        custo_ajustado = custo_componentes + ajuste_total_valor
        if ajuste_total_valor != 0:
            st.metric("Custo Ajustado", f"R$ {custo_ajustado:,.2f}".replace('.', ','), delta=f"R$ {ajuste_total_valor:,.2f} (Total de Ajustes)")
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### Definição de Preço")
            markup = st.number_input("Markup", min_value=1.0, value=2.0, step=0.1)
        with col2:
            st.markdown("##### Comissões")
            comissao_vendedor = st.number_input("Comissão Vendedor (%)", min_value=0.0, value=1.5, step=0.1)
            comissao_promotor = st.number_input("Comissão Promotor (%)", min_value=0.0, value=1.7, step=0.1)
        
        total_comissao_percent = comissao_vendedor + comissao_promotor
        custo_com_comissao = custo_ajustado * (1 + total_comissao_percent / 100)
        preco_venda = custo_com_comissao * markup
        st.metric("Custo Final (Ajustado + Comissões)", f"R$ {custo_com_comissao:,.2f}".replace('.', ','))
        st.metric("Preço de Venda Unitário Sugerido", f"R$ {preco_venda:,.2f}".replace('.', ','))
        st.divider()
        
        from generate_pdf import generate_proposal_pdf
        import os
                
        from collections import defaultdict

        if st.button("💾 Salvar e Gerar Proposta de Orçamento"):
            if not selected_client or not selected_product:
                st.warning("Selecione um cliente e um produto para salvar o orçamento.")
            else:
                validade_orcamento = "10 dias"
                prazo_entrega = "15 dias"

                # Busca dados do cliente selecionado
                cliente_row = st.session_state.df_clientes[st.session_state.df_clientes["Nome"] == selected_client]
                razao_social = cliente_row["Razao Social"].values[0] if not cliente_row.empty else selected_client
                contato_cliente = cliente_row["Contato"].values[0] if not cliente_row.empty else ""

                # Agrupamento e descrição dos componentes (igual ao seu código)
                grupos = defaultdict(list)
                for item in all_costs:
                    nome = item.get("name", "").strip()
                    detalhes = item.get("details", "")
                    nome_lower = nome.lower()
                    if "mod + ggf" in nome_lower:
                        continue
                    if nome_lower.startswith("capa"):
                        grupos["Capa"].append(f"{nome}: {detalhes}")
                    elif nome_lower.startswith("guarda"):
                        grupos["Guarda"].append(f"{nome}: {detalhes}")
                    elif nome_lower.startswith("miolo"):
                        grupos["Miolo"].append(f"{nome}: {detalhes}")
                    elif nome_lower.startswith("acabamento"):
                        grupos["Acabamento"].append(f"{nome}: {detalhes}")
                    elif nome_lower.startswith("bolsa") or nome_lower.startswith("servico de terceiro - bolsa"):
                        grupos["Bolsa"].append(f"{nome}: {detalhes}")
                    else:
                        grupos[nome].append(f"{nome}: {detalhes}")

                ordem = ["Capa", "Guarda", "Miolo", "Bolsa"]
                descricao_componentes = []
                for grupo in ordem:
                    if grupos[grupo]:
                        descricao_componentes.append(f"{grupo}:\n" + "\n".join(grupos[grupo]))
                for grupo in grupos:
                    if grupo not in ordem and grupo != "Acabamento":
                        descricao_componentes.append(f"{grupo}:\n" + "\n".join(grupos[grupo]))
                if grupos["Acabamento"]:
                    descricao_componentes.append("Acabamento:\n" + "\n".join(grupos["Acabamento"]))

                descricao_produto = "\n\n".join(descricao_componentes)

                # --- NOVO: Geração do número sequencial e versão ---
                editing_id = st.session_state.get('editing_id')
                if editing_id:
                    orcamento_id = editing_id
                    # Busca versão
                    idx = st.session_state.df_orcamentos[st.session_state.df_orcamentos['ID'] == editing_id].index[0]
                    versoes_json = st.session_state.df_orcamentos.loc[idx].get("VersoesJSON", "[]")
                    try:
                        versoes = json.loads(versoes_json)
                        versao_num = len(versoes) + 1
                    except Exception:
                        versao_num = 1
                else:
                    def get_next_orcamento_number():
                        """Gera o próximo número sequencial de orçamento com base no DataFrame atual."""
                        df = st.session_state.df_orcamentos
                        if "ID" in df.columns and not df.empty:
                            # IDs no formato ORC123, extrai o número
                            numeros = df["ID"].str.extract(r'ORC(\d+)')[0].dropna().astype(int)
                            if not numeros.empty:
                                return numeros.max() + 1
                        return 1
                    orcamento_num = get_next_orcamento_number()
                    orcamento_id = f"ORC{orcamento_num}"
                    versao_num = 1

                proposal_data = {
                    "data": datetime.now().strftime("%d/%m/%Y"),
                    "cliente": razao_social,
                    "responsavel": contato_cliente,
                    "numero_orcamento": orcamento_id,
                    "versao_orcamento": versao_num,
                    "produto": selected_product,
                    "quantidade": budget_quantity,
                    "descrição": descricao_produto,
                    "Unitario": round(preco_venda, 2),
                    "total": round(preco_venda * budget_quantity, 2),
                    "atendente": st.session_state.full_name,
                    "validade": validade_orcamento,
                    "prazo_de_entrega": prazo_entrega,
                }

                # Define o diretório de propostas
                propostas_dir = "Propostas"
                if not os.path.exists(propostas_dir):
                    os.makedirs(propostas_dir, exist_ok=True)
                output_pdf = os.path.join(
                    propostas_dir,
                    f"Proposta_{selected_client}_{selected_product}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                )
                generate_proposal_pdf(proposal_data, output_pdf)

                # Salva o PDF também no GitHub (pasta Propostas)
                with open(output_pdf, "rb") as fpdf:
                    import base64, requests
                    repo = "controleciceropapelaria-design/Orcamentoperosnalizado"
                    path = f"Propostas/{os.path.basename(output_pdf)}"
                    url = f"https://api.github.com/repos/{repo}/contents/{path}"
                    headers = {"Authorization": f"token {st.secrets['github_token']}"}
                    # Verifica se já existe para pegar o SHA
                    get_resp = requests.get(url, headers=headers)
                    sha = get_resp.json().get("sha") if get_resp.status_code == 200 else None
                    b64_content = base64.b64encode(fpdf.read()).decode()
                    data = {
                        "message": f"Upload proposta {os.path.basename(output_pdf)} via Streamlit",
                        "content": b64_content,
                        "branch": "main"
                    }
                    if sha:
                        data["sha"] = sha
                    put_resp = requests.put(url, headers=headers, json=data)
                    if put_resp.status_code in (200, 201):
                        st.success("Proposta PDF salva no GitHub!")
                    else:
                        st.warning("Não foi possível salvar a proposta PDF no GitHub.")

                # --- GERAÇÃO DA ORDEM DE PROTÓTIPO ---
                ordem_path = os.path.join(
                    propostas_dir,
                    f"OrdemPrototipo_{selected_client}_{selected_product}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                )
                generate_ordem_prototipo_pdf(proposal_data, ordem_path)
                if os.path.exists(ordem_path):
                    with open(ordem_path, "rb") as fpdf:
                        st.download_button("Baixar Ordem de Protótipo PDF", fpdf, file_name=os.path.basename(ordem_path))

                # --- Lógica de edição ou novo orçamento ---
                editing_id = st.session_state.get('editing_id')
                selecoes = {key: st.session_state[key] for key in st.session_state if key.startswith(('sel_', 'paper_', 'mat_cost_', 'serv_cost_', 'util_', 'rings_', 'vu_', 'cd_'))}
                # Adiciona campos de capa e acabamento explicitamente
                for extra_key in [
                    'selected_laminacao', 'selected_hot_stamping', 'selected_silk',
                    'sel_capa_papel', 'sel_capa_impressao', 'sel_capa_couro', 'sel_produto'
                ]:
                    if extra_key in st.session_state:
                        selecoes[extra_key] = st.session_state[extra_key]

                if editing_id:
                    # Atualiza orçamento existente e salva versão anterior acumulando todas as versões
                    idx = st.session_state.df_orcamentos[st.session_state.df_orcamentos['ID'] == editing_id].index[0]
                    orcamento_antigo = st.session_state.df_orcamentos.loc[idx].to_dict()
                    versoes = []
                    try:
                        versoes = json.loads(st.session_state.df_orcamentos.loc[idx].get("VersoesJSON", "[]"))
                    except Exception:
                        versoes = []
                    versoes.append({
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "data": orcamento_antigo
                    })
                    st.session_state.df_orcamentos.loc[idx, "VersoesJSON"] = json.dumps(versoes)
                    st.session_state.df_orcamentos.loc[idx, "VersoesOrcamento"] = len(versoes)
                    # Atualiza orçamento
                    st.session_state.df_orcamentos.loc[idx, "Cliente"] = selected_client
                    st.session_state.df_orcamentos.loc[idx, "Produto"] = selected_product
                    st.session_state.df_orcamentos.loc[idx, "Quantidade"] = budget_quantity
                    st.session_state.df_orcamentos.loc[idx, "CustoBase"] = round(custo_componentes, 4)
                    st.session_state.df_orcamentos.loc[idx, "ComissaoPct"] = total_comissao_percent
                    st.session_state.df_orcamentos.loc[idx, "Markup"] = markup
                    st.session_state.df_orcamentos.loc[idx, "PrecoVenda"] = round(preco_venda, 2)
                    st.session_state.df_orcamentos.loc[idx, "AjustesJSON"] = json.dumps(st.session_state.ajustes)
                    st.session_state.df_orcamentos.loc[idx, "Data"] = datetime.now().strftime("%d/%m/%Y")
                    st.session_state.df_orcamentos.loc[idx, "PropostaPDF"] = output_pdf
                    st.session_state.df_orcamentos.loc[idx, "SelecoesJSON"] = json.dumps(selecoes)
                    storage.save_csv(st.session_state.df_orcamentos, config.ORCAMENTOS_FILE)
                    # Salva no GitHub após editar orçamento
                    storage.save_orcamentos_to_github(st.session_state.df_orcamentos, st.secrets["github_token"])
                    st.session_state.ajustes = []
                    st.session_state.pop('editing_id')
                    if 'edit_loaded' in st.session_state:
                        st.session_state.pop('edit_loaded')
                    st.success(f"Orçamento {editing_id} editado com sucesso!")
                else:
                    # Cria novo orçamento
                    new_budget = {
                        "ID": orcamento_id,
                        "Usuario": st.session_state.username,
                        "NomeOrcamentista": st.session_state.full_name,
                        "Cliente": selected_client,
                        "Produto": selected_product,
                        "Quantidade": budget_quantity,
                        "CustoBase": round(custo_componentes, 4),
                        "ComissaoPct": total_comissao_percent,
                        "Markup": markup,
                        "PrecoVenda": round(preco_venda, 2),
                        "AjustesJSON": json.dumps(st.session_state.ajustes),
                        "Data": datetime.now().strftime("%d/%m/%Y"),
                        "PropostaPDF": output_pdf,
                        "SelecoesJSON": json.dumps(selecoes),
                        "StatusOrcamento": "Pendente",
                        "VersoesJSON": json.dumps([]),
                        "VersoesOrcamento": 1
                    }
                    # Antes de concatenar:
                    for col in config.COLUNAS_ORCAMENTOS:
                        if col not in new_budget:
                            new_budget[col] = ""  # valor padrão

                    new_budget_df = pd.DataFrame([new_budget])

                    # Garante que todos os campos sejam string ou número
                    for col in new_budget_df.columns:
                        if new_budget_df[col].dtype == "object":
                            new_budget_df[col] = new_budget_df[col].astype(str)
                    st.session_state.df_orcamentos = pd.concat([st.session_state.df_orcamentos, new_budget_df], ignore_index=True)[config.COLUNAS_ORCAMENTOS]
                    storage.save_csv(st.session_state.df_orcamentos, config.ORCAMENTOS_FILE)
                    # Salva no GitHub após criar orçamento
                    storage.save_orcamentos_to_github(st.session_state.df_orcamentos, st.secrets["github_token"])
                    st.session_state.ajustes = []
                    st.success(f"Orçamento {new_budget['ID']} salvo com sucesso!")

                # Download automático do PDF
                if os.path.exists(output_pdf):
                    with open(output_pdf, "rb") as fpdf:
                        st.download_button("Baixar Proposta PDF", fpdf, file_name=os.path.basename(output_pdf))

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
        page_options = ["Orçamento", "Cadastro de Clientes", "Histórico de Orçamentos"]
        if st.session_state.get("role") == "admin":
            page_options.append("Painel Admin")

        st.sidebar.success(f"Bem-vindo, {st.session_state.full_name}!")
        # Renderiza o menu lateral de navegação sempre, mesmo durante edição
        page = st.session_state.get('page')
        if page not in page_options:
            page = st.sidebar.radio("Navegação", page_options)
            st.session_state['page'] = page
        else:
            page = st.sidebar.radio("Navegação", page_options, index=page_options.index(page))
            st.session_state['page'] = page

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