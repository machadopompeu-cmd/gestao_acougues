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
# MÓDULO DE FICHA TÉCNICA E PRECIFICAÇÃO (AJUSTADO CONFORME SOLICITADO)
# =========================================================================
def render_modulo_ficha_tecnica():
    st.markdown("""
        <div style="background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%); padding: 25px; border-radius: 12px; color: white; margin-bottom: 25px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
            <h2 style="margin: 0; color: white !important;">📋 Módulo de Ficha Técnica & Precificação</h2>
            <p style="margin: 8px 0 0 0; font-size: 15px; opacity: 0.9;">Gerencie fichas técnicas de produtos, controle insumos em tabelas e apure custos de produção e preços de venda em tempo real.</p>
        </div>
    """, unsafe_allow_html=True)

    emp_id_ativo = st.session_state.get('empresa_id', 1)
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
            
            col_sel_f, col_btn_fpdf = st.columns([3, 1])
            with col_sel_f:
                ficha_selecionada_label = st.selectbox("Selecione a Ficha Técnica", list(opcoes_fichas.keys()), key="sel_ficha_cadastrada")
            
            ficha_id_ativo = opcoes_fichas[ficha_selecionada_label]
            ficha_row = df_fichas[df_fichas['id'] == ficha_id_ativo].iloc[0]

            conn = get_connection()
            df_insumos = pd.read_sql_query("SELECT * FROM insumos_ficha WHERE ficha_id = ?", conn, params=(ficha_id_ativo,))
            df_nao_ali = pd.read_sql_query("SELECT * FROM insumos_nao_alimenticios_ficha WHERE ficha_id = ?", conn, params=(ficha_id_ativo,))
            conn.close()

            # Cálculos de custos independentes e consistentes
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
            
            unidades_prod_cadastrada = ficha_row['unidades_produzidas'] if 'unidades_produzidas' in ficha_row and ficha_row['unidades_produzidas'] > 0 else 1.0
            custo_unidade_produzida = custo_total / unidades_prod_cadastrada if unidades_prod_cadastrada > 0 else 0.0
            
            # Cálculo independente e rigoroso para Custo do Pacote: Custo da Unidade x Quantidade por Pacote
            qtd_pacote_atual = ficha_row['qtd_por_pacote'] if 'qtd_por_pacote' in ficha_row and ficha_row['qtd_por_pacote'] is not None else 1.0
            custo_pacote = custo_unidade_produzida * qtd_pacote_atual

            st.markdown("---")
            st.markdown("### 📊 Indicadores e Custos Consolidados")
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Custo Total", f"R$ {custo_total:.2f}")
            m2.metric("Custo / Unid. Produzida", f"R$ {custo_unidade_produzida:.2f}")
            m3.metric("Custo / Kg Crua", f"R$ {custo_kg_crua:.2f}")
            m4.metric("Custo / Kg (Assada)", f"R$ {custo_kg_assada:.2f}")
            m5.metric("Custo / Pacote", f"R$ {custo_pacote:.2f}")

            st.markdown("---")
            st.markdown("### 🥩 Insumos Alimentícios")
            if not df_insumos.empty:
                df_ins_view = df_insumos[['codigo', 'produto_insumo', 'qtd_bruta', 'unidade', 'preco_bruto', 'rendimento_pct_val', 'qtd_liquida', 'preco_liquido']].copy()
                df_ins_view.columns = ['Código', 'Insumo', 'Qtd Bruta', 'Unidade', 'Preço Bruto (R$)', 'Rendimento %', 'Qtd Líquida', 'Preço Líquido (R$)']
                
                # Adicionando linha de somatório para colunas numéricas
                linha_soma_ins = pd.DataFrame([{
                    'Código': 'TOTAL',
                    'Insumo': '',
                    'Qtd Bruta': df_ins_view['Qtd Bruta'].sum(),
                    'Unidade': '',
                    'Preço Bruto (R$)': df_ins_view['Preço Bruto (R$)'].sum(),
                    'Rendimento %': '',
                    'Qtd Líquida': df_ins_view['Qtd Líquida'].sum(),
                    'Preço Líquido (R$)': df_ins_view['Preço Líquido (R$)'].sum()
                }])
                df_ins_view_tot = pd.concat([df_ins_view, linha_soma_ins], ignore_index=True)
                
                st.dataframe(
                    df_ins_view_tot.style.format({
                        'Qtd Bruta': '{:.3f}',
                        'Preço Bruto (R$)': lambda x: f"R$ {x:.2f}" if isinstance(x, (int, float)) else x,
                        'Rendimento %': lambda x: f"{x:.1f}%" if isinstance(x, (int, float)) else x,
                        'Qtd Líquida': '{:.3f}',
                        'Preço Líquido (R$)': lambda x: f"R$ {x:.2f}" if isinstance(x, (int, float)) else x
                    }),
                    use_container_width=True
                )
            else:
                st.info("Nenhum insumo alimentício cadastrado.")

            st.markdown("---")
            st.markdown("### 📦 Insumos Não Alimentícios")
            if not df_nao_ali.empty:
                df_nao_view = df_nao_ali[['codigo', 'produto_insumo', 'qtd_bruta', 'unidade', 'preco_bruto', 'rendimento_pct_val', 'qtd_liquida', 'preco_liquido']].copy()
                df_nao_view.columns = ['Código', 'Insumo', 'Qtd Bruta', 'Unidade', 'Preço Bruto (R$)', 'Rendimento %', 'Qtd Líquida', 'Preço Líquido (R$)']
                
                # Adicionando linha de somatório para colunas numéricas
                linha_soma_nao = pd.DataFrame([{
                    'Código': 'TOTAL',
                    'Insumo': '',
                    'Qtd Bruta': df_nao_view['Qtd Bruta'].sum(),
                    'Unidade': '',
                    'Preço Bruto (R$)': df_nao_view['Preço Bruto (R$)'].sum(),
                    'Rendimento %': '',
                    'Qtd Líquida': df_nao_view['Qtd Líquida'].sum(),
                    'Preço Líquido (R$)': df_nao_view['Preço Líquido (R$)'].sum()
                }])
                df_nao_view_tot = pd.concat([df_nao_view, linha_soma_nao], ignore_index=True)
                
                st.dataframe(
                    df_nao_view_tot.style.format({
                        'Qtd Bruta': '{:.3f}',
                        'Preço Bruto (R$)': lambda x: f"R$ {x:.2f}" if isinstance(x, (int, float)) else x,
                        'Rendimento %': lambda x: f"{x:.1f}%" if isinstance(x, (int, float)) else x,
                        'Qtd Líquida': '{:.3f}',
                        'Preço Líquido (R$)': lambda x: f"R$ {x:.2f}" if isinstance(x, (int, float)) else x
                    }),
                    use_container_width=True
                )
            else:
                st.info("Nenhum insumo não alimentício cadastrado.")

def init_db():
    conn = sqlite3.connect("desossa_db.db")
    cursor = conn.cursor()
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
            data_criacao TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()