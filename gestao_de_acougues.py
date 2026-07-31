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
    
    /* CORREÇÃO DO FILE UPLOADER NA BARRA LATERAL */
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
# MÓDULO 1: GESTÃO DE DESOSSA
# =========================================================================
def render_modulo_desossa():
    st.header("🥩 Nova Desossa de Carcaça")
    emp_id_ativo = st.session_state.empresa_id
    tipos_desossa = get_tipos_desossa(emp_id_ativo)

    with st.form("form_nova_desossa"):
        col1, col2, col3 = st.columns(3)
        with col1:
            data_acao = st.date_input("Data da Desossa", datetime.date.today())
            tipo_animal = st.selectbox("Tipo de Carcaça", tipos_desossa)
        with col2:
            peso_bruto = st.number_input("Peso Bruto da Carcaça (KG)", min_value=0.1, value=250.0, step=0.5)
            preco_animal_kg = st.number_input("Preço de Aquisição por KG (R$)", min_value=0.01, value=18.50, step=0.10)
        with col3:
            ossos_muxiba = st.number_input("Ossos / Muxiba (KG)", min_value=0.0, value=35.0, step=0.5)
            exsudato = st.number_input("Exsudato / Quebra (KG)", min_value=0.0, value=5.0, step=0.5)

        st.markdown("---")
        st.subheader("Parâmetros de Custos Variáveis (%)")
        cp1, cp2, cp3, cp4 = st.columns(4)
        p_cartao = cp1.number_input("Taxa Cartão (%)", min_value=0.0, value=3.0, step=0.1)
        p_impostos = cp2.number_input("Impostos (%)", min_value=0.0, value=4.0, step=0.1)
        p_embalagens = cp3.number_input("Embalagens (%)", min_value=0.0, value=1.5, step=0.1)
        p_comissao = cp4.number_input("Comissão (%)", min_value=0.0, value=2.0, step=0.1)

        btn_salvar_desossa = st.form_submit_button("💾 Salvar Registro de Desossa")

        if btn_salvar_desossa:
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO acoes (empresa_id, data_acao, tipo_animal, peso_bruto, preco_animal_kg, ossos_muxiba, quebra_nao_identificada, exsudato_escorrimento, p_cartao, p_impostos, p_embalagens, p_comissao)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (emp_id_ativo, str(data_acao), tipo_animal, peso_bruto, preco_animal_kg, ossos_muxiba, 0.0, exsudato, p_cartao, p_impostos, p_embalagens, p_comissao))
                conn.commit()
                conn.close()
                st.success("🎉 Registro de desossa salvo com sucesso!")
            except Exception as e:
                st.error(f"Erro ao salvar desossa: {e}")

