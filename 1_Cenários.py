import streamlit as st
import pandas as pd
import datetime as dt
from copy import deepcopy
import plotly.express as px
import io


# ---- PONTOS DO CÓDIGO NÃO-AUTOMATIZADOS.
# 1- dict_cenarios: nome e probabilidade dos cenários;
# 2- função get_excel_cenarios: largura do excel;
# 3- função tratar_base: ao multiplicar valores por 100 para deixar na mesma base;
# 4- dict_data_ref: data do último valor divulgado de cada indicador;
# 5- data_ref_ultim_atual: data da última atualização do cenário.



# ---- VARIÁVEIS GLOBAIS ---- 

# página do streamlit
st.set_page_config(page_title = 'GRM-AM',
                   page_icon  = ':bar_chart:',
                   layout     = 'wide')

# remove menu de opções
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True
)
# remove botão de depl
st.markdown(
    r"""
    <style>
    .stDeployButton {
            visibility: hidden;
        }
    </style>
    """, unsafe_allow_html=True
)

#GithubIcon {
  visibility: hidden;
}

path_bd_cenarios = "C:\\Users\\Mateus\\Documents\\1 doc (esse aqui)\\repository\\Cenário Macro (GRM_AM).xlsx"

# data da última atualização de cenário
data_ref_ultim_atual = dt.date(2024,8,13)

# 
dict_cenarios = {
    'Base': ['Inflação Global Resiliente', '45%'],
    'Alternativo': ['Hard Landing US', '20%'],
    'Pessimista': ['Desancoragem das Expectativas', '35%']
}

# data do último dado disponível para cada indicador 
dict_data_ref = {
    'CDI': '2024-08-01',
    'IGP-M': '2024-07-01',
    'IPCA': '2024-07-01',
    'R$/US$': '2024-07-01',
    'Risco-país': '2024-07-01',
    'SELIC Meta': '2024-08-01',
    'PIB': '2024-03-01'
}



# ---- COLETA + TRATAMENTO DA BASE
# esta seção pode ir para um script próprio

# @st.cache_data
@st.cache_resource
class DashCenarios:
    
    def __init__(self, df_structure='long'):
        self.df_structure = df_structure
        pass
    
    @staticmethod
    def tratar_base(df: pd.DataFrame, freq: str, type: str):
        """
        Trata a aba do excel e retorna um dataframe no formato long.
        Args:
            df (pd.DataFrame): recebe o df coletado do excel
            freq (str): recebe a frequencia que é também o nome da aba do excel
        Returns:
            _type_: dict onde cada chave é uma aba do excel
        """
        # lista com indicadores macro a partir das colunas do excel
        df_raw_indic = [
            name_column for name_column in df.columns.unique() 
            if all(substring not in name_column for substring in ['Unnamed', '.1', '.2', 'Média'])
            ]

        # trata nome do primeiro nivel da coluna (indicadores macro)
        list_column_name = ['Data']
        list_column_names = df_raw_indic[1:]
        list_column_names_new = [i for i in list_column_names for _ in range(3)]

        df_temp = deepcopy(df)

        # nomeia colunas
        df_temp.columns = list_column_name + list_column_names_new

        # define coluna como index
        df_temp.set_index('Data', inplace=True)

        # trata nome do segundo nivel da coluna (cenarios)
        columns = [*zip(tuple(df_temp.columns.values), tuple(df_temp.iloc[0,:].values))]
        df_temp.columns = pd.MultiIndex.from_tuples(columns)
        df_temp.drop(index=df_temp.index[0], axis=0, inplace=True)

        # transforma df em long
        df_final = pd.melt(df_temp, ignore_index=False)
        # nomes para novas colunas
        columns_long = ['Indicador', 'Cenário', 'Valor']
        df_final.columns = columns_long
        # ordena o dataframe
        df_final.sort_values(['Data', 'Indicador', 'Cenário'], inplace=True)

        # trata tipo da coluna (Valor)
        df_final = df_final.astype({'Valor': 'float32'})
        # multiplica a coluna Valor por 100 para visualização
        df_final.loc[df_final['Indicador'].isin(['CDI', 'IGP-M', 'IPCA', 'SELIC Meta']), 'Valor'] = df_final.loc[df_final['Indicador'].isin(['CDI', 'IGP-M', 'IPCA', 'SELIC Meta']), 'Valor'] * 100
        # arredonda a coluna Valor para 2 casas decimais
        df_final['Valor'] = df_final['Valor'].round(2)

        # cria coluna com a frequencia
        df_final['Frequência'] = freq
        
        if type == 'wide':
            df_final = df_final.pivot_table(index=['Data'], columns=['Indicador', 'Cenário'], values=['Valor'])

        elif type == 'long':
            pass
        
        return df_final
        
    
    def get_excel_cenario(self):
        """
        Coleta os cenários do excel de acordo com os parametros e os números de abas;
        Aplica a função tratar_base.
        
        Returns:
            _type_: nested dict com cada aba do excel
        """
        # lê o excel
        excel_raw = pd.ExcelFile("Cenário Macro (GRM_AM).xlsx")
        
        # coleta o nome das abas (que são as frequencias)
        nomes_abas = excel_raw.sheet_names[:3]
        
        # parametros da coleta do excel: (linhas para pular, até qual coluna filtrar)
        params = [(2,19), (0,22), (0,22)]
        
        # une os parametros acima (linhas para pular, até qual coluna filtrar) com a frequencia (nome da aba do excel)
        dict_frequencia = {freq: params[i] for i, freq in enumerate(nomes_abas)}

        # coleta as sheets do excel, aplica a função de tratar_base e gera um dict com um dataframe para cada frequencia/sheet
        dict_df = {nomes_abas: 
            DashCenarios.tratar_base(
                df=pd.read_excel(excel_raw, sheet_name=nomes_abas, skiprows=param[0]).iloc[:,:param[1]],
                freq=nomes_abas, type=self.df_structure)
            for nomes_abas, param in dict_frequencia.items()
            }
        
        return dict_df


