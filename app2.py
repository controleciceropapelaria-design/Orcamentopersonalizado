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

# Importa os módulos da aplicação
import config
import storage
import auth
import data_services as ds
import ui_components as ui
import calculations as calc

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
    selected_client = col1.selectbox("Selecione o Cliente", client_list)
    budget_quantity = col2.number_input("Quantidade total do orçamento:", min_value=1, value=15000, step=100)

    st.divider()

    all_costs = []
    direct_purchases_render = direct_purchases_cats.copy()

    # --- CORREÇÃO DEFINITIVA DO COURO ---
    # Cria uma cópia do dicionário de compras diretas
    direct_purchases_render = direct_purchases_cats.copy()
    # Remove a categoria "COURO" incondicionalmente da cópia que será renderizada
    direct_purchases_render.pop("COURO", None)

    # --- Lógica da Capa ---
    with st.container(border=True):
        st.markdown("### 📕 Capa")
        selected_product = st.selectbox("Selecione o produto:", options=[""] + sorted(config.PRODUTOS_BASE), key="sel_produto")
# --- NOVO: Seletor de Hot Stamping ---
        hot_stamping_options = ["Nenhum", "Interno (sem custo adicional)", "Externo Pequeno", "Externo Grande"]
        selected_hot_stamping = st.selectbox("Acabamento: Hot Stamping", options=hot_stamping_options)
# --- NOVO: Seletor de Laminação ---
        laminacao_options = ["Nenhum", "Laminação Fosca"]
        selected_laminacao = st.selectbox("Acabamento: Laminação", options=laminacao_options)
# --- NOVO: Seletor de SILK ---
        silk_options = ["Nenhum", "1/0","2/0","3/0","4/0"]
        selected_silk = st.selectbox("Acabamento: SILK", options=silk_options)
        #Calculo de Capa
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
                        cover_cost_result = calc.calculate_leather_cover_cost(selected_leather, direct_purchases_cats)
            else: # Policromia
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
                    "details": hot_stamping_cost_result.get("details", ""), 
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
                # Itera sobre todas as chaves no estado da sessão
                for key, value in st.session_state.items():
                    # --- MUDANÇA AQUI: Captura TODAS as chaves relevantes ---
                    if key.startswith(('sel_', 'paper_', 'mat_cost_', 'serv_cost_', 'util_', 'rings_', 'vu_', 'cd_')):
                        current_selections[key] = value
                
                new_template = {"NomeTemplate": new_template_name, "SelecoesJSON": json.dumps(current_selections)}
                new_template_df = pd.DataFrame([new_template])
                st.session_state.df_templates = pd.concat([st.session_state.df_templates, new_template_df], ignore_index=True)
                storage.save_csv(st.session_state.df_templates, config.TEMPLATES_FILE)
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
                # ... (código dos ajustes que já funciona)
                st.markdown("##### Ajustes Manuais de Custo")
                with st.form("add_ajuste_form", clear_on_submit=True):
                    c1, c2 = st.columns(2)
                    new_ajuste_desc = c1.text_input("Componente/Motivo do Novo Ajuste")
                    new_ajuste_valor = c2.number_input("Adicionar/Subtrair Valor (R$)", format="%.2f", step=1.0)
                    add_button = st.form_submit_button("Adicionar Ajuste")
                    if add_button and new_ajuste_desc and new_ajuste_valor != 0:
                        st.session_state.ajustes.append({"descricao": new_ajuste_desc, "valor": new_ajuste_valor})
                        st.rerun()
                if st.session_state.ajustes:
                    st.write("**Ajustes Adicionados:**")
                    for i, ajuste in enumerate(st.session_state.ajustes):
                        c1, c2, c3 = st.columns([3, 1, 1])
                        c1.write(f"- {ajuste['descricao']}")
                        c2.write(f"R$ {ajuste['valor']:,.2f}")
                        if c3.button("Remover", key=f"remove_ajuste_{i}"):
                            st.session_state.ajustes.pop(i)
                            st.rerun()
        
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
                elif (
                    "ELASTICO" in item["name"]
                    or "FITA DE CETIM" in item["name"]
                    or "PAPELAO" in item["name"]
                    or "ILHOS" in item["name"]
                    or "FERRAGEM" in item["name"]
                    or "REBITES" in item["name"]
                    or "PENDENTE" in item["name"]
                    or "SACO ADESIVADO" in item["name"]
                    or "WIRE-O" in item["name"]
                ):
                    # Usa o aproveitamento informado pelo usuário
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
                cost_df["Quantidade"] = cost_df["Quantidade"].round(0)
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
        
        # Salvar Orçamento e Gerar Proposta em PDF
        if st.button("💾 Salvar e Gerar Proposta de Orçamento"):
            if not selected_client or not selected_product:
                st.warning("Selecione um cliente e um produto para salvar o orçamento.")
            else:
                # Defina a descrição do produto conforme sua lógica
                descricao_produto = f"{selected_product} - {budget_quantity} unidades"

                validade_orcamento = "10 dias"
                prazo_entrega = "15 dias"

                proposal_data = {
                    "data": datetime.now().strftime("%d/%m/%Y"),
                    "cliente": selected_client,
                    "responsavel": st.session_state.full_name,
                    "numero_orcamento": f"ORC{int(datetime.now().timestamp())}",
                    "produto": selected_product,
                    "quantidade": budget_quantity,
                    "descrição": descricao_produto,
                    "Unitario": round(preco_venda, 2),
                    "total": round(preco_venda * budget_quantity, 2),
                    "atendente": st.session_state.username,
                    "validade": validade_orcamento,
                    "prazo_de_entrega": prazo_entrega,
                }

                import os
                from generate_pdf import generate_proposal_pdf

                # Salva PDF na pasta Propostas
                propostas_dir = "Propostas"
                if not os.path.exists(propostas_dir):
                    os.makedirs(propostas_dir)
                output_pdf = os.path.join(propostas_dir, f"Proposta_{selected_client}_{selected_product}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
                generate_proposal_pdf(proposal_data, output_pdf)
                pdf_path = output_pdf

                # Salva o orçamento no histórico, incluindo o caminho do PDF
                new_budget = {
                    "ID": f"ORC{int(datetime.now().timestamp())}",
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
                    "PropostaPDF": pdf_path
                }
                new_budget_df = pd.DataFrame([new_budget])
                st.session_state.df_orcamentos = pd.concat([st.session_state.df_orcamentos, new_budget_df], ignore_index=True)[config.COLUNAS_ORCAMENTOS]
                storage.save_csv(st.session_state.df_orcamentos, config.ORCAMENTOS_FILE)
                st.session_state.ajustes = []

                # Download automático do PDF
                if pdf_path and os.path.exists(pdf_path) and pdf_path.endswith(".pdf"):
                    with open(pdf_path, "rb") as fpdf:
                        st.download_button("Baixar Proposta PDF", fpdf, file_name=os.path.basename(pdf_path))
                st.success(f"Orçamento {new_budget['ID']} salvo com sucesso!")

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