import streamlit as st
import pandas as pd

from datetime import datetime
from io import BytesIO
import fitz
import tempfile
import os, time
import base64
import json
import yaml

from openai import OpenAI

from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings

from langchain_community.document_loaders import PyMuPDFLoader

from langchain_pinecone import PineconeVectorStore
from langchain.text_splitter import RecursiveCharacterTextSplitter

from langchain.chains import RetrievalQA
from langchain.schema import SystemMessage, HumanMessage, AIMessage

from pinecone import Pinecone, ServerlessSpec

import logging
logging.basicConfig(level=logging.INFO)

def list_news(index, namespace):
    id_generator = index.list(namespace=namespace)

    vector_ids = list(id_generator)
    
    list_news=[]
    
    if len(vector_ids) > 0:
        fetch_response = index.fetch(ids=vector_ids[0], namespace=namespace)

        for vector_id, vector_data in fetch_response['vectors'].items():
            metadata = vector_data.get('metadata', {})
            list_news.append(metadata)
    
    return list_news

def delete_news(index, namespace):
    id_generator = index.list(namespace=namespace)

    vector_ids = list(id_generator)
    
    if len(vector_ids) > 0:
        delete_response = index.delete(ids=vector_ids[0], namespace=namespace)
    
    return len(vector_ids)

if 'login' in st.session_state:
    if ( st.session_state['login'] and ( "auth" in st.session_state ) ) or st.session_state.DISABLE_LOGIN:
        
        col1, col2 = st.columns([5, 1])
        
        col1.write('Chat')
        col2.write('Envio das notícias!')

        with col1:
            with st.spinner("Loading..."):
                os.environ['OPENAI_API_KEY']   = st.secrets.store_api_key.OPENAI_API_KEY
                os.environ['PINECONE_API_KEY'] = st.secrets.store_api_key.PINECONE_API_KEY
                
                if st.session_state.DISABLE_LOGIN:
                    st.write("Logged in DEV MODE")
                    index_name = 'dev-1024'
                else:
                    st.write("Logged in")
                    index_name = st.session_state["auth"].split('@')[0].replace('.','-')

                namespace = 'default'
                
                pinecone_client = Pinecone()
                index           = pinecone_client.Index(index_name)

                data = list_news(index, namespace)

                data_editor_options = {
                    "column_config": {
                        "id": st.column_config.NumberColumn(
                            "ID",
                            help="ID",
                            width=100,
                        ),
                        "text": st.column_config.TextColumn(
                            "Text",
                            help="Content",
                            width=1000,
                        ),
                        "action": st.column_config.CheckboxColumn(
                            "Update?",
                            help="Update?"
                        )
                    },
                    "use_container_width": False,
                    "num_rows": "dynamic"
                }

                df = pd.DataFrame(data)
                edited_df = st.data_editor(df, **data_editor_options)
                
                embeddings = pinecone_client.inference.embed(
                    model="multilingual-e5-large",
                    inputs=[d['text'] for d in data],
                    parameters={"input_type": "passage", "truncate": "END"}
                )

                #st.write(embeddings)

                data_hora = datetime.now().strftime('%Y%m%d_%H%M')

                records = []
                id = 1
                for d, e in zip(data, embeddings):
                    records.append({
                        "id": id,
                        "values": e['values'],
                        "metadata": {'text': d['text'], 'type': 'news', 'date_time': data_hora }
                    })
                    id += 1

                question = st.text_area(
                    "Faça uma pergunta pertinente as noticias.",
                    #placeholder="Ajuda!",
                    value="Tell me about the tech company known as Apple.",
                    disabled=False,
                )

                st.write(question)

                query_embedding = pinecone_client.inference.embed(
                    model="multilingual-e5-large",
                    inputs=[question],
                    parameters={
                        "input_type": "query"
                    }
                )

                results = index.query(
                    namespace=namespace,
                    vector=query_embedding[0].values,
                    top_k=3,
                    include_values=False,
                    include_metadata=True
                )

                st.write(results)

        with col2:
            if st.button("Delete news"):
                number_delete_news = delete_news(index, namespace)
                st.write(f"news deleted: {number_delete_news}")

            if st.button("Insert news"):
                index.upsert(vectors=records,namespace=namespace)
            
            if st.button("List news"):
                news = list_news(index, namespace)
                st.write(f"list news: {news}")

            if st.button('Ir para Noticias'):
                st.switch_page('pages/rag_news.py')

            if st.button('Ir para Documentos'):
                st.switch_page('pages/rag_pdf.py')