# aplica a class para coleta e tratamento da base de dados em formato long
dict_df_geral_wide = DashCenarios(df_structure='wide').get_excel_cenario()
# drop o primeiro level das colunas
for key in dict_df_geral_wide:
    dict_df_geral_wide[key].columns = dict_df_geral_wide[key].columns.droplevel(0)

# aplica a class para coleta e tratamento da base de dados em formato long
dict_df_geral_long = DashCenarios(df_structure='long').get_excel_cenario()
# une os dataframes do dict
df_geral_long = pd.concat(dict_df_geral_long, axis=0)
# drop o primeiro level do index
df_geral_long.index = df_geral_long.index.droplevel(0)


# trata os dados acima para datetime
dict_data_ref = {indicador: pd.to_datetime(data_corte) for indicador, data_corte in dict_data_ref.items()}
# função para criar coluna de Realizado e Projeção 
def define_status(row):
    # atribui a um objeto o valor da linha na coluna 'Indicador'
    indicador = row['Indicador']
    # atribui a um objeto a data de corte presente no dict a partir do objeto acima
    data_corte = dict_data_ref[indicador]
    # name aqui é o index, então compara o index de cada linha com a data do dict
    if row.name > data_corte:
        return 'Projeção'
    else:
        return 'Realizado'
df_geral_long['Status'] = df_geral_long.apply(define_status, axis=1)



# ---- STREAMLIT ----

# --- SIDEBAR
def config_sidebar(df, dict_cenarios):
    
    # título do sidebar
    st.sidebar.header("Pesquisa:")
    
    # filtro para selecionar data
    col_1, col_2 = st.sidebar.columns(2)
    with col_1:
        start_year = st.selectbox(
            'Ano inicial:',
            df.index.year.unique(),
            index=list(df.index.year.unique()).index(dt.date.today().year),
            key='start_year'
            )
        # end_month = st.selectbox(
        #     'Selecione um período:',
        #     df.index.month.unique(),
        #     key='end_month'
        #     )
    with col_2:
        start_month = st.selectbox(
            "Mês inicial:",
            df.index.month.unique(),
            index=0,
            key='start_month'
            )
        # end_year = st.selectbox(
        #     'Selecione um período:',
        #     df.index.year.unique(),
        #     key='end_year'
        #     )

    # filtro para selecionar cenário
    sb_cenario = st.sidebar.selectbox(
        "Selecione o Cenário:",
        options=[f"({key}) {value[0]}" if key == 'Base' else value[0] for key, value in dict_cenarios.items()],
        index=0)
    
    # filtro para selecionar período
    sb_frequencia = st.sidebar.selectbox(
        "Selecione a Frequência:",
        options=df['Frequência'].unique(),
        index=0)
    
    # filtro para selecionar indic
    sb_indicador = st.sidebar.multiselect(
        "Selecione o Indicador:",
        options=df['Indicador'].unique(),
        default=df.loc[df['Frequência']==sb_frequencia]['Indicador'].unique())
    
    return sb_cenario, sb_frequencia, sb_indicador, start_year, start_month # start_date, end_date

