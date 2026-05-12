"""
Dashboard de Gamificação de Vendas — Casa do Celular
Gerente Geral: Teixeira de Freitas | Barreiras | Laranjeiras

Como rodar:
    pip install streamlit pandas plotly
    streamlit run dashboard_cdc.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

# ══════════════════════════════════════════════════════════════════
#  CONFIGURAÇÃO — ajuste aqui se seu CSV tiver nomes diferentes
# ══════════════════════════════════════════════════════════════════
CONFIG = {
    # ── Separador do CSV ──────────────────────────────────────────
    # Confirmado: ponto e vírgula
    "sep": ";",

    # ── Nomes das colunas (confirmados) ──────────────────────────
    "col_data":     "Data",
    "col_valor":    "Valor Total",   # confirmado
    "col_status":   "Status",        # confirmado — texto ex: "Cancelado"
    "col_vendedor": "Vendedor",
    "col_loja":     "Loja",          # confirmado

    # ── Termos que indicam cancelamento/devolução ────────────────
    # (case-insensitive — adicione qualquer variação que apareça no seu CSV)
    "status_negativos": [
        "cancelado", "cancelamento", "cancelada",
        "devolução", "devolucao", "devolvido", "devol",
        "estorno", "cancel",
    ],

    # ── Nomes das lojas (como aparecem na coluna "Loja" do CSV) ──
    # Se o nome no CSV for diferente, ajuste aqui
    "lojas": [
        "CDC TEIXEIRA DE FREITAS NOVO",
        "CDC BARREIRAS",
        "CDC LARANJEIRAS",
    ],
    "lojas_apelidos": {
        "CDC TEIXEIRA DE FREITAS NOVO": "Teixeira de Freitas",
        "CDC BARREIRAS":                "Barreiras",
        "CDC LARANJEIRAS":              "Laranjeiras",
    },

    # ── Formato da data ──────────────────────────────────────────
    # "mixed" = pandas detecta automaticamente (recomendado)
    # Exemplos manuais: "%d/%m/%Y"  →  01/05/2026
    #                   "%d/%m/%y"  →  01/05/26
    "formato_data": "mixed",
}

# ══════════════════════════════════════════════════════════════════
#  ESTILOS — mobile-first, fundo escuro, visual de app
# ══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="CDC · Rankings",
    page_icon="🏆",
    layout="centered",          # melhor em celular
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
/* ── Paleta ── */
:root {
    --bg:       #0F0F13;
    --surface:  #1A1A22;
    --border:   #2A2A35;
    --accent:   #4F8EF7;
    --gold:     #F5C518;
    --silver:   #C0C0C0;
    --bronze:   #CD7F32;
    --green:    #34D399;
    --red:      #F87171;
    --text:     #F0F0F5;
    --muted:    #8888AA;
}

/* ── Fundo e tipografia ── */
html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
    color: var(--text);
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
}
[data-testid="stSidebar"] { background-color: var(--surface) !important; }
[data-testid="stHeader"]  { background-color: transparent !important; }

/* ── Abas ── */
.stTabs [data-baseweb="tab-list"]    { background: var(--surface); border-radius: 12px; padding: 4px; gap: 4px; }
.stTabs [data-baseweb="tab"]         { background: transparent; color: var(--muted); border-radius: 8px; font-weight: 600; padding: 8px 18px; }
.stTabs [aria-selected="true"]       { background: var(--accent) !important; color: #fff !important; }
.stTabs [data-baseweb="tab-border"]  { display: none; }
.stTabs [data-baseweb="tab-panel"]   { padding-top: 20px; }

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 16px !important;
}
[data-testid="stMetricLabel"]  { color: var(--muted) !important; font-size: 12px !important; }
[data-testid="stMetricValue"]  { color: var(--text) !important; font-size: 26px !important; font-weight: 800 !important; }
[data-testid="stMetricDelta"]  { font-size: 13px !important; }

/* ── Botões / Upload ── */
[data-testid="stFileUploader"] { background: var(--surface); border-radius: 12px; border: 1px dashed var(--border); }
.stButton > button {
    background: var(--accent); color: #fff; border: none;
    border-radius: 10px; font-weight: 700; width: 100%;
}

/* ── Selectbox ── */
[data-baseweb="select"] > div { background: var(--surface) !important; border-color: var(--border) !important; }

/* ── Scrollbar fina ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 99px; }

/* ── Tabela ── */
.dataframe tbody tr:nth-child(even) { background-color: var(--surface); }
.dataframe { border: none !important; }

/* ── Ranking card custom ── */
.rank-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 12px 16px;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 12px;
}
.rank-pos   { font-size: 22px; font-weight: 900; min-width: 36px; }
.rank-name  { font-size: 15px; font-weight: 700; flex: 1; }
.rank-valor { font-size: 16px; font-weight: 800; color: var(--green); white-space: nowrap; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
#  FUNÇÕES AUXILIARES
# ══════════════════════════════════════════════════════════════════
def formatar_brl(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def icone_posicao(pos: int) -> str:
    icons = ["🥇", "🥈", "🥉"]
    return icons[pos - 1] if 1 <= pos <= 3 else f"#{pos}"

def cor_posicao(pos: int) -> str:
    cores = ["#F5C518", "#C0C0C0", "#CD7F32"]
    return cores[pos - 1] if 1 <= pos <= 3 else "#8888AA"

@st.cache_data(show_spinner=False)
def carregar_csv(file_bytes: bytes, sep: str) -> pd.DataFrame:
    import io
    try:
        df = pd.read_csv(io.BytesIO(file_bytes), sep=sep, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(io.BytesIO(file_bytes), sep=sep, encoding="latin-1")
    return df


def processar_dados(df: pd.DataFrame) -> pd.DataFrame | None:
    cfg = CONFIG
    erros = []

    # ── Normaliza nomes de colunas ANTES de verificar ──
    df.columns = df.columns.str.strip()

    # ── Verificar colunas obrigatórias ──
    colunas_ok = {
        cfg["col_data"]:     "Data",
        cfg["col_valor"]:    "Valor Total",
        cfg["col_status"]:   "Status",
        cfg["col_vendedor"]: "Vendedor",
        cfg["col_loja"]:     "Loja",
    }
    for col_csv, apelido in colunas_ok.items():
        if col_csv not in df.columns:
            erros.append(f"Coluna **{col_csv}** ({apelido}) não encontrada.")
    if erros:
        st.error("⚠️ Problema nas colunas do CSV:\n\n" + "\n".join(f"- {e}" for e in erros))
        st.info(f"Colunas encontradas: `{'` | `'.join(df.columns.tolist())}`")
        return None

    df = df.copy()
    # DEBUG temporário — remover após resolver
    with st.expander("🔧 Debug (remover depois)", expanded=True):
        st.write("Shape:", df.shape)
        st.write("Colunas:", df.columns.tolist())
        st.write("Primeiras linhas:")
        st.dataframe(df.head(3))

    # ── Datas ──
    # Suporta formatos como "Sáb, 02/05/26 09:01" extraindo dd/mm/yy
    import re as _re
    def _parse_date(val):
        if pd.isna(val):
            return pd.NaT
        s = str(val).strip()
        # Remove dia da semana abreviado ex: "sáb., " ou "Sáb, "
        s = _re.sub(r'^[a-záàâãéèêíïóôõöúüçñ]{2,4}\.?,?\s*', '', s, flags=_re.IGNORECASE)
        s = s.strip()
        # Extrai dd/mm/yy ou dd/mm/yyyy
        m = _re.search(r'(\d{1,2}/\d{1,2}/\d{2,4})', s)
        if m:
            parte = m.group(1)
            for fmt in ("%d/%m/%y", "%d/%m/%Y"):
                try:
                    return pd.to_datetime(parte, format=fmt)
                except Exception:
                    continue
        # Formato ISO ex: "2026-05-12"
        m2 = _re.search(r'(\d{4}-\d{2}-\d{2})', s)
        if m2:
            try:
                return pd.to_datetime(m2.group(1))
            except Exception:
                pass
        # Fallback
        try:
            return pd.to_datetime(s, dayfirst=True)
        except Exception:
            return pd.NaT

    if cfg["formato_data"] == "mixed":
        df["_data"] = df[cfg["col_data"]].apply(_parse_date)
    else:
        df["_data"] = pd.to_datetime(df[cfg["col_data"]], format=cfg["formato_data"], errors="coerce")

    df = df.dropna(subset=["_data"])

    # ── Valor numérico ──
    def _parse_valor(val):
        """Converte valores como 1.499,00 ou 1499.00 ou 1499 para float."""
        import re as _re2
        if pd.isna(val):
            return 0.0
        s = str(val).strip().replace("R$", "").replace(" ", "")
        # Formato brasileiro: 1.499,00 → separador de milhar=. e decimal=,
        if "," in s and "." in s:
            # ex: 1.499,00
            s = s.replace(".", "").replace(",", ".")
        elif "," in s and "." not in s:
            # ex: 1499,00
            s = s.replace(",", ".")
        # else: já é float americano ex: 1499.00 ou inteiro 1499
        try:
            return float(s)
        except Exception:
            return 0.0
    df["_valor_raw"] = df[cfg["col_valor"]].apply(_parse_valor)

    # ── Calcular Venda Líquida ──
    negativos = cfg["status_negativos"]
    df["_is_negativo"] = df[cfg["col_status"]].fillna("").astype(str).str.lower().str.strip().apply(
        lambda s: any(neg in s for neg in negativos)
    )
    # Se status negativo → valor vira negativo (cancelamento subtrai)
    df["_valor_liquido"] = df.apply(
        lambda r: -abs(r["_valor_raw"]) if r["_is_negativo"] else abs(r["_valor_raw"]),
        axis=1,
    )

    # ── Normalizar Loja (upper + strip) ──
    df["_loja"] = df[cfg["col_loja"]].astype(str).str.upper().str.strip()

    # ── Renomear apelidos ──
    apelidos = {k.upper(): v for k, v in cfg["lojas_apelidos"].items()}
    df["_loja_apelido"] = df["_loja"].map(apelidos).fillna(df["_loja"])

    df["_vendedor"] = df[cfg["col_vendedor"]].astype(str).str.strip()
    df["_date"] = df["_data"].dt.date

    return df


# ══════════════════════════════════════════════════════════════════
#  COMPONENTES VISUAIS
# ══════════════════════════════════════════════════════════════════
def card_metrica(col, label: str, valor: float, delta=None, prefix="R$"):
    valor_fmt = formatar_brl(valor) if prefix == "R$" else f"{valor:,}"
    col.metric(label, valor_fmt, delta)


def ranking_vendedores(df_filtrado: pd.DataFrame, titulo: str):
    if df_filtrado.empty:
        st.info("Sem dados para este período.")
        return

    ranking = (
        df_filtrado.groupby("_vendedor")["_valor_liquido"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    ranking.columns = ["Vendedor", "Venda Líquida"]
    ranking = ranking[ranking["Venda Líquida"] != 0]

    if ranking.empty:
        st.info("Nenhuma venda líquida positiva no período.")
        return

    st.markdown(f"#### {titulo}")

    # Cards do pódio (top 3) + lista do restante
    for i, row in ranking.iterrows():
        pos = i + 1
        icone = icone_posicao(pos)
        cor   = cor_posicao(pos)
        pct   = (row["Venda Líquida"] / ranking["Venda Líquida"].max()) * 100

        st.markdown(f"""
        <div class="rank-card" style="border-left: 4px solid {cor};">
            <div class="rank-pos" style="color:{cor}">{icone}</div>
            <div style="flex:1">
                <div class="rank-name">{row["Vendedor"]}</div>
                <div style="background:#2A2A35;border-radius:99px;height:5px;margin-top:6px;overflow:hidden">
                  <div style="background:{cor};width:{pct:.0f}%;height:100%;border-radius:99px"></div>
                </div>
            </div>
            <div class="rank-valor">{formatar_brl(row["Venda Líquida"])}</div>
        </div>
        """, unsafe_allow_html=True)

    # Gráfico de barras horizontal
    fig = px.bar(
        ranking.head(15).iloc[::-1],
        x="Venda Líquida", y="Vendedor",
        orientation="h",
        color="Venda Líquida",
        color_continuous_scale=["#1A3A6A", "#4F8EF7", "#34D399"],
        text=ranking.head(15)["Venda Líquida"].apply(formatar_brl).iloc[::-1],
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#F0F0F5", coloraxis_showscale=False,
        margin=dict(l=0, r=10, t=10, b=0),
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False),
        height=max(200, len(ranking.head(15)) * 44),
    )
    fig.update_traces(textposition="outside", textfont_size=11)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def grafico_lojas(df_filtrado: pd.DataFrame):
    resumo = (
        df_filtrado.groupby("_loja_apelido")["_valor_liquido"]
        .sum()
        .reset_index()
        .sort_values("_valor_liquido", ascending=False)
    )
    resumo.columns = ["Loja", "Venda Líquida"]

    fig = px.bar(
        resumo, x="Loja", y="Venda Líquida",
        color="Venda Líquida",
        color_continuous_scale=["#1A3A6A", "#4F8EF7", "#34D399"],
        text=resumo["Venda Líquida"].apply(formatar_brl),
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#F0F0F5", coloraxis_showscale=False,
        margin=dict(l=0, r=0, t=10, b=0),
        xaxis_title="", yaxis_title="", yaxis=dict(showgrid=False),
        height=280,
    )
    fig.update_traces(textposition="outside", textfont_size=11)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def grafico_evolucao_diaria(df_filtrado: pd.DataFrame):
    evolucao = (
        df_filtrado.groupby("_date")["_valor_liquido"]
        .sum()
        .reset_index()
        .sort_values("_date")
    )
    evolucao["_date_fmt"] = pd.to_datetime(evolucao["_date"]).dt.strftime("%d/%m")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=evolucao["_date_fmt"], y=evolucao["_valor_liquido"],
        mode="lines+markers",
        line=dict(color="#4F8EF7", width=2.5),
        marker=dict(size=7, color="#4F8EF7"),
        fill="tozeroy", fillcolor="rgba(79,142,247,0.12)",
        hovertemplate="%{x}: %{y:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#F0F0F5",
        margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="#2A2A35"),
        height=220,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ══════════════════════════════════════════════════════════════════
#  APP PRINCIPAL
# ══════════════════════════════════════════════════════════════════
# ── Header ──
st.markdown("""
<div style="text-align:center;padding:20px 0 8px">
  <div style="font-size:36px">📱</div>
  <div style="font-size:22px;font-weight:900;letter-spacing:-0.03em">Casa do Celular</div>
  <div style="font-size:13px;color:#8888AA;margin-top:2px">Ranking de Vendas · Tempo Real</div>
