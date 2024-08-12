import streamlit as st
import os
import pandas as pd
import locale

# --- Configurações gerais ---

# página do streamlit
st.set_page_config(page_title = 'GRM-AM',
                   page_icon  = ':bar_chart:',
                   layout     = 'wide')

# define localidade para datas
#locale.setlocale(locale.LC_ALL, 'pt_pt.UTF-8')

# path para a base de dados
#path_base_dados = f'c:\\Users\\{os.getlogin()}\\OneDrive - Petros - Fundação Petrobras de Seguridade Social\\GRM_Macro\\Banco de Dados'

# página do streamlit
# st.set_page_config(page_title = 'GRM-AM',
#                    page_icon  = ':bar_chart:',
#                    layout     = 'wide')

st.title("Mercado de Trabalho - PNAD")

# adiciona separação
#st.markdown("---")


# --- Dados ---

# importar dados pnad
df_raw = pd.read_excel(f'dados-pnad.xlsx')
df_raw.set_index('Data', inplace=True)


# --- Valores do Cabeçalho ---
pnad_data_ref = df_raw.index[-1].strftime("%b/%Y")
pnad_taxa_desem = round(df_raw['Desemprego'].iloc[-1], 2)
pnad_taxa_parti = round(df_raw['Participação'].iloc[-1], 1)


left_block, middle_block, right_block = st.columns(3)
with left_block:
    st.subheader("Data ref.: ")
    st.subheader(pnad_data_ref)
with middle_block:
    st.subheader("Taxa de Participação: ")
    st.subheader(f"{pnad_taxa_parti:,}%")
with right_block:
    st.subheader("Taxa de Desemprego: ")
    st.subheader(f"{pnad_taxa_desem:,}%")

# st interpreta o df
st.dataframe(df_raw)

# adiciona separação
st.markdown("---")