# sb_cenario, sb_frequencia, sb_indicador, start_year, end_month, end_year, start_month #start_date, end_date
sb_cenario, sb_frequencia, sb_indicador, start_year, start_month = config_sidebar(df_geral_long, dict_cenarios)

sb_cenario = [key for key, value in dict_cenarios.items() if value[0] in sb_cenario][0]

df_selection = (
    df_geral_long
    .loc[
        (df_geral_long['Cenário'] == sb_cenario) & 
        (df_geral_long['Frequência'] == sb_frequencia) & 
        (df_geral_long['Indicador'].isin(sb_indicador)) & 
        (df_geral_long.index >= pd.to_datetime(dt.date(start_year, start_month, 1))) & 
        (df_geral_long.index <= pd.to_datetime(dt.date(2026,12,1)))
        ]
    )



# BOTAO PARA DOWNLOAD
# @st.cache_data
buffer = io.BytesIO() #"C:\\Users\\ps21820\\Downloads\\cenarios.xlsx"
with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
    
    dict_df_geral_wide['Mensal'].to_excel(writer, sheet_name='Mensal')
    dict_df_geral_wide['Trimestral'].to_excel(writer, sheet_name='Trimestral')
    dict_df_geral_wide['Anual'].to_excel(writer, sheet_name='Anual')
    writer.close()
    
    st.sidebar.download_button(
        label="Download Cenários",
        data=buffer,
        file_name="cenarios.xlsx",
        # mime="application/vnd.ms-excel"
        )



# --- HEADER

# título da página
st.title("Cenários Macroeconômicos",
         anchor=False)


# --- SUBHEADER
def style_subheader(text):
    return f"<h2 style='font-size:20px; color: black;'>{text}</h2>"

# header da página
col1, col2, col3 = st.columns(3)
with col1:
    # título do subheader
    st.markdown(
        style_subheader(f"{dict_cenarios[sb_cenario][0]} ({sb_cenario})"),
        unsafe_allow_html=True)
with col2:
    # título do subheader
    st.markdown(
        style_subheader(f"Probabilidade: {dict_cenarios[sb_cenario][1]}"),
        unsafe_allow_html=True)
with col3:
    # título do subheader
    st.markdown(
        style_subheader(f"Última atualização: {data_ref_ultim_atual}"),
        unsafe_allow_html=True)

# st.subheader(f"Cenário {sb_cenario}: {dict_cenarios[sb_cenario][0]} ({dict_cenarios[sb_cenario][1]}) - Dado {sb_frequencia}",
#          anchor=False)


# --- FIGURAS

# tabela inicial
# def table_1():
    
# converte para formato wide
df_wide = df_selection.pivot_table(index=df_selection.index, columns=['Indicador'], values=['Valor'])
# drop primeiro nivel das colunas
df_wide.columns = df_wide.columns.droplevel(0)

# função 
def destacar_projecao(coluna):
    # pega a data do dicionario a partir do nome da coluna da linha
    cutoff = dict_data_ref[coluna.name]
    # compara se a data no index é maior que a data do dicionário
    is_greater = pd.to_datetime(coluna.index) > pd.to_datetime(cutoff)
    # aplica cor se valor TRUE
    return ['background-color: #D1E1DE' if v else '' for v in is_greater]

# formatação da tabela
df_inicial = df_wide.style.format(precision=2, thousands='.', decimal=',')
for indicador in df_inicial.columns:
    df_inicial = df_inicial.apply(destacar_projecao, subset=[indicador])

st.dataframe(
    df_inicial,
    column_config={
        "Data": st.column_config.DateColumn(format="MM/YYYY"),
        },
    use_container_width=True,
    height=350,
    width=800
    )