</div>
""", unsafe_allow_html=True)

# ── Upload ──
# ── ID da planilha Google Sheets ──
SHEET_ID = "1xC9E9Ux5nyxuEO6zdbMcfjFU7_iv3jXuJTLJmzzkIU0"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

@st.cache_data(ttl=300, show_spinner=False)  # cache de 5 minutos
def carregar_sheets(url: str) -> pd.DataFrame:
    import io, urllib.request
    from io import StringIO
    try:
        with urllib.request.urlopen(url) as r:
            raw = r.read()
        # O Sheets exporta 2 versões: col A (original ;) com acentos corretos
        # e cols B+ (separadas por vírgula) com encoding corrompido.
        # Lemos sempre a col A com separador ; que preserva os acentos.
        for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
            try:
                candidate = pd.read_csv(io.BytesIO(raw), sep=";", encoding=enc)
                sample = " ".join(candidate.iloc[:, 1].astype(str).head(5).tolist())
                if "Ã" not in sample and "©" not in sample:
                    return candidate
            except Exception:
                continue
        return pd.read_csv(io.BytesIO(raw), sep=";", encoding="utf-8")
    except Exception as e:
        st.error(f"❌ Erro ao carregar a planilha: {e}")
        st.stop()

# ── Botão de atualizar ──
col_refresh, col_info = st.columns([1, 3])
with col_refresh:
    if st.button("🔄 Atualizar dados"):
        st.cache_data.clear()
        st.rerun()
with col_info:
    st.markdown(
        "<div style='padding:8px 0;font-size:12px;color:#8888AA'>Dados atualizados a cada 5 min automaticamente</div>",
        unsafe_allow_html=True
    )

# ── Carregar e processar ──
with st.spinner("Carregando dados da planilha..."):
    df_raw = carregar_sheets(SHEET_URL)
    df = processar_dados(df_raw)

if df is None:
    st.error("Não foi possível processar os dados. Verifique a planilha.")
    st.stop()

hoje        = datetime.now().date()
mes_atual   = hoje.month
ano_atual   = hoje.year

# ── Filtro de Loja ──
apelidos_disponiveis = sorted(df["_loja_apelido"].unique().tolist())
opcoes = ["🏢 Todas as lojas"] + apelidos_disponiveis

loja_selecionada = st.selectbox(
    "🏪 Loja",
    opcoes,
    index=0,
    help="Selecione uma loja ou veja o consolidado",
)

if loja_selecionada == "🏢 Todas as lojas":
    df_filtrado = df
    titulo_loja = "Consolidado — 3 Lojas"
else:
    df_filtrado = df[df["_loja_apelido"] == loja_selecionada]
    titulo_loja = loja_selecionada

st.markdown(f"<div style='font-size:12px;color:#8888AA;margin-bottom:16px'>📍 {titulo_loja}</div>",
            unsafe_allow_html=True)

# ── Abas ──
tab1, tab2 = st.tabs(["🚀 Hoje", "📅 Este Mês"])

# ════════════════════════════
#  ABA 1 — VENDAS DO DIA
# ════════════════════════════
with tab1:
    df_dia = df_filtrado[df_filtrado["_date"] == hoje]

    # Garante colunas mesmo se df_dia for vazio
    for _col, _val in [("_is_negativo", False), ("_valor_liquido", 0.0)]:
        if _col not in df_dia.columns:
            df_dia = df_dia.copy()
            df_dia[_col] = _val
    _neg = df_dia["_is_negativo"].astype(bool)
    total_dia  = float(df_dia["_valor_liquido"].sum())
    qtd_vendas = int((~_neg).sum())
    qtd_cancel = int(_neg.sum())
    cancel_val = float(df_dia.loc[_neg, "_valor_liquido"].sum())

    # KPIs
    c1, c2, c3 = st.columns(3)
    card_metrica(c1, "💰 Venda Líquida", total_dia)
    c2.metric("🛒 Vendas", int(qtd_vendas))
    c3.metric("❌ Cancelamentos", int(qtd_cancel),
              delta=formatar_brl(cancel_val) if qtd_cancel > 0 else None,
              delta_color="inverse")

    st.markdown("---")

    if df_dia.empty:
        st.info(f"Nenhuma venda registrada hoje ({hoje.strftime('%d/%m/%Y')}).")
    else:
        ranking_vendedores(df_dia, f"🏆 Ranking do Dia — {hoje.strftime('%d/%m/%Y')}")


# ════════════════════════════
#  ABA 2 — PERFORMANCE MENSAL
# ════════════════════════════
with tab2:
    df_mes = df_filtrado[
        (df_filtrado["_data"].dt.month == mes_atual) &
        (df_filtrado["_data"].dt.year  == ano_atual)
    ]

    for _col, _val in [("_is_negativo", False), ("_valor_liquido", 0.0)]:
        if _col not in df_mes.columns:
            df_mes = df_mes.copy()
            df_mes[_col] = _val
    _neg_mes = df_mes["_is_negativo"].astype(bool)
    total_mes  = float(df_mes["_valor_liquido"].sum())
    qtd_mes    = int((~_neg_mes).sum())
    ticket_med = df_mes.loc[~_neg_mes, "_valor_liquido"].mean()
    cancel_mes = float(df_mes.loc[_neg_mes, "_valor_liquido"].sum())

    # KPIs
    c1, c2 = st.columns(2)
    card_metrica(c1, "💰 Faturamento Líquido", total_mes)
    card_metrica(c2, "🎫 Ticket Médio", ticket_med if not pd.isna(ticket_med) else 0)
    c3, c4 = st.columns(2)
    c3.metric("🛒 Total de Vendas", int(qtd_mes))
    c4.metric("❌ Cancelamentos (R$)", formatar_brl(abs(cancel_mes)) if cancel_mes < 0 else "R$ 0,00")

    st.markdown("---")

    if df_mes.empty:
        st.info("Nenhuma venda neste mês.")
    else:
        # Evolução diária
        st.markdown("#### 📈 Evolução Diária")
        grafico_evolucao_diaria(df_mes)

        # Performance por loja (só no consolidado)
        if loja_selecionada == "🏢 Todas as lojas":
            st.markdown("#### 🏪 Performance por Loja")
            grafico_lojas(df_mes)
            st.markdown("---")

        # Ranking do mês
        ranking_vendedores(df_mes, "🥇 Grande Competição — Mês")

# ── Dados brutos ──
with st.expander("🔍 Ver dados brutos (conferência)"):
    colunas_exibir = [
        CONFIG["col_data"], CONFIG["col_vendedor"], CONFIG["col_loja"],
        CONFIG["col_status"], CONFIG["col_valor"], "_valor_liquido"
    ]
    colunas_exibir = [c for c in colunas_exibir if c in df_filtrado.columns]
    df_exibir = df_filtrado[colunas_exibir].copy()
    if "_data" in df_filtrado.columns:
        df_exibir = df_exibir.assign(_ordem=df_filtrado["_data"].values).sort_values("_ordem", ascending=False).drop(columns=["_ordem"])
    st.dataframe(
        df_exibir.head(200),
        use_container_width=True,
        height=300,
    )

# ── Rodapé ──
st.markdown(f"""
<div style="text-align:center;padding:30px 0 10px;font-size:11px;color:#555577">
    Atualizado ao fazer upload · {hoje.strftime("%d/%m/%Y")} · Casa do Celular
</div>
""", unsafe_allow_html=True)
