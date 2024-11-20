import streamlit as st
import pandas as pd

from pinecone import Pinecone, ServerlessSpec

import logging
logging.basicConfig(level=logging.INFO)

st.write('Pesquisar em notícias')

if 'login' in st.session_state:
    if ( st.session_state['login'] and ( "auth" in st.session_state ) ) or st.session_state.DISABLE_LOGIN:

        data = [
            {"id": "vec1", "text": "A maçã é uma fruta popular conhecida por sua doçura e textura crocante."},
            {"id": "vec2", "text": "A empresa de tecnologia Apple é conhecida por seus produtos inovadores como o iPhone."},
            {"id": "vec3", "text": "Muitas pessoas gostam de comer maçãs como um lanche saudável."},
            {"id": "vec4", "text": "A maça lembra designs elegantes e interfaces amigáveis."},
            {"id": "vec5", "text": "Uma maçã por dia mantém o médico longe, como diz o ditado."},
            {"id": "vec6", "text": "A empresa da maça foi fundada em 1º de abril de 1976, por Steve Jobs, Steve Wozniak e Ronald Wayne como uma parceria."}
        ]

        df = pd.DataFrame(data)

        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)

        pinecone_client = Pinecone()
        index           = pinecone_client.Index(index_name)

        # Convert the text into numerical vectors that Pinecone can index
        embeddings = pinecone_client.inference.embed(
            model="multilingual-e5-large",
            inputs=[d['text'] for d in data],
            parameters={"input_type": "passage", "truncate": "END"}
        )