# table_1()

st.markdown("---")

# gráficos
left_column, right_column = st.columns(2)
for indicador in sb_indicador:
    if indicador in ['CDI']:
        pass
    elif indicador in ['SELIC Meta', 'IPCA', 'R$/US$', 'Risco-país', 'PIB', 'IGP-M']:
        # tratamento/filtragem para o plot.
        # se quiser que a seleção do gráfico seja igual a seleção da tabela: usar o df_selection e só indicar qual o Indicador, de resto filtra sozinho.
        df_1 = (
        # df_selection
        df_geral_long
        .loc[
            (df_geral_long['Cenário'] == sb_cenario) & 
            (df_geral_long['Frequência'] == sb_frequencia) &
            # (df_geral_long.index >= pd.to_datetime(start_date)) & 
            # (df_geral_long.index <= pd.to_datetime(end_date)) &
            (df_geral_long['Indicador'] == str(indicador)) 
            ]
        )
        
        if indicador in ['IPCA', 'IGP-M', 'PIB'] or sb_frequencia == 'Anual':
            # cria a figura para o plot
            fig = px.bar(
                df_1,
                x=df_1.index,
                y='Valor',
                color='Status',
                color_discrete_sequence=["#042b48", "#6FA399"],
                title=str(indicador)
            )
        else:
            # cria a figura para o plot
            fig = px.line(
                df_1,
                x=df_1.index,
                y='Valor',
                color='Status',
                color_discrete_sequence=["#042b48", "#6FA399"],
                title=str(indicador)
            )
            
        fig.update_xaxes(
            rangeslider_visible=True,
            title='')
            
        fig.update_yaxes(
            title='')
        
        fig.update_layout(legend=dict(
            title='',
            orientation='h',
            x=0.3))
        
        idx = sb_indicador.index(indicador)
        
        if idx % 2 == 0:
            left_column.plotly_chart(fig, use_container_width=True)
        else:
            right_column.plotly_chart(fig, use_container_width=True)
    else:
        pass













# # --- CRIANDO NOVAS COLUNAS PARA SALVAR BASE
# df_geral_long_save = deepcopy(df_geral_long)
# dict_cenarios

# df_geral_long_save.loc[df_geral_long_save['Cenário'] == list(dict_cenarios)[0], 'Probabilidade'] = dict_cenarios[list(dict_cenarios)[0]][1]
# df_geral_long_save.loc[df_geral_long_save['Cenário'] == list(dict_cenarios)[1], 'Probabilidade'] = dict_cenarios[list(dict_cenarios)[1]][1]
# df_geral_long_save.loc[df_geral_long_save['Cenário'] == list(dict_cenarios)[2], 'Probabilidade'] = dict_cenarios[list(dict_cenarios)[2]][1]

# df_geral_long_save.loc[df_geral_long_save['Cenário'] == list(dict_cenarios)[0], 'Título'] = dict_cenarios[list(dict_cenarios)[0]][0]
# df_geral_long_save.loc[df_geral_long_save['Cenário'] == list(dict_cenarios)[1], 'Título'] = dict_cenarios[list(dict_cenarios)[1]][0]
# df_geral_long_save.loc[df_geral_long_save['Cenário'] == list(dict_cenarios)[2], 'Título'] = dict_cenarios[list(dict_cenarios)[2]][0]

# df_geral_long_save['last_update'] = pd.to_datetime(data_ref_ultim_atual, format='YYYYMMDD')


# # MELHORANDO PROCESSO ACIMA
# def define_proba(row):
#     # atribui a um objeto o valor da linha na coluna 'Indicador'
#     cenario = row['Cenário']
#     # atribui a um objeto a data de corte presente no dict a partir do objeto acima
#     dict_cenarios_values = dict_cenarios[cenario][1]
#     # name aqui é o index, então compara o index de cada linha com a data do dict
#     if cenario == dict_cenarios_values:
#         return dict_cenarios_values
#     else:
#         pass
# df_geral_long_save['Título'] = df_geral_long.apply(define_status, axis=1)
# df_geral_long_save['Probabilidade'] = df_geral_long.apply(define_proba, axis=0)