# =========================================================================
# MÓDULO 2: HISTÓRICO & EDIÇÃO DE DESOSSA (COM PDF COMPLETO)
# =========================================================================
def render_modulo_historico():
    st.header("📂 Histórico de Desossas & Relatórios Detalhados")
    emp_id_ativo = st.session_state.empresa_id
    
    conn = get_connection()
    df_acoes = pd.read_sql_query("SELECT * FROM acoes WHERE empresa_id = ? ORDER BY data_acao DESC", conn, params=(emp_id_ativo,))
    conn.close()

    if df_acoes.empty:
        st.warning("⚠️ Nenhuma desossa registrada no histórico.")
    else:
        opcoes_desossas = {f"ID: {r['id']} - {r['tipo_animal']} (Data: {r['data_acao']} | Peso: {r['peso_bruto']}kg)": r['id'] for _, r in df_acoes.iterrows()}
        selecao_lbl = st.selectbox("Selecione o Registro de Desossa", list(opcoes_desossas.keys()))
        acao_id_sel = opcoes_desossas[selecao_lbl]
        
        acao_row = df_acoes[df_acoes['id'] == acao_id_sel].iloc[0]
        
        conn = get_connection()
        df_cortes = pd.read_sql_query("SELECT * FROM cortes WHERE acao_id = ?", conn, params=(acao_id_sel,))
        conn.close()

        st.markdown(f"### Detalhes do Registro #{acao_id_sel} - {acao_row['tipo_animal']}")
        st.write(f"**Data:** {acao_row['data_acao']} | **Peso Bruto:** {acao_row['peso_bruto']} kg | **Custo Aquisição:** R$ {acao_row['preco_animal_kg']:.2f}/kg")
        
        if not df_cortes.empty:
            st.dataframe(df_cortes, use_container_width=True)
            custo_total_animal = acao_row['peso_bruto'] * acao_row['preco_animal_kg']
            faturamento_total = (df_cortes['peso'] * df_cortes['preco_venda']).sum()
            st.markdown(f"**Custo Total Carcaça:** R$ {custo_total_animal:,.2f} | **Faturamento Cortes:** R$ {faturamento_total:,.2f}")
        else:
            st.info("Nenhum corte cadastrado para este registro. Você pode adicioná-los abaixo.")

        with st.form(f"form_add_corte_{acao_id_sel}"):
            st.subheader("Adicionar Corte ao Registro")
            c1, c2, c3, c4 = st.columns(4)
            nome_c_novo = c1.text_input("Nome do Corte")
            qualidade_c = c2.selectbox("Qualidade", ["PRIME", "COMERCIAL", "INDUSTRIAL"])
            peso_c = c3.number_input("Peso (KG)", min_value=0.0, value=5.0, step=0.1)
            preco_c = c4.number_input("Preço Venda (R$/kg)", min_value=0.0, value=25.0, step=0.1)
            
            if st.form_submit_button("➕ Adicionar Corte") and nome_c_novo:
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO cortes (acao_id, nome_corte, qualidade, peso, preco_venda) VALUES (?, ?, ?, ?, ?)",
                                   (acao_id_sel, nome_c_novo.strip().upper(), qualidade_c, peso_c, preco_c))
                    conn.commit()
                    conn.close()
                    st.success("Corte adicionado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

        st.markdown("---")
        st.markdown("### 📄 Exportar Relatório de Desossa em PDF")
        def gerar_pdf_desossa():
            pdf = FPDF(orientation='L', unit='mm', format='A4')
            pdf.add_page()
            criar_cabecalho_pdf_padrao(pdf, f"Relatorio de Desossa - {acao_row['tipo_animal']}", st.session_state.get('empresa_nome', 'Empresa'))
            pdf.set_font("Arial", style="B", size=9)
            pdf.cell(277, 6, f"Data: {acao_row['data_acao']} | Peso Bruto: {acao_row['peso_bruto']} kg | Preco/kg: R$ {acao_row['preco_animal_kg']:.2f}", ln=1)
            pdf.cell(277, 6, f"Ossos/Muxiba: {acao_row['ossos_muxiba']} kg | Exsudato: {acao_row['exsudato_escorrimento']} kg", ln=1)
            pdf.ln(4)
            if not df_cortes.empty:
                pdf.set_fill_color(30, 58, 138)
                pdf.set_text_color(255, 255, 255)
                pdf.cell(80, 6, "Corte", 1, 0, "C", True)
                pdf.cell(50, 6, "Qualidade", 1, 0, "C", True)
                pdf.cell(50, 6, "Peso (KG)", 1, 0, "C", True)
                pdf.cell(50, 6, "Preco Venda (R$)", 1, 1, "C", True)
                pdf.set_text_color(15, 23, 42)
                pdf.set_font("Arial", size=8)
                for _, r in df_cortes.iterrows():
                    pdf.cell(80, 5, str(r['nome_corte']).encode('latin1', 'replace').decode('latin1'), 1)
                    pdf.cell(50, 5, str(r['qualidade']), 1, align="C")
                    pdf.cell(50, 5, f"{r['peso']:.2f}", 1, align="R")
                    pdf.cell(50, 5, f"R$ {r['preco_venda']:.2f}", 1, align="R")
                    pdf.ln()
            return pdf.output(dest="S").encode("latin1")

        pdf_bytes_desossa = gerar_pdf_desossa()
        st.download_button(
            label="📄 Baixar Relatório Completo de Desossa (.pdf)",
            data=pdf_bytes_desossa,
            file_name=f"relatorio_desossa_{acao_id_sel}.pdf",
            mime="application/pdf",
            key=f"dl_pdf_des_{acao_id_sel}"
        )

# =========================================================================
# MÓDULO 3: CÁLCULO FINANCEIRO (COM PDF COMPLETO)
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

    sistema_amortizacao = st.selectbox("Sistema de Amortização", ["Sistema Price (Prestações Fixas)", "Sistema SAC (Amortização Constante)"])
    tipo_calculo = st.selectbox("O que você deseja calcular?", ["Calcular Prestação / Primeira Parcela", "Calcular Capital / Valor Presente (PV)", "Calcular Taxa de Juros (i)", "Calcular Prazo da Operação (n)"])

    with st.form("form_calculo_financeiro_flexivel"):
        col1, col2, col3 = st.columns(3)
        with col1:
            valor_presente_input = st.number_input("Valor Presente / Capital (R$)", min_value=0.0, value=10000.0, step=100.0)
        with col2:
            taxa_informada = st.number_input("Taxa de Juros (%)", min_value=0.0, value=2.3, step=0.01, format="%.4f")
            periodo_taxa = st.selectbox("Unidade da Taxa", ["Dias", "Meses", "Anos"])
        with col3:
            prazo_informado = st.number_input("Prazo da Operação", min_value=1, value=12, step=1)
            periodo_prazo = st.selectbox("Unidade do Prazo", ["Dias", "Meses", "Anos"])

        prestacao_informada = st.number_input("Valor da Prestação / Parcela (R$)", min_value=0.0, value=950.0, step=10.0)
        btn_calcular = st.form_submit_button("🚀 Calcular e Gerar Tabela de Amortização")

    if btn_calcular:
        try:
            i_equivalente = taxa_informada / 100.0
            n_perodos = int(prazo_informado)
            
            if "Price" in sistema_amortizacao:
                prestacao = valor_presente_input * (i_equivalente * (1.0 + i_equivalente) ** n_perodos) / (((1.0 + i_equivalente) ** n_perodos) - 1.0) if i_equivalente > 0 else valor_presente_input / n_perodos
                tabela = []
                vp = valor_presente_input
                for t in range(0, n_perodos + 1):
                    if t == 0:
                        tabela.append({"t": 0, "VALOR PRESENTE": vp, "Amortização": 0.0, "Juros": 0.0, "Prestação": 0.0, "Taxa (%)": 0.0})
                    else:
                        j = vp * i_equivalente
                        a = prestacao - j
                        vp -= a
                        tabela.append({"t": t, "VALOR PRESENTE": max(0.0, vp), "Amortização": a, "Juros": j, "Prestação": prestacao, "Taxa (%)": i_equivalente * 100.0})
                df_fin = pd.DataFrame(tabela)
                nome_sistema = "Sistema Price"
            else:
                amort_c = valor_presente_input / n_perodos
                tabela = []
                vp = valor_presente_input
                for t in range(0, n_perodos + 1):
                    if t == 0:
                        tabela.append({"t": 0, "VALOR PRESENTE": vp, "Amortização": 0.0, "Juros": 0.0, "Prestação": 0.0, "Taxa (%)": 0.0})
                    else:
                        j = vp * i_equivalente
                        p = amort_c + j
                        vp -= amort_c
                        tabela.append({"t": t, "VALOR PRESENTE": max(0.0, vp), "Amortização": amort_c, "Juros": j, "Prestação": p, "Taxa (%)": i_equivalente * 100.0})
                df_fin = pd.DataFrame(tabela)
                nome_sistema = "Sistema SAC"

            st.session_state.df_fin = df_fin
            st.session_state.valor_presente = valor_presente_input
            st.session_state.n_perodos = n_perodos
            st.session_state.i_equivalente = i_equivalente
            st.session_state.nome_sistema = nome_sistema
        except Exception as e:
            st.error(f"Erro no cálculo: {e}")

    if st.session_state.df_fin is not None and not st.session_state.df_fin.empty:
        st.markdown(f"### 📋 Tabela de Amortização - {st.session_state.nome_sistema}")
        st.dataframe(st.session_state.df_fin, use_container_width=True)
        
        def gerar_pdf_fin():
            pdf = FPDF(orientation='L', unit='mm', format='A4')
            pdf.add_page()
            criar_cabecalho_pdf_padrao(pdf, st.session_state.nome_sistema, st.session_state.get('empresa_nome', 'Empresa'))
            pdf.set_font("Arial", size=8)
            for _, r in st.session_state.df_fin.iterrows():
                pdf.cell(30, 5, f"Periodo {int(r['t'])}", 1, 0, "C")
                pdf.cell(50, 5, f"VP: R$ {r['VALOR PRESENTE']:,.2f}", 1, 0, "R")
                pdf.cell(50, 5, f"Amort: R$ {r['Amortização']:,.2f}", 1, 0, "R")
                pdf.cell(50, 5, f"Juros: R$ {r['Juros']:,.2f}", 1, 0, "R")
                pdf.cell(50, 5, f"Prest: R$ {r['Prestação']:,.2f}", 1, 1, "R")
            return pdf.output(dest="S").encode("latin1")

        st.download_button("📄 Baixar Relatório Financeiro em PDF", data=gerar_pdf_fin(), file_name="relatorio_financeiro.pdf", mime="application/pdf")

# =========================================================================
# MÓDULO 4: FICHA TÉCNICA E PRECIFICAÇÃO (COM PDF COMPLETO)
# =========================================================================
def render_modulo_ficha_tecnica():
    st.markdown("""
        <div style="background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%); padding: 25px; border-radius: 12px; color: white; margin-bottom: 25px;">
            <h2 style="margin: 0; color: white !important;">📋 Módulo de Ficha Técnica & Precificação</h2>
            <p style="margin: 8px 0 0 0; font-size: 15px; opacity: 0.9;">Gerencie fichas técnicas de produtos, controle insumos em tabelas e apure custos e preços de venda.</p>
        </div>
    """, unsafe_allow_html=True)

    emp_id_ativo = st.session_state.empresa_id
    aba_ficha = st.selectbox("Selecione a Ação", ["Consultar / Editar Fichas Existentes", "Cadastrar Nova Ficha Técnica"])

    if aba_ficha == "Cadastrar Nova Ficha Técnica":
        st.markdown("### ➕ Criar Nova Ficha Técnica")
        with st.form("form_nova_ficha"):
            nome_produto = st.text_input("Nome do Produto / Prato")
            rend_kg = st.number_input("Rendimento Total (KG)", min_value=0.0, value=10.0, step=0.1)
            rend_assado = st.number_input("Rendimento Assada (KG)", min_value=0.0, value=8.5, step=0.1)
            peso_un = st.number_input("Peso da Unidade (KG)", min_value=0.0, value=0.1, step=0.01)
            unid_prod = st.number_input("Unidades Produzidas", min_value=0.0, value=85.0, step=1.0)
            
            if st.form_submit_button("💾 Salvar Ficha Técnica") and nome_produto:
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO fichas_tecnicas (empresa_id, produto, rendimento_kg, rendimento_assada_kg, peso_unidade_kg, unidades_produzidas, data_criacao)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (emp_id_ativo, nome_produto.strip().upper(), rend_kg, rend_assado, peso_un, unid_prod, str(datetime.date.today())))
                    conn.commit()
                    conn.close()
                    st.success("Ficha técnica cadastrada com sucesso!")
                except Exception as e:
                    st.error(f"Erro: {e}")
    else:
        conn = get_connection()
        df_fichas = pd.read_sql_query("SELECT * FROM fichas_tecnicas WHERE empresa_id = ? OR empresa_id IS NULL ORDER BY id DESC", conn, params=(emp_id_ativo,))
        conn.close()

        if df_fichas.empty:
            st.warning("Nenhuma ficha técnica encontrada.")
        else:
            opcoes = {f"{r['id']} - {r['produto']}": r['id'] for _, r in df_fichas.iterrows()}
            sel = st.selectbox("Selecione a Ficha", list(opcoes.keys()))
            fid = opcoes[sel]
            f_row = df_fichas[df_fichas['id'] == fid].iloc[0]

            conn = get_connection()
            df_ins = pd.read_sql_query("SELECT * FROM insumos_ficha WHERE ficha_id = ?", conn, params=(fid,))
            df_nao = pd.read_sql_query("SELECT * FROM insumos_nao_alimenticios_ficha WHERE ficha_id = ?", conn, params=(fid,))
            conn.close()

            st.markdown(f"### ✏️ Editando Ficha: `{f_row['produto']}`")
            
            c_tot = (df_ins['preco_bruto'] * df_ins['qtd_bruta']).sum() + (df_nao['preco_bruto'] * df_nao['qtd_bruta']).sum() if not df_ins.empty or not df_nao.empty else 0.0
            custo_kg_assada = c_tot / f_row['rendimento_assada_kg'] if f_row['rendimento_assada_kg'] > 0 else 0.0

            st.markdown(f"**Custo Total da Receita:** R$ {c_tot:,.2f} | **Custo por KG Assada:** R$ {custo_kg_assada:,.2f}")

            with st.form(f"add_ins_f_{fid}"):
                st.subheader("Adicionar Insumo Alimentício")
                ic1, ic2, ic3, ic4 = st.columns(4)
                nome_i = ic1.text_input("Insumo")
                qtd_i = ic2.number_input("Qtd Bruta", min_value=0.0, value=1.0)
                un_i = ic3.text_input("Unidade", value="KG")
                preco_i = ic4.number_input("Preço Bruto (R$)", min_value=0.0, value=10.0)
                if st.form_submit_button("➕ Adicionar Insumo") and nome_i:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO insumos_ficha (ficha_id, produto_insumo, qtd_bruta, unidade, preco_bruto) VALUES (?, ?, ?, ?, ?)",
                                   (fid, nome_i.upper(), qtd_i, un_i.upper(), preco_i))
                    conn.commit()
                    conn.close()
                    st.success("Insumo adicionado!")
                    st.rerun()

            st.markdown("---")
            def gerar_pdf_ficha():
                pdf = FPDF(orientation='P', unit='mm', format='A4')
                pdf.add_page()
                criar_cabecalho_pdf_padrao(pdf, f"Ficha Tecnica - {f_row['produto']}", st.session_state.get('empresa_nome', 'Empresa'))
                pdf.set_font("Arial", size=9)
                pdf.cell(190, 6, f"Produto: {f_row['produto']} | Rendimento Assada: {f_row['rendimento_assada_kg']} kg", ln=1)
                pdf.cell(190, 6, f"Custo Total: R$ {c_tot:,.2f} | Custo por KG Assada: R$ {custo_kg_assada:,.2f}", ln=1)
                if not df_ins.empty:
                    pdf.ln(2)
                    pdf.cell(190, 6, "Insumos Alimenticios:", ln=1)
                    for _, ri in df_ins.iterrows():
                        pdf.cell(190, 5, f"- {ri['produto_insumo']}: {ri['qtd_bruta']} {ri['unidade']} (R$ {ri['preco_bruto']:.2f})", ln=1)
                return pdf.output(dest="S").encode("latin1")

            st.download_button("📄 Baixar Relatório Completo da Ficha Técnica em PDF", data=gerar_pdf_ficha(), file_name=f"ficha_tecnica_{fid}.pdf", mime="application/pdf")

