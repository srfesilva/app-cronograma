"""Cronograma interativo do Censo Escolar (Streamlit)."""
import io
from datetime import timedelta
import html

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

from Parametro import df as original

st.set_page_config(page_title="Cronograma do Censo Escolar", page_icon="📅", layout="wide")
COLS = ["Atividade", "Início", "Fim", "Responsável"]
MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]


def validar(tabela):
    """Conserva a ordem e exige datas válidas e atividade preenchida."""
    t = tabela.copy()
    if not set(COLS).issubset(t.columns):
        raise ValueError("Colunas obrigatórias: " + ", ".join(COLS))
    t = t[COLS].reset_index(drop=True)
    for col in ("Início", "Fim"):
        t[col] = pd.to_datetime(t[col], dayfirst=True, errors="coerce").dt.normalize()
    t["Atividade"] = t["Atividade"].fillna("").astype(str).str.strip()
    t["Responsável"] = t["Responsável"].fillna("").astype(str).str.strip().replace("", "Não informado")
    incorretas = t.index[t[["Início", "Fim"]].isna().any(axis=1) | (t["Fim"] < t["Início"]) | (t["Atividade"] == "")]
    if len(incorretas):
        raise ValueError("Corrija as linhas: " + ", ".join(str(x + 1) for x in incorretas))
    return t


def janela_periodo(modo, ano, periodo):
    if modo == "Completa":
        return None
    if modo == "Semestral":
        mes = 1 if periodo == "1º semestre (jan–jun)" else 7
        duracao = 6
    else:
        mes = 1 + (int(periodo[0]) - 1) * 2
        duracao = 2
    inicio = pd.Timestamp(year=ano, month=mes, day=1)
    fim_exclusivo = inicio + pd.DateOffset(months=duracao)
    return inicio, fim_exclusivo


def filtrar_periodo(tabela, janela):
    """Inclui qualquer atividade que cruze a janela, preservando datas originais."""
    if janela is None:
        return tabela.copy().reset_index(drop=True)
    inicio, fim_exclusivo = janela
    return tabela[(tabela["Início"] < fim_exclusivo) & (tabela["Fim"] >= inicio)].copy().reset_index(drop=True)