# # --- EXPORTAR CENÁRIOS
# import os
# path_base_dados = f'c:\\Users\\{os.getlogin()}\\OneDrive - Petros\\GRM_Macro\\Banco de Dados'
# if not os.path.exists(path_base_dados):
#     path_base_dados = f'c:\\Users\\{os.getlogin()}\\OneDrive - Petros - Fundação Petrobras de Seguridade Social\\GRM_Macro\\Banco de Dados'

# # to excel
# df_geral_long_save.to_csv(f"{path_base_dados}\\{data_ref_ultim_atual.strftime('%Y%m%d')}_cenario.csv")

# # to parquet
# import pyarrow as pa
# import pyarrow.parquet as pq
# # transforma de pandas em parquet
# df_geral_long_save_pq = pa.Table.from_pandas(df_geral_long_save)
# pq.write_table(
#     table = df_geral_long_save_pq,
#     where = f"{path_base_dados}/{data_ref_ultim_atual.strftime('%Y%m%d')}_cenario.parquet"
#     )
# novo_cenario_pq = pq.read_table(f"{path_base_dados}/{data_ref_ultim_atual.strftime('%Y%m%d')}_cenario.parquet")
# # transforma do parquet para pandas
# novo_cenario_pd = novo_cenario_pq.to_pandas()













############################################  ############################################

# datas não utilizadas
# data_ref = dt.date.today() - relativedelta(months=1)
# data_ref = dt.date(data_ref.year, data_ref.month, 1)
# data_ref_lag_24 = dt.date.today() - relativedelta(months=24)
# data_ref_lag_24 = dt.date(data_ref_lag_24.year, data_ref_lag_24.month, 1)

# --- tentativa de remover ícone anchor do subheader
# hide_anchor_link_css = """
# <style>
# h1 > a:first-child, h2 > a:first-child, h3 > a:first-child, h4 > a:first-child, h5 > a:first-child, h6 > a:first-child {
#     display: none;
# }
# </style>
# """
# st.markdown(hide_anchor_link_css, unsafe_allow_html=True)

# --- def to plot
# def plot_1():
#     # tratamento/filtragem para o plot    
#     # se quiser que a seleção do gráfico seja igual a seleção da tabela:
#     # usar o df_selection e só indicar qual o Indicador, de resto filtra sozinho.
#     df_1 = (
#     # df_selection
#     df_geral_long
#     .loc[
#         (df_geral_long['Cenário'] == sb_cenario) & 
#         (df_geral_long['Frequência'] == sb_frequencia) & 
#         (df_geral_long['Indicador'] == 'SELIC Meta') & 
#         (df_geral_long.index >= pd.to_datetime(start_date)) & 
#         (df_geral_long.index <= pd.to_datetime(end_date))
#         ]
#     )
    
#     # cria a figura para o plot
#     fig = px.line(
#         df_1,
#         x=df_1.index,
#         y='Valor',
#         color='Status',
#         title='SELIC Meta'
#     )
    
#     fig.update_xaxes(rangeslider_visible=True)
#     # fig.show()
#     # chama o plot no streamlit
#     st.plotly_chart(fig, use_container_width=True)
    



# --- tentativa de realçar projeções a partir de um df em formato long

# # # try 1
# def destacar_projecao(row):
#     if row['Status'] == 'projeção':
#         return ['background-color: yellow' if col == 'Valor' else '' for col in row.name]
#     else:
#         return [''] * len(row)
# df_selection_style = df_selection.style.apply(destacar_projecao, axis=1)


# # # try 1
# def destacar_projecao(value):
#     return ['background-color: yellow' if status == 'projeção' else '' for status in value]
# df_selection_style = df_selection.style.apply(destacar_projecao, subset=['Valor'], axis=0)


# # # try 2
# df_inicial = df_selection.pivot_table(index=['Data'], columns=['Indicador'], values=['Valor'])
# def destacar_projecao(s):
#     return ['background-color: yellow' if v == 'projeção' else '' for v in s]
# df_inicial = df_selection.style.apply(destacar_projecao, subset=['Status'])


# # # try 3
# def highlight_projection(s):
#     if s.name.startswith('valor') and s.index[1].endswith('projeção'):
#         return ['background-color: yellow'] * len(s)
#     else:
#         return [''] * len(s)

# # Aplicando o estilo
# styled_df = df_wide.style.apply(highlight_projection, axis=1)
# - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - 
