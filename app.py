import io
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from Parametro import df as original

st.set_page_config(page_title='Cronograma do Censo Escolar', page_icon='📅', layout='wide')
COLS = ['Atividade', 'Início', 'Fim', 'Responsável']
MESES = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']

def validar(tabela):
    tabela = tabela.copy()
    if not set(COLS).issubset(tabela.columns):
        raise ValueError('Colunas obrigatórias: ' + ', '.join(COLS))
    tabela = tabela[COLS].reset_index(drop=True)
    for c in ['Início', 'Fim']:
        tabela[c] = pd.to_datetime(tabela[c], errors='coerce', dayfirst=not pd.api.types.is_datetime64_any_dtype(tabela[c]))
    tabela['Atividade'] = tabela['Atividade'].fillna('').astype(str).str.strip()
    tabela['Responsável'] = tabela['Responsável'].fillna('Não informado').astype(str).str.strip().replace('', 'Não informado')
    invalidos = tabela.index[tabela[['Início','Fim']].isna().any(axis=1) | (tabela['Fim'] < tabela['Início']) | (tabela['Atividade'] == '')].tolist()
    if invalidos:
        raise ValueError('Verifique atividade, início e fim nas linhas: ' + ', '.join(str(i+1) for i in invalidos))
    return tabela

def grafico(tabela, mostrar_rotulos=True):
    d = validar(tabela)
    d['Linha'] = range(len(d))
    inicio = d['Início'].min().replace(day=1)
    fim = (d['Fim'].max() + pd.offsets.MonthBegin(1)).normalize()
    meses = pd.date_range(inicio, fim, freq='MS')
    resp = d['Responsável'].unique()
    paleta = px.colors.qualitative.Set2
    cores = {r: paleta[i % len(paleta)] for i, r in enumerate(resp)}
    fig = go.Figure()
    for r in resp:
        sub = d[d['Responsável'] == r]
        duracao = (sub['Fim'] - sub['Início']).dt.total_seconds() * 1000 + 86400000
        fig.add_trace(go.Bar(x=duracao, base=sub['Início'], y=sub['Linha'], orientation='h', width=.70,
            name=r, marker=dict(color=cores[r], line=dict(color='white', width=.6)),
            customdata=list(zip(sub['Atividade'],sub['Início'].dt.strftime('%d/%m/%Y'),sub['Fim'].dt.strftime('%d/%m/%Y'))),
            hovertemplate='<b>%{customdata[0]}</b><br>Início: %{customdata[1]}<br>Fim: %{customdata[2]}<br>Responsável: '+r+'<extra></extra>'))
    if mostrar_rotulos:
        for _, item in d.iterrows():
            fig.add_annotation(x=item['Fim']+pd.Timedelta(days=2), y=item['Linha'], xref='x', yref='y',
                text=item['Responsável'], showarrow=False, xanchor='left', yanchor='middle',
                font=dict(family='Arial', size=10, color='#334155'), bgcolor='rgba(255,255,255,0.65)', borderpad=2)
    for i in range(len(meses)-1):
        atual, proximo = meses[i], meses[i+1]
        if i % 2 == 0:
            fig.add_vrect(x0=atual, x1=proximo, fillcolor='#e9eef5', opacity=.55, line_width=0, layer='below')
        fig.add_vline(x=atual, line_color='#64748b' if atual.month == 1 else '#cbd5e1', line_width=2 if atual.month == 1 else 1)
    fig.add_vline(x=meses[-1], line_color='#cbd5e1', line_width=1)
    posicoes = [meses[i]+(meses[i+1]-meses[i])/2 for i in range(len(meses)-1)]
    rotulos = [f'{MESES[meses[i].month-1]}<br><b>{meses[i].year}</b>' for i in range(len(meses)-1)]
    fig.update_xaxes(type='date', range=[inicio, fim], tickmode='array', tickvals=posicoes, ticktext=rotulos,
        tickangle=0, side='top', showgrid=False, showline=True, linecolor='#94a3b8', tickfont=dict(size=11,color='#334155'), title='')
    fig.update_yaxes(tickmode='array', tickvals=d['Linha'], ticktext=d['Atividade'], range=[len(d)-.5,-.5],
        showgrid=False, title='', tickfont=dict(size=11,color='#243b53'), automargin=True)
    fig.update_layout(title=dict(text='<b>Cronograma Detalhado de Atividades</b><br><sup>Censo Escolar</sup>',x=.5,xanchor='center',font=dict(size=21)),
        height=max(700,len(d)*43+180), template='plotly_white', margin=dict(l=340,r=60,t=130,b=120),
        font=dict(family='Arial',size=11,color='#243b53'), barmode='overlay',bargap=.25,
        legend=dict(title='Responsáveis',orientation='h',x=.5,xanchor='center',y=-.09,font=dict(size=10)),
        plot_bgcolor='white',paper_bgcolor='white',hovermode='closest')
    return fig

if 'tabela' not in st.session_state:
    st.session_state.tabela = original[COLS].copy()

st.title('📅 Cronograma do Censo Escolar')
st.caption('Planejamento de atividades | edição, validação e visualização interativa')
with st.sidebar:
    st.header('Configurações')
    mostrar = st.checkbox('Exibir responsáveis após as barras', value=True)
    arquivo = st.file_uploader('Importar cronograma (CSV ou Excel)',type=['csv','xlsx'])
    if arquivo is not None:
        identificador = (arquivo.name, arquivo.size)
        if st.session_state.get('arquivo_importado') != identificador:
            try:
                bruto = pd.read_csv(arquivo, sep=None, engine='python') if arquivo.name.lower().endswith('.csv') else pd.read_excel(arquivo)
                st.session_state.tabela = validar(bruto)
                st.session_state.arquivo_importado = identificador
                st.rerun()
            except Exception as e:
                st.error(f'Erro na importação: {e}')
    if st.button('Restaurar dados originais'):
        st.session_state.tabela = original[COLS].copy()
        st.session_state.pop('arquivo_importado', None)
        st.rerun()

st.subheader('Editar atividades')
st.info('As alterações são mantidas durante a sessão do navegador. Exporte o CSV para guardar uma versão permanente.')
editado = st.data_editor(st.session_state.tabela, num_rows='dynamic', hide_index=True, use_container_width=True,
    column_config={'Atividade': st.column_config.TextColumn('Atividade', required=True),
                   'Responsável': st.column_config.TextColumn('Responsável'),
                   'Início': st.column_config.DateColumn('Início',format='DD/MM/YYYY',required=True),
                   'Fim': st.column_config.DateColumn('Fim',format='DD/MM/YYYY',required=True)}, key='editor')
try:
    pronto = validar(editado)
    st.session_state.tabela = pronto
    st.success(f'{len(pronto)} atividades válidas | {pronto["Início"].min():%d/%m/%Y} a {pronto["Fim"].max():%d/%m/%Y}')
    figura = grafico(pronto,mostrar)
    st.plotly_chart(figura, use_container_width=True, config={'displaylogo':False,'scrollZoom':True,'responsive':True})
    a,b = st.columns(2)
    with a:
        st.download_button('⬇️ Baixar atividades (CSV)', pronto.to_csv(index=False, date_format='%Y-%m-%d').encode('utf-8-sig'), 'cronograma_censo.csv','text/csv')
    with b:
        st.download_button('⬇️ Baixar gráfico interativo (HTML)',figura.to_html(full_html=True,include_plotlyjs=True).encode('utf-8'), 'cronograma_censo.html','text/html')
except ValueError as e:
    st.error(str(e))
    st.warning('Corrija as linhas indicadas para visualizar e exportar o cronograma.')
