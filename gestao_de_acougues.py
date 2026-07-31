import streamlit as st
import pandas as pd
import sqlite3
import datetime
import os
import io
import numpy as np
from scipy.optimize import brentq
from fpdf import FPDF

# =========================================================================
# 1. CONFIGURAÇÃO VISUAL E PALETA DE CORES (BOTÕES EM #A3A3A3)
# =========================================================================
st.set_page_config(page_title="Gestão de Açougues - Renato Frigotudo & Associados", layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background-color: #F8FAFC;
        font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
        color: #0F172A; 
    }
    div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input, div[data-testid="stSelectbox"] select {
        border: 1px solid #94A3B8 !important;
        border-radius: 8px !important;
        color: #0F172A !important;
        background-color: #FFFFFF !important;
        font-weight: 600 !important;
        padding: 6px 12px !important;
    }
    div[data-testid="stTextInput"] input:focus, div[data-testid="stNumberInput"] input:focus {
        border-color: #A3A3A3 !important;
        box-shadow: 0 0 0 2px rgba(163, 163, 163, 0.3) !important;
    }
    label {
        color: #334155 !important;
        font-weight: 700 !important;
        font-size: 14px !important;
    }
    div.stButton > button,
    div.stDownloadButton > button {
        background-color: #A3A3A3 !important;
        color: #0F172A !important;
        border-radius: 8px !important;
        border: 1px solid #737373 !important;
        padding: 8px 18px !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        transition: all 0.2s ease;
    }
    div.stButton > button:hover,
    div.stDownloadButton > button:hover {
        background-color: #8C8C8C !important;
        color: #0F172A !important;
        border-color: #525252 !important;
    }
    form button,
    div.stFormSubmitButton > button {
        background-color: #A3A3A3 !important;
        color: #0F172A !important;
        border-radius: 8px !important;
        border: 1px solid #737373 !important;
        font-weight: 700 !important;
    }
    form button:hover,
    div.stFormSubmitButton > button:hover {
        background-color: #8C8C8C !important;
        color: #0F172A !important;
    }
    h1, h2, h3, h4 {
        color: #0F172A !important; 
        font-weight: 800 !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #0F172A !important;
        border-right: 2px solid #1E293B;
    }
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] h4 {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }
    section[data-testid="stSidebar"] div.stButton > button,
    section[data-testid="stSidebar"] div.stDownloadButton > button,
    section[data-testid="stSidebar"] a {
        background-color: #A3A3A3 !important;
        color: #0F172A !important;
        border: 1px solid #737373 !important;
        width: 100% !important;
        font-weight: 700 !important;
    }
    section[data-testid="stSidebar"] div.stButton > button:hover,
    section[data-testid="stSidebar"] div.stDownloadButton > button:hover {
        background-color: #8C8C8C !important;
        color: #0F172A !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# =========================================================================
# FUNÇÃO PADRÃO DE CABEÇALHO PARA RELATÓRIOS PDF
# =========================================================================
def criar_cabecalho_pdf_padrao(pdf, titulo_relatorio, nome_empresa_usuaria):
    logo_pdf = None
    for lp in ["logo_renato.jpeg", "logo_renato.jpg", "LOGO FINALIZADA.jpeg", "logo_renato.png"]:
        if os.path.exists(lp):
            logo_pdf = lp
            break
            
    if logo_pdf:
        pdf.image(logo_pdf, x=10, y=8, w=18)

    pdf.set_fill_color(30, 58, 138)
    pdf.rect(30, 8, 257, 12, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", style="B", size=10)
    pdf.set_xy(30, 10)
    pdf.cell(257, 8, f"RENATO FRIGOTUDO & ASSOCIADOS - {titulo_relatorio.upper()}", ln=1, align="C")
    
    pdf.set_text_color(15, 23, 42)
    pdf.set_font("Arial", style="B", size=8.5)
    pdf.set_xy(10, 22)
    txt_empresa = f"Empresa Usuária: {nome_empresa_usuaria}"
    pdf.cell(277, 5, txt_empresa.encode("latin1", "replace").decode("latin1"), ln=1, align="C")
    
    pdf.set_draw_color(30, 58, 138)
    pdf.set_line_width(0.6)
    pdf.line(10, 28, 287, 28)
    pdf.set_xy(10, 31)

# =========================================================================
# MÓDULO DE CÁLCULO FINANCEIRO (PRICE & SAC)
# =========================================================================
def render_modulo_financeiro():
    st.header("🧮 Módulo de Cálculo Financeiro & Amortização (Price & SAC)")
    st.markdown("Selecione o sistema de amortização e insira as variáveis correspondentes.")

    if "df_fin" not in st.session_state:
        st.session_state.df_fin = None
    if "valor_presente" not in st.session_state:
        st.session_state.valor_presente = 0.0
    if "n_perodos" not in st.session_state:
        st.session_state.n_perodos = 0
    if "i_equivalente" not in st.session_state:
        st.session_state.i_equivalente = 0.0
    if "nome_sistema" not in st.session_state:
        st.session_state.nome_sistema = "Sistema Price"

    sistema_amortizacao = st.selectbox(
        "Sistema de Amortização",
        ["Sistema Price (Prestações Fixas)", "Sistema SAC (Amortização Constante)"],
        key="select_sistema_amortizacao"
    )

    tipo_calculo = st.selectbox(
        "O que você deseja calcular?",
        [
            "Calcular Prestação / Primeira Parcela",
            "Calcular Capital / Valor Presente (PV)",
            "Calcular Taxa de Juros (i)",
            "Calcular Prazo da Operação (n)"
        ],
        key="select_tipo_calculo_financeiro"
    )

    with st.form("form_calculo_financeiro_flexivel"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if tipo_calculo != "Calcular Capital / Valor Presente (PV)":
                valor_presente_input = st.number_input("Valor Presente / Capital (R$)", min_value=0.0, value=10000.0, step=100.0, format="%.2f", key="input_vp_fin")
            else:
                valor_presente_input = 0.0
                st.info("📌 **Capital (PV):** Será calculado.")

        with col2:
            if tipo_calculo != "Calcular Taxa de Juros (i)":
                taxa_informada = st.number_input("Taxa de Juros (%)", min_value=0.0, value=2.3, step=0.01, format="%.4f", key="input_taxa_fin")
                periodo_taxa = st.selectbox("Unidade da Taxa", ["Dias", "Meses", "Anos"], key="sel_periodo_taxa_fin")
            else:
                taxa_informada = 0.0
                periodo_taxa = "Meses"
                st.info("📌 **Taxa:** Será calculada.")

        with col3:
            if tipo_calculo != "Calcular Prazo da Operação (n)":
                prazo_informado = st.number_input("Prazo da Operação", min_value=1, value=12, step=1, key="input_prazo_fin")
                periodo_prazo = st.selectbox("Unidade do Prazo", ["Dias", "Meses", "Anos"], key="sel_periodo_prazo_fin")
            else:
                prazo_informado = 0
                periodo_prazo = "Meses"
                st.info("📌 **Prazo:** Será calculado.")

        if tipo_calculo != "Calcular Prestação / Primeira Parcela":
            st.markdown("---")
            prestacao_informada = st.number_input("Valor da Prestação / Parcela (R$)", min_value=0.0, value=950.0, step=10.0, format="%.2f", key="input_pmt_fin")
        else:
            prestacao_informada = 0.0

        btn_calcular = st.form_submit_button("🚀 Calcular e Gerar Tabela de Amortização")

    if btn_calcular:
        def obter_taxa_equivalente(t_inf, p_t, p_p, p_val):
            if p_t == p_p:
                return t_inf / 100.0, int(p_val)
            else:
                if p_t == "Anos":
                    i_diaria = ((1.0 + (t_inf / 100.0)) ** (1.0 / 360.0)) - 1.0
                elif p_t == "Meses":
                    i_diaria = ((1.0 + (t_inf / 100.0)) ** (1.0 / 30.0)) - 1.0
                else:
                    i_diaria = t_inf / 100.0

                if p_p == "Anos":
                    n_dias = int(p_val * 360)
                elif p_p == "Meses":
                    n_dias = int(p_val * 30)
                else:
                    n_dias = int(p_val)

                if p_p == "Anos":
                    i_eq = ((1.0 + i_diaria) ** 360.0) - 1.0
                elif p_p == "Meses":
                    i_eq = ((1.0 + i_diaria) ** 30.0) - 1.0
                else:
                    i_eq = i_diaria
                return i_eq, n_dias

        try:
            i_equivalente, n_perodos = obter_taxa_equivalente(taxa_informada, periodo_taxa, periodo_prazo, prazo_informado if prazo_informado > 0 else 12)
            
            if "Price" in sistema_amortizacao:
                if tipo_calculo == "Calcular Prestação / Primeira Parcela":
                    valor_presente = valor_presente_input
                    if i_equivalente > 0:
                        prestacao = valor_presente * (i_equivalente * (1.0 + i_equivalente) ** n_perodos) / (((1.0 + i_equivalente) ** n_perodos) - 1.0)
                    else:
                        prestacao = valor_presente / n_perodos

                elif tipo_calculo == "Calcular Capital / Valor Presente (PV)":
                    prestacao = prestacao_informada
                    if i_equivalente > 0:
                        valor_presente = prestacao * ((1.0 + i_equivalente)**n_perodos - 1.0) / (i_equivalente * (1.0 + i_equivalente)**n_perodos)
                    else:
                        valor_presente = prestacao * n_perodos

                elif tipo_calculo == "Calcular Taxa de Juros (i)":
                    n_perodos = int(prazo_informado)
                    valor_presente = valor_presente_input
                    prestacao = prestacao_informada
                    
                    def f_taxa(i_val):
                        if i_val <= 0:
                            return valor_presente * n_perodos - prestacao * n_perodos
                        return valor_presente * i_val * (1.0 + i_val)**n_perodos - prestacao * ((1.0 + i_val)**n_perodos - 1.0)
                    
                    i_equivalente = brentq(f_taxa, 0.0000001, 5.0)

                elif tipo_calculo == "Calcular Prazo da Operação (n)":
                    valor_presente = valor_presente_input
                    prestacao = prestacao_informada
                    if i_equivalente == 0:
                        n_perodos = int(round(valor_presente / prestacao))
                    else:
                        if prestacao <= valor_presente * i_equivalente:
                            raise ValueError("A prestação informada não cobre os juros do período!")
                        num = np.log(prestacao / (prestacao - valor_presente * i_equivalente))
                        den = np.log(1.0 + i_equivalente)
                        n_perodos = int(round(num / den))

                tabela_amortizacao = []
                vp_atual = valor_presente

                for t in range(0, n_perodos + 1):
                    if t == 0:
                        tabela_amortizacao.append({
                            "t": 0, "VALOR PRESENTE": vp_atual, "Amortização": 0.0, "Juros": 0.0, "Prestação": 0.0, "Taxa (%)": 0.0
                        })
                    else:
                        juros_t = vp_atual * i_equivalente
                        amortizacao_t = prestacao - juros_t
                        vp_atual -= amortizacao_t
                        if vp_atual < 0.01:
                            vp_atual = 0.00

                        tabela_amortizacao.append({
                            "t": t, "VALOR PRESENTE": vp_atual, "Amortização": amortizacao_t, "Juros": juros_t, "Prestação": prestacao, "Taxa (%)": i_equivalente * 100.0
                        })
                df_fin = pd.DataFrame(tabela_amortizacao)
                nome_sistema = "Sistema Price"

            else: # Sistema SAC
                if tipo_calculo == "Calcular Capital / Valor Presente (PV)":
                    prestacao = prestacao_informada
                    n_perodos = int(prazo_informado)
                    valor_presente = prestacao / ((1.0 / n_perodos) + i_equivalente)
                else:
                    valor_presente = valor_presente_input
                    n_perodos = int(prazo_informado)

                amortizacao_constante = valor_presente / n_perodos if n_perodos > 0 else 0.0
                tabela_amortizacao = []
                vp_atual = valor_presente

                for t in range(0, n_perodos + 1):
                    if t == 0:
                        tabela_amortizacao.append({
                            "t": 0, "VALOR PRESENTE": vp_atual, "Amortização": 0.0, "Juros": 0.0, "Prestação": 0.0, "Taxa (%)": 0.0
                        })
                    else:
                        juros_t = vp_atual * i_equivalente
                        amortizacao_t = amortizacao_constante
                        prestacao_t = amortizacao_t + juros_t
                        vp_atual -= amortizacao_t
                        if vp_atual < 0.01:
                            vp_atual = 0.00
                        tabela_amortizacao.append({
                            "t": t, "VALOR PRESENTE": vp_atual, "Amortização": amortizacao_t, "Juros": juros_t, "Prestação": prestacao_t, "Taxa (%)": i_equivalente * 100.0
                        })
                df_fin = pd.DataFrame(tabela_amortizacao)
                nome_sistema = "Sistema SAC"

            st.session_state.df_fin = df_fin
            st.session_state.valor_presente = valor_presente
            st.session_state.n_perodos = n_perodos
            st.session_state.i_equivalente = i_equivalente
            st.session_state.nome_sistema = nome_sistema

        except Exception as e:
            st.error(f"Erro ao realizar o cálculo financeiro: {e}")

    if st.session_state.df_fin is not None and not st.session_state.df_fin.empty:
        df_fin = st.session_state.df_fin
        valor_presente = st.session_state.valor_presente
        n_perodos = st.session_state.n_perodos
        i_equivalente = st.session_state.i_equivalente
        nome_sistema = st.session_state.nome_sistema

        st.success(f"""
        📊 **Resultados Calculados ({nome_sistema}):**
        * **Capital (PV):** R$ {valor_presente:,.2f}
        * **Taxa Equivalente:** {i_equivalente*100:.4f}% por período
        * **Prazo Total:** {n_perodos} períodos
        """)

        st.markdown(f"### 📋 Tabela de Amortização - {nome_sistema}")
        st.dataframe(
            df_fin.style.format({
                "VALOR PRESENTE": "R$ {:,.2f}",
                "Amortização": "R$ {:,.2f}",
                "Juros": "R$ {:,.2f}",
                "Prestação": "R$ {:,.2f}",
                "Taxa (%)": "{:.4f}%"
            }),
            use_container_width=True,
            key="df_tabela_amortizacao_estavel"
        )

# =========================================================================
# MÓDULO DE FICHA TÉCNICA E PRECIFICAÇÃO
# =========================================================================
def render_modulo_ficha_tecnica():
    st.markdown("""
        <div style="background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%); padding: 25px; border-radius: 12px; color: white; margin-bottom: 25px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
            <h2 style="margin: 0; color: white !important;">📋 Módulo de Ficha Técnica & Precificação</h2>
            <p style="margin: 8px 0 0 0; font-size: 15px; opacity: 0.9;">Gerencie fichas técnicas de produtos, controle insumos em tabelas e apure custos de produção e preços de venda em tempo real.</p>
        </div>
    """, unsafe_allow_html=True)

    emp_id_ativo = st.session_state.empresa_id
    aba_ficha = st.selectbox("Selecione a Ação", ["Consultar / Editar Fichas Existentes", "Cadastrar Nova Ficha Técnica"], key="sel_aba_ficha")

    if aba_ficha == "Cadastrar Nova Ficha Técnica":
        st.markdown("### ➕ Criar Nova Ficha Técnica")
        with st.form("form_nova_ficha_tecnica"):
            col1, col2 = st.columns(2)
            with col1:
                nome_produto = st.text_input("Nome do Produto / Prato", value="")
                rendimento_kg_novo = st.number_input("Rendimento Total (KG)", min_value=0.0, value=0.0, step=0.1, format="%.3f", key="novo_rend_total")
                rendimento_assada_kg_novo = st.number_input("Rendimento Depois de Assada (KG)", min_value=0.0, value=0.0, step=0.01, format="%.3f", key="novo_rend_assado")
            with col2:
                peso_unidade_kg = st.number_input("Peso da Unidade (KG)", min_value=0.0, value=0.0, step=0.001, format="%.3f")
                qtd_por_pacote = st.number_input("Quantidade por Pacote", min_value=1.0, value=1.0, step=1.0)
                unidades_produzidas_input = st.number_input("Quantidade de Unidades Produzidas", min_value=0.0, value=1.0, step=1.0, key="novo_qtd_unidades")
            
            perda_calculada_nova = (rendimento_kg_novo - rendimento_assada_kg_novo) / rendimento_kg_novo if rendimento_kg_novo > 0 else 0.0
            if perda_calculada_nova < 0:
                perda_calculada_nova = 0.0

            st.markdown(f"**Perda % Calculada (Indicador):** `{perda_calculada_nova*100:.2f}%` ({perda_calculada_nova:.4f})")
            
            btn_salvar_ficha = st.form_submit_button("💾 Salvar Ficha Técnica e Continuar")
            if btn_salvar_ficha:
                if not nome_produto.strip():
                    st.error("Informe o nome do produto!")
                else:
                    try:
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO fichas_tecnicas (empresa_id, produto, rendimento_kg, rendimento_assada_kg, peso_unidade_kg, qtd_por_pacote, unidades_produzidas, perda_pct, data_criacao)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (emp_id_ativo, nome_produto.strip().upper(), rendimento_kg_novo, rendimento_assada_kg_novo, peso_unidade_kg, qtd_por_pacote, unidades_produzidas_input, perda_calculada_nova, str(datetime.date.today())))
                        conn.commit()
                        conn.close()
                        st.success("🎉 Ficha técnica criada com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao salvar ficha técnica: {e}")

    else:
        conn = get_connection()
        df_fichas = pd.read_sql_query("SELECT * FROM fichas_tecnicas WHERE empresa_id = ? OR empresa_id IS NULL ORDER BY id DESC", conn, params=(emp_id_ativo,))
        conn.close()

        if df_fichas.empty:
            st.warning("⚠️ Nenhuma ficha técnica cadastrada.")
        else:
            opcoes_fichas = {f"ID: {row['id']} - {row['produto']} (Criada em: {row['data_criacao']})": row['id'] for _, row in df_fichas.iterrows()}
            ficha_selecionada_label = st.selectbox("Selecione a Ficha Técnica", list(opcoes_fichas.keys()), key="sel_ficha_cadastrada")
            ficha_id_ativo = opcoes_fichas[ficha_selecionada_label]
            ficha_row = df_fichas[df_fichas['id'] == ficha_id_ativo].iloc[0]
            st.info(f"Ficha selecionada: **{ficha_row['produto']}**")

# =========================================================================
# MÓDULO DE CAPITAL DE GIRO (NCG) COM HISTÓRICO E GESTÃO COMPLETA
# =========================================================================
def render_modulo_ncg():
    st.markdown("""
        <div style="background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%); padding: 25px; border-radius: 12px; color: white; margin-bottom: 25px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
            <h2 style="margin: 0; color: white !important;">📈 Análise de Necessidade de Capital de Giro (NCG)</h2>
            <p style="margin: 8px 0 0 0; font-size: 15px; opacity: 0.9;">Calcule, armazene, filtre por data e compare cenários de capital de giro e prazos operacionais.</p>
        </div>
    """, unsafe_allow_html=True)

    emp_id_ativo = st.session_state.empresa_id

    aba_ncg = st.selectbox(
        "Selecione a Ação no Módulo NCG", 
        ["Novo Cálculo / Simulação", "Consultar Histórico, Filtrar por Data e Editar"], 
        key="sel_aba_ncg_geral"
    )

    if aba_ncg == "Novo Cálculo / Simulação":
        st.markdown("Insira os dados financeiros da sua empresa, configure os prazos e salve sua simulação para estudos futuros.")

        with st.form("form_ncg_calculo"):
            st.subheader("0. Identificação da Simulação")
            nome_simulacao = st.text_input("Nome / Descrição da Simulação", value=f"Simulação NCG - {datetime.date.today().strftime('%d/%m/%Y')}")
            data_simulacao = st.date_input("Data de Referência", datetime.date.today())

            st.markdown("---")
            st.subheader("1. Dados Financeiros da Empresa (Entrada)")
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                fat_mensal = st.number_input("Faturamento Bruto Mensal (R$)", min_value=0.0, value=157399.10, step=100.0, format="%.2f", key="ncg_fat")
                cmv_mensal = st.number_input("Custo da Mercadoria Vendida - CMV (R$)", min_value=0.0, value=98409.78, step=100.0, format="%.2f", key="ncg_cmv")
                contas_receber = st.number_input("Contas a Receber Acumuladas (R$)", min_value=0.0, value=1193.67, step=10.0, format="%.2f", key="ncg_rec")
            with col_d2:
                estoque_atual = st.number_input("Estoque Atual (R$)", min_value=0.0, value=18700.00, step=100.0, format="%.2f", key="ncg_est")
                contas_pagar = st.number_input("Contas a Pagar / Fornecedores (R$)", min_value=0.0, value=50971.32, step=100.0, format="%.2f", key="ncg_pag")
                reserva_financeira = st.number_input("Reserva Financeira / Caixa (R$)", min_value=0.0, value=0.0, step=100.0, format="%.2f", key="ncg_res")

            st.markdown("---")
            st.subheader("2. Prazos Médios Operacionais (em dias)")
            col_p1, col_p2, col_p3 = st.columns(3)
            with col_p1:
                pme_atual = st.number_input("Prazo Médio de Estoque (PME) - Atual", min_value=0.0, value=8.5, step=0.5, key="ncg_pme_a")
                pme_prop = st.number_input("Prazo Médio de Estoque (PME) - Proposto", min_value=0.0, value=7.0, step=0.5, key="ncg_pme_p")
            with col_p2:
                pmr_atual = st.number_input("Prazo Médio de Recebimento (PMR) - Atual", min_value=0.0, value=1.0, step=0.5, key="ncg_pmr_a")
                pmr_prop = st.number_input("Prazo Médio de Recebimento (PMR) - Proposto", min_value=0.0, value=7.0, step=0.5, key="ncg_pmr_p")
            with col_p3:
                pmp_atual = st.number_input("Prazo Médio de Pagamento (PMP) - Atual", min_value=0.0, value=14.0, step=0.5, key="ncg_pmp_a")
                pmp_prop = st.number_input("Prazo Médio de Pagamento (PMP) - Proposto", min_value=0.0, value=18.0, step=0.5, key="ncg_pmp_p")

            btn_calc_ncg = st.form_submit_button("🚀 Calcular e Salvar Simulação de NCG")

        # Realizar Cálculos
        margem_bruta = fat_mensal - cmv_mensal
        margem_bruta_pct = (margem_bruta / fat_mensal) if fat_mensal > 0 else 0.0
        cmv_diario = cmv_mensal / 30.0
        fat_diario = fat_mensal / 30.0

        ciclo_atual = pme_atual + pmr_atual - pmp_atual
        ciclo_prop = pme_prop + pmr_prop - pmp_prop

        ncg_atual = cmv_diario * ciclo_atual
        ncg_prop = cmv_diario * ciclo_prop

        deficit_imediato = contas_receber - contas_pagar + reserva_financeira
        entradas_atual = fat_diario * pmp_atual
        entradas_prop = fat_diario * pmp_prop

        novo_saldo_atual = entradas_atual + contas_receber - contas_pagar
        novo_saldo_prop = entradas_prop + contas_receber - contas_pagar

        economia_ncg = ncg_atual - ncg_prop

        if btn_calc_ncg:
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO historico_ncg (
                        empresa_id, nome_simulacao, data_simulacao, fat_mensal, cmv_mensal, 
                        contas_receber, estoque_atual, contas_pagar, reserva_financeira, 
                        pme_atual, pme_prop, pmr_atual, pmr_prop, pmp_atual, pmp_prop,
                        ncg_atual, ncg_prop, economia_ncg
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    emp_id_ativo, nome_simulacao, str(data_simulacao), fat_mensal, cmv_mensal,
                    contas_receber, estoque_atual, contas_pagar, reserva_financeira,
                    pme_atual, pme_prop, pmr_atual, pmr_prop, pmp_atual, pmp_prop,
                    ncg_atual, ncg_prop, economia_ncg
                ))
                conn.commit()
                conn.close()
                st.success("🎉 Simulação calculada e salva com sucesso no histórico!")
            except Exception as e:
                st.error(f"Erro ao salvar no banco de dados: {e}")

        st.markdown("---")
        st.markdown("### 📊 3. Resultados da Simulação Atual")
        
        calc_data = {
            "Indicador": [
                "Margem Bruta (R$)", "Margem Bruta (%)", "CMV Diário (R$)", "Faturamento Diário (R$)",
                "CICLO FINANCEIRO (dias)", "NCG - Necessidade de Capital de Giro (R$)"
            ],
            "Cenário Atual": [
                f"R$ {margem_bruta:,.2f}", f"{margem_bruta_pct*100:.2f}%", f"R$ {cmv_diario:,.2f}", f"R$ {fat_diario:,.2f}",
                f"{ciclo_atual:.1f} dias", f"R$ {ncg_atual:,.2f}"
            ],
            "Cenário Proposto": [
                f"R$ {margem_bruta:,.2f}", f"{margem_bruta_pct*100:.2f}%", f"R$ {cmv_diario:,.2f}", f"R$ {fat_diario:,.2f}",
                f"{ciclo_prop:.1f} dias", f"R$ {ncg_prop:,.2f}"
            ],
            "Fórmula / Observação": [
                "Faturamento - CMV", "(Margem / Faturamento) × 100", "CMV / 30 dias", "Faturamento / 30 dias",
                "PME + PMR - PMP", "CMV Diário × Ciclo Financeiro"
            ]
        }
        df_calc_tabela = pd.DataFrame(calc_data).set_index("Indicador")
        st.table(df_calc_tabela)

        st.markdown("### ⚖️ 4. Análise de Liquidez e Risco")
        liq_data = {
            "Indicador": [
                "Déficit/Superávit Imediato (R$)", "Entradas previstas conforme o PMP", 
                "Novo Saldo após o Ciclo Financeiro", "Economia de NCG com mudança (R$)"
            ],
            "Cenário Atual": [
                f"R$ {deficit_imediato:,.2f}", f"R$ {entradas_atual:,.2f}", f"R$ {novo_saldo_atual:,.2f}", "-"
            ],
            "Cenário Proposto": [
                f"R$ {deficit_imediato:,.2f}", f"R$ {entradas_prop:,.2f}", f"R$ {novo_saldo_prop:,.2f}", f"R$ {economia_ncg:,.2f}"
            ],
            "Fórmula / Observação": [
                "Contas a Receber - Contas a Pagar + Caixa", "Faturamento Diário × PMP", 
                "Entradas + Receber - Pagar", "NCG Atual - NCG Proposto"
            ]
        }
        df_liq_tabela = pd.DataFrame(liq_data).set_index("Indicador")
        st.table(df_liq_tabela)

        st.markdown("### 💡 5. Diagnóstico Automático")
        ciclo_texto = f"{ciclo_atual:.1f} dias (NEGATIVO)" if ciclo_atual < 0 else f"{ciclo_atual:.1f} dias (POSITIVO)"
        interp_ciclo = "Fornecedor financia a empresa" if ciclo_atual < 0 else "Empresa precisa imobilizar capital"
        sit_liq = f"DÉFICIT DE R$ {abs(deficit_imediato):,.2f}" if deficit_imediato < 0 else f"SUPERÁVIT DE R$ {deficit_imediato:,.2f}"

        diag_data = {
            "Indicador": ["Ciclo Financeiro Atual", "Situação de Liquidez", "Recomendação Principal"],
            "Resultado": [ciclo_texto, sit_liq, "Manter política atual" if ciclo_atual < 0 else "Ajustar prazos de recebimento/pagamento"],
            "Interpretação": [interp_ciclo, "ALERTA: Risco de inadimplência" if deficit_imediato < 0 else "Caixa saudável", "-"]
        }
        df_diag_tabela = pd.DataFrame(diag_data).set_index("Indicador")
        st.table(df_diag_tabela)

    else:
        # Aba de Histórico, Filtro por Data, Alteração e Exclusão
        st.markdown("### 📂 Histórico de Simulações de Capital de Giro")
        st.markdown("Filtre as simulações salvas por período, visualize detalhes, edite descrições ou exclua registros antigos.")

        col_f1, col_f2 = st.columns(2)
        hoje = datetime.date.today()
        inicio_ano_padrao = hoje.replace(month=1, day=1)

        data_ini_hist = col_f1.date_input("Data Inicial do Filtro", inicio_ano_padrao, key="ncg_hist_ini")
        data_fim_hist = col_f2.date_input("Data Final do Filtro", hoje, key="ncg_hist_fim")

        conn = get_connection()
        query_hist = """
            SELECT * FROM historico_ncg 
            WHERE empresa_id = ? 
              AND data_simulacao BETWEEN ? AND ? 
            ORDER BY data_simulacao DESC, id DESC
        """
        df_historico_ncg = pd.read_sql_query(query_hist, conn, params=(emp_id_ativo, str(data_ini_hist), str(data_fim_hist)))
        conn.close()

        if df_historico_ncg.empty:
            st.warning("⚠️ Nenhuma simulação encontrada no intervalo de datas selecionado.")
        else:
            opcoes_sim = {}
            lista_sim_labels = []
            for _, row in df_historico_ncg.iterrows():
                dt_fmt = datetime.datetime.strptime(row['data_simulacao'], "%Y-%m-%d").strftime("%d/%m/%Y")
                label = f"ID: {row['id']} - {row['nome_simulacao']} ({dt_fmt})"
                opcoes_sim[label] = row['id']
                lista_sim_labels.append(label)

            sim_selecionada_label = st.selectbox("Selecione a Simulação Salva", lista_sim_labels, key="sel_sim_ncg_hist")
            sim_id_ativo = opcoes_sim[sim_selecionada_label]
            sim_row = df_historico_ncg[df_historico_ncg['id'] == sim_id_ativo].iloc[0]

            st.markdown("---")
            col_info1, col_info2, col_info3 = st.columns(3)
            col_info1.metric("Faturamento Mensal", f"R$ {sim_row['fat_mensal']:,.2f}")
            col_info2.metric("NCG Atual", f"R$ {sim_row['ncg_atual']:,.2f}")
            col_info3.metric("Economia NCG Proposta", f"R$ {sim_row['economia_ncg']:,.2f}")

            col_A, col_B = st.columns(2)
            with col_A:
                with st.form(f"form_editar_nome_sim_{sim_id_ativo}"):
                    novo_nome_sim = st.text_input("Alterar Nome da Simulação", value=sim_row['nome_simulacao'])
                    if st.form_submit_button("💾 Atualizar Nome"):
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("UPDATE historico_ncg SET nome_simulacao = ? WHERE id = ?", (novo_nome_sim, sim_id_ativo))
                        conn.commit()
                        conn.close()
                        st.success("Nome atualizado com sucesso!")
                        st.rerun()

            with col_B:
                with st.form(f"form_excluir_sim_{sim_id_ativo}"):
                    st.markdown("**Excluir Registro**")
                    conf_del = st.checkbox("Confirmar exclusão desta simulação")
                    if st.form_submit_button("🗑️ Excluir Simulação Permanentemente"):
                        if conf_del:
                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM historico_ncg WHERE id = ?", (sim_id_ativo,))
                            conn.commit()
                            conn.close()
                            st.success("Simulação excluída com sucesso!")
                            st.rerun()
                        else:
                            st.error("Marque a caixa de confirmação para excluir.")

# =========================================================================
# 2. ESTRUTURA DO BANCO DE DADOS (SQLITE AUTOMÁTICO)
# =========================================================================
def init_db():
    conn = sqlite3.connect("desossa_db.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS empresas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            login TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            ativo INTEGER DEFAULT 1
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tipos_desossa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            empresa_id INTEGER DEFAULT NULL,
            UNIQUE(nome, empresa_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cortes_padrao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_desossa TEXT NOT NULL,
            nome_corte TEXT NOT NULL,
            empresa_id INTEGER DEFAULT NULL,
            UNIQUE(tipo_desossa, nome_corte, empresa_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS acoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER,
            data_acao TEXT,
            tipo_animal TEXT,
            peso_bruto REAL,
            preco_animal_kg REAL,
            ossos_muxiba REAL,
            quebra_nao_identificada REAL,
            exsudato_escorrimento REAL,
            p_cartao REAL DEFAULT 0.0,
            p_impostos REAL DEFAULT 0.0,
            p_embalagens REAL DEFAULT 0.0,
            p_comissao REAL DEFAULT 0.0,
            FOREIGN KEY(empresa_id) REFERENCES empresas(id) ON DELETE CASCADE
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fichas_tecnicas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER,
            produto TEXT NOT NULL,
            rendimento_kg REAL DEFAULT 0.0,
            rendimento_assada_kg REAL DEFAULT 0.0,
            peso_unidade_kg REAL DEFAULT 0.0,
            qtd_por_pacote REAL DEFAULT 4.0,
            unidades_produzidas REAL DEFAULT 1.0,
            perda_pct REAL DEFAULT 0.0,
            data_criacao TEXT,
            FOREIGN KEY(empresa_id) REFERENCES empresas(id) ON DELETE CASCADE
        )
    """)

    # Nova tabela para o Histórico de NCG
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico_ncg (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER,
            nome_simulacao TEXT,
            data_simulacao TEXT,
            fat_mensal REAL,
            cmv_mensal REAL,
            contas_receber REAL,
            estoque_atual REAL,
            contas_pagar REAL,
            reserva_financeira REAL,
            pme_atual REAL,
            pme_prop REAL,
            pmr_atual REAL,
            pmr_prop REAL,
            pmp_atual REAL,
            pmp_prop REAL,
            ncg_atual REAL,
            ncg_prop REAL,
            economia_ncg REAL,
            FOREIGN KEY(empresa_id) REFERENCES empresas(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cortes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            acao_id INTEGER,
            nome_corte TEXT,
            qualidade TEXT,
            peso REAL,
            preco_venda REAL,
            FOREIGN KEY(acao_id) REFERENCES acoes(id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    conn.close()

init_db()

def get_connection():
    return sqlite3.connect("desossa_db.db")

def get_tipos_desossa(empresa_id):
    conn = get_connection()
    cursor = conn.cursor()
    if empresa_id == 0:
        cursor.execute("SELECT DISTINCT nome FROM tipos_desossa ORDER BY nome ASC")
    else:
        cursor.execute("SELECT DISTINCT nome FROM tipos_desossa WHERE empresa_id IS NULL OR empresa_id = ? ORDER BY nome ASC", (empresa_id,))
    tipos = [r[0] for r in cursor.fetchall()]
    conn.close()
    return tipos

# =========================================================================
# 3. CONTROLE DE ESTADOS DO FORMULÁRIO
# =========================================================================
def init_form_states():
    if "form_version" not in st.session_state:
        st.session_state.form_version = 0
    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0
    if "cortes_temp" not in st.session_state:
        st.session_state.cortes_temp = []

def reset_form_states():
    st.session_state.form_version += 1
    st.session_state.cortes_temp = []

# =========================================================================
# 4. ELEMENTOS VISUAIS DE CABEÇALHO DA APLICAÇÃO
# =========================================================================
def exibir_cabecalho(nome_empresa_usuaria=None):
    col_logo, col_info = st.columns([1, 4])
    with col_logo:
        logo_encontrada = None
        for nome_possivel in ["logo_renato.jpeg", "logo_renato.jpg", "LOGO FINALIZADA.jpeg", "logo_renato.png"]:
            if os.path.exists(nome_possivel):
                logo_encontrada = nome_possivel
                break
                
        if logo_encontrada:
            st.image(logo_encontrada, width=120)
        else:
            st.markdown("### 🍖 [LOGO]")
            
    with col_info:
        cabecalho_principal = "RENATO FRIGOTUDO & ASSOCIADOS"
        subtitulo_empresa = nome_empresa_usuaria.upper() if nome_empresa_usuaria else "PORTAL DE ACESSO"

        st.markdown(
            f"""
            <div style="padding-top: 5px;">
                <h1 style="margin: 0; color: #1E3A8A; font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 28px; font-weight: 800; letter-spacing: 1px;">
                    {cabecalho_principal}
                </h1>
                <h3 style="margin: 4px 0 0 0; color: #0F172A; font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 18px; font-weight: 700;">
                    🏢 Empresa Usuária: {subtitulo_empresa}
                </h3>
            </div>
            """, 
            unsafe_allow_html=True
        )
    st.markdown("<hr style='margin-top: 10px; margin-bottom: 20px; border-top: 3px solid #1E3A8A;'>", unsafe_allow_html=True)

# =========================================================================
# 5. GERENCIAMENTO DE SESSÃO E LOGIN
# =========================================================================
if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.empresa_id = None
    st.session_state.empresa_nome = ""
    st.session_state.e_admin = False

init_form_states()

if not st.session_state.logado:
    exibir_cabecalho(nome_empresa_usuaria=None)
    st.title("🔒 Portal de Acesso - Gestão de Açougues")
    
    with st.form("form_login"):
        st.subheader("Login de Acesso")
        campo_login = st.text_input("Usuário / Login")
        campo_senha = st.text_input("Senha", type="password")
        btn_entrar = st.form_submit_button("Entrar no Sistema")
        
        if btn_entrar:
            login_formatado = campo_login.strip().lower() 
            
            if login_formatado == "admin" and campo_senha == "renato123":
                st.session_state.logado = True
                st.session_state.empresa_id = 0
                st.session_state.empresa_nome = "Administrador Geral"
                st.session_state.e_admin = True
                st.success("Acesso administrativo concedido!")
                st.rerun()
            else:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT id, nome, ativo FROM empresas WHERE LOWER(login) = ? AND senha = ?", (login_formatado, campo_senha))
                user = cursor.fetchone()
                conn.close()
                
                if user:
                    empresa_id, empresa_nome, status_ativo = user
                    if status_ativo == 0:
                        st.error("🚫 O acesso da sua empresa está suspenso temporariamente.")
                    else:
                        st.session_state.logado = True
                        st.session_state.empresa_id = empresa_id
                        st.session_state.empresa_nome = empresa_nome
                        st.session_state.e_admin = False
                        st.success(f"Login realizado como: {empresa_nome}!")
                        st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")

else:
    st.sidebar.markdown(f"**🏢 Empresa Usuária:**\n`{st.session_state.empresa_nome.upper()}`")
    st.sidebar.markdown("---")
    
    if st.sidebar.button("🚪 Sair do Sistema", key="btn_sair_sistema"):
        st.session_state.logado = False
        st.session_state.empresa_id = None
        st.session_state.empresa_nome = ""
        st.session_state.e_admin = False
        reset_form_states()
        st.rerun()

    if st.session_state.e_admin:
        menu = st.sidebar.radio("Selecione a Tela:", ["Cálculo Financeiro", "Ficha Técnica", "Capital de Giro (NCG)"], key="menu_admin")
    else:
        menu = st.sidebar.radio("Selecione a Tela:", ["Nova Desossa", "Histórico & Edição", "Cálculo Financeiro", "Ficha Técnica", "Capital de Giro (NCG)"], key="menu_operacional")

    exibir_cabecalho(nome_empresa_usuaria=st.session_state.empresa_nome)

    if menu == "Cálculo Financeiro":
        render_modulo_financeiro()
    elif menu == "Ficha Técnica":
        render_modulo_ficha_tecnica()
    elif menu == "Capital de Giro (NCG)":
        render_modulo_ncg()
    else:
        st.markdown("### Bem-vindo ao sistema operacional de desossas e gestão!")
        st.markdown("Utilize o menu lateral para navegar entre os módulos.")