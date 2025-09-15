# orcamento_pro/calculations.py
"""
Módulo para a lógica de negócios principal (cálculos de custos).
Inclui a nova lógica para cálculo de componentes personalizados.
"""
import pandas as pd
import numpy as np
import re

# ================== FUNÇÕES AUXILIARES ==================
def get_average_paper_price(paper_name: str, df_paper_purchases: pd.DataFrame) -> tuple[float | None, str | None]:
    df_specific_paper = df_paper_purchases[df_paper_purchases['PapelLimpo'] == paper_name]
    if df_specific_paper.empty:
        return None, f"Papel '{paper_name}' não foi encontrado nos registros de compra."
    last_3_purchases = df_specific_paper.head(3)
    average_price = last_3_purchases['ValorUnitario'].mean()
    return average_price, None

# ================== CÁLCULO DA CAPA ==================
# orcamento_pro/calculations.py
def calculate_offset_cover_cost(
    product_name: str,
    quantity: int,
    paper_name: str,
    df_paper_purchases: pd.DataFrame,
    df_impression_table: pd.DataFrame
) -> dict:
    if df_impression_table.empty:
        return {"error": f"Tabela de impressão para '{product_name}' não encontrada ou vazia."}
    try:
        service_row = df_impression_table[df_impression_table['LAMINAS'] >= quantity].iloc[0]
    except IndexError:
        service_row = df_impression_table.iloc[-1]
    
    total_sheets = int(service_row['QTD_FLS'])
    impression_cost_total = service_row['VALOR ML (R$)']
    paper_avg_price, error = get_average_paper_price(paper_name, df_paper_purchases)
    if error: return {"error": error}
    paper_cost_total = paper_avg_price * total_sheets
    total_cost_unit = (paper_cost_total + impression_cost_total) / quantity if quantity > 0 else 0
    
    return {
        "total_cost_unit": total_cost_unit,
        "paper_cost_unit": paper_cost_total / quantity if quantity > 0 else 0,
        "service_cost_unit": impression_cost_total / quantity if quantity > 0 else 0,
        "total_sheets": total_sheets,
        "paper_name": paper_name,
        "quantity": total_sheets,  # ← Nova linha: quantidade de folhas usadas
        "error": None
    }

def calculate_leather_cover_cost(material_name: str, direct_purchases_cats: dict) -> dict:
    """
    Busca o custo de um material de couro a partir dos dados de compras diretas.
    """
    if "COURO" in direct_purchases_cats:
        for item in direct_purchases_cats["COURO"]:
            if item["NomeLimpo"] == material_name:
                return {
                    "total_cost_unit": item["VALOR_UNITARIO"],
                    "paper_cost_unit": item["VALOR_UNITARIO"],
                    "service_cost_unit": 0,
                    "paper_name": material_name,
                    "quantity": 1,  # ← Nova linha: quantidade de folhas usadas
                    "error": None
                }
    return {"error": f"Material de couro '{material_name}' não encontrado."}