# =========================================================================
# MÓDULO 5: CAPITAL DE GIRO NCG (COM PDF COMPLETO)
# =========================================================================
def render_modulo_ncg():
    st.markdown("""
        <div style="background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%); padding: 25px; border-radius: 12px; color: white; margin-bottom: 25px;">
            <h2 style="margin: 0; color: white !important;">📈 Análise de Necessidade de Capital de Giro (NCG)</h2>
            <p style="margin: 8px 0 0 0; font-size: 15px; opacity: 0.9;">Calcule e armazene simulações de capital de giro e prazos operacionais.</p>
        </div>
    """, unsafe_allow_html=True)

    emp_id_ativo = st.session_state.empresa_id
    aba_ncg = st.selectbox("Ação NCG", ["Novo Cálculo / Simulação", "Consultar Histórico"])

    if aba_ncg == "Novo Cálculo / Simulação":
        with st.form("form_ncg"):
            nome_sim = st.text_input("Descrição da Simulação", value=f"Simulação NCG - {datetime.date.today().strftime('%d/%m/%Y')}")
            fat = st.number_input("Faturamento Mensal (R$)", min_value=0.0, value=150000.0)
            cmv = st.number_input("CMV Mensal (R$)", min_value=0.0, value=95000.0)
            pme = st.number_input("PME Atual (dias)", min_value=0.0, value=10.0)
            pmr = st.number_input("PMR Atual (dias)", min_value=0.0, value=5.0)
            pmp = st.number_input("PMP Atual (dias)", min_value=0.0, value=20.0)
            
            if st.form_submit_button("🚀 Calcular e Salvar NCG"):
                try:
                    cmv_d = cmv / 30.0
                    ncg_val = cmv_d * (pme + pmr - pmp)
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO historico_ncg (empresa_id, nome_simulacao, data_simulacao, fat_mensal, cmv_mensal, ncg_atual)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (emp_id_ativo, nome_sim, str(datetime.date.today()), fat, cmv, ncg_val))
                    conn.commit()
                    conn.close()
                    st.success(f"Simulação salva! NCG Calculado: R$ {ncg_val:,.2f}")
                except Exception as e:
                    st.error(f"Erro: {e}")
    else:
        conn = get_connection()
        df_h = pd.read_sql_query("SELECT * FROM historico_ncg WHERE empresa_id = ?", conn, params=(emp_id_ativo,))
        conn.close()
        if df_h.empty:
            st.warning("Nenhum histórico NCG encontrado.")
        else:
            st.dataframe(df_h, use_container_width=True)
            def gerar_pdf_ncg():
                pdf = FPDF(orientation='L', unit='mm', format='A4')
                pdf.add_page()
                criar_cabecalho_pdf_padrao(pdf, "Relatorio de Capital de Giro NCG", st.session_state.get('empresa_nome', 'Empresa'))
                pdf.set_font("Arial", size=8)
                for _, r in df_h.iterrows():
                    pdf.cell(277, 6, f"Simulacao: {r['nome_simulacao']} | Faturamento: R$ {r['fat_mensal']:,.2f} | NCG: R$ {r['ncg_atual']:,.2f}", 1, 1)
                return pdf.output(dest="S").encode("latin1")
            st.download_button("📄 Baixar Histórico Completo NCG em PDF", data=gerar_pdf_ncg(), file_name="relatorio_ncg.pdf", mime="application/pdf")

