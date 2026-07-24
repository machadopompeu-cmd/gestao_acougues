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
    section[data-testid="stSidebar"] section[data-testid="stFileUploaderDropzone"] {
        background-color: #1E293B !important;
        border: 2px dashed #A3A3A3 !important;
        border-radius: 8px !important;
    }
    section[data-testid="stSidebar"] section[data-testid="stFileUploaderDropzone"] div {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }
    section[data-testid="stSidebar"] section[data-testid="stFileUploaderDropzone"] button,
    section[data-testid="stSidebar"] section[data-testid="stFileUploaderDropzone"] button *,
    section[data-testid="stSidebar"] section[data-testid="stFileUploaderDropzone"] a,
    section[data-testid="stSidebar"] section[data-testid="stFileUploaderDropzone"] a * {
        color: #0F172A !important;
        fill: #0F172A !important;
        font-weight: 700 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# =========================================================================
# FUNÇÃO PADRÃO DE CABEÇALHO PARA RELATÓRIOS PDF (DIMENSIONADA)
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
    pdf.rect(30, 8, 170, 12, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", style="B", size=10)
    pdf.set_xy(30, 10)
    pdf.cell(170, 8, f"RENATO FRIGOTUDO & ASSOCIADOS - {titulo_relatorio.upper()}", ln=1, align="C")
    
    pdf.set_text_color(15, 23, 42)
    pdf.set_font("Arial", style="B", size=8.5)
    pdf.set_xy(10, 22)
    txt_empresa = f"Empresa Usuária: {nome_empresa_usuaria}"
    pdf.cell(190, 5, txt_empresa.encode("latin1", "replace").decode("latin1"), ln=1, align="C")
    
    pdf.set_draw_color(30, 58, 138)
    pdf.set_line_width(0.6)
    pdf.line(10, 28, 200, 28)
    pdf.set_xy(10, 31)

# =========================================================================
# MÓDULO DE CÁLCULO FINANCEIRO (SISTEMA PRICE & SISTEMA SAC)
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
                    pdf.set_font("Arial", style="B", size=8.5)
                    pdf.set_fill_color(30, 58, 138)
                    pdf.set_text_color(255, 255, 255)
                    
                    headers = ["Periodo", "Valor Presente", "Amortizacao", "Juros", "Prestacao", "Taxa"]
                    widths = [25, 55, 50, 50, 50, 47]
                    
                    for text_h, w_h in zip(headers, widths):
                        pdf.cell(w_h, 6, text_h.encode("latin1", "replace").decode("latin1"), border=1, align="C", fill=True)
                    pdf.ln()

                pdf.add_page()
                criar_cabecalho_tabela()

                pdf.set_font("Arial", size=8)
                pdf.set_text_color(15, 23, 42)
                for _, r in df_fin.iterrows():
                    if pdf.get_y() > 185:
                        pdf.add_page()
                        criar_cabecalho_tabela()
                        pdf.set_font("Arial", size=8)
                        pdf.set_text_color(15, 23, 42)

                    pdf.cell(25, 5, str(int(r["t"])), border=1, align="C")
                    pdf.cell(55, 5, f"R$ {r['VALOR PRESENTE']:,.2f}", border=1, align="R")
                    pdf.cell(50, 5, f"R$ {r['Amortização']:,.2f}", border=1, align="R")
                    pdf.cell(50, 5, f"R$ {r['Juros']:,.2f}", border=1, align="R")
                    pdf.cell(50, 5, f"R$ {r['Prestação']:,.2f}", border=1, align="R")
                    pdf.cell(47, 5, f"{r['Taxa (%)']:.4f}%", border=1, align="C")
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
# MÓDULO DE FICHA TÉCNICA E PRECIFICAÇÃO (ALIMENTÍCIOS E NÃO ALIMENTÍCIOS)
# =========================================================================
def render_modulo_ficha_tecnica():
    st.markdown("""
        <div style="background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%); padding: 20px; border-radius: 12px; color: white; margin-bottom: 25px;">
            <h2 style="margin: 0; color: white !important;">📋 Módulo de Ficha Técnica & Precificação</h2>
            <p style="margin: 5px 0 0 0; font-size: 15px; opacity: 0.9;">Gerencie fichas técnicas de produtos, controle insumos em tabelas e apure custos de produção em tempo real.</p>
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
            
            # Cálculo automático da perda % para o cadastro novo
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
                            INSERT INTO fichas_tecnicas (empresa_id, produto, rendimento_kg, rendimento_assada_kg, peso_unidade_kg, qtd_por_pacote, perda_pct, data_criacao)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (emp_id_ativo, nome_produto.strip().upper(), rendimento_kg_novo, rendimento_assada_kg_novo, peso_unidade_kg, qtd_por_pacote, perda_calculada_nova, str(datetime.date.today())))
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

            custo_alimenticios = (df_insumos['qtd_bruta'] * df_insumos['preco_bruto']).sum() if not df_insumos.empty else 0.0
            custo_nao_alimenticios = (df_nao_ali['qtd_bruta'] * df_nao_ali['preco_bruto']).sum() if not df_nao_ali.empty else 0.0
            custo_total = custo_alimenticios + custo_nao_alimenticios

            custo_kg_crua = custo_total / ficha_row['rendimento_kg'] if ficha_row['rendimento_kg'] > 0 else 0.0
            custo_kg_assada = custo_total / ficha_row['rendimento_assada_kg'] if ficha_row['rendimento_assada_kg'] > 0 else 0.0
            
            unidades_produzidas = ficha_row['rendimento_assada_kg'] / ficha_row['peso_unidade_kg'] if ficha_row['peso_unidade_kg'] > 0 else 0.0
            pacotes = unidades_produzidas / ficha_row['qtd_por_pacote'] if ficha_row['qtd_por_pacote'] > 0 else 0.0
            
            custo_unidade = custo_total / unidades_produzidas if unidades_produzidas > 0 else 0.0
            custo_pacote = custo_unidade * ficha_row['qtd_por_pacote']

            with col_btn_fpdf:
                st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                def gerar_pdf_ficha_tecnica():
                    pdf = FPDF(orientation='P', unit='mm', format='A4')
                    
                    def montar_cabecalho_ficha():
                        criar_cabecalho_pdf_padrao(pdf, f"Ficha Tecnica - {ficha_row['produto']}", st.session_state.empresa_nome)

                    pdf.add_page()
                    montar_cabecalho_ficha()

                    # Parâmetros Gerais
                    pdf.set_font("Arial", style="B", size=10)
                    pdf.set_fill_color(226, 232, 240)
                    pdf.cell(190, 6, "1. PARAMETROS DE RENDIMENTO", ln=1, fill=True)
                    pdf.set_font("Arial", size=9)
                    pdf.cell(95, 5, f"Produto: {ficha_row['produto']}", border=1)
                    pdf.cell(95, 5, f"Data de Criacao: {ficha_row['data_criacao']}", border=1, ln=1)
                    pdf.cell(63, 5, f"Rendimento Total: {ficha_row['rendimento_kg']:.3f} KG", border=1)
                    pdf.cell(63, 5, f"Rend. Assada: {ficha_row['rendimento_assada_kg']:.3f} KG", border=1)
                    pdf.cell(64, 5, f"Peso Unidade: {ficha_row['peso_unidade_kg']:.3f} KG", border=1, ln=1)
                    pdf.cell(95, 5, f"Qtd por Pacote: {ficha_row['qtd_por_pacote']}", border=1)
                    pdf.cell(95, 5, f"Perda % (Indicador): {ficha_row['perda_pct']*100:.2f}%", border=1, ln=1)
                    pdf.ln(4)

                    # Indicadores Financeiros
                    pdf.set_font("Arial", style="B", size=10)
                    pdf.set_fill_color(226, 232, 240)
                    pdf.cell(190, 6, "2. INDICADORES E CUSTOS CONSOLIDADOS", ln=1, fill=True)
                    pdf.set_font("Arial", size=9)
                    pdf.cell(95, 5, f"Custo Insumos Alimenticios: R$ {custo_alimenticios:.2f}", border=1)
                    pdf.cell(95, 5, f"Custo Insumos Nao Alimenticios: R$ {custo_nao_alimenticios:.2f}", border=1, ln=1)
                    pdf.cell(95, 5, f"Custo Total de Producao: R$ {custo_total:.2f}", border=1)
                    pdf.cell(95, 5, f"Custo por KG (Crua): R$ {custo_kg_crua:.2f}", border=1, ln=1)
                    pdf.cell(95, 5, f"Custo por KG (Assada): R$ {custo_kg_assada:.2f}", border=1)
                    pdf.cell(95, 5, f"Custo por Unidade: R$ {custo_unidade:.2f}", border=1, ln=1)
                    pdf.cell(95, 5, f"Custo por Pacote: R$ {custo_pacote:.2f}", border=1)
                    pdf.cell(95, 5, f"Unidades Produzidas: {unidades_produzidas:.2f}", border=1, ln=1)
                    pdf.ln(4)

                    # Insumos Alimentícios
                    pdf.set_font("Arial", style="B", size=10)
                    pdf.set_fill_color(226, 232, 240)
                    pdf.cell(190, 6, "3. INSUMOS ALIMENTICIOS", ln=1, fill=True)
                    pdf.set_font("Arial", style="B", size=8.5)
                    pdf.set_fill_color(30, 58, 138)
                    pdf.set_text_color(255, 255, 255)
                    pdf.cell(25, 5, "Codigo", border=1, align="C", fill=True)
                    pdf.cell(85, 5, "Produto / Insumo", border=1, align="L", fill=True)
                    pdf.cell(25, 5, "Qtd Bruta", border=1, align="C", fill=True)
                    pdf.cell(20, 5, "Un.", border=1, align="C", fill=True)
                    pdf.cell(35, 5, "Preco Bruto", border=1, align="R", fill=True)
                    pdf.ln()

                    pdf.set_font("Arial", size=8.5)
                    pdf.set_text_color(15, 23, 42)
                    if df_insumos.empty:
                        pdf.cell(190, 5, "Nenhum insumo alimenticio cadastrado.", border=1, align="C", ln=1)
                    else:
                        for _, ri in df_insumos.iterrows():
                            pdf.cell(25, 5, str(ri['codigo'] or ""), border=1, align="C")
                            pdf.cell(85, 5, str(ri['produto_insumo'])[:45].encode("latin1", "replace").decode("latin1"), border=1)
                            pdf.cell(25, 5, f"{ri['qtd_bruta']:.3f}", border=1, align="R")
                            pdf.cell(20, 5, str(ri['unidade']), border=1, align="C")
                            pdf.cell(35, 5, f"R$ {ri['preco_bruto']:.2f}", border=1, align="R")
                            pdf.ln()
                    pdf.ln(4)

                    # Insumos Não Alimentícios
                    pdf.set_font("Arial", style="B", size=10)
                    pdf.set_fill_color(226, 232, 240)
                    pdf.cell(190, 6, "4. INSUMOS NAO ALIMENTICIOS (EMBALAGENS, GAS, ETC.)", ln=1, fill=True)
                    pdf.set_font("Arial", style="B", size=8.5)
                    pdf.set_fill_color(30, 58, 138)
                    pdf.set_text_color(255, 255, 255)
                    pdf.cell(25, 5, "Codigo", border=1, align="C", fill=True)
                    pdf.cell(85, 5, "Produto / Insumo", border=1, align="L", fill=True)
                    pdf.cell(25, 5, "Qtd Bruta", border=1, align="C", fill=True)
                    pdf.cell(20, 5, "Un.", border=1, align="C", fill=True)
                    pdf.cell(35, 5, "Preco Bruto", border=1, align="R", fill=True)
                    pdf.ln()

                    pdf.set_font("Arial", size=8.5)
                    pdf.set_text_color(15, 23, 42)
                    if df_nao_ali.empty:
                        pdf.cell(190, 5, "Nenhum insumo nao alimenticio cadastrado.", border=1, align="C", ln=1)
                    else:
                        for _, rna in df_nao_ali.iterrows():
                            pdf.cell(25, 5, str(rna['codigo'] or ""), border=1, align="C")
                            pdf.cell(85, 5, str(rna['produto_insumo'])[:45].encode("latin1", "replace").decode("latin1"), border=1)
                            pdf.cell(25, 5, f"{rna['qtd_bruta']:.3f}", border=1, align="R")
                            pdf.cell(20, 5, str(rna['unidade']), border=1, align="C")
                            pdf.cell(35, 5, f"R$ {rna['preco_bruto']:.2f}", border=1, align="R")
                            pdf.ln()

                    return pdf.output(dest="S").encode("latin1")

                pdf_bytes_ficha = gerar_pdf_ficha_tecnica()
                st.download_button(
                    label="📄 Baixar PDF da Ficha",
                    data=pdf_bytes_ficha,
                    file_name=f"ficha_tecnica_{ficha_row['produto'].lower().replace(' ', '_')}_{datetime.date.today().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    key="btn_dl_pdf_ficha_tecnica"
                )

            # Painel de Cards com Indicadores Principais
            st.markdown("### 📊 Indicadores e Custos Consolidados")
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Custo Total", f"R$ {custo_total:.2f}")
            m2.metric("Custo / Kg (Assada)", f"R$ {custo_kg_assada:.2f}")
            m3.metric("Custo da Unidade", f"R$ {custo_unidade:.2f}")
            m4.metric("Custo do Pacote", f"R$ {custo_pacote:.2f}")

            with st.expander("✏️ Editar Parâmetros de Rendimento desta Ficha", expanded=False):
                with st.form(f"form_edit_parametros_ficha_{ficha_id_ativo}"):
                    ed_col1, ed_col2 = st.columns(2)
                    with ed_col1:
                        edit_nome_prod = st.text_input("Nome do Produto / Prato", value=ficha_row['produto'])
                        edit_rend_kg = st.number_input("Rendimento Total (KG)", min_value=0.0, value=float(ficha_row['rendimento_kg']), step=0.1, format="%.3f", key="edit_rend_t")
                        edit_rend_ass = st.number_input("Rendimento Depois de Assada (KG)", min_value=0.0, value=float(ficha_row['rendimento_assada_kg']), step=0.01, format="%.3f", key="edit_rend_a")
                    with ed_col2:
                        edit_peso_un = st.number_input("Peso da Unidade (KG)", min_value=0.0, value=float(ficha_row['peso_unidade_kg']), step=0.001, format="%.3f")
                        edit_qtd_pct = st.number_input("Quantidade por Pacote", min_value=1.0, value=float(ficha_row['qtd_por_pacote']), step=1.0)
                    
                    # Cálculo automático da perda % no painel de edição
                    perda_calculada_edit = (edit_rend_kg - edit_rend_ass) / edit_rend_kg if edit_rend_kg > 0 else 0.0
                    if perda_calculada_edit < 0:
                        perda_calculada_edit = 0.0

                    st.markdown(f"**📉 Perda % (Indicador Automático):** `{perda_calculada_edit*100:.2f}%` ({perda_calculada_edit:.4f})")
                    
                    if st.form_submit_button("💾 Salvar Alterações dos Parâmetros"):
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE fichas_tecnicas 
                            SET produto = ?, rendimento_kg = ?, rendimento_assada_kg = ?, peso_unidade_kg = ?, qtd_por_pacote = ?, perda_pct = ?
                            WHERE id = ?
                        """, (edit_nome_prod.strip().upper(), edit_rend_kg, edit_rend_ass, edit_peso_un, edit_qtd_pct, perda_calculada_edit, ficha_id_ativo))
                        conn.commit()
                        conn.close()
                        st.success("Parâmetros e Perda % atualizados com sucesso!")
                        st.rerun()

            with st.expander("🗑️ Excluir esta Ficha Técnica Inteira", expanded=False):
                confirmar_exclusao_ficha = st.checkbox("Confirmar exclusão da ficha e todos os seus insumos", key=f"chk_exc_ficha_{ficha_id_ativo}")
                if st.button("🗑️ Excluir Ficha Permanentemente", key=f"btn_exc_ficha_{ficha_id_ativo}"):
                    if confirmar_exclusao_ficha:
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM insumos_ficha WHERE ficha_id = ?", (ficha_id_ativo,))
                        cursor.execute("DELETE FROM insumos_nao_alimenticios_ficha WHERE ficha_id = ?", (ficha_id_ativo,))
                        cursor.execute("DELETE FROM fichas_tecnicas WHERE id = ?", (ficha_id_ativo,))
                        conn.commit()
                        conn.close()
                        st.success("🗑️ Ficha técnica excluída com sucesso!")
                        st.rerun()
                    else:
                        st.error("Marque a caixa de confirmação para prosseguir.")

            st.markdown("---")
            st.markdown("### 🥩 Insumos Alimentícios")
            
            with st.form(f"form_add_insumo_{ficha_id_ativo}"):
                st.markdown("**Adicionar Novo Insumo Alimentício**")
                c1, c2, c3, c4, c5 = st.columns(5)
                codigo_ins = c1.text_input("Código", value="", key=f"cod_ali_{ficha_id_ativo}")
                produto_ins = c2.text_input("Produto / Insumo", value="", key=f"prod_ali_{ficha_id_ativo}")
                qtd_bruta_ins = c3.number_input("Qtd Bruta", min_value=0.0, value=1.0, step=0.1, format="%.3f", key=f"qtd_ali_{ficha_id_ativo}")
                unidade_ins = c4.selectbox("Unidade", ["KG", "UN", "L", "G"], key=f"un_ali_{ficha_id_ativo}")
                preco_bruto_ins = c5.number_input("Preço Bruto (R$)", min_value=0.0, value=10.0, step=0.1, format="%.2f", key=f"pc_ali_{ficha_id_ativo}")
                
                btn_add_ins = st.form_submit_button("➕ Adicionar Insumo Alimentício")
                if btn_add_ins:
                    if not produto_ins.strip():
                        st.error("Informe o nome do produto/insumo!")
                    else:
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO insumos_ficha (ficha_id, codigo, produto_insumo, qtd_bruta, unidade, preco_bruto, rendimento)
                            VALUES (?, ?, ?, ?, ?, ?, 1.0)
                        """, (ficha_id_ativo, codigo_ins.strip().upper(), produto_ins.strip().upper(), qtd_bruta_ins, unidade_ins, preco_bruto_ins))
                        conn.commit()
                        conn.close()
                        st.success("Insumo alimentício adicionado com sucesso!")
                        st.rerun()

            if df_insumos.empty:
                st.info("Nenhum insumo alimentício cadastrado nesta ficha ainda.")
            else:
                st.markdown("#### 📋 Tabela de Insumos Alimentícios Cadastrados")
                
                df_insumos_view = df_insumos[['id', 'codigo', 'produto_insumo', 'qtd_bruta', 'unidade', 'preco_bruto']].copy()
                df_insumos_view.columns = ['ID', 'Código', 'Insumo', 'Qtd Bruta', 'Unidade', 'Preço Bruto (R$)']
                st.dataframe(
                    df_insumos_view.style.format({
                        'Qtd Bruta': '{:.3f}',
                        'Preço Bruto (R$)': 'R$ {:.2f}'
                    }),
                    use_container_width=True,
                    key="tabela_insumos_alimenticios"
                )

                st.markdown("#### ✏️ Alterar ou Excluir Insumos Alimentícios por Seleção")
                opcoes_insumos = {f"ID: {r['id']} - {r['produto_insumo']} ({r['qtd_bruta']} {r['unidade']})": r['id'] for _, r in df_insumos.iterrows()}
                sel_ins_gerenciar = st.selectbox("Selecione o Insumo Alimentício para Editar/Excluir", list(opcoes_insumos.keys()), key="sel_gerenciar_ins_ali")
                id_ins_gerenciar = opcoes_insumos[sel_ins_gerenciar]
                
                row_ins_sel = df_insumos[df_insumos['id'] == id_ins_gerenciar].iloc[0]
                
                with st.form(f"form_alt_ins_tabela_{id_ins_gerenciar}"):
                    ac1, ac2, ac3, ac4, ac5 = st.columns(5)
                    alt_cod = ac1.text_input("Código", value=str(row_ins_sel['codigo']) if row_ins_sel['codigo'] else "", key=f"tab_alt_cod_{id_ins_gerenciar}")
                    alt_prod = ac2.text_input("Produto", value=str(row_ins_sel['produto_insumo']), key=f"tab_alt_prod_{id_ins_gerenciar}")
                    alt_qtd = ac3.number_input("Qtd Bruta", min_value=0.0, value=float(row_ins_sel['qtd_bruta']), step=0.1, format="%.3f", key=f"tab_alt_qtd_{id_ins_gerenciar}")
                    
                    unidades_disponiveis = ["KG", "UN", "L", "G"]
                    un_atual = str(row_ins_sel['unidade']).upper()
                    idx_un = unidades_disponiveis.index(un_atual) if un_atual in unidades_disponiveis else 0
                    alt_un = ac4.selectbox("Unidade", unidades_disponiveis, index=idx_un, key=f"tab_alt_un_{id_ins_gerenciar}")
                    
                    alt_preco = ac5.number_input("Preço Bruto", min_value=0.0, value=float(row_ins_sel['preco_bruto']), step=0.1, format="%.2f", key=f"tab_alt_pc_{id_ins_gerenciar}")
                    
                    btn_salvar_alt = st.form_submit_button("💾 Salvar Alterações do Insumo")
                    
                    if btn_salvar_alt:
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE insumos_ficha 
                            SET codigo = ?, produto_insumo = ?, qtd_bruta = ?, unidade = ?, preco_bruto = ?
                            WHERE id = ?
                        """, (alt_cod.strip().upper(), alt_prod.strip().upper(), alt_qtd, alt_un, alt_preco, id_ins_gerenciar))
                        conn.commit()
                        conn.close()
                        st.success("Insumo atualizado com sucesso!")
                        st.rerun()

                if st.button("🗑️ Excluir Insumo Alimentício Selecionado", key=f"del_ins_tab_{id_ins_gerenciar}"):
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM insumos_ficha WHERE id = ?", (id_ins_gerenciar,))
                    conn.commit()
                    conn.close()
                    st.success("Insumo excluído com sucesso!")
                    st.rerun()

            st.markdown("---")
            st.markdown("### 📦 Insumos Não Alimentícios (Embalagens, Gás, etc.)")
            
            with st.form(f"form_add_nao_ali_{ficha_id_ativo}"):
                st.markdown("**Adicionar Novo Insumo Não Alimentício**")
                nc1, nc2, nc3, nc4, nc5 = st.columns(5)
                n_codigo_ins = nc1.text_input("Código", value="", key=f"cod_nao_{ficha_id_ativo}")
                n_produto_ins = nc2.text_input("Produto / Insumo", value="", key=f"prod_nao_{ficha_id_ativo}")
                n_qtd_bruta_ins = nc3.number_input("Qtd Bruta", min_value=0.0, value=1.0, step=0.1, format="%.3f", key=f"qtd_nao_{ficha_id_ativo}")
                n_unidade_ins = nc4.selectbox("Unidade", ["UNID", "UN", "KG", "L", "PCT"], key=f"un_nao_{ficha_id_ativo}")
                n_preco_bruto_ins = nc5.number_input("Preço Bruto (R$)", min_value=0.0, value=50.0, step=1.0, format="%.2f", key=f"pc_nao_{ficha_id_ativo}")
                
                btn_add_nao = st.form_submit_button("➕ Adicionar Insumo Não Alimentício")
                if btn_add_nao:
                    if not n_produto_ins.strip():
                        st.error("Informe o nome do produto/insumo não alimentício!")
                    else:
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO insumos_nao_alimenticios_ficha (ficha_id, codigo, produto_insumo, qtd_bruta, unidade, preco_bruto, rendimento)
                            VALUES (?, ?, ?, ?, ?, ?, 1.0)
                        """, (ficha_id_ativo, n_codigo_ins.strip().upper(), n_produto_ins.strip().upper(), n_qtd_bruta_ins, n_unidade_ins, n_preco_bruto_ins))
                        conn.commit()
                        conn.close()
                        st.success("Insumo não alimentício adicionado com sucesso!")
                        st.rerun()

            if df_nao_ali.empty:
                st.info("Nenhum insumo não alimentício cadastrado nesta ficha ainda.")
            else:
                st.markdown("#### 📋 Tabela de Insumos Não Alimentícios Cadastrados")
                
                df_nao_view = df_nao_ali[['id', 'codigo', 'produto_insumo', 'qtd_bruta', 'unidade', 'preco_bruto']].copy()
                df_nao_view.columns = ['ID', 'Código', 'Insumo', 'Qtd Bruta', 'Unidade', 'Preço Bruto (R$)']
                st.dataframe(
                    df_nao_view.style.format({
                        'Qtd Bruta': '{:.3f}',
                        'Preço Bruto (R$)': 'R$ {:.2f}'
                    }),
                    use_container_width=True,
                    key="tabela_insumos_nao_alimenticios"
                )

                st.markdown("#### ✏️ Alterar ou Excluir Insumos Não Alimentícios por Seleção")
                opcoes_nao = {f"ID: {r['id']} - {r['produto_insumo']} ({r['qtd_bruta']} {r['unidade']})": r['id'] for _, r in df_nao_ali.iterrows()}
                sel_nao_gerenciar = st.selectbox("Selecione o Insumo Não Alimentício para Editar/Excluir", list(opcoes_nao.keys()), key="sel_gerenciar_ins_nao")
                id_nao_gerenciar = opcoes_nao[sel_nao_gerenciar]
                
                row_nao_sel = df_nao_ali[df_nao_ali['id'] == id_nao_gerenciar].iloc[0]
                
                with st.form(f"form_alt_nao_tabela_{id_nao_gerenciar}"):
                    nac1, nac2, nac3, nac4, nac5 = st.columns(5)
                    alt_n_cod = nac1.text_input("Código", value=str(row_nao_sel['codigo']) if row_nao_sel['codigo'] else "", key=f"tab_alt_n_cod_{id_nao_gerenciar}")
                    alt_n_prod = nac2.text_input("Produto", value=str(row_nao_sel['produto_insumo']), key=f"tab_alt_n_prod_{id_nao_gerenciar}")
                    alt_n_qtd = nac3.number_input("Qtd Bruta", min_value=0.0, value=float(row_nao_sel['qtd_bruta']), step=0.1, format="%.3f", key=f"tab_alt_n_qtd_{id_nao_gerenciar}")
                    
                    un_nao_disponiveis = ["UNID", "UN", "KG", "L", "PCT"]
                    un_n_atual = str(row_nao_sel['unidade']).upper()
                    idx_un_n = un_nao_disponiveis.index(un_n_atual) if un_n_atual in un_nao_disponiveis else 0
                    alt_n_un = nac4.selectbox("Unidade", un_nao_disponiveis, index=idx_un_n, key=f"tab_alt_n_un_{id_nao_gerenciar}")
                    
                    alt_n_preco = nac5.number_input("Preço Bruto", min_value=0.0, value=float(row_nao_sel['preco_bruto']), step=1.0, format="%.2f", key=f"tab_alt_n_pc_{id_nao_gerenciar}")
                    
                    btn_salvar_alt_n = st.form_submit_button("💾 Salvar Alterações (Não Alimentício)")
                    
                    if btn_salvar_alt_n:
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE insumos_nao_alimenticios_ficha 
                            SET codigo = ?, produto_insumo = ?, qtd_bruta = ?, unidade = ?, preco_bruto = ?
                            WHERE id = ?
                        """, (alt_n_cod.strip().upper(), alt_n_prod.strip().upper(), alt_n_qtd, alt_n_un, alt_n_preco, id_nao_gerenciar))
                        conn.commit()
                        conn.close()
                        st.success("Insumo não alimentício atualizado com sucesso!")
                        st.rerun()

                if st.button("🗑️ Excluir Insumo Não Alimentício Selecionado", key=f"del_nao_tab_{id_nao_gerenciar}"):
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM insumos_nao_alimenticios_ficha WHERE id = ?", (id_nao_gerenciar,))
                    conn.commit()
                    conn.close()
                    st.success("Insumo excluído com sucesso!")
                    st.rerun()

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
            perda_pct REAL DEFAULT 0.0,
            data_criacao TEXT,
            FOREIGN KEY(empresa_id) REFERENCES empresas(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS insumos_ficha (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ficha_id INTEGER,
            codigo TEXT,
            produto_insumo TEXT NOT NULL,
            qtd_bruta REAL DEFAULT 0.0,
            unidade TEXT,
            preco_bruto REAL DEFAULT 0.0,
            rendimento REAL DEFAULT 1.0,
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
            rendimento REAL DEFAULT 1.0,
            FOREIGN KEY(ficha_id) REFERENCES fichas_tecnicas(id) ON DELETE CASCADE
        )
    """)
    
    novas_colunas = [
        ("p_cartao", "REAL DEFAULT 0.0"),
        ("p_impostos", "REAL DEFAULT 0.0"),
        ("p_embalagens", "REAL DEFAULT 0.0"),
        ("p_comissao", "REAL DEFAULT 0.0")
    ]
    for col_nome, col_def in novas_colunas:
        try:
            cursor.execute(f"ALTER TABLE acoes ADD COLUMN {col_nome} {col_def}")
        except sqlite3.OperationalError:
            pass

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
            ("VACA CASADA", "COSTELA RIPA", None), ("VACA CASADA", "MATAMBRE", None),
            ("VACA CASADA", "MUSCULO TRASEIRO", None), ("VACA CASADA", "CARNE MOIDA", None),
            ("VACA CASADA", "CAPA DE FILE", None),
            ("QUARTO TRASEIRO", "PICANHA", None), ("QUARTO TRASEIRO", "ALCATRA", None), 
            ("QUARTO TRASEIRO", "MAMINHA", None), ("QUARTO TRASEIRO", "CONTRA FILE", None),
            ("QUARTO DIANTEIRO", "ACEM", None), ("QUARTO DIANTEIRO", "PEITO", None), 
            ("QUARTO DIANTEIRO", "PALETA", None),
            ("SUINO", "PERNIL", None), ("SUINO", "PALETA", None), ("SUINO", "LOMBO", None), ("SUINO", "COSTELINHA", None)
        ]
        cursor.executemany("INSERT OR IGNORE INTO cortes_padrao (tipo_desossa, nome_corte, empresa_id) VALUES (?, ?, ?)", cortes_iniciais)
        
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
    except Exception as e:
        st.sidebar.error("Erro ao gerar backup.")
        
    backup_upload = st.sidebar.file_uploader("📤 Restaurar Backup (.db)", type=["db"], key="file_uploader_backup")
    if backup_upload is not None:
        if st.sidebar.button("⚠️ Confirmar Restauração", key="btn_conf_restaurar"):
            try:
                with open("desossa_db.db", "wb") as f:
                    f.write(backup_upload.getbuffer())
                st.sidebar.success("🎉 Sistema restaurado! Recarregando...")
                st.rerun()
            except Exception as f_err:
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
        menu = st.sidebar.radio("Selecione a Tela:", ["Gerenciar Empresas", "Cadastrar Empresa", "Gerenciar Cadastro de Cortes", "Importar Cortes (CSV)", "Cálculo Financeiro", "Ficha Técnica"], key="menu_admin")
    else:
        st.sidebar.markdown("### 🥩 Menu de Operações")
        menu = st.sidebar.radio("Selecione a Tela:", ["Nova Desossa", "Histórico & Edição", "Gerenciar Cadastro de Cortes", "Cálculo Financeiro", "Ficha Técnica"], key="menu_operacional")

    exibir_cabecalho(nome_empresa_usuaria=st.session_state.empresa_nome)

    # =========================================================================
    # 6. TELAS EXCLUSIVAS DO ADMINISTRADOR
    # =========================================================================
    if st.session_state.e_admin and menu not in ["Gerenciar Cadastro de Cortes", "Cálculo Financeiro", "Ficha Técnica"]:
        
        if menu == "Importar Cortes (CSV)":
            st.header("📥 Importação Massiva de Cortes (CSV)")
            
            conn = get_connection()
            df_empresas_list = pd.read_sql_query("SELECT id, nome FROM empresas ORDER BY nome ASC", conn)
            conn.close()
            
            if df_empresas_list.empty:
                st.warning("⚠️ Cadastre primeiro uma empresa parceira no menu para poder importar cortes para ela.")
            else:
                emp_options = {row['nome']: row['id'] for _, row in df_empresas_list.iterrows()}
                emp_options["Cortes Globais (Sistema)"] = None
                
                selected_emp_name = st.selectbox("1. Selecione a Empresa de Destino", list(emp_options.keys()), key="sel_emp_csv")
                target_emp_id = emp_options[selected_emp_name]
                
                tipos_empresa_destino = get_tipos_desossa(target_emp_id if target_emp_id is not None else 0)
                
                if not tipos_empresa_destino:
                    st.warning("⚠️ Esta empresa não possui tipos de desossa cadastrados. Crie pelo menos um tipo antes de importar.")
                else:
                    selected_tipo_desossa = st.selectbox("2. Selecione o Tipo de Desossa", tipos_empresa_destino, key="sel_tipo_csv")
                    
                    st.markdown("### 📄 Instruções do arquivo CSV")
                    uploaded_csv = st.file_uploader("3. Selecione o arquivo CSV para Importar", type=["csv"], key=f"csv_uploader_{st.session_state.uploader_key}")
                    
                    if uploaded_csv is not None:
                        try:
                            df_imported = None
                            encodings_to_try = ["latin-1", "utf-8-sig", "utf-8", "cp1252"]
                            
                            for enc in encodings_to_try:
                                try:
                                    uploaded_csv.seek(0)
                                    df_imported = pd.read_csv(uploaded_csv, encoding=enc, sep=";")
                                    if len(df_imported.columns) == 1:
                                        uploaded_csv.seek(0)
                                        df_imported = pd.read_csv(uploaded_csv, encoding=enc)
                                    break
                                except Exception:
                                    continue
                            
                            if df_imported is None:
                                uploaded_csv.seek(0)
                                df_imported = pd.read_csv(uploaded_csv, encoding="latin-1")
                            
                            col_map_imp = {col: str(col).strip().lower().replace(" ", "_").replace("\ufeff", "") for col in df_imported.columns}
                            df_imported.rename(columns=col_map_imp, inplace=True)
                            
                            for c_var in ["nom_corte", "corte", "nome"]:
                                if c_var in df_imported.columns and "nome_corte" not in df_imported.columns:
                                    df_imported.rename(columns={c_var: "nome_corte"}, inplace=True)
                                    break

                            if "nome_corte" not in df_imported.columns:
                                st.error("❌ Erro: O arquivo CSV não possui a coluna 'nome_corte'.")
                            else:
                                df_imported['nome_corte'] = df_imported['nome_corte'].dropna().astype(str).str.strip().str.upper()
                                df_imported = df_imported[df_imported['nome_corte'] != ""]
                                st.dataframe(df_imported, key="df_preview_csv")
                                
                                if st.button("🚀 Confirmar e Importar para o Banco de Dados", key="btn_conf_import_csv"):
                                    conn = get_connection()
                                    cursor = conn.cursor()
                                    sucessos = 0
                                    duplicados = 0
                                    for _, row in df_imported.iterrows():
                                        corte_nome = row['nome_corte']
                                        try:
                                            cursor.execute("INSERT INTO cortes_padrao (tipo_desossa, nome_corte, empresa_id) VALUES (?, ?, ?)", (selected_tipo_desossa, corte_nome, target_emp_id))
                                            sucessos += 1
                                        except sqlite3.IntegrityError:
                                            duplicados += 1
                                    conn.commit()
                                    conn.close()
                                    st.success(f"🎉 Importação concluída! Adicionados: {sucessos} | Duplicados ignorados: {duplicados}")
                                    st.session_state.uploader_key += 1
                                    st.rerun()
                        except Exception as e_csv:
                            st.error(f"❌ Ocorreu um erro ao processar o arquivo: {e_csv}")
        
        elif menu == "Cadastrar Empresa":
            st.header("📝 Cadastrar Nova Empresa Parceira")
            with st.form("form_cadastro_admin"):
                novo_nome = st.text_input("Nome Comercial")
                novo_login = st.text_input("Nome de Usuário (Sem espaços)")
                nova_senha = st.text_input("Senha de Acesso", type="password")
                btn_salvar_cadastro = st.form_submit_button("💾 Salvar Novo Cadastro")
                
                if btn_salvar_cadastro:
                    if not novo_nome or not novo_login or not nova_senha:
                        st.error("Preencha todos os campos!")
                    else:
                        login_salvar = novo_login.strip().lower()
                        try:
                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute("INSERT INTO empresas (nome, login, senha, ativo) VALUES (?, ?, ?, 1)", (novo_nome, login_salvar, nova_senha))
                            conn.commit()
                            conn.close()
                            st.success(f"🎉 Empresa '{novo_nome}' cadastrada!")
                        except sqlite3.IntegrityError:
                            st.error("Este nome de usuário já existe.")
                            
        elif menu == "Gerenciar Empresas":
            st.header("🏢 Painel de Controle de Empresas")
            conn = get_connection()
            df_empresas = pd.read_sql_query("SELECT id, nome, login, senha, ativo FROM empresas ORDER BY nome ASC", conn)
            conn.close()
            
            if df_empresas.empty:
                st.warning("Não existem empresas parceiras cadastradas.")
            else:
                for index, row in df_empresas.iterrows():
                    emp_id = row['id']
                    emp_nome = row['nome']
                    emp_login = row['login']
                    emp_senha = row['senha']
                    emp_status = row['ativo']
                    
                    col_info_emp, col_status_badge, col_btn_action, col_btn_edit = st.columns([3, 1, 1, 1])
                    with col_info_emp:
                        st.markdown(f"**🏢 {emp_nome.upper()}** (Usuário: `{emp_login}`)")
                    with col_status_badge:
                        st.markdown("🟢 **ATIVO**" if emp_status == 1 else "🔴 **BLOQUEADO**")
                    
                    with col_btn_action:
                        if emp_status == 1:
                            if st.button("🚫 Bloquear", key=f"bloq_{emp_id}"):
                                conn = get_connection()
                                cursor = conn.cursor()
                                cursor.execute("UPDATE empresas SET ativo = 0 WHERE id = ?", (emp_id,))
                                conn.commit()
                                conn.close()
                                st.rerun()
                        else:
                            if st.button("✅ Ativar", key=f"ativ_{emp_id}"):
                                conn = get_connection()
                                cursor = conn.cursor()
                                cursor.execute("UPDATE empresas SET ativo = 1 WHERE id = ?", (emp_id,))
                                conn.commit()
                                conn.close()
                                st.rerun()
                                
                    with col_btn_edit:
                        expandir_edicao = st.checkbox("✏️ Editar", key=f"expand_edit_{emp_id}")

                    if expandir_edicao:
                        with st.form(key=f"form_edicao_emp_{emp_id}"):
                            edit_nome = st.text_input("Nome Comercial", value=emp_nome)
                            edit_login = st.text_input("Nome de Usuário", value=emp_login)
                            edit_senha = st.text_input("Senha de Acesso", value=emp_senha)
                            if st.form_submit_button("💾 Confirmar Alterações"):
                                try:
                                    conn = get_connection()
                                    cursor = conn.cursor()
                                    cursor.execute("UPDATE empresas SET nome=?, login=?, senha=? WHERE id=?", (edit_nome, edit_login.strip().lower(), edit_senha, emp_id))
                                    conn.commit()
                                    conn.close()
                                    st.success("Dados alterados!")
                                    st.rerun()
                                except sqlite3.IntegrityError:
                                    st.error("Usuário já existe.")
                    st.markdown("<hr style='margin: 4px 0; border-top: 1px dashed #e0e0e0;'>", unsafe_allow_html=True)

    # =========================================================================
    # 7. TELA GLOBAL: GERENCIAR CADASTRO DE CORTES
    # =========================================================================
    elif menu == "Gerenciar Cadastro de Cortes":
        st.header("🥩 Configurar e Gerenciar Tipos de Desossa e Cortes")
        emp_id_ativo = st.session_state.empresa_id
        
        st.markdown("### ⚙️ Cadastro de Tipos de Desossa")
        col_t1, col_t2 = st.columns(2)
        
        with col_t1:
            st.markdown("#### ➕ Inserir Novo Tipo")
            with st.form("form_add_tipo_desossa"):
                novo_tipo_des_input = st.text_input("Nome do Tipo de Desossa")
                if st.form_submit_button("💾 Salvar Tipo") and novo_tipo_des_input:
                    tipo_fmt = novo_tipo_des_input.strip().upper()
                    db_id_dono = None if st.session_state.e_admin else emp_id_ativo
                    try:
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO tipos_desossa (nome, empresa_id) VALUES (?, ?)", (tipo_fmt, db_id_dono))
                        conn.commit()
                        conn.close()
                        st.success(f"Tipo '{tipo_fmt}' inserido!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Este tipo de desossa já está cadastrado.")
                        
        with col_t2:
            st.markdown("#### ✏️ Alterar / 🗑️ Excluir Tipo")
            lista_tipos_gerenciáveis = get_tipos_desossa(emp_id_ativo)
            if lista_tipos_gerenciáveis:
                tipo_gerenciar_sel = st.selectbox("Selecione o Tipo", lista_tipos_gerenciáveis, key="tipo_ger_sel")
                col_btn_alt, col_btn_exc = st.columns(2)
                with col_btn_alt:
                    alterar_tipo_chk = st.checkbox("✏️ Alterar Nome", key="chk_alt_tipo")
                with col_btn_exc:
                    if st.button("🗑️ Excluir Tipo", key="btn_exc_tipo"):
                        conn = get_connection()
                        cursor = conn.cursor()
                        if st.session_state.e_admin:
                            cursor.execute("DELETE FROM tipos_desossa WHERE nome = ? AND empresa_id IS NULL", (tipo_gerenciar_sel,))
                            cursor.execute("DELETE FROM cortes_padrao WHERE tipo_desossa = ? AND empresa_id IS NULL", (tipo_gerenciar_sel,))
                        else:
                            cursor.execute("DELETE FROM tipos_desossa WHERE nome = ? AND empresa_id = ?", (tipo_gerenciar_sel, emp_id_ativo))
                            cursor.execute("DELETE FROM cortes_padrao WHERE tipo_desossa = ? AND empresa_id = ?", (tipo_gerenciar_sel, emp_id_ativo))
                        conn.commit()
                        conn.close()
                        st.rerun()
                        
                if alterar_tipo_chk:
                    with st.form("form_alterar_tipo_nome"):
                        novo_nome_tipo = st.text_input("Alterar Nome para:", value=tipo_gerenciar_sel)
                        if st.form_submit_button("Confirmar Alteração"):
                            if novo_nome_tipo:
                                novo_nome_fmt = novo_nome_tipo.strip().upper()
                                conn = get_connection()
                                cursor = conn.cursor()
                                if st.session_state.e_admin:
                                    cursor.execute("UPDATE tipos_desossa SET nome = ? WHERE nome = ? AND empresa_id IS NULL", (novo_nome_fmt, tipo_gerenciar_sel))
                                    cursor.execute("UPDATE cortes_padrao SET tipo_desossa = ? WHERE tipo_desossa = ? AND empresa_id IS NULL", (novo_nome_fmt, tipo_gerenciar_sel))
                                else:
                                    cursor.execute("UPDATE tipos_desossa SET nome = ? WHERE nome = ? AND empresa_id = ?", (novo_nome_fmt, tipo_gerenciar_sel, emp_id_ativo))
                                    cursor.execute("UPDATE cortes_padrao SET tipo_desossa = ? WHERE tipo_desossa = ? AND empresa_id = ?", (novo_nome_fmt, tipo_gerenciar_sel, emp_id_ativo))
                                conn.commit()
                                conn.close()
                                st.rerun()

        st.markdown("---")
        st.markdown("### 🥩 Cadastro e Edição de Cortes")
        tipos_disponiveis = get_tipos_desossa(emp_id_ativo)
        if tipos_disponiveis:
            tipo_sel = st.selectbox("Selecione o Tipo de Desossa", tipos_disponiveis, key="tipo_sel_cortes")
            dono_id = None if st.session_state.e_admin else emp_id_ativo
            
            st.markdown("#### ➕ Cadastrar Novo Corte")
            with st.form("cadastrar_corte_padrao_form"):
                novo_corte_nome = st.text_input("Nome do Corte")
                btn_cad_corte_p = st.form_submit_button("💾 Salvar Novo Corte")
                if btn_cad_corte_p and novo_corte_nome:
                    corte_nome_formatado = novo_corte_nome.strip().upper()
                    try:
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO cortes_padrao (tipo_desossa, nome_corte, empresa_id) VALUES (?, ?, ?)", (tipo_sel, corte_nome_formatado, dono_id))
                        conn.commit()
                        conn.close()
                        st.success(f"Corte '{corte_nome_formatado}' adicionado!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.warning("Este corte já existe.")
            
            st.markdown("---")
            st.subheader(f"📋 Cadastro de Cortes para {tipo_sel}")
            conn = get_connection()
            if st.session_state.e_admin:
                df_padroes = pd.read_sql_query(f"SELECT id, nome_corte FROM cortes_padrao WHERE tipo_desossa = '{tipo_sel}' AND empresa_id IS NULL ORDER BY nome_corte ASC", conn)
            else:
                df_padroes = pd.read_sql_query(f"SELECT id, nome_corte FROM cortes_padrao WHERE tipo_desossa = '{tipo_sel}' AND empresa_id = {emp_id_ativo} ORDER BY nome_corte ASC", conn)
            conn.close()
            
            if not df_padroes.empty:
                for idx_p, row_p in df_padroes.iterrows():
                    c_id = row_p['id']
                    c_nome = row_p['nome_corte']
                    col_txt_p, col_btn_edit_p, col_btn_del_p = st.columns([4, 1, 1])
                    with col_txt_p:
                        st.markdown(f"🔸 **{c_nome}**")
                    with col_btn_edit_p:
                        expandir_edit_corte = st.checkbox("✏️ Editar", key=f"exp_edit_corte_{c_id}")
                    with col_btn_del_p:
                        if st.button("🗑️ Excluir", key=f"del_p_corte_{c_id}"):
                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM cortes_padrao WHERE id = ?", (c_id,))
                            conn.commit()
                            conn.close()
                            st.rerun()
                            
                    if expandir_edit_corte:
                        with st.form(key=f"form_ed_corte_{c_id}"):
                            novo_nome_input = st.text_input("Atualizar Nome", value=c_nome)
                            if st.form_submit_button("Confirmar Alteração"):
                                if novo_nome_input:
                                    nome_ajustado = novo_nome_input.strip().upper()
                                    try:
                                        conn = get_connection()
                                        cursor = conn.cursor()
                                        cursor.execute("UPDATE cortes_padrao SET nome_corte = ? WHERE id = ?", (nome_ajustado, c_id))
                                        conn.commit()
                                        conn.close()
                                        st.rerun()
                                    except sqlite3.IntegrityError:
                                        st.error("Corte duplicado!")
                    st.markdown("<hr style='margin: 2px 0; border-top: 1px dotted #cbd5e1;'>", unsafe_allow_html=True)

    # =========================================================================
    # 8. MÓDULO DE CÁLCULO FINANCEIRO
    # =========================================================================
    elif menu == "Cálculo Financeiro":
        render_modulo_financeiro()

    # =========================================================================
    # 9. MÓDULO DE FICHA TÉCNICA E PRECIFICAÇÃO
    # =========================================================================
    elif menu == "Ficha Técnica":
        render_modulo_ficha_tecnica()

    # =========================================================================
    # 10. TELAS OPERACIONAIS DAS EMPRESAS PARCEIRAS
    # =========================================================================
    else:
        emp_id_ativo = st.session_state.empresa_id
        v_form = st.session_state.form_version
        
        if menu == "Nova Desossa":
            st.header("📋 Lançar Nova Ação de Desossa")
            tipos_empresa = get_tipos_desossa(emp_id_ativo)
            
            if not tipos_empresa:
                st.warning("Cadastre os seus 'Tipos de Desossa' no menu 'Gerenciar Cadastro de Cortes' primeiro.")
            else:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown("##### 📦 Parâmetros Gerais")
                    data_input = st.date_input("Data da Ação", datetime.date.today(), key=f"date_picker_{v_form}")
                    tipo_animal = st.selectbox("Tipo de Desossa", tipos_empresa, key=f"tipo_animal_select_{v_form}")
                    peso_bruto = st.number_input("Peso Bruto (KG)", min_value=0.0, step=0.001, format="%.3f", key=f"input_peso_bruto_{v_form}")
                    preco_animal_kg = st.number_input("Preço do Animal (R$/KG)", min_value=0.0, step=0.01, key=f"input_preco_animal_{v_form}")
                    
                with col2:
                    st.markdown("##### ⚖️ Rendimento e Perdas")
                    ossos_muxiba = st.number_input("Ossos / Muxiba (KG)", min_value=0.0, step=0.001, format="%.3f", key=f"input_ossos_{v_form}")
                    quebra_nao_identificada = st.number_input("Quebra Não Identificada (KG)", min_value=0.0, step=0.001, format="%.3f", key=f"input_quebra_{v_form}")
                    exsudato_escorrimento = st.number_input("Exsudato / Escorrimento (KG)", min_value=0.0, step=0.001, format="%.3f", key=f"input_exsudato_{v_form}")

                with col3:
                    st.markdown("##### 📊 Custos Variáveis (%)")
                    p_cartao = st.number_input("Taxas de Cartão (%)", min_value=0.0, max_value=100.0, step=0.01, key=f"input_p_cartao_{v_form}")
                    p_impostos = st.number_input("Impostos (%)", min_value=0.0, max_value=100.0, step=0.01, key=f"input_p_impostos_{v_form}")
                    p_embalagens = st.number_input("Embalagens (%)", min_value=0.0, max_value=100.0, step=0.01, key=f"input_p_embalagens_{v_form}")
                    p_comissao = st.number_input("Comissão (%)", min_value=0.0, max_value=100.0, step=0.01, key=f"input_p_comissao_{v_form}")

                st.markdown("---")
                st.subheader("🥩 Cortes do Lote (Digitação Manual ou Upload por Arquivo)")
                
                with st.expander("📥 Importar Cortes de Arquivo (CSV / CFC / Excel)", expanded=False):
                    st.info("O arquivo para lote deve conter as colunas: **nome_corte**, **qualidade**, **peso**, **preço_de_venda** (ou preco_venda).")
                    file_cortes = st.file_uploader("Selecione o arquivo de cortes (.csv, .cfc, .xlsx)", type=["csv", "cfc", "xlsx", "xls"], key=f"file_cortes_lote_{v_form}")
                    
                    if file_cortes is not None:
                        try:
                            file_name = file_cortes.name.lower()
                            if file_name.endswith('.xlsx') or file_name.endswith('.xls'):
                                df_uploaded_cortes = pd.read_excel(file_cortes)
                            else:
                                df_uploaded_cortes = None
                                for enc in ["latin-1", "utf-8-sig", "utf-8", "cp1252"]:
                                    try:
                                        file_cortes.seek(0)
                                        df_uploaded_cortes = pd.read_csv(file_cortes, encoding=enc, sep=";")
                                        if len(df_uploaded_cortes.columns) == 1:
                                            file_cortes.seek(0)
                                            df_uploaded_cortes = pd.read_csv(file_cortes, encoding=enc)
                                        break
                                    except Exception:
                                        continue
                                if df_uploaded_cortes is None:
                                    file_cortes.seek(0)
                                    df_uploaded_cortes = pd.read_csv(file_cortes, encoding="latin-1")
                            
                            col_map = {col: str(col).strip().lower().replace(" ", "_").replace("\ufeff", "") for col in df_uploaded_cortes.columns}
                            df_uploaded_cortes.rename(columns=col_map, inplace=True)
                            
                            if "nom_corte" in df_uploaded_cortes.columns and "nome_corte" not in df_uploaded_cortes.columns:
                                df_uploaded_cortes.rename(columns={"nom_corte": "nome_corte"}, inplace=True)
                            
                            preco_col = None
                            for p_c in ["preco_de_venda", "preço_de_venda", "preco_venda", "preço_venda"]:
                                if p_c in df_uploaded_cortes.columns:
                                    preco_col = p_c
                                    break
                            
                            if "nome_corte" in df_uploaded_cortes.columns and "qualidade" in df_uploaded_cortes.columns and "peso" in df_uploaded_cortes.columns and preco_col:
                                if st.button("🚀 Confirmar e Carregar Cortes para este Lote", key=f"btn_confirm_file_cortes_{v_form}"):
                                    qtd_adicionada = 0
                                    for _, r_corte in df_uploaded_cortes.iterrows():
                                        n_corte = str(r_corte["nome_corte"]).strip().upper()
                                        q_corte = str(r_corte["qualidade"]).strip().upper()
                                        
                                        peso_raw = str(r_corte["peso"]).replace(",", ".").strip()
                                        p_corte = float(peso_raw) if peso_raw != "" else 0.0
                                        
                                        preco_raw = str(r_corte[preco_col]).upper().replace("R$", "").replace(",", ".").strip()
                                        pv_corte = float(preco_raw) if preco_raw != "" else 0.0
                                        
                                        if n_corte != "" and p_corte > 0:
                                            st.session_state.cortes_temp.append({
                                                "nome_corte": n_corte,
                                                "qualidade": "OURO" if "OURO" in q_corte else "PRATA",
                                                "peso": p_corte,
                                                "preco_venda": pv_corte
                                            })
                                            qtd_adicionada += 1
                                    st.success(f"🎉 {qtd_adicionada} cortes importados com sucesso para a lista!")
                                    st.rerun()
                            else:
                                st.error("❌ O arquivo não possui as colunas obrigatórias: nome_corte, qualidade, peso, preço_de_venda.")
                        except Exception as e_file:
                            st.error(f"❌ Erro ao ler o arquivo de cortes: {e_file}")

                conn = get_connection()
                df_rec_cortes = pd.read_sql_query(f"SELECT nome_corte FROM cortes_padrao WHERE tipo_desossa = '{tipo_animal}' AND (empresa_id IS NULL OR empresa_id = {emp_id_ativo}) ORDER BY nome_corte ASC", conn)
                conn.close()
                
                lista_cortes_disponiveis = df_rec_cortes["nome_corte"].tolist() if not df_rec_cortes.empty else []
                
                with st.form(f"adicionar_corte_{v_form}"):
                    col_c1, col_c2, col_c3, col_c4 = st.columns(4)
                    if lista_cortes_disponiveis:
                        nome_corte = col_c1.selectbox("Corte Cadastrado", lista_cortes_disponiveis, key=f"sel_corte_cad_{v_form}")
                    else:
                        nome_corte = col_c1.text_input("Nome do Corte Manual", key=f"input_corte_nome_manual_{v_form}")
                        
                    qualidade = col_c2.selectbox("Qualidade", ["OURO", "PRATA"], key=f"sel_qual_corte_{v_form}")
                    peso_corte = col_c3.number_input("Peso do Corte (KG)", min_value=0.0, step=0.001, format="%.3f", key=f"input_corte_peso_{v_form}")
                    preco_venda = col_c4.number_input("Preço de Venda (R$/KG)", min_value=0.0, step=0.01, key=f"input_corte_preco_{v_form}")
                    
                    submitted = st.form_submit_button("➕ Adicionar Corte Manualmente")
                    if submitted and nome_corte != "":
                        name_fmt_c = nome_corte.upper()
                        st.session_state.cortes_temp.append({
                            "nome_corte": name_fmt_c,
                            "qualidade": qualidade,
                            "peso": peso_corte,
                            "preco_venda": preco_venda
                        })
                        st.success(f"Corte '{name_fmt_c}' adicionado!")
                        st.rerun()

                if st.session_state.cortes_temp:
                    st.markdown("##### 📋 Gerenciar Cortes do Lote Adicionados:")
                    for idx, c in enumerate(st.session_state.cortes_temp):
                        col_ver, col_btn = st.columns([5, 1])
                        col_ver.write(f"**{c['nome_corte']}** ({c['qualidade']}) - {c['peso']:.3f} KG - R$ {c['preco_venda']:.2f}/KG")
                        if col_btn.button("❌ Remover", key=f"rem_temp_{idx}_{v_form}"):
                            st.session_state.cortes_temp.pop(idx)
                            st.rerun()

                if st.button("💾 Salvar Ação no Banco de Dados", key=f"btn_salvar_db_{v_form}"):
                    if not st.session_state.cortes_temp:
                        st.error("Adicione pelo menos um corte antes de salvar!")
                    else:
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO acoes (empresa_id, data_acao, tipo_animal, peso_bruto, preco_animal_kg, ossos_muxiba, quebra_nao_identificada, exsudato_escorrimento, p_cartao, p_impostos, p_embalagens, p_comissao)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (emp_id_ativo, str(data_input), tipo_animal, peso_bruto, preco_animal_kg, ossos_muxiba, quebra_nao_identificada, exsudato_escorrimento, p_cartao, p_impostos, p_embalagens, p_comissao))
                        acao_id = cursor.lastrowid
                        
                        for c in st.session_state.cortes_temp:
                            cursor.execute("INSERT INTO cortes (acao_id, nome_corte, qualidade, peso, preco_venda) VALUES (?, ?, ?, ?, ?)", (acao_id, c["nome_corte"], c["qualidade"], c["peso"], c["preco_venda"]))
                        conn.commit()
                        conn.close()
                        st.success("🎉 Lote de Desossa salvo com sucesso!")
                        reset_form_states()
                        st.rerun()

        elif menu == "Histórico & Edição":
            st.header("📂 Histórico & Edição de Desossas")
            tipos_empresa = get_tipos_desossa(emp_id_ativo)
            
            st.markdown("#### 📅 Filtrar por Período de Date")
            col_f1, col_f2 = st.columns(2)
            
            hoje = datetime.date.today()
            inicio_mes_padrao = hoje.replace(day=1)
            
            data_inicio_filtro = col_f1.date_input("Data Inicial", inicio_mes_padrao, key="filtro_data_inicio")
            data_fim_filtro = col_f2.date_input("Data Final", hoje, key="filtro_data_fim")
            
            conn = get_connection()
            query_historico = """
                SELECT * FROM acoes 
                WHERE empresa_id = ? 
                  AND data_acao BETWEEN ? AND ? 
                ORDER BY data_acao DESC
            """
            df_acoes = pd.read_sql_query(query_historico, conn, params=(emp_id_ativo, str(data_inicio_filtro), str(data_fim_filtro)))
            conn.close()
            
            if df_acoes.empty:
                st.warning(f"Ainda não existem desossas cadastradas para a sua empresa entre {data_inicio_filtro.strftime('%d/%m/%Y')} e {data_fim_filtro.strftime('%d/%m/%Y')}.")
            else:
                opcoes_map = {}
                opcoes_lista = []
                for idx, row in df_acoes.iterrows():
                    data_original = datetime.datetime.strptime(row['data_acao'], "%Y-%m-%d").date()
                    data_br = data_original.strftime("%d/%m/%Y")
                    label = f"ID: {row['id']} - {data_br} | {row['tipo_animal']}"
                    opcoes_map[label] = row['id']
                    opcoes_lista.append(label)
                    
                if "lote_selecionado_id" not in st.session_state or st.session_state.lote_selecionado_id not in opcoes_map.values():
                    st.session_state.lote_selecionado_id = opcoes_map[opcoes_lista[0]]
                    
                label_inicial = [k for k, v in opcoes_map.items() if v == st.session_state.lote_selecionado_id]
                idx_default_sel = opcoes_lista.index(label_inicial[0]) if label_inicial else 0
                
                selecionado = st.selectbox("Selecione um lote para visualizar, editar ou exportar:", opcoes_lista, index=idx_default_sel, key="sel_lote_historico")
                id_selecionado = opcoes_map[selecionado]
                st.session_state.lote_selecionado_id = id_selecionado
                
                with st.expander("🗑️ EXCLUIR ESTA DESOSSA", expanded=False):
                    st.warning("⚠️ Atenção: A exclusão deste lote é irreversível e removerá todos os cortes associados.")
                    confirmar_exclusao = st.checkbox("Confirmar exclusão deste lote", key=f"chk_exc_lote_{id_selecionado}")
                    if st.button("🗑️ Excluir Lote Permanentemente", key=f"btn_exc_lote_{id_selecionado}"):
                        if confirmar_exclusao:
                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM cortes WHERE acao_id = ?", (id_selecionado,))
                            cursor.execute("DELETE FROM acoes WHERE id = ? AND empresa_id = ?", (id_selecionado, emp_id_ativo))
                            conn.commit()
                            conn.close()
                            st.success("🗑️ Lote de desossa excluído com sucesso!")
                            st.rerun()
                        else:
                            st.error("❌ Por favor, marque a caixa de confirmação para excluir o lote.")

                acao_row = df_acoes[df_acoes["id"] == id_selecionado].iloc[0]
                conn = get_connection()
                df_cortes = pd.read_sql_query(f"SELECT * FROM cortes WHERE acao_id = {id_selecionado}", conn)
                conn.close()
                
                tx_cartao = acao_row["p_cartao"] if "p_cartao" in acao_row and acao_row["p_cartao"] is not None else 0.0
                tx_impostos = acao_row["p_impostos"] if "p_impostos" in acao_row and acao_row["p_impostos"] is not None else 0.0
                tx_embalagens = acao_row["p_embalagens"] if "p_embalagens" in acao_row and acao_row["p_embalagens"] is not None else 0.0
                tx_comissao = acao_row["p_comissao"] if "p_comissao" in acao_row and acao_row["p_comissao"] is not None else 0.0

                with st.expander("📝 EDITAR DADOS GERAIS, RENDIMENTO E CUSTOS VARIÁVEIS"):
                    col_ed1, col_ed2, col_ed3 = st.columns(3)
                    with col_ed1:
                        st.markdown("**Dados Operacionais**")
                        ed_data = st.date_input("Editar Data", datetime.datetime.strptime(acao_row["data_acao"], "%Y-%m-%d").date(), key=f"ed_data_{id_selecionado}")
                        ed_tipo = st.selectbox("Editar Tipo", tipos_empresa, index=tipos_empresa.index(acao_row["tipo_animal"]) if acao_row["tipo_animal"] in tipos_empresa else 0, key=f"ed_tipo_{id_selecionado}")
                        ed_p_bruto = st.number_input("Editar Peso Bruto (KG)", value=float(acao_row["peso_bruto"]), step=0.001, format="%.3f", key=f"ed_pb_{id_selecionado}")
                        ed_preco_animal = st.number_input("Editar Preço (R$/KG)", value=float(acao_row["preco_animal_kg"]), step=0.01, key=f"ed_pa_{id_selecionado}")
                    with col_ed2:
                        st.markdown("**Pesos de Perdas**")
                        ed_ossos = st.number_input("Editar Ossos/Muxiba (KG)", value=float(acao_row["ossos_muxiba"]), step=0.001, format="%.3f", key=f"ed_oss_{id_selecionado}")
                        ed_quebra = st.number_input("Editar Quebra Não Identificada (KG)", value=float(acao_row["quebra_nao_identificada"]), step=0.001, format="%.3f", key=f"ed_q_{id_selecionado}")
                        ed_exsudato = st.number_input("Editar Exsudato/Escorrimento (KG)", value=float(acao_row["exsudato_escorrimento"]), step=0.001, format="%.3f", key=f"ed_exs_{id_selecionado}")
                    with col_ed3:
                        st.markdown("**Percentuais de Custos Variáveis**")
                        ed_p_cartao = st.number_input("Editar Taxa Cartão (%)", value=float(tx_cartao), step=0.01, key=f"ed_pc_{id_selecionado}")
                        ed_p_impostos = st.number_input("Editar Impostos (%)", value=float(tx_impostos), step=0.01, key=f"ed_pi_{id_selecionado}")
                        ed_p_embalagens = st.number_input("Editar Embalagens (%)", value=float(tx_embalagens), step=0.01, key=f"ed_pe_{id_selecionado}")
                        ed_p_comissao = st.number_input("Editar Comissão (%)", value=float(tx_comissao), step=0.01, key=f"ed_pcom_{id_selecionado}")
                        
                    if st.button("💾 CONFIRMAR ATUALIZAÇÃO DO LOTE", key=f"btn_conf_up_{id_selecionado}"):
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE acoes 
                            SET data_acao = ?, tipo_animal = ?, peso_bruto = ?, preco_animal_kg = ?, ossos_muxiba = ?, quebra_nao_identificada = ?, exsudato_escorrimento = ?,
                                p_cartao = ?, p_impostos = ?, p_embalagens = ?, p_comissao = ?
                            WHERE id = ? AND empresa_id = ?
                        """, (str(ed_data), ed_tipo, ed_p_bruto, ed_preco_animal, ed_ossos, ed_quebra, ed_exsudato, ed_p_cartao, ed_p_impostos, ed_p_embalagens, ed_p_comissao, id_selecionado, emp_id_ativo))
                        conn.commit()
                        conn.close()
                        st.success("✅ Lote atualizado com sucesso!")
                        st.rerun()

                with st.expander("🥩 GERENCIAR CORTES INDIVIDUALMENTE"):
                    for i, corte_row in df_cortes.iterrows():
                        st.markdown(f"##### Corte: **{corte_row['nome_corte']}**")
                        col_c1, col_c2, col_c3, col_btn_salvar, col_btn_excluir = st.columns([2, 2, 2, 1, 1])
                        c_qual = col_c1.selectbox("Qualidade", ["OURO", "PRATA"], index=["OURO", "PRATA"].index(corte_row["qualidade"]), key=f"c_qual_{corte_row['id']}")
                        c_peso = col_c2.number_input("Peso (KG)", value=float(corte_row["peso"]), step=0.001, format="%.3f", key=f"c_peso_{corte_row['id']}")
                        c_preco = col_c3.number_input("Preço (R$/KG)", value=float(corte_row["preco_venda"]), step=0.01, key=f"c_preco_{corte_row['id']}")
                        
                        if col_btn_salvar.button("💾 Salvar", key=f"save_c_{corte_row['id']}"):
                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute("UPDATE cortes SET qualidade = ?, peso = ?, preco_venda = ? WHERE id = ?", (c_qual, c_peso, c_preco, corte_row["id"]))
                            conn.commit()
                            conn.close()
                            st.success("Corte atualizado!")
                            st.rerun()
                            
                        if col_btn_excluir.button("🗑️ Excluir", key=f"del_c_{corte_row['id']}"):
                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM cortes WHERE id = ?", (corte_row["id"],))
                            conn.commit()
                            conn.close()
                            st.rerun()
                        st.markdown("---")

                p_bruto = acao_row["peso_bruto"]
                p_comp_kg = acao_row["preco_animal_kg"]
                valor_total_compra = p_bruto * p_comp_kg
                
                ossos_val = acao_row["ossos_muxiba"] if acao_row["ossos_muxiba"] else 0.0
                quebra_val = acao_row["quebra_nao_identificada"] if acao_row["quebra_nao_identificada"] else 0.0
                exsudato_val = acao_row["exsudato_escorrimento"] if acao_row["exsudato_escorrimento"] else 0.0
                
                peso_final = p_bruto - ossos_val - quebra_val - exsudato_val
                total_quebra = ossos_val + quebra_val + exsudato_val
                
                porc_ossos = (ossos_val / p_bruto * 100) if p_bruto > 0 else 0.0
                porc_quebra = (quebra_val / p_bruto * 100) if p_bruto > 0 else 0.0
                porc_exsudato = (exsudato_val / p_bruto * 100) if p_bruto > 0 else 0.0
                porc_final = (peso_final / p_bruto * 100) if p_bruto > 0 else 0.0
                porc_total_quebra = (total_quebra / p_bruto * 100) if p_bruto > 0 else 0.0

                st.subheader("📊 Apuração Geral do Lote")
                apuracao_data = {
                    "Apuração do Lote": ["PESO BRUTO/KG", "OSSOS/MUXIBA", "QUEBRA NÃO IDENTIF", "ESCORRIMENTO", "Peso Final", "TOTAL DE QUEBRA"],
                    "Peso (KG)": [f"{p_bruto:.3f}", f"{ossos_val:.3f}", f"{quebra_val:.3f}", f"{exsudato_val:.3f}", f"{peso_final:.3f}", f"{total_quebra:.3f}"],
                    "R$": [f"R$ {valor_total_compra:.2f}", "-", "-", "-", f"R$ {valor_total_compra:.2f}", "-"],
                    "Porcentagem": ["100,00%", f"{porc_ossos:.2f}%", f"{porc_quebra:.2f}%", f"{porc_exsudato:.2f}%", f"{porc_final:.2f}%", f"{porc_total_quebra:.2f}%"]
                }
                df_apuracao_tabela = pd.DataFrame(apuracao_data).set_index("Apuração do Lote")
                st.table(df_apuracao_tabela)

                total_vendas_ouro = sum(df_cortes[df_cortes["qualidade"] == "OURO"]["peso"] * df_cortes[df_cortes["qualidade"] == "OURO"]["preco_venda"])
                total_vendas_prata = sum(df_cortes[df_cortes["qualidade"] == "PRATA"]["peso"] * df_cortes[df_cortes["qualidade"] == "PRATA"]["preco_venda"])
                total_vendas_total = total_vendas_ouro + total_vendas_prata
                
                coeficiente = valor_total_compra / total_vendas_total if total_vendas_total > 0 else 0
                compra_ouro = total_vendas_ouro * coeficiente
                compra_prata = total_vendas_prata * coeficiente
                
                peso_desossado_ouro = sum(df_cortes[df_cortes["qualidade"] == "OURO"]["peso"])
                peso_desossado_prata = sum(df_cortes[df_cortes["qualidade"] == "PRATA"]["peso"])
                peso_desossado_total = peso_desossado_ouro + peso_desossado_prata
                
                custo_efetivo_total_ouro = 0
                custo_efetivo_total_prata = 0
                
                for idx_c, row_c in df_cortes.iterrows():
                    peso = row_c['peso']
                    p_venda = row_c['preco_venda']
                    p_custo_kg = p_venda * coeficiente
                    
                    v_cartao_kg = p_venda * (tx_cartao / 100)
                    v_impostos_kg = p_venda * (tx_impostos / 100)
                    v_embalagens_kg = p_venda * (tx_embalagens / 100)
                    v_comissao_kg = p_venda * (tx_comissao / 100)
                    
                    custo_efetivo_kg = p_custo_kg + v_cartao_kg + v_impostos_kg + v_embalagens_kg + v_comissao_kg
                    custo_efetivo_total = peso * custo_efetivo_kg
                    
                    if row_c['qualidade'] == "OURO":
                        custo_efetivo_total_ouro += custo_efetivo_total
                    else:
                        custo_efetivo_total_prata += custo_efetivo_total
                        
                custo_efetivo_total_geral = custo_efetivo_total_ouro + custo_efetivo_total_prata
                margem_r_ouro = total_vendas_ouro - custo_efetivo_total_ouro
                margem_r_prata = total_vendas_prata - custo_efetivo_total_prata
                margem_r_total = total_vendas_total - custo_efetivo_total_geral
                
                margem_p_ouro = (margem_r_ouro / total_vendas_ouro) if total_vendas_ouro > 0 else 0
                margem_p_prata = (margem_r_prata / total_vendas_prata) if total_vendas_prata > 0 else 0
                st_margem_p_total = (margem_r_total / total_vendas_total) if total_vendas_total > 0 else 0
                
                markup_ouro = (total_vendas_ouro / custo_efetivo_total_ouro) - 1 if custo_efetivo_total_ouro > 0 else 0
                markup_prata = (total_vendas_prata / custo_efetivo_total_prata) - 1 if custo_efetivo_total_prata > 0 else 0
                markup_total = (total_vendas_total / custo_efetivo_total_geral) - 1 if custo_efetivo_total_geral > 0 else 0
                
                p_medio_compra_ouro = compra_ouro / peso_desossado_ouro if peso_desossado_ouro > 0 else 0
                p_medio_compra_prata = compra_prata / peso_desossado_prata if peso_desossado_prata > 0 else 0
                p_medio_compra_total = valor_total_compra / peso_desossado_total if peso_desossado_total > 0 else 0
                
                p_medio_compra_com_ouro = custo_efetivo_total_ouro / peso_desossado_ouro if peso_desossado_ouro > 0 else 0
                p_medio_compra_com_prata = custo_efetivo_total_prata / peso_desossado_prata if peso_desossado_prata > 0 else 0
                p_medio_compra_com_total = custo_efetivo_total_geral / peso_desossado_total if peso_desossado_total > 0 else 0
                
                p_medio_venda_ouro = total_vendas_ouro / peso_desossado_ouro if peso_desossado_ouro > 0 else 0
                p_medio_venda_prata = total_vendas_prata / peso_desossado_prata if peso_desossado_prata > 0 else 0
                p_medio_venda_total = total_vendas_total / peso_desossado_total if peso_desossado_total > 0 else 0
                
                st.markdown(
                    f"""
                    <div style="background-color: #1E3A8A; padding: 12px; border-radius: 6px; margin-top: 20px; margin-bottom: 10px; color: #FFFFFF; font-weight: bold;">
                        <strong>🟩 Quadro de Indicadores (Taxas Aplicadas: Cartão {tx_cartao}% | Impostos {tx_impostos}% | Embalagens {tx_embalagens}% | Comissão {tx_comissao}%)</strong>
                    </div>
                    """, unsafe_allow_html=True
                )
                
                indicadores_data = {
                    "INDICADORES": [
                        "PREÇO TOTAL/Compra Sem Custos Variáveis", "PREÇO TOTAL/Venda", "Peso Desossado", 
                        "COEFICIENTE", "Custo Efetivo Total", "Margem de Contribuição R$", 
                        "Margem de Contribuição %", "Markup", "Preço médio de Compra/KG SEM-Custo Variável",
                        "Preço médio de Compra/KG COM-Custo Variável", "Preço médio de Venda/KG"
                    ],
                    "OURO": [
                        f"R$ {compra_ouro:.2f}", f"R$ {total_vendas_ouro:.2f}", f"{peso_desossado_ouro:.3f}",
                        f"{coeficiente:.6f}", f"R$ {custo_efetivo_total_ouro:.2f}", f"R$ {margem_r_ouro:.2f}",
                        f"{margem_p_ouro*100:.2f}%", f"{markup_ouro*100:.2f}%", f"R$ {p_medio_compra_ouro:.2f}",
                        f"R$ {p_medio_compra_com_ouro:.2f}", f"R$ {p_medio_venda_ouro:.2f}"
                    ],
                    "PRATA": [
                        f"R$ {compra_prata:.2f}", f"R$ {total_vendas_prata:.2f}", f"{peso_desossado_prata:.3f}",
                        f"{coeficiente:.6f}", f"R$ {custo_efetivo_total_prata:.2f}", f"R$ {margem_r_prata:.2f}",
                        f"{margem_p_prata*100:.2f}%", f"{markup_prata*100:.2f}%", f"R$ {p_medio_compra_prata:.2f}",
                        f"R$ {p_medio_compra_com_prata:.2f}", f"R$ {p_medio_venda_prata:.2f}"
                    ],
                    "Total": [
                        f"R$ {valor_total_compra:.2f}", f"R$ {total_vendas_total:.2f}", f"{peso_desossado_total:.3f}",
                        f"{coeficiente:.6f}", f"R$ {custo_efetivo_total_geral:.2f}", f"R$ {margem_r_total:.2f}",
                        f"{st_margem_p_total*100:.2f}%", f"{markup_total*100:.2f}%", f"R$ {p_medio_compra_total:.2f}",
                        f"R$ {p_medio_compra_com_total:.2f}", f"R$ {p_medio_venda_total:.2f}"
                    ]
                }
                df_indicadores_tabela = pd.DataFrame(indicadores_data).set_index("INDICADORES")
                st.table(df_indicadores_tabela)
                
                st.markdown(
                    """
                    <div style="background-color: #334155; padding: 10px; border-radius: 6px; margin-top: 20px; margin-bottom: 10px; color: #FFFFFF; font-weight: bold;">
                        <strong>🟨 Detalhes de Rendimento, Margens e Custos Variáveis por Linha (Fiel ao Modelo Excel)</strong>
                    </div>
                    """, unsafe_allow_html=True
                )
                
                linhas_detalhes = []
                for idx_l, row_l in df_cortes.iterrows():
                    peso = row_l["peso"]
                    p_venda = row_l["preco_venda"]
                    p_custo_kg = p_venda * coeficiente
                    preco_custo_total_linha = peso * p_custo_kg
                    fat_linha = peso * p_venda
                    lucro_bruto = fat_linha - preco_custo_total_linha
                    pct_cortes = peso / peso_final if peso_final > 0 else 0.0
                    
                    v_cartao = p_venda * (tx_cartao / 100)
                    v_impostos = p_venda * (tx_impostos / 100)
                    v_embalagem = p_venda * (tx_embalagens / 100)
                    v_comissao = p_venda * (tx_comissao / 100)
                    
                    custo_efetivo_kg = p_custo_kg + v_cartao + v_impostos + v_embalagem + v_comissao
                    custo_efetivo_total = peso * custo_efetivo_kg
                    
                    linhas_detalhes.append({
                        "Corte/Código": row_l["nome_corte"],
                        "Qualidade": row_l["qualidade"],
                        "Peso /KG": peso,
                        "PREÇO CUSTO/KG": p_custo_kg,
                        "PREÇO/CUSTO": preco_custo_total_linha,
                        "PREÇO VENDA/KG": p_venda,
                        "VALOR TOTAL DE VENDAS": fat_linha,
                        "LUCRO BRUTO": lucro_bruto,
                        "PERCENTUAL/CORTES": pct_cortes,
                        "TAXAS DE CARTÃO": v_cartao,
                        "IMPOSTOS": v_impostos,
                        "EMBALAGENS": v_embalagem,
                        "COMISSÃO": v_comissao,
                        "CUSTO EFETIVO/KG": custo_efetivo_kg,
                        "CUSTO EFETIVO TOTAL": custo_efetivo_total
                    })
                    
                df_final = pd.DataFrame(linhas_detalhes)
                
                total_peso = df_final["Peso /KG"].sum()
                total_preco_custo = df_final["PREÇO/CUSTO"].sum()
                total_faturamento = df_final["VALOR TOTAL DE VENDAS"].sum()
                total_lucro_bruto = df_final["LUCRO BRUTO"].sum()
                total_pct_cortes = df_final["PERCENTUAL/CORTES"].sum()
                total_custo_efetivo_total = df_final["CUSTO EFETIVO TOTAL"].sum()
                
                linha_total = pd.DataFrame([{
                    "Corte/Código": "TOTAL SOMA",
                    "Qualidade": "",
                    "Peso /KG": total_peso,
                    "PREÇO CUSTO/KG": None,
                    "PREÇO/CUSTO": total_preco_custo,
                    "PREÇO VENDA/KG": None,
                    "VALOR TOTAL DE VENDAS": total_faturamento,
                    "LUCRO BRUTO": total_lucro_bruto,
                    "PERCENTUAL/CORTES": total_pct_cortes,
                    "TAXAS DE CARTÃO": None,
                    "IMPOSTOS": None,
                    "EMBALAGENS": None,
                    "COMISSÃO": None,
                    "CUSTO EFETIVO/KG": None,
                    "CUSTO EFETIVO TOTAL": total_custo_efetivo_total
                }])
                
                df_com_total = pd.concat([df_final, linha_total], ignore_index=True)
                
                st.dataframe(
                    df_com_total.style.format({
                        "Peso /KG": "{:.3f}",
                        "PREÇO CUSTO/KG": lambda x: f"R$ {x:.2f}" if pd.notnull(x) else "-",
                        "PREÇO/CUSTO": lambda x: f"R$ {x:.2f}" if pd.notnull(x) else "-",
                        "PREÇO VENDA/KG": lambda x: f"R$ {x:.2f}" if pd.notnull(x) else "-",
                        "VALOR TOTAL DE VENDAS": "R$ {:.2f}",
                        "LUCRO BRUTO": "R$ {:.2f}",
                        "PERCENTUAL/CORTES": lambda x: f"{x*100:.2f}%" if pd.notnull(x) else "-",
                        "TAXAS DE CARTÃO": lambda x: f"R$ {x:.2f}" if pd.notnull(x) else "-",
                        "IMPOSTOS": lambda x: f"R$ {x:.2f}" if pd.notnull(x) else "-",
                        "EMBALAGENS": lambda x: f"R$ {x:.2f}" if pd.notnull(x) else "-",
                        "COMISSÃO": lambda x: f"R$ {x:.2f}" if pd.notnull(x) else "-",
                        "CUSTO EFETIVO/KG": lambda x: f"R$ {x:.2f}" if pd.notnull(x) else "-",
                        "CUSTO EFETIVO TOTAL": "R$ {:.2f}"
                    }),
                    key=f"df_detalhes_lote_{id_selecionado}"
                )

                st.markdown("---")
                st.markdown("### 📥 Exportar Relatório Completo do Lote em PDF")
                
                def gerar_pdf_lote_desossa():
                    pdf = FPDF(orientation='L', unit='mm', format='A4')
                    
                    def montar_cabecalho_desossa():
                        criar_cabecalho_pdf_padrao(pdf, f"Relatorio de Desossa - {acao_row['tipo_animal']} (ID: {id_selecionado})", st.session_state.empresa_nome)

                    pdf.add_page()
                    montar_cabecalho_desossa()

                    pdf.set_font("Arial", style="B", size=9)
                    pdf.cell(277, 5, f"Data da Acao: {acao_row['data_acao']} | Peso Bruto: {p_bruto:.3f} KG | Preço Animal: R$ {p_comp_kg:.2f}/KG", ln=1)
                    pdf.ln(3)

                    pdf.set_font("Arial", style="B", size=9)
                    pdf.set_fill_color(226, 232, 240)
                    pdf.cell(277, 6, "QUADRO DE APURACAO GERAL DO LOTE", ln=1, fill=True)
                    pdf.set_font("Arial", style="B", size=8)
                    pdf.cell(85, 5, "Apuração do Lote", border=1, align="C", fill=True)
                    pdf.cell(65, 5, "Peso (KG)", border=1, align="C", fill=True)
                    pdf.cell(65, 5, "R$", border=1, align="C", fill=True)
                    pdf.cell(62, 5, "Porcentagem", border=1, align="C", fill=True)
                    pdf.ln()

                    pdf.set_font("Arial", size=8)
                    for ap_idx, ap_row in df_apuracao_tabela.reset_index().iterrows():
                        pdf.cell(85, 5, str(ap_row["Apuração do Lote"]).encode("latin1", "replace").decode("latin1"), border=1)
                        pdf.cell(65, 5, str(ap_row["Peso (KG)"]), border=1, align="R")
                        pdf.cell(65, 5, str(ap_row["R$"]), border=1, align="R")
                        pdf.cell(62, 5, str(ap_row["Porcentagem"]), border=1, align="C")
                        pdf.ln()
                    pdf.ln(3)

                    if pdf.get_y() > 160:
                        pdf.add_page()
                        montar_cabecalho_desossa()

                    pdf.set_font("Arial", style="B", size=9)
                    pdf.set_fill_color(226, 232, 240)
                    pdf.cell(277, 6, f"QUADRO DE INDICADORES (Cartao {tx_cartao}% | Impostos {tx_impostos}% | Embalagens {tx_embalagens}% | Comissao {tx_comissao}%)", ln=1, fill=True)
                    pdf.set_font("Arial", style="B", size=8)
                    pdf.cell(107, 5, "Indicadores", border=1, align="C", fill=True)
                    pdf.cell(56, 5, "Ouro", border=1, align="C", fill=True)
                    pdf.cell(56, 5, "Prata", border=1, align="C", fill=True)
                    pdf.cell(58, 5, "Total", border=1, align="C", fill=True)
                    pdf.ln()

                    pdf.set_font("Arial", size=7.5)
                    for ind_idx, ind_row in df_indicadores_tabela.reset_index().iterrows():
                        pdf.cell(107, 5, str(ind_row["INDICADORES"])[:60].encode("latin1", "replace").decode("latin1"), border=1)
                        pdf.cell(56, 5, str(ind_row["OURO"]), border=1, align="R")
                        pdf.cell(56, 5, str(ind_row["PRATA"]), border=1, align="R")
                        pdf.cell(58, 5, str(ind_row["Total"]), border=1, align="R")
                        pdf.ln()
                    pdf.ln(3)

                    if pdf.get_y() > 150:
                        pdf.add_page()
                        montar_cabecalho_desossa()

                    pdf.set_font("Arial", style="B", size=9)
                    pdf.set_fill_color(226, 232, 240)
                    pdf.cell(277, 6, "DETALHAMENTO ANALITICO DE CORTES E CUSTOS", ln=1, fill=True)

                    pdf.set_fill_color(30, 58, 138)
                    pdf.set_text_color(255, 255, 255)
                    pdf.set_font("Arial", style="B", size=8)
                    
                    headers_d = ["Corte", "Qualid.", "Peso (KG)", "P.Custo/KG", "Total Custo", "P.Venda/KG", "Total Vendas", "Lucro Bruto", "Custo Efet. Total"]
                    widths_d = [45, 18, 25, 25, 30, 25, 33, 38, 38]
                    
                    for th, wh in zip(headers_d, widths_d):
                        pdf.cell(wh, 6, th.encode("latin1", "replace").decode("latin1"), border=1, align="C", fill=True)
                    pdf.ln()

                    pdf.set_font("Arial", size=7.5)
                    pdf.set_text_color(15, 23, 42)
                    for _, r_det in df_com_total.iterrows():
                        if pdf.get_y() > 185:
                            pdf.add_page()
                            montar_cabecalho_desossa()
                            pdf.set_font("Arial", style="B", size=8)
                            for th, wh in zip(headers_d, widths_d):
                                pdf.cell(wh, 6, th.encode("latin1", "replace").decode("latin1"), border=1, align="C", fill=True)
                            pdf.ln()
                            pdf.set_font("Arial", size=7.5)

                        pdf.cell(45, 5, str(r_det["Corte/Código"])[:25].encode("latin1", "replace").decode("latin1"), border=1, align="L")
                        pdf.cell(18, 5, str(r_det["Qualidade"]), border=1, align="C")
                        pdf.cell(25, 5, f"{r_det['Peso /KG']:.3f}" if pd.notnull(r_det['Peso /KG']) else "-", border=1, align="R")
                        pdf.cell(25, 5, f"R$ {r_det['PREÇO CUSTO/KG']:.2f}" if pd.notnull(r_det['PREÇO CUSTO/KG']) else "-", border=1, align="R")
                        pdf.cell(30, 5, f"R$ {r_det['PREÇO/CUSTO']:.2f}" if pd.notnull(r_det['PREÇO/CUSTO']) else "-", border=1, align="R")
                        pdf.cell(25, 5, f"R$ {r_det['PREÇO VENDA/KG']:.2f}" if pd.notnull(r_det['PREÇO VENDA/KG']) else "-", border=1, align="R")
                        pdf.cell(33, 5, f"R$ {r_det['VALOR TOTAL DE VENDAS']:.2f}" if pd.notnull(r_det['VALOR TOTAL DE VENDAS']) else "-", border=1, align="R")
                        pdf.cell(38, 5, f"R$ {r_det['LUCRO BRUTO']:.2f}" if pd.notnull(r_det['LUCRO BRUTO']) else "-", border=1, align="R")
                        pdf.cell(38, 5, f"R$ {r_det['CUSTO EFETIVO TOTAL']:.2f}" if pd.notnull(r_det['CUSTO EFETIVO TOTAL']) else "-", border=1, align="R")
                        pdf.ln()

                    return pdf.output(dest="S").encode("latin1")

                pdf_bytes_desossa = gerar_pdf_lote_desossa()
                st.download_button(
                    label="📄 Baixar Relatório Completo do Lote em PDF (.pdf)",
                    data=pdf_bytes_desossa,
                    file_name=f"relatorio_desossa_lote_{id_selecionado}_{datetime.date.today().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    key=f"btn_dl_pdf_desossa_{id_selecionado}"
                )