def calculate_digital_cover_cost(
    product_name: str,
    paper_name: str,
    impression_type: str,
    budget_quantity: int,
    df_paper_purchases: pd.DataFrame
) -> dict:
    """
    Calcula o custo unitário da capa para produtos de policromia (Digital).
    """
    # Dimensões do produto
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
    base_product = product_name.replace(" - POLICROMIA", "").strip()
    if base_product not in formatos_abertos:
        return {"error": f"Formato do produto '{base_product}' não encontrado."}
    larg_capa, alt_capa = formatos_abertos[base_product]['larg'], formatos_abertos[base_product]['alt']
    
    # Determinar o formato útil de impressão
    if "17X24" in base_product or "20X28" in base_product:
        util_l, util_a = 56, 33
        formato_preco = '56x33'
    else:
        util_l, util_a = 47, 33
        formato_preco = '47x33'
    
    # Determinar o tipo de impressão
    tipo_impressao = None
    for tipo in ['4/0', '4/1', '1/0', '1/1']:
        if tipo in impression_type:
            tipo_impressao = tipo
            break
    if not tipo_impressao:
        return {"error": "Tipo de impressão digital não especificado."}
    
    # Preço unitário da impressão digital
    PRECO_DIGITAL = {
        '47x33': {
            '4/0': 1.16,
            '4/1': 1.40,
            '1/0': 0.24,
            '1/1': 0.48
        },
        '56x33': {
            '4/0': 2.32,
            '4/1': 2.80,
            '1/0': 0.48,
            '1/1': 0.96
        }
    }
    preco_unitario = PRECO_DIGITAL[formato_preco][tipo_impressao]
    
    # Calcular o número de capas por folha útil
    def max_por_folha(folha_l, folha_a, peca_l, peca_a):
        h1 = (folha_l // peca_l) * (folha_a // peca_a)
        h2 = (folha_l // peca_a) * (folha_a // peca_l)
        return max(h1, h2) if h1 > 0 or h2 > 0 else 0
    
    capas_por_folha_util = max_por_folha(util_l, util_a, larg_capa, alt_capa)
    if capas_por_folha_util == 0:
        return {"error": "Não é possível encaixar capas na folha útil."}
    
    # Folhas úteis necessárias
    folhas_uteis_necessarias = int(np.ceil(budget_quantity / capas_por_folha_util))
    
    # Custo total da impressão
    custo_impressao_total = folhas_uteis_necessarias * preco_unitario
    custo_impressao_unitario = custo_impressao_total / budget_quantity
    
    # Custo do papel
    df_paper = df_paper_purchases[df_paper_purchases['PapelLimpo'] == paper_name]
    if df_paper.empty:
        return {"error": f"Papel '{paper_name}' não encontrado nos registros de compra."}
    paper_avg_price, error = get_average_paper_price(paper_name, df_paper_purchases)
    if error:
        return {"error": error}

    match = re.search(r'(\d+)\s*[xX×]\s*(\d+)', paper_name.replace('g/m2', '').replace('gsm', ''))
    if not match:
        return {"error": "Dimensões do papel não encontradas no nome do papel."}
    
    papel_l, papel_a = float(match.group(1)), float(match.group(2))
    if papel_l < papel_a: papel_l, papel_a = papel_a, papel_l
    
    pecas_por_folha_de_papel = max_por_folha(papel_l, papel_a, util_l, util_a)
    if pecas_por_folha_de_papel == 0:
        return {"error": "Não é possível encaixar folhas úteis no papel."}
        
    folhas_papel_necessarias = int(np.ceil(folhas_uteis_necessarias / pecas_por_folha_de_papel))
    custo_papel_total = folhas_papel_necessarias * paper_avg_price
    custo_papel_unitario = custo_papel_total / budget_quantity if budget_quantity > 0 else 0
    
    # Custo total
    total_cost_unit = custo_papel_unitario + custo_impressao_unitario
    return {
        "total_cost_unit": total_cost_unit,
        "paper_cost_unit": custo_papel_unitario,
        "service_cost_unit": custo_impressao_unitario,
        "total_sheets": folhas_papel_necessarias,
        "paper_name": paper_name,
        "quantity": folhas_papel_necessarias,  # ← Nova linha: quantidade de folhas usadas
        "folhas_uteis_necessarias": folhas_uteis_necessarias,  # NOVO: quantidade de folhas úteis necessárias
        "error": None
    }

# ================== CÁLCULO DE COMPONENTES ==================
def calculate_component_cost(
    item_name: str, df_component_data: pd.DataFrame,
    df_paper_purchases: pd.DataFrame, budget_quantity: int, component_type: str
) -> dict:
    """
    Calcula o custo de um componente padrão (ex: Miolo Pautado).
    """
    try:
        item_row = df_component_data[df_component_data[component_type] == item_name].iloc[0]
        paper_needed = item_row['Papel']
        total_paper_sheets = item_row.get('QuantidadePapel', 0)
        approved_quantity = item_row.get('QuantidadeAprovada', 1)
        if approved_quantity <= 0: approved_quantity = 1

        paper_avg_price, error = get_average_paper_price(paper_needed, df_paper_purchases)
        if error: return {"error": error}

        paper_cost_per_unit = (paper_avg_price * total_paper_sheets) / approved_quantity
        
        # --- LÓGICA CORRIGIDA E COMPLETA ---
        service_cost_per_unit = 0
        if 'UnitImpressao' in item_row and item_row['UnitImpressao'] > 0:
            service_cost_per_unit = item_row['UnitImpressao']
        else:
            impression_cost_total = item_row.get('ValorImpressao', 0)
            if budget_quantity > 0:
                service_cost_per_unit = impression_cost_total / budget_quantity
        
        total_cost = paper_cost_per_unit + service_cost_per_unit
        
        last_nf_date_ts = df_paper_purchases[df_paper_purchases['PapelLimpo'] == paper_needed].iloc[0]['DataEmissaoNF']
        last_nf_date = pd.to_datetime(last_nf_date_ts).strftime('%d/%m/%Y') if pd.notna(last_nf_date_ts) else "N/A"

        return {
            "total_cost_unit": total_cost,
            "paper_cost_unit": paper_cost_per_unit,
            "service_cost_unit": service_cost_per_unit,
            "paper_name": paper_needed,
            "last_nf_date": last_nf_date,
            "quantity": budget_quantity,  # ← Nova linha: quantidade de folhas usadas
            "error": None
        }
    except Exception as e:
        return {"error": f"Erro ao calcular o custo do componente '{item_name}': {e}"}
    
    # ================== CÁLCULO DE ACABAMENTOS ==================
def calculate_hot_stamping_cost(
    hot_stamping_type: str,
    budget_quantity: int
) -> dict:
    """
    Calcula o custo unitário do serviço de hot stamping externo com custo mínimo.
    - Pequeno: R$ 750 para as primeiras 1000 unidades, depois proporcional.
    - Grande: R$ 1500 para as primeiras 1000 unidades, depois proporcional.
    """
    if budget_quantity <= 0:
        return {"error": "Quantidade do orçamento deve ser maior que zero."}

    cost_per_thousand = 0
    if "Pequeno" in hot_stamping_type:
        cost_per_thousand = 750.0
    elif "Grande" in hot_stamping_type:
        cost_per_thousand = 1500.0
    else:
        # Se for 'Nenhum' ou 'Interno', o custo adicional é zero.
        return {"total_cost_unit": 0, "details": hot_stamping_type, "error": None}

    # --- LÓGICA CORRIGIDA AQUI ---
    # Se a quantidade for 1000 ou menos, o custo total é o valor base fixo.
    if budget_quantity <= 1000:
        total_cost = cost_per_thousand
    # Se for maior que 1000, o custo é proporcional à quantidade total.
    else:
        total_cost = (budget_quantity / 1000) * cost_per_thousand
    
    # O custo unitário é sempre o custo total dividido pela quantidade.
    cost_per_unit = total_cost / budget_quantity

    return {
        "total_cost_unit": cost_per_unit,
        "details": f"{hot_stamping_type} (R$ {total_cost:,.2f} total)",
        "error": None
    }

def calculate_lamination_cost(
    impression_type: str,
    paper_name: str,
    quantity: int,
    df_paper_purchases: pd.DataFrame,
    offset_sheets: int = None,
    digital_sheets: int = None,
    product_name: str = None
) -> dict:
    """
    Calcula o custo de laminação para Offset ou Digital.
    - Offset: pega formato do papel, divide largura por 2, calcula custo usando quantidade de folhas do CSV.
    - Digital: usa quantidade de folhas úteis e formato útil baseado no tipo de produto.
      Se o produto for 17x24 ou 20x28, usa formato útil 56x33, senão usa 47x33.
      Para digital, a quantidade de folhas é igual à quantidade de folhas úteis necessárias para imprimir o produto.
    Fórmula: (altura_m * largura_m) * 1.60 * quantidade de folhas
    """
    # Offset: usa formato do papel selecionado
    if "Offset" in impression_type:
        match = re.search(r'(\d+)\s*[xX×]\s*(\d+)', paper_name.replace('g/m2', '').replace('gsm', ''))
        if not match:
            return {"error": "Dimensões do papel não encontradas no nome do papel."}
        largura = float(match.group(1))
        altura = float(match.group(2))
        largura_m = largura / 100
        altura_m = altura / 100
        # Divide a altura por 2 (sempre pela altura)
        largura_laminacao_m = largura_m
        altura_laminacao_m = altura_m / 2
        # Cada folha inteira vira 2 folhas laminadas
        qtd_folhas = (offset_sheets if offset_sheets is not None else quantity) * 2

    # Digital: lógica por tipo de produto
    else:
        # Define formato útil conforme o tipo de produto
        formato_util = "47x33"
        if product_name:
            base_product = product_name.replace(" - POLICROMIA", "").strip().upper()
            if "17X24" in base_product or "20X28" in base_product:
                formato_util = "56x33"
        match = re.search(r'(\d+)\s*[xX×]\s*(\d+)', formato_util)
        if not match:
            return {"error": "Dimensões do formato útil não encontradas."}
        largura = float(match.group(1))
        altura = float(match.group(2))
        largura_m = largura / 100
        altura_m = altura / 100
        largura_laminacao_m = largura_m
        altura_laminacao_m = altura_m
        # Para digital, a quantidade de folhas é a quantidade de folhas úteis necessárias
        qtd_folhas = digital_sheets if digital_sheets is not None else quantity

    custo_laminacao_total = largura_laminacao_m * altura_laminacao_m * 1.60 * qtd_folhas
    custo_laminacao_unit = custo_laminacao_total / quantity if quantity > 0 else 0

    return {
        "total_cost_unit": custo_laminacao_unit,
        "total_cost": custo_laminacao_total,
        "details": f"Laminação ({largura_laminacao_m:.2f}m x {altura_laminacao_m:.2f}m) x {qtd_folhas} folhas",
        "error": None
    }

def calculate_silk_cost(silk_type: str, budget_quantity: int) -> dict:
    """
    Calcula o custo de impressão Silk na capa.
    - 1/0: R$290 até 100 unidades, acima disso R$290 + (qtd - 100) * 1.30
    - 2/0: valor do 1/0 + R$200 até 100 unidades, acima disso R$290 + (qtd - 100) * 2.60
    - 3/0: valor do 2/0 + R$200 até 100 unidades, acima disso R$290 + (qtd - 100) * 3.90
    - 4/0: valor do 3/0 + R$200 até 100 unidades, acima disso R$290 + (qtd - 100) * 5.20
    """
    if budget_quantity <= 0:
        return {"error": "Quantidade do orçamento deve ser maior que zero."}

    base_price_1_0 = 290.0
    extra_price_per_color = 200.0

    # Extrai o número de cores do silk_type (ex: "3/0" → 3)
    try:
        num_cores = int(silk_type.split('/')[0])
    except Exception:
        return {"error": "Tipo de Silk inválido."}

    # Define o preço por peça acima de 100 unidades conforme o número de cores
    price_per_piece = 1.30 * num_cores

    # Cálculo para até 100 unidades
    if budget_quantity <= 100:
        total_cost = base_price_1_0 + extra_price_per_color * (num_cores - 1)
    else:
        # Para acima de 100 unidades, preço por peça depende do número de cores
        if num_cores == 1:
            price_per_piece = 1.30
        elif num_cores == 2:
            price_per_piece = 2.60
        elif num_cores == 3:
            price_per_piece = 3.90
        elif num_cores == 4:
            price_per_piece = 5.20
        else:
            return {"error": "Quantidade de cores não suportada."}
        total_cost = base_price_1_0 + (budget_quantity - 100) * price_per_piece

    cost_per_unit = total_cost / budget_quantity if budget_quantity > 0 else 0

    return {
        "total_cost_unit": cost_per_unit,
        "total_cost": total_cost,
        "details": f"Silk {silk_type} ({budget_quantity} un.)",
        "error": None
    }
    
# --- NOVA FUNÇÃO PARA CÁLCULO PERSONALIZADO ---
def calculate_custom_component_cost(
    total_material_cost: float,
    total_service_cost: float,
    budget_quantity: int
) -> dict:
    """
    Calcula o custo de um componente personalizado com base nos custos totais informados.
    Lógica: (Custo Total do Material + Custo Total do Serviço) / Quantidade do Orçamento.
    """
    if budget_quantity <= 0:
        return {"error": "A quantidade do orçamento deve ser maior que zero."}

    material_cost_unit = total_material_cost / budget_quantity
    service_cost_unit = total_service_cost / budget_quantity
    total_cost = material_cost_unit + service_cost_unit

    return {
        "total_cost_unit": total_cost,
        "paper_cost_unit": material_cost_unit,
        "service_cost_unit": service_cost_unit,
        "quantity": budget_quantity,
        "error": None
    }

def calculate_synthetic_leather_cover_cost(
    product_name: str,
    leather_material_name: str,
    budget_quantity: int,
    direct_purchases_cats: dict
) -> dict:
    """
    Calcula o custo do couro sintético considerando o aproveitamento da faca.
    - largura_bobina: 130cm (fixo)
    - altura_faca: conforme produto
    - Aproveitamento: quantos produtos cabem em cada corte de faca
    - Calcula área total de couro necessária e custo total
    """
    # Tabela de altura da faca por produto
    altura_faca_map = {
        'CADERNETA 9X13': 40,
        'CADERNETA 14X21': 40,
        'REVISTA 9X13': 40,
        'REVISTA 14X21': 40,
        'REVISTA 19X25': 47,
        'CADERNO WIRE-O 17X24': 53,
        'CADERNO WIRE-O 20X28': 53,
        'PLANNER WIRE-O A5': 47,
        'BLOCO WIRE-O 12X20': 40,
        'FICHARIO A6': 40,
        'FICHARIO A5': 50,
        'FICHARIO 17X24': 53,
        'CADERNO ORGANIZADOR A5': 50,
        'CADERNO ORGANIZADOR 17X24': 53
    }
    formatos_abertos = {
        'CADERNETA 9X13': {'larg': 22, 'alt': 15.8},
        'CADERNETA 14X21': {'larg': 33.7, 'alt': 24.5},
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
    largura_bobina = 130  # cm

    base_product = product_name.replace(" - POLICROMIA", "").replace(" - COURO SINTÉTICO", "").strip().upper()
    altura_faca = altura_faca_map.get(base_product)
    formato = formatos_abertos.get(base_product)
    if not altura_faca or not formato:
        return {"error": f"Altura da faca ou formato aberto não definido para o produto '{base_product}'."}

    # Busca preço do couro
    preco_couro = None
    if "COURO" in direct_purchases_cats:
        for item in direct_purchases_cats["COURO"]:
            if item["NomeLimpo"] == leather_material_name:
                preco_couro = item["VALOR_UNITARIO"]
                break
    if preco_couro is None:
        return {"error": f"Material de couro '{leather_material_name}' não encontrado."}

    # Aproveitamento: quantas capas cabem em cada tira (pedaço 40x130)
    capa_larg = formato['larg']
    capa_alt = formato['alt']
    tira_larg = largura_bobina
    tira_alt = altura_faca

    def max_por_tira(tira_l, tira_a, capa_l, capa_a):
        # Tenta encaixar capas tanto na orientação normal quanto girada
        h1 = int(tira_l // capa_l) * int(tira_a // capa_a)
        h2 = int(tira_l // capa_a) * int(tira_a // capa_l)
        return max(h1, h2)

    capas_por_tira = max_por_tira(tira_larg, tira_alt, capa_larg, capa_alt)
    if capas_por_tira == 0:
        return {"error": "Não é possível encaixar capas na tira do couro."}

    # Quantidade de tiras necessárias
    tiras_necessarias = int(np.ceil(budget_quantity / capas_por_tira))

    # Área total de couro necessária (em m2)
    area_total_m2 = tiras_necessarias * (tira_larg / 100) * (tira_alt / 100)

    # Custo total do couro
    custo_total_couro = area_total_m2 * preco_couro
    custo_unitario = custo_total_couro / budget_quantity if budget_quantity > 0 else 0

    return {
        "total_cost_unit": custo_unitario,
        "paper_cost_unit": custo_unitario,
        "service_cost_unit": 0,
        "paper_name": leather_material_name,
        "quantity": area_total_m2,
        "details": f"{tiras_necessarias} tiras de {tira_alt}x{tira_larg}cm, {capas_por_tira} capas por tira, área total {area_total_m2:.2f}m²",
        "error": None
    }