def grafico(tabela, janela=None, mostrar_rotulos=True, titulo_periodo="Visualização completa"):
    d = validar(tabela)
    if d.empty:
        raise ValueError("Não há atividades para apresentar no período selecionado.")
    d["Linha"] = range(len(d))
    if janela is None:
        inicio = d["Início"].min().replace(day=1)
        fim = (d["Fim"].max() + pd.offsets.MonthBegin(1)).normalize()
    else:
        inicio, fim = janela
    # Intervalo exibido em dias, para não ultrapassar o limite direito da janela.
    d["Inicio_visivel"] = d["Início"].clip(lower=inicio)
    d["Fim_visivel_exclusivo"] = (d["Fim"] + pd.Timedelta(days=1)).clip(upper=fim)
    meses = pd.date_range(inicio, fim, freq="MS")
    responsaveis = d["Responsável"].unique()
    paleta = px.colors.qualitative.Set2
    cores = {r: paleta[i % len(paleta)] for i, r in enumerate(responsaveis)}
    fig = go.Figure()
    for r in responsaveis:
        sub = d[d["Responsável"] == r]
        duracoes = (sub["Fim_visivel_exclusivo"] - sub["Inicio_visivel"]).dt.total_seconds() * 1000
        fig.add_trace(go.Bar(
            x=duracoes, base=sub["Inicio_visivel"], y=sub["Linha"], orientation="h",
            width=0.7, name=r,
            marker=dict(color=cores[r], line=dict(color="white", width=0.6)),
            customdata=list(zip(sub["Atividade"], sub["Início"].dt.strftime("%d/%m/%Y"), sub["Fim"].dt.strftime("%d/%m/%Y"))),
            hovertemplate="<b>%{customdata[0]}</b><br>Início original: %{customdata[1]}<br>Fim original: %{customdata[2]}<br>Responsável: " + html.escape(r) + "<extra></extra>",
        ))
    if mostrar_rotulos:
        # Texto posicionado após barra, mas dentro da janela: sem corte no limite direito.
        largura = (fim - inicio).days
        for _, item in d.iterrows():
            pos = item["Fim_visivel_exclusivo"] + pd.Timedelta(days=max(1, round(largura * 0.005)))
            if pos < fim - pd.Timedelta(days=max(4, round(largura * 0.07))):
                fig.add_annotation(
                    x=pos, y=item["Linha"], xref="x", yref="y", text=html.escape(item["Responsável"]),
                    showarrow=False, xanchor="left", yanchor="middle",
                    font=dict(family="Arial", size=10, color="#334155"),
                    bgcolor="rgba(255,255,255,0.72)", borderpad=2,
                )
            else:
                # Ao encostar na borda direita, mantém o texto visível dentro da barra.
                fig.add_annotation(
                    x=fim - pd.Timedelta(days=max(1, round(largura * 0.01))),
                    y=item["Linha"], xref="x", yref="y", text=html.escape(item["Responsável"]),
                    showarrow=False, xanchor="right", yanchor="middle",
                    font=dict(family="Arial", size=9, color="#334155"),
                    bgcolor="rgba(255,255,255,0.85)", borderpad=2,
                )
    for i in range(len(meses) - 1):
        atual, proximo = meses[i], meses[i + 1]
        if i % 2 == 0:
            fig.add_vrect(x0=atual, x1=proximo, fillcolor="#e9eef5", opacity=0.55, line_width=0, layer="below")
        fig.add_vline(x=atual, line_color="#64748b" if atual.month == 1 else "#cbd5e1", line_width=2 if atual.month == 1 else 1)
    fig.add_vline(x=meses[-1], line_color="#cbd5e1", line_width=1)
    posicoes = [meses[i] + (meses[i + 1] - meses[i]) / 2 for i in range(len(meses) - 1)]
    rotulos = [f"{MESES[meses[i].month - 1]}<br><b>{meses[i].year}</b>" for i in range(len(meses) - 1)]
    fig.update_xaxes(type="date", range=[inicio, fim], tickmode="array", tickvals=posicoes, ticktext=rotulos,
                     tickangle=0, side="top", showgrid=False, showline=True, linecolor="#94a3b8",
                     tickfont=dict(size=11, color="#334155"), title="", fixedrange=False)
    fig.update_yaxes(tickmode="array", tickvals=d["Linha"], ticktext=d["Atividade"],
                     range=[len(d) - .5, -.5], showgrid=False, title="", tickfont=dict(size=11, color="#243b53"), automargin=True)
    fig.update_layout(
        title=dict(text=f"<b>Cronograma Detalhado de Atividades</b><br><sup>Censo Escolar | {html.escape(titulo_periodo)}</sup>", x=.5, xanchor="center", font=dict(size=20)),
        height=max(600, len(d) * 43 + 190), template="plotly_white",
        margin=dict(l=340, r=80, t=130, b=120), font=dict(family="Arial", size=11, color="#243b53"),
        barmode="overlay", bargap=.25, legend=dict(title="Responsáveis", orientation="h", x=.5, xanchor="center", y=-.12, font=dict(size=10)),
        plot_bgcolor="white", paper_bgcolor="white", hovermode="closest",
    )
    return fig


def excel_formatado(tabela, filtrada, descricao):
    """Gera XLSX editável com tabela, autofiltro, datas reais e instruções simples."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Cronograma completo"
    abas = [(ws, tabela)]
    segunda = wb.create_sheet("Período selecionado")
    abas.append((segunda, filtrada))
    for aba, base in abas:
        aba.merge_cells("A1:D2")
        cab = aba["A1"]
        cab.value = "CRONOGRAMA DO CENSO ESCOLAR"
        cab.fill = PatternFill("solid", fgColor="17365D")
        cab.font = Font(name="Aptos", size=16, bold=True, color="FFFFFF")
        cab.alignment = Alignment(vertical="center", horizontal="left", indent=1)
        aba.row_dimensions[1].height = 26
        aba.row_dimensions[2].height = 15
        aba.merge_cells("A3:D3")
        aba["A3"] = "Visão: completa" if aba is ws else f"Visão: {descricao}"
        aba["A3"].font = Font(name="Aptos", size=11, italic=True, color="53657E")
        aba.row_dimensions[3].height = 23
        for col, titulo in enumerate(COLS, start=1):
            cel = aba.cell(5, col, titulo)
            cel.fill = PatternFill("solid", fgColor="22577A")
            cel.font = Font(name="Aptos", size=11, bold=True, color="FFFFFF")
            cel.alignment = Alignment(vertical="center")
        aba.row_dimensions[5].height = 25
        for idx, (_, linha) in enumerate(base.iterrows(), start=6):
            valores = [linha["Atividade"], linha["Início"].to_pydatetime(), linha["Fim"].to_pydatetime(), linha["Responsável"]]
            for coluna, valor in enumerate(valores, start=1):
                cel = aba.cell(idx, coluna, valor)
                cel.font = Font(name="Aptos", size=10, color="243B53")
                cel.alignment = Alignment(vertical="center", wrap_text=(coluna in (1, 4)))
                if coluna in (2, 3):
                    cel.number_format = "DD/MM/YYYY"
                if idx % 2 == 0:
                    cel.fill = PatternFill("solid", fgColor="F1F6FB")
            aba.row_dimensions[idx].height = 28
        aba.column_dimensions["A"].width = 55
        aba.column_dimensions["B"].width = 19
        aba.column_dimensions["C"].width = 19
        aba.column_dimensions["D"].width = 62
        aba.freeze_panes = "B6"
        ultima = max(6, len(base) + 5)
        if len(base):
            tabela_excel = Table(displayName="CronogramaCompleto" if aba is ws else "CronogramaFiltrado", ref=f"A5:D{ultima}")
            tabela_excel.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True, showColumnStripes=False)
            aba.add_table(tabela_excel)
        else:
            aba.auto_filter.ref = "A5:D5"
            aba["A6"] = "Nenhuma atividade neste período."
    guia = wb.create_sheet("Orientações")
    guia.column_dimensions["A"].width = 105
    guia["A1"] = "COMO UTILIZAR ESTA PLANILHA"
    guia["A1"].font = Font(bold=True, size=16, color="17365D")
    orientacoes = [
        "Aba 'Cronograma completo': todas as atividades, independentemente do filtro utilizado no aplicativo.",
        "Aba 'Período selecionado': atividades que coincidem com o intervalo escolhido no aplicativo.",
        "As colunas Início e Fim mantêm as datas originais, mesmo quando a barra foi cortada pela visualização.",
        "Use as setas de filtro no cabeçalho para localizar atividades e responsáveis.",
        "Para importar a planilha novamente no aplicativo, utilize a aba 'Cronograma completo' em um arquivo XLSX separado, ou importe este arquivo diretamente (a primeira aba será lida).",
        "Alterações realizadas neste arquivo não são sincronizadas automaticamente com o aplicativo online.",
    ]
    for pos, frase in enumerate(orientacoes, start=3):
        guia.cell(pos, 1, frase)
        guia.row_dimensions[pos].height = 29
    saida = io.BytesIO()
    wb.save(saida)
    return saida.getvalue()


if "tabela" not in st.session_state:
    st.session_state.tabela = original[COLS].copy()

st.title("📅 Cronograma do Censo Escolar")
st.caption("Edição de atividades, visualização por períodos e exportação em Excel formatado")

with st.sidebar:
    st.header("Configurações")
    mostrar = st.checkbox("Exibir responsáveis após as barras", value=True)
    st.subheader("Período de visualização")
    modo = st.radio("Tipo de visualização", ["Completa", "Semestral", "Bimestral"], horizontal=False)
    ano = None
    periodo = None
    if modo != "Completa":
        base = st.session_state.tabela
        datas = pd.concat([pd.to_datetime(base["Início"], errors="coerce"), pd.to_datetime(base["Fim"], errors="coerce")]).dropna()
        anos = sorted(set(datas.dt.year.tolist())) if len(datas) else [pd.Timestamp.today().year]
        ano = st.selectbox("Ano", anos, index=0)
        if modo == "Semestral":
            periodo = st.selectbox("Semestre", ["1º semestre (jan–jun)", "2º semestre (jul–dez)"])
        else:
            periodo = st.selectbox("Bimestre", [
                "1º bimestre (jan–fev)", "2º bimestre (mar–abr)", "3º bimestre (mai–jun)",
                "4º bimestre (jul–ago)", "5º bimestre (set–out)", "6º bimestre (nov–dez)",
            ])
    st.divider()
    arquivo = st.file_uploader("Importar cronograma (Excel ou CSV)", type=["xlsx", "csv"])
    if arquivo is not None:
        identificador = (arquivo.name, arquivo.size, arquivo.getvalue())
        if st.session_state.get("arquivo_importado") != identificador:
            try:
                bruto = pd.read_csv(arquivo, sep=None, engine="python") if arquivo.name.lower().endswith(".csv") else pd.read_excel(arquivo, sheet_name=0, header=4)
                # Suporta também Excel comum com cabeçalho na primeira linha.
                if not set(COLS).issubset(bruto.columns) and arquivo.name.lower().endswith(".xlsx"):
                    arquivo.seek(0)
                    bruto = pd.read_excel(arquivo)
                st.session_state.tabela = validar(bruto)
                st.session_state.arquivo_importado = identificador
                st.rerun()
            except Exception as e:
                st.error(f"Erro na importação: {e}")
    if st.button("Restaurar dados originais"):
        st.session_state.tabela = original[COLS].copy()
        st.session_state.pop("arquivo_importado", None)
        st.rerun()

st.subheader("Editar atividades")
st.info("As alterações são mantidas durante esta sessão. Baixe o Excel formatado para salvar e compartilhar seu cronograma.")
editado = st.data_editor(
    st.session_state.tabela, num_rows="dynamic", hide_index=True, use_container_width=True,
    column_config={
        "Atividade": st.column_config.TextColumn("Atividade", required=True),
        "Responsável": st.column_config.TextColumn("Responsável"),
        "Início": st.column_config.DateColumn("Início", format="DD/MM/YYYY", required=True),
        "Fim": st.column_config.DateColumn("Fim", format="DD/MM/YYYY", required=True),
    },
    key="editor",
)

try:
    pronto = validar(editado)
    if pronto.empty:
        st.warning("Adicione ao menos uma atividade ao cronograma.")
        st.stop()
    st.session_state.tabela = pronto
    janela = janela_periodo(modo, ano, periodo)
    visiveis = filtrar_periodo(pronto, janela)
    descricao = "Completa" if janela is None else f"{ano} | {periodo}"
    c1, c2, c3 = st.columns(3)
    c1.metric("Atividades cadastradas", len(pronto))
    c2.metric("Atividades no período", len(visiveis))
    c3.metric("Visualização", "Completa" if modo == "Completa" else modo)
    if visiveis.empty:
        st.warning("Nenhuma atividade coincide com o período selecionado. Escolha outro semestre/bimestre.")
    else:
        figura = grafico(visiveis, janela=janela, mostrar_rotulos=mostrar, titulo_periodo=descricao)
        st.plotly_chart(figura, use_container_width=True, config={"displaylogo": False, "scrollZoom": True, "responsive": True})
    st.subheader("Downloads")
    dados_excel = excel_formatado(pronto, visiveis, descricao)
    a, b = st.columns(2)
    with a:
        st.download_button("📗 Baixar atividades (Excel formatado)", dados_excel,
                           file_name="cronograma_censo_escolar.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)
    with b:
        if not visiveis.empty:
            st.download_button("🌐 Baixar gráfico interativo (HTML)",
                               figura.to_html(full_html=True, include_plotlyjs=True).encode("utf-8"),
                               file_name="cronograma_censo_escolar.html", mime="text/html", use_container_width=True)
    with st.expander("Outras opções de exportação"):
        st.download_button("Baixar atividades (CSV)",
                           pronto.to_csv(index=False, date_format="%Y-%m-%d").encode("utf-8-sig"),
                           file_name="cronograma_censo.csv", mime="text/csv")
except ValueError as e:
    st.error(str(e))
    st.warning("Corrija as linhas indicadas para visualizar e exportar o cronograma.")