# =========================================================================
# CONTROLE DE SESSÃO E LOGIN
# =========================================================================
if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.empresa_id = None
    st.session_state.empresa_nome = ""
    st.session_state.e_admin = False

if not st.session_state.logado:
    st.title("🔒 Portal de Acesso - Gestão de Açougues")
    with st.form("form_login"):
        campo_login = st.text_input("Usuário / Login")
        campo_senha = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar no Sistema"):
            if campo_login.strip().lower() == "admin" and campo_senha == "renato123":
                st.session_state.logado = True
                st.session_state.empresa_id = 0
                st.session_state.empresa_nome = "Administrador Geral"
                st.session_state.e_admin = True
                st.rerun()
            else:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT id, nome, ativo FROM empresas WHERE LOWER(login) = ? AND senha = ?", (campo_login.strip().lower(), campo_senha))
                user = cursor.fetchone()
                conn.close()
                if user and user[2] == 1:
                    st.session_state.logado = True
                    st.session_state.empresa_id = user[0]
                    st.session_state.empresa_nome = user[1]
                    st.session_state.e_admin = False
                    st.rerun()
                else:
                    st.error("Credenciais inválidas ou usuário inativo.")
else:
    st.sidebar.markdown(f"**🏢 Empresa:** `{st.session_state.empresa_nome.upper()}`")
    if st.sidebar.button("🚪 Sair"):
        st.session_state.logado = False
        st.rerun()

    menu = st.sidebar.radio("Menu do Sistema", ["Nova Desossa", "Histórico & Edição", "Cálculo Financeiro", "Ficha Técnica", "Capital de Giro (NCG)"])

    if menu == "Nova Desossa":
        render_modulo_desossa()
    elif menu == "Histórico & Edição":
        render_modulo_historico()
    elif menu == "Cálculo Financeiro":
        render_modulo_financeiro()
    elif menu == "Ficha Técnica":
        render_modulo_ficha_tecnica()
    elif menu == "Capital de Giro (NCG)":
        render_modulo_ncg()