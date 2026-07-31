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
# 1. CONFIGURAÇÃO VISUAL E PALETA DE CORES
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
    
    /* CORREÇÃO ROBUSTA DO FILE UPLOADER NA BARRA LATERAL */
    section[data-testid="stSidebar"] [data-testid="stFileUploader"] {
        background-color: #1E293B !important;
        border: 1px dashed #94A3B8 !important;
        border-radius: 8px !important;
        padding: 10px !important;
    }
    section[data-testid="stSidebar"] [data-testid="stFileUploader"] section {
        background-color: #1E293B !important;
    }
    section[data-testid="stSidebar"] [data-testid="stFileUploader"] label,
    section[data-testid="stSidebar"] [data-testid="stFileUploader"] span,
    section[data-testid="stSidebar"] [data-testid="stFileUploader"] small,
    section[data-testid="stSidebar"] [data-testid="stFileUploader"] p {
        color: #FFFFFF !important;
    }
    section[data-testid="stSidebar"] [data-testid="stFileUploader"] button {
        background-color: #A3A3A3 !important;
        color: #0F172A !important;
        border: 1px solid #737373 !important;
        font-weight: 700 !important;
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
# MÓDULO DE CÁLCULO FINANCEIRO
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
    if "params_fin" not in st.session_state:
        st.session_state.params_fin = {}

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

            else: 
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
            st.session_state.params_fin = {
                "sistema": sistema_amortizacao,
                "tipo_calculo": tipo_calculo,
                "taxa_informada": taxa_informada,
                "periodo_taxa": periodo_taxa,
                "prazo_informado": prazo_informado,
                "periodo_prazo": periodo_prazo,
                "prestacao_informada": prestacao_informada
            }

        except Exception as e:
            st.error(f"Erro ao realizar o cálculo financeiro: {e}")

    if st.session_state.df_fin is not None and not st.session_state.df_fin.empty:
        df_fin = st.session_state.df_fin
        valor_presente = st.session_state.valor_presente
        n_perodos = st.session_state.n_perodos
        i_equivalente = st.session_state.i_equivalente
        nome_sistema = st.session_state.nome_sistema
        params = st.session_state.get("params_fin", {})

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

        total_amortizacao = df_fin["Amortização"].sum()
        total_juros = df_fin["Juros"].sum()
        total_prestacao = df_fin["Prestação"].sum()

        st.markdown(f"""
        * **Total Amortizado:** R$ {total_amortizacao:,.2f}
        * **Total de Juros:** R$ {total_juros:,.2f}
        * **Montante Total Pago:** R$ {total_prestacao:,.2f}
        """)

        st.markdown("---")
        st.markdown("### 📥 Exportar Relatório Financeiro")
        
        col_exp1, col_exp2 = st.columns(2)

        with col_exp1:
            output_excel = io.BytesIO()
            with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
                df_fin.to_excel(writer, sheet_name=nome_sistema, index=False)
            output_excel.seek(0)
            
            st.download_button(
                label="📥 Baixar Planilha em Excel (.xlsx)",
                data=output_excel,
                file_name=f"tabela_{nome_sistema.lower().replace(' ', '_')}_{datetime.date.today().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="btn_dl_excel_fin"
            )

        with col_exp2:
            def gerar_pdf_financeiro():
                pdf = FPDF(orientation='L', unit='mm', format='A4')
                
                def criar_cabecalho_tabela():
                    criar_cabecalho_pdf_padrao(pdf, nome_sistema, st.session_state.get('empresa_nome', 'Empresa'))
                    
                    pdf.set_font("Arial", style="B", size=9)
                    pdf.set_fill_color(226, 232, 240)
                    pdf.cell(277, 5, "PARAMETROS UTILIZADOS NO CALCULO FINANCEIRO", ln=1, fill=True)
                    
                    pdf.set_font("Arial", size=8)
                    pdf.set_text_color(15, 23, 42)
                    
                    p_sys = params.get('sistema', nome_sistema)
                    p_tipo = params.get('tipo_calculo', 'N/A')
                    p_tx = params.get('taxa_informada', 0.0)
                    p_un_tx = params.get('periodo_taxa', 'Meses')
                    p_pz = params.get('prazo_informado', n_perodos)
                    p_un_pz = params.get('periodo_prazo', 'Meses')
                    
                    txt_param1 = f"Sistema: {p_sys} | Operacao: {p_tipo}"
                    txt_param2 = f"Taxa Informada: {p_tx:.4f}% a. {p_un_tx.lower()} | Taxa Equivalente por Periodo: {i_equivalente*100:.4f}% | Prazo: {p_pz} {p_un_pz.lower()} | Capital (PV): R$ {valor_presente:,.2f}"
                    
                    pdf.cell(277, 5, txt_param1.encode("latin1", "replace").decode("latin1"), ln=1)
                    pdf.cell(277, 5, txt_param2.encode("latin1", "replace").decode("latin1"), ln=1)
                    pdf.ln(2)

                    pdf.set_font("Arial", style="B", size=8.5)
                    pdf.set_fill_color(30, 58, 138)
                    pdf.set_text_color(255, 255, 255)
                    
                    headers = ["Periodo", "Valor Presente", "Amortizacao", "Juros", "Prestacao", "Taxa (%)"]
                    widths = [25, 55, 50, 50, 50, 47]
                    
                    for text_h, w_h in zip(headers, widths):
                        pdf.cell(w_h, 6, text_h.encode("latin1", "replace").decode("latin1"), border=1, align="C", fill=True)
                    pdf.ln()

                pdf.add_page()
                criar_cabecalho_tabela()

                pdf.set_font("Arial", size=8)
                pdf.set_text_color(15, 23, 42)
                for _, r in df_fin.iterrows():
                    if pdf.get_y() > 180:
                        pdf.add_page()
                        criar_cabecalho_tabela()
                        pdf.set_font("Arial", size=8)
                        pdf.set_text_color(15, 23, 42)

                    pdf.cell(25, 5, str(int(r["t"])), border=1, align="C")
                    pdf.cell(55, 5, f"R$ {r['VALOR PRESENTE']:,.2f}", border=1, align="R")
                    pdf.cell(50, 5, f"R$ {r['Amortização']:,.2f}", border=1, align="R")
                    pdf.cell(50, 5, f"R$ {r['Juros']:,.2f}", border=1, align="R")
                    pdf.cell(50, 5, f"R$ {r['Prestação']:,.2f}", border=1, align="R")
                    pdf.cell(47, 5, f"{r['Taxa (%)']:.4f}%".encode("latin1", "replace").decode("latin1"), border=1, align="C")
                    pdf.ln()

                return pdf.output(dest="S").encode("latin1")

            pdf_bytes_fin = gerar_pdf_financeiro()
            st.download_button(
                label="📄 Baixar Relatório em PDF (.pdf)",
                data=pdf_bytes_fin,
                file_name=f"relatorio_financeiro_{datetime.date.today().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                key="btn_dl_pdf_fin"
            )

# =========================================================================
# MÓDULO DE FICHA TÉCNICA E PRECIFICAÇÃO (COM EMISSÃO DE PDF)
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
            
            st.markdown("<br>", unsafe_allow_html=True)
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
                        st.success("🎉 Ficha técnica criada com sucesso! Agora você pode gerenciar seus insumos no menu de consulta.")
                    except Exception as e:
                        st.error(f"Erro ao salvar ficha técnica: {e}")

    else:
        conn = get_connection()
        df_fichas = pd.read_sql_query("SELECT * FROM fichas_tecnicas WHERE empresa_id = ? OR empresa_id IS NULL ORDER BY id DESC", conn, params=(emp_id_ativo,))
        conn.close()

        if df_fichas.empty:
            st.warning("⚠️ Nenhuma ficha técnica cadastrada. Selecione 'Cadastrar Nova Ficha Técnica' acima.")
        else:
            opcoes_fichas = {f"ID: {row['id']} - {row['produto']} (Criada em: {row['data_criacao']})": row['id'] for _, row in df_fichas.iterrows()}
            
            col_sel_f, col_btn_fpdf = st.columns([3, 1])
            with col_sel_f:
                ficha_selecionada_label = st.selectbox("Selecione a Ficha Técnica", list(opcoes_fichas.keys()), key="sel_ficha_cadastrada")
            
            ficha_id_ativo = opcoes_fichas[ficha_selecionada_label]
            ficha_row = df_fichas[df_fichas['id'] == ficha_id_ativo].iloc[0]

            conn = get_connection()
            df_insumos = pd.read_sql_query("SELECT * FROM insumos_ficha WHERE ficha_id = ?", conn, params=(ficha_id_ativo,))
            df_nao_ali = pd.read_sql_query("SELECT * FROM insumos_nao_alimenticios_ficha WHERE ficha_id = ?", conn, params=(ficha_id_ativo,))
            conn.close()

            if not df_insumos.empty:
                df_insumos['rendimento_pct_val'] = df_insumos['rendimento'].fillna(100.0)
                df_insumos['qtd_liquida'] = df_insumos['qtd_bruta'] * (df_insumos['rendimento_pct_val'] / 100.0)
                df_insumos['preco_liquido'] = df_insumos['qtd_liquida'] * df_insumos['preco_bruto']
                custo_alimenticios = df_insumos['preco_liquido'].sum()
            else:
                custo_alimenticios = 0.0

            if not df_nao_ali.empty:
                df_nao_ali['rendimento_pct_val'] = df_nao_ali['rendimento'].fillna(100.0)
                df_nao_ali['qtd_liquida'] = df_nao_ali['qtd_bruta'] * (df_nao_ali['rendimento_pct_val'] / 100.0)
                df_nao_ali['preco_liquido'] = df_nao_ali['qtd_liquida'] * df_nao_ali['preco_bruto']
                custo_nao_alimenticios = df_nao_ali['preco_liquido'].sum()
            else:
                custo_nao_alimenticios = 0.0

            custo_total = custo_alimenticios + custo_nao_alimenticios

            custo_kg_crua = custo_total / ficha_row['rendimento_kg'] if ficha_row['rendimento_kg'] > 0 else 0.0
            custo_kg_assada = custo_total / ficha_row['rendimento_assada_kg'] if ficha_row['rendimento_assada_kg'] > 0 else 0.0
            
            unidades_prod_cadastrada = ficha_row['unidades_produzidas'] if 'unidades_produzidas' in ficha_row and ficha_row['unidades_produzidas'] > 0 else (ficha_row['rendimento_assada_kg'] / ficha_row['peso_unidade_kg'] if ficha_row['peso_unidade_kg'] > 0 else 0.0)
            custo_unidade_produzida = custo_total / unidades_prod_cadastrada if unidades_prod_cadastrada > 0 else 0.0
            qtd_pacote_atual = ficha_row['qtd_por_pacote'] if 'qtd_por_pacote' in ficha_row and ficha_row['qtd_por_pacote'] is not None else 1.0
            custo_pacote = custo_unidade_produzida * qtd_pacote_atual

            st.markdown("---")
            st.markdown("### 🏷️ Cálculo de Precificação (Simulador de Venda)")
            col_p1, col_p2, col_p3 = st.columns(3)
            with col_p1:
                aliquota_imposto = st.number_input("Imposto (%)", min_value=0.0, max_value=100.0, value=5.0, step=0.1, key=f"aliq_imp_{ficha_id_ativo}")
                taxa_cartao = st.number_input("Tx. de Cartão e Antecip. (%)", min_value=0.0, max_value=100.0, value=5.0, step=0.1, key=f"tx_cart_{ficha_id_ativo}")
                comissao_venda = st.number_input("Comissão (%)", min_value=0.0, max_value=100.0, value=3.5, step=0.1, key=f"comissao_{ficha_id_ativo}")
            with col_p2:
                outros_custos_var = st.number_input("Outros custos Variáveis e Oper. (%)", min_value=0.0, max_value=100.0, value=1.0, step=0.1, key=f"out_cust_{ficha_id_ativo}")
                part_desp_fixas = st.number_input("Partic. Desp. Fixas e não Oper. (%)", min_value=0.0, max_value=100.0, value=2.0, step=0.1, key=f"p_fixas_{ficha_id_ativo}")
                desconto_venda = st.number_input("Simulação de Desconto (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.1, key=f"desconto_{ficha_id_ativo}")
            with col_p3:
                indicador_cer_escolhido = st.selectbox(
                    "Custo de aquisição (CER):",
                    ["Custo por Unidade Produzida", "Custo por KG (Assada)", "Custo por KG (Crua)", "Custo por Pacote", "Custo Total"],
                    key=f"ind_cer_{ficha_id_ativo}"
                )
                modo_precificacao = st.radio(
                    "Modo de Definição do Preço:",
                    ["Informar Margem de Lucro (%)", "Informar Preço de Venda Praticado (R$)"],
                    key=f"modo_prec_{ficha_id_ativo}"
                )

            if indicador_cer_escolhido == "Custo por Unidade Produzida": cer_base = custo_unidade_produzida
            elif indicador_cer_escolhido == "Custo por KG (Assada)": cer_base = custo_kg_assada
            elif indicador_cer_escolhido == "Custo por KG (Crua)": cer_base = custo_kg_crua
            elif indicador_cer_escolhido == "Custo por Pacote": cer_base = custo_pacote
            else: cer_base = custo_total

            if modo_precificacao == "Informar Margem de Lucro (%)":
                margem_lucro = st.number_input("Margem de Lucro:", min_value=0.0, max_value=100.0, value=31.07, step=0.1, key=f"margem_{ficha_id_ativo}")
                soma_percentuais = (aliquota_imposto + taxa_cartao + comissao_venda + outros_custos_var + part_desp_fixas + margem_lucro) / 100.0
                divisor_preco = 1.0 - soma_percentuais
                preco_venda_tabela = cer_base / divisor_preco if divisor_preco > 0 else 0.0
            else:
                preco_venda_tabela = st.number_input("Preço de Venda Praticado (R$)", min_value=0.0, value=cer_base * 1.5, step=0.50, format="%.2f", key=f"preco_praticado_{ficha_id_ativo}")
                soma_sem_margem = (aliquota_imposto + taxa_cartao + comissao_venda + outros_custos_var + part_desp_fixas) / 100.0
                if preco_venda_tabela > 0:
                    custos_perc_valor = preco_venda_tabela * soma_sem_margem
                    lucro_calculado_val = preco_venda_tabela - cer_base - custos_perc_valor
                    margem_lucro = (lucro_calculado_val / preco_venda_tabela) * 100.0
                else:
                    margem_lucro = 0.0

            fator_desconto = (1.0 - (desconto_venda / 100.0))
            preco_venda_efetivo = preco_venda_tabela * fator_desconto
            valor_lucro_efetivo = preco_venda_efetivo - cer_base - (preco_venda_efetivo * ((aliquota_imposto + taxa_cartao + comissao_venda + outros_custos_var + part_desp_fixas) / 100.0))
            markup_calculado = (preco_venda_efetivo / cer_base - 1.0) * 100.0 if cer_base > 0 else 0.0

            st.success(f"""
            🎯 **Resultado da Precificação ({indicador_cer_escolhido}):**
            * **Custo Base (CER):** R$ {cer_base:,.2f}
            * **Preço de Venda de Tabela:** R$ {preco_venda_tabela:,.2f}
            * **Preço de Venda Efetivo (Com Desconto de {desconto_venda}%):** **R$ {preco_venda_efetivo:,.2f}**
            * **Margem de Lucro Efetiva:** {margem_lucro:.2f}%
            * **MARKUP >>:** {markup_calculado:.2f}%
            * **Lucro Líquido Previsto:** R$ {valor_lucro_efetivo:,.2f}
            """)

            st.markdown("---")
            st.markdown("### 📥 Exportar Relatório da Ficha Técnica em PDF")
            
            def gerar_pdf_ficha_tecnica():
                pdf = FPDF(orientation='P', unit='mm', format='A4')
                pdf.add_page()
                criar_cabecalho_pdf_padrao(pdf, f"Ficha Tecnica - {ficha_row['produto']}", st.session_state.get('empresa_nome', 'Empresa'))
                
                pdf.set_font("Arial", style="B", size=9)
                pdf.cell(190, 6, f"Produto: {ficha_row['produto']} | Data: {ficha_row['data_criacao']}", ln=1)
                pdf.cell(190, 6, f"Rendimento Total: {ficha_row['rendimento_kg']:.3f} KG | Assada: {ficha_row['rendimento_assada_kg']:.3f} KG", ln=1)
                pdf.cell(190, 6, f"Custo Total da Receita: R$ {custo_total:,.2f} | Custo por KG Assada: R$ {custo_kg_assada:,.2f}", ln=1)
                pdf.cell(190, 6, f"Preço de Venda Efetivo: R$ {preco_venda_efetivo:,.2f} | Margem: {margem_lucro:.2f}%", ln=1)
                pdf.ln(4)
                
                return pdf.output(dest="S").encode("latin1")

            pdf_bytes_ficha = gerar_pdf_ficha_tecnica()
            st.download_button(
                label="📄 Baixar Relatório da Ficha Técnica (.pdf)",
                data=pdf_bytes_ficha,
                file_name=f"ficha_tecnica_{ficha_row['produto'].lower().replace(' ', '_')}.pdf",
                mime="application/pdf",
                key=f"btn_dl_pdf_ficha_{ficha_id_ativo}"
            )

# =========================================================================
# MÓDULO DE CAPITAL DE GIRO (NCG)
# =========================================================================
def render_modulo_ncg():
    st.markdown("""
        <div style="background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%); padding: 25px; border-radius: 12px; color: white; margin-bottom: 25px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
            <h2 style="margin: 0; color: white !important;">📈 Análise de Necessidade de Capital de Giro (NCG)</h2>
            <p style="margin: 8px 0 0 0; font-size: 15px; opacity: 0.9;">Calcule, armazene no banco de dados, filtre por período, edite parâmetros ou exporte em PDF.</p>
        </div>
    """, unsafe_allow_html=True)

    emp_id_ativo = st.session_state.empresa_id
    aba_ncg = st.selectbox("Selecione a Ação no Módulo NCG", ["Novo Cálculo / Simulação", "Consultar Histórico, Filtrar por Data e Editar"], key="sel_aba_ncg_geral")

    def gerar_relatorio_pdf_ncg(nome_simulacao, data_sim, faturamento, cmv):
        pdf = FPDF(orientation='L', unit='mm', format='A4')
        pdf.add_page()
        criar_cabecalho_pdf_padrao(pdf, "Relatorio de Necessidade de Capital de Giro (NCG)", st.session_state.get('empresa_nome', 'Empresa'))
        pdf.set_font("Arial", style="B", size=9)
        pdf.cell(277, 5, f"Simulacao: {nome_simulacao} | Data: {data_sim} | Faturamento: R$ {faturamento:,.2f} | CMV: R$ {cmv:,.2f}", ln=1)
        pdf.ln(3)
        return pdf.output(dest="S").encode("latin1")

    if aba_ncg == "Novo Cálculo / Simulação":
        with st.form("form_ncg_calculo"):
            st.subheader("0. Identificação da Simulação")
            nome_simulacao = st.text_input("Nome / Descrição da Simulação", value=f"Simulação NCG - {datetime.date.today().strftime('%d/%m/%Y')}")
            data_simulacao = st.date_input("Data de Referência", datetime.date.today())
            st.markdown("---")
            st.subheader("1. Dados Financeiros da Empresa (Entrada)")
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                fat_mensal = st.number_input("Faturamento Bruto Mensal (R$)", min_value=0.0, value=157399.10, step=100.0, format="%.2f")
                cmv_mensal = st.number_input("Custo da Mercadoria Vendida - CMV (R$)", min_value=0.0, value=98409.78, step=100.0, format="%.2f")
                contas_receber = st.number_input("Contas a Receber Acumuladas (R$)", min_value=0.0, value=1193.67, step=10.0, format="%.2f")
            with col_d2:
                estoque_atual = st.number_input("Estoque Atual (R$)", min_value=0.0, value=18700.00, step=100.0, format="%.2f")
                contas_pagar = st.number_input("Contas a Pagar / Fornecedores (R$)", min_value=0.0, value=50971.32, step=100.0, format="%.2f")
                reserva_financeira = st.number_input("Reserva Financeira / Caixa (R$)", min_value=0.0, value=0.0, step=100.0, format="%.2f")

            st.markdown("---")
            st.subheader("2. Prazos Médios Operacionais (em dias)")
            col_p1, col_p2, col_p3 = st.columns(3)
            with col_p1:
                pme_atual = st.number_input("PME Atual", min_value=0.0, value=8.5, step=0.5)
                pme_prop = st.number_input("PME Proposto", min_value=0.0, value=7.0, step=0.5)
            with col_p2:
                pmr_atual = st.number_input("PMR Atual", min_value=0.0, value=1.0, step=0.5)
                pmr_prop = st.number_input("PMR Proposto", min_value=0.0, value=7.0, step=0.5)
            with col_p3:
                pmp_atual = st.number_input("PMP Atual", min_value=0.0, value=14.0, step=0.5)
                pmp_prop = st.number_input("PMP Proposto", min_value=0.0, value=18.0, step=0.5)

            btn_calc_ncg = st.form_submit_button("🚀 Calcular e Salvar Simulação de NCG")

        if btn_calc_ncg:
            try:
                cmv_diario = cmv_mensal / 30.0
                ciclo_atual = pme_atual + pmr_atual - pmp_atual
                ciclo_prop = pme_prop + pmr_prop - pmp_prop
                ncg_atual = cmv_diario * ciclo_atual
                ncg_prop = cmv_diario * ciclo_prop
                economia_ncg = ncg_atual - ncg_prop

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
                st.success("🎉 Simulação calculada e salva com sucesso!")
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")
    else:
        st.markdown("### 📂 Histórico de Simulações NCG")
        conn = get_connection()
        df_hist = pd.read_sql_query("SELECT * FROM historico_ncg WHERE empresa_id = ? ORDER BY data_simulacao DESC", conn, params=(emp_id_ativo,))
        conn.close()
        if df_hist.empty:
            st.warning("Nenhuma simulação salva encontrada.")
        else:
            st.dataframe(df_hist, use_container_width=True)

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
    
    try:
        cursor.execute("ALTER TABLE tipos_desossa ADD COLUMN empresa_id INTEGER DEFAULT NULL")
    except sqlite3.OperationalError:
        pass

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

    try:
        cursor.execute("ALTER TABLE fichas_tecnicas ADD COLUMN unidades_produzidas REAL DEFAULT 1.0")
    except sqlite3.OperationalError:
        pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS insumos_ficha (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ficha_id INTEGER,
            codigo TEXT,
            produto_insumo TEXT NOT NULL,
            qtd_bruta REAL DEFAULT 0.0,
            unidade TEXT,
            preco_bruto REAL DEFAULT 0.0,
            rendimento REAL DEFAULT 100.0,
            FOREIGN KEY(ficha_id) REFERENCES fichas_tecnicas(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS insumos_nao_alimenticios_ficha (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ficha_id INTEGER,
            codigo TEXT,
            produto_insumo TEXT NOT NULL,
            qtd_bruta REAL DEFAULT 0.0,
            unidade TEXT,
            preco_bruto REAL DEFAULT 0.0,
            rendimento REAL DEFAULT 100.0,
            FOREIGN KEY(ficha_id) REFERENCES fichas_tecnicas(id) ON DELETE CASCADE
        )
    """)

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
    
    cursor.execute("SELECT COUNT(*) FROM tipos_desossa")
    if cursor.fetchone()[0] == 0:
        tipos_iniciais = [
            ("QUARTO TRASEIRO", None), ("QUARTO DIANTEIRO", None), 
            ("VACA CASADA", None), ("BOI CASADO", None), ("SUINO", None)
        ]
        cursor.executemany("INSERT INTO tipos_desossa (nome, empresa_id) VALUES (?, ?)", tipos_iniciais)
    
    cursor.execute("SELECT COUNT(*) FROM cortes_padrao")
    if cursor.fetchone()[0] == 0:
        cortes_iniciais = [
            ("VACA CASADA", "COXAO DURO", None), ("VACA CASADA", "COXAO MOLE", None), 
            ("VACA CASADA", "PATINHO", None), ("VACA CASADA", "ALCATRA C MAMINHA", None),
            ("VACA CASADA", "PICANHA", None), ("VACA CASADA", "FILET MIGNON", None),
            ("VACA CASADA", "FRALDINHA", None), ("VACA CASADA", "COSTELA MINGA", None),
            ("QUARTO TRASEIRO", "PICANHA", None), ("QUARTO TRASEIRO", "ALCATRA", None), 
            ("QUARTO DIANTEIRO", "ACEM", None), ("SUINO", "PERNIL", None)
        ]
        cursor.executemany("INSERT OR IGNORE INTO cortes_padrao (tipo_desossa, nome_corte, empresa_id) VALUES (?, ?, ?)", cortes_iniciais)

    cursor.execute("SELECT COUNT(*) FROM fichas_tecnicas WHERE produto = 'ESPETINHO ASSADO'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO fichas_tecnicas (empresa_id, produto, rendimento_kg, rendimento_assada_kg, peso_unidade_kg, qtd_por_pacote, unidades_produzidas, perda_pct, data_criacao)
            VALUES (NULL, 'ESPETINHO ASSADO', 13.013, 11.83, 0.100, 4.0, 118.3, 0.0908, ?)
        """, (str(datetime.date.today()),))
        ficha_espetinho_id = cursor.lastrowid

        insumos_alimenticios_espetinho = [
            (ficha_espetinho_id, None, 'CARNE PARA ESPETO', 11.42, 'KG', 33.9, 100.0),
            (ficha_espetinho_id, None, 'GORDURA PARA ESPETO', 1.128, 'KG', 9.9, 100.0),
            (ficha_espetinho_id, None, 'SAL', 0.12, 'KG', 3.99, 100.0)
        ]
        cursor.executemany("""
            INSERT INTO insumos_ficha (ficha_id, codigo, produto_insumo, qtd_bruta, unidade, preco_bruto, rendimento)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, insumos_alimenticios_espetinho)

        insumos_nao_alimenticios_espetinho = [
            (ficha_espetinho_id, None, 'ESPETO DE BAMBU', 118.0, 'UNID', 0.06, 100.0)
        ]
        cursor.executemany("""
            INSERT INTO insumos_nao_alimenticios_ficha (ficha_id, codigo, produto_insumo, qtd_bruta, unidade, preco_bruto, rendimento)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, insumos_nao_alimenticios_espetinho)
        
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
    st.sidebar.markdown("### 💾 Backup do Sistema")
    
    try:
        with open("desossa_db.db", "rb") as db_file:
            db_bytes = db_file.read()
        st.sidebar.download_button(
            label="📥 Exportar Backup (.db)",
            data=db_bytes,
            file_name=f"backup_acougue_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
            mime="application/octet-stream",
            key="btn_bkp_db"
        )
    except Exception:
        st.sidebar.error("Erro ao gerar backup.")
        
    backup_upload = st.sidebar.file_uploader("📤 Restaurar Backup (.db)", type=["db"], key="file_uploader_backup")
    if backup_upload is not None:
        if st.sidebar.button("⚠️ Confirmar Restauração", key="btn_conf_restaurar"):
            try:
                with open("desossa_db.db", "wb") as f:
                    f.write(backup_upload.getbuffer())
                st.sidebar.success("🎉 Sistema restaurado! Recarregando...")
                st.rerun()
            except Exception:
                st.sidebar.error("Erro ao restaurar arquivo.")
                
    st.sidebar.markdown("---")
    
    if st.sidebar.button("🚪 Sair do Sistema", key="btn_sair_sistema"):
        st.session_state.logado = False
        st.session_state.empresa_id = None
        st.session_state.empresa_nome = ""
        st.session_state.e_admin = False
        reset_form_states()
        st.rerun()

    if st.session_state.e_admin:
        st.sidebar.markdown("### 🛠️ Menu Administrativo")
        menu = st.sidebar.radio("Selecione a Tela:", ["Gerenciar Empresas", "Cadastrar Empresa", "Gerenciar Cadastro de Cortes", "Importar Cortes (CSV)", "Cálculo Financeiro", "Ficha Técnica", "Capital de Giro (NCG)"], key="menu_admin")
    else:
        st.sidebar.markdown("### 🥩 Menu de Operações")
        menu = st.sidebar.radio("Selecione a Tela:", ["Nova Desossa", "Histórico & Edição", "Gerenciar Cadastro de Cortes", "Cálculo Financeiro", "Ficha Técnica", "Capital de Giro (NCG)"], key="menu_operacional")

    exibir_cabecalho(nome_empresa_usuaria=st.session_state.empresa_nome)

    if menu == "Cálculo Financeiro":
        render_modulo_financeiro()
    elif menu == "Ficha Técnica":
        render_modulo_ficha_tecnica()
    elif menu == "Capital de Giro (NCG)":
        render_modulo_ncg()
    elif menu == "Gerenciar Cadastro de Cortes":
        st.header("🥩 Configurar e Gerenciar Tipos de Desossa e Cortes")
        emp_id_ativo = st.session_state.empresa_id
        tipos_disponiveis = get_tipos_desossa(emp_id_ativo)
        if tipos_disponiveis:
            tipo_sel = st.selectbox("Selecione o Tipo de Desossa", tipos_disponiveis, key="tipo_sel_cortes")
            st.markdown(f"Gerenciando cortes para: **{tipo_sel}**")
    else:
        st.header(f"Bem-vindo ao sistema - Tela: {menu}")