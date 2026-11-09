
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# ==========================================
# 1. PREPARAÇÃO DOS DADOS
# ==========================================

dados = df.copy().reset_index(drop=True)

for coluna in ["Início", "Fim"]:
    dados[coluna] = pd.to_datetime(
        dados[coluna],
        dayfirst=True,
        errors="coerce"
    )

if dados[["Início", "Fim"]].isna().any().any():
    raise ValueError("Existem datas inválidas ou ausentes.")

if (dados["Fim"] < dados["Início"]).any():
    raise ValueError("Existem atividades com término anterior ao início.")

dados["Atividade"] = dados["Atividade"].fillna("").astype(str)
dados["Responsável"] = dados["Responsável"].fillna(
    "Não informado"
).astype(str)

# Cada atividade recebe uma posição independente
dados["Linha"] = range(len(dados))

# ==========================================
# 2. CONFIGURAÇÕES VISUAIS
# ==========================================

meses_pt = [
    "Janeiro", "Fevereiro", "Março", "Abril",
    "Maio", "Junho", "Julho", "Agosto",
    "Setembro", "Outubro", "Novembro", "Dezembro"
]

responsaveis = dados["Responsável"].unique()

paleta = px.colors.qualitative.Set2

cores = {
    resp: paleta[i % len(paleta)]
    for i, resp in enumerate(responsaveis)
}

altura = max(700, len(dados) * 43 + 180)

# ==========================================
# 3. PERÍODO DO CRONOGRAMA
# ==========================================

inicio = dados["Início"].min().replace(day=1)

fim = (
    dados["Fim"].max()
    + pd.offsets.MonthBegin(1)
).normalize()

meses = pd.date_range(
    start=inicio,
    end=fim,
    freq="MS"
)

# ==========================================
# 4. CRIAR GRÁFICO
# ==========================================

fig = go.Figure()

# ==========================================
# 5. BARRAS E RESPONSÁVEIS
# ==========================================

for responsavel in responsaveis:

    subset = dados[
        dados["Responsável"] == responsavel
    ]

    duracoes = (
        subset["Fim"] - subset["Início"]
    ).dt.total_seconds() * 1000

    # Incluir o último dia da atividade
    duracoes += 86400000

    fig.add_trace(
        go.Bar(
            x=duracoes,
            base=subset["Início"],
            y=subset["Linha"],
            orientation="h",
            width=0.70,
            name=responsavel,

            marker=dict(
                color=cores[responsavel],
                line=dict(
                    color="white",
                    width=0.6
                )
            ),

            customdata=list(zip(
                subset["Atividade"],
                subset["Início"].dt.strftime("%d/%m/%Y"),
                subset["Fim"].dt.strftime("%d/%m/%Y")
            )),

            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Início: %{customdata[1]}<br>"
                "Fim: %{customdata[2]}<br>"
                "Responsável: " + responsavel +
                "<extra></extra>"
            )
        )
    )

# ==========================================
# 6. TEXTOS DOS RESPONSÁVEIS
# ==========================================

for _, item in dados.iterrows():

    # Posicionar texto após o fim da barra
    posicao_texto = item["Fim"] + pd.Timedelta(days=2)

    fig.add_annotation(
        x=posicao_texto,
        y=item["Linha"],
        xref="x",
        yref="y",
        text=item["Responsável"],
        showarrow=False,
        xanchor="left",
        yanchor="middle",
        font=dict(
            family="Arial",
            size=10,
            color="#334155"
        ),
        bgcolor="rgba(255,255,255,0.65)",
        borderpad=2
    )

# ==========================================
# 7. FUNDO ALTERNADO DOS MESES
# ==========================================

for i in range(len(meses)-1):

    atual = meses[i]
    proximo = meses[i+1]

    if i % 2 == 0:
        fig.add_vrect(
            x0=atual,
            x1=proximo,
            fillcolor="#e9eef5",
            opacity=0.55,
            line_width=0,
            layer="below"
        )

    fig.add_vline(
        x=atual,
        line_color=(
            "#64748b" if atual.month == 1
            else "#cbd5e1"
        ),
        line_width=2 if atual.month == 1 else 1
    )

fig.add_vline(
    x=meses[-1],
    line_color="#cbd5e1",
    line_width=1
)

# ==========================================
# 8. NOMES DOS MESES EM PORTUGUÊS
# ==========================================

posicoes = []
rotulos = []

for i in range(len(meses)-1):

    atual = meses[i]
    proximo = meses[i+1]

    centro = atual + (proximo-atual)/2

    posicoes.append(centro)

    rotulos.append(
        f"{meses_pt[atual.month-1]}<br>"
        f"<b>{atual.year}</b>"
    )

# ==========================================
# 9. CONFIGURAÇÃO DOS EIXOS
# ==========================================

fig.update_xaxes(
    type="date",
    range=[inicio, fim],
    tickmode="array",
    tickvals=posicoes,
    ticktext=rotulos,
    tickangle=0,
    side="top",
    showgrid=False,
    showline=True,
    linecolor="#94a3b8",
    tickfont=dict(
        size=11,
        color="#334155"
    ),
    title=""
)

fig.update_yaxes(
    tickmode="array",
    tickvals=dados["Linha"],
    ticktext=dados["Atividade"],
    range=[len(dados)-0.5, -0.5],
    showgrid=False,
    title="",
    tickfont=dict(
        size=11,
        color="#243b53"
    ),
    automargin=True
)

# ==========================================
# 10. LAYOUT FINAL
# ==========================================

fig.update_layout(
    title=dict(
        text="<b>Cronograma Detalhado de Atividades</b>"
             "<br><sup>Censo Escolar 2027</sup>",
        x=0.5,
        xanchor="center",
        font=dict(size=21)
    ),

    height=altura,
    width=1900,

    template="plotly_white",

    margin=dict(
        l=340,
        r=60,
        t=130,
        b=120
    ),

    font=dict(
        family="Arial",
        size=11,
        color="#243b53"
    ),

    barmode="overlay",
    bargap=0.25,

    legend=dict(
        title="Responsáveis",
        orientation="h",
        x=0.5,
        xanchor="center",
        y=-0.09,
        font=dict(size=10)
    ),

    plot_bgcolor="white",
    paper_bgcolor="white",

    hovermode="closest"
)

# ==========================================
# 11. EXIBIR
# ==========================================

fig.show(
    config={
        "displaylogo": False,
        "scrollZoom": True,
        "responsive": True
    }
)
