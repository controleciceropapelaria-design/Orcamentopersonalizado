from fpdf import FPDF

def get_multicell_height(pdf, w, h, text):
    # Cria uma página temporária para calcular a altura
    tmp_pdf = FPDF()
    tmp_pdf.add_page()
    tmp_pdf.set_font(pdf.font_family, pdf.font_style, pdf.font_size_pt)
    tmp_pdf.set_xy(0, 0)
    tmp_pdf.multi_cell(w, h, text)
    return tmp_pdf.get_y()

def format_brl(value):
    """Formata um número float para o padrão brasileiro: 1.234,56"""
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def generate_proposal_pdf(proposal_data, output_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Logo
    logo_path = "logo_cicero.png"
    if logo_path:
        pdf.image(logo_path, x=80, y=20, w=60)

    # Cabeçalho
    pdf.set_font("Times", size=10)
    pdf.set_text_color(0, 0, 0)
    pdf.set_xy(10, 45)
    pdf.ln(4)
    pdf.cell(0, 8, f"Rio de Janeiro, {proposal_data['data']}", ln=True, align="R")

    pdf.set_xy(10, 55)
    pdf.set_font("Times", "B", 10)
    pdf.cell(0, 8, "À", ln=True)
    pdf.set_font("Times", size=10)
    pdf.cell(0, 8, f"{proposal_data['cliente']}", ln=True)
    pdf.set_font("Times", "I", 10)
    pdf.cell(0, 8, f"A/C: {proposal_data['responsavel']}", ln=True)
    pdf.ln(2)

    pdf.set_font("Times", size=10)
    pdf.multi_cell(0, 8, "Prezado(s) Senhor(es), Conforme Solicitação de V.Sra., apresentamos nossos preços para os produtos abaixo:")
    pdf.ln(2)
    pdf.set_font("Times", "B", 10)
    pdf.cell(0, 8, f"Nº Proposta: {proposal_data['numero_orcamento']}", ln=True)
    pdf.set_font("Times", "B", 12)
    pdf.cell(0, 10, proposal_data['produto'], ln=True, align="C")
    pdf.ln(2)

    # Tabela de produto
    pdf.set_font("Times", "B", 10)
    pdf.set_fill_color(220, 220, 220)
    table_header_height = 10

    # Novas larguras ainda menores para cabeçalhos curtos
    w_quantidade = 18
    w_descricao = 144
    w_unitario = 18
    w_total = 18

    # Cabeçalho da tabela com nomes curtos
    pdf.cell(w_quantidade, table_header_height, "Qtd", border=1, align="C", fill=True)
    pdf.cell(w_descricao, table_header_height, "Descrição", border=1, align="C", fill=True)
    pdf.cell(w_unitario, table_header_height, "Unit.", border=1, align="C", fill=True)
    pdf.cell(w_total, table_header_height, "Total", border=1, align="C", fill=True)
    pdf.ln()


    # Linha de dados da tabela (layout ajustado e alinhado)
    pdf.set_font("Times", size=8)
    descricao_text = proposal_data['descrição']
    cell_height = 5
    x = pdf.get_x()
    y = pdf.get_y()

    # Calcula altura da descrição
    desc_lines = pdf.multi_cell(w_descricao, cell_height, descricao_text, border=0, align="L", split_only=True)
    num_lines = len(desc_lines)
    desc_height = cell_height * num_lines

    # Quantidade
    pdf.set_xy(x, y)
    pdf.set_font("Times", "B", 8)
    pdf.multi_cell(w_quantidade, desc_height, str(proposal_data['quantidade']), border=1, align="C")

    # Descrição
    pdf.set_xy(x + w_quantidade, y)
    pdf.multi_cell(w_descricao, cell_height, descricao_text, border=1, align="L")

    # Unitário
    pdf.set_xy(x + w_quantidade + w_descricao, y)
    pdf.set_font("Times", "B", 8)
    pdf.multi_cell(w_unitario, desc_height, format_brl(proposal_data['Unitario']), border=1, align="C")

    # Total
    pdf.set_xy(x + w_quantidade + w_descricao + w_unitario, y)
    pdf.multi_cell(w_total, desc_height, format_brl(proposal_data['total']), border=1, align="C")

    # Move para a próxima linha
    pdf.set_y(y + desc_height)
    pdf.ln(3)

    # Observações e condições
    pdf.set_font("Times", size=10)
    pdf.multi_cell(0, 6,
        "Substituição Tributária não inclusa. Alíquota a ser destacada em Nota Fiscal, sobre o valor total do orçamento. "
        "Caso seja contribuinte acrescente-se entre 6% e 18% de substituição tributária, sobre o valor total do pedido. "
        "Neste caso, enviaremos uma pré nota para aprovação dos impostos antes de realizar o faturamento e expedir a produção. "
        "Como isso poderá impactar no prazo de entrega, pedimos que aprove tão logo receber a pré nota. Após aprovada é de inteira responsabilidade do cliente as informações que constam na mesma, ou seja, uma vez aprovada qualquer alteração posterior que tenha ou não dados financeiros será de responsabilidade do cliente. IPI NÃO INCLUSO."
    )
    pdf.ln(3)
    pdf.multi_cell(0, 6,
        "FRETE grátis para as cidades de Rio de Janeiro, São Paulo e Belo Horizonte. Demais destinos o frete não está incluso e será somado à Nota Fiscal, sobre o valor total do orçamento. "
        "As propostas acima não estão assegurando a disponibilidade de matéria-prima. Antes de aprovar o orçamento, assegure-se com o nosso comercial de que as cores e o modelo que você deseja possuem disponibilidade para suprir a sua demanda dentro do prazo desejado."
    )
    pdf.ln(10)  # Espaço extra entre os blocos

    pdf.set_font("Times", "B", 10)
    pdf.cell(0, 6, f"Contato: {proposal_data['atendente']}", ln=True)
    pdf.set_font("Times", size=10)
    pdf.cell(0, 6, f"Validade da Proposta: {proposal_data['validade']}", ln=True)
    pdf.cell(0, 6, "Condição: Sujeito a análise", ln=True)
    pdf.cell(0, 6, f"Prazo de Entrega: {proposal_data['prazo_de_entrega']}", ln=True)

    # Bloco de condições do orçamento (negrito)
    pdf.ln(10)
    pdf.set_font("Times", "B", 10)
    pdf.cell(0, 6, "Condições do Orçamento:", ln=True)
    condicoes = (
        "1. Este orçamento deverá ser aprovado por e-mail.\n"
        "2. As artes e as criações deverão ser fornecidas pelo cliente nas devidas proporções, caso contrário serão cobradas separadamente.\n"
        "3. A Cicero Papelaria se reserva o direito de analisar a arte antes de considerá-la aprovada.\n"
        "4. A Cicero Papelaria se reserva o direito de usar as imagens dos projetos em sua comunicação.\n"
        "5. A Cicero Papelaria não aceita devolução de pedidos que não possuírem protótipo físico ou layout virtual aprovado.\n"
        "6. Prazo de envio do protótipo é de 10* dias úteis a partir da data de confirmação do recebimento das artes nos formatos corretos.\n"
        "7. Dentro do nosso processo de aprovação de projeto, enviamos uma amostra física para o cliente, o protótipo. A produção do protótipo leva em média 8 dias úteis + prazo de transporte. Caso o cliente pela ausência desta etapa por qualquer razão, nos isentamos de qualquer alteração na produção final.\n"
        "8. O prazo de entrega do pedido é de 15 dias úteis de produção + prazo de transporte, a partir da aprovação do protótipo.\n"
        "9. Caso o prazo seja fixado pelo cliente será programado um cronograma para produção que inclui etapas de aprovação por parte do cliente. Os atrasos nos prazos do cronograma, por parte do cliente, atrasará a entrega final.\n"
        "10. Trabalhos com prazos urgentes poderão ter acrescidos taxa de urgência, equivalente a 5% do orçamento total.\n"
        "11. Qualquer alteração no projeto no decorrer do processo poderá acarretar em custos adicionais para a produção e/ou prorrogação do prazo de entrega.\n"
        "12. Em caso de cancelamento do pedido será cobrado o custo de 10% do orçamento total para cobrir custos de prototipagem e atendimento.\n"
        "13. Em caso de cancelamento do projeto já produzido será cobrado 100% do orçamento total para cobrir todos os custos.\n"
        "14. O pagamento será de acordo com o prazo combinado, em dias corridos a partir da data de faturamento.\n"
        "15. Todas as NFs acompanham a mercadoria e possuem boletos que serão enviados por e-mail em até 3 dias úteis após a emissão da nota fiscal.\n"
        "16. Caso não receba o boleto, envie um e-mail para cobranca2@ciceropapelaria.com.br solicitando uma segunda via.\n"
        "17. Em caso de vencimento do boleto de cobrança, será cobrada multa no valor de 5% do boleto e juros mora proporcional de 3% ao mês no período vencido.\n"
        "18. Qualquer segunda via solicitada após o prazo de vencimento será atualizada com a multa e juros."
    )
    pdf.set_font("Times", "B", 10)
    pdf.multi_cell(0, 6, condicoes)
    pdf.ln(12)

    # Rodapé de assinatura centralizado
    pdf.set_font("Times", "B", 10)
    pdf.cell(0, 6, "Atenciosamente", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Times", size=10)
    pdf.cell(80, 6, "_____________________________", ln=False, align="C")
    pdf.cell(0, 6, "_____________________________", ln=True, align="C")
    pdf.cell(80, 6, "Cicero", ln=False, align="C")
    pdf.cell(0, 6, f"{proposal_data['cliente']}", ln=True, align="C")
    pdf.cell(80, 6, "", ln=False, align="C")
    pdf.cell(0, 6, "......de...............de 2025.", ln=True, align="C")
    pdf.ln(8)

    # Rodapé endereço
    pdf.set_font("Times", size=9)
    pdf.cell(0, 6, "Rua São Luis Gonzaga, 418 - São Cristóvão - Rio de Janeiro - RJ", ln=True, align="C")

    pdf.output(output_path)