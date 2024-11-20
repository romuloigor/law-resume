import streamlit as st
import pandas as pd

import logging
logging.basicConfig(level=logging.INFO)

st.write('Pesquisar em notícias')

dados = [
    {"id": "vec1", "texto": "A maçã é uma fruta popular conhecida por sua doçura e textura crocante."},
    {"id": "vec2", "texto": "A empresa de tecnologia Apple é conhecida por seus produtos inovadores como o iPhone."},
    {"id": "vec3", "texto": "Muitas pessoas gostam de comer maçãs como um lanche saudável."},
    {"id": "vec4", "texto": "A maça lembra designs elegantes e interfaces amigáveis."},
    {"id": "vec5", "texto": "Uma maçã por dia mantém o médico longe, como diz o ditado."},
    {"id": "vec6", "texto": "A empresa da maça foi fundada em 1º de abril de 1976, por Steve Jobs, Steve Wozniak e Ronald Wayne como uma parceria."}
]


df = pd.DataFrame(data)

edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)