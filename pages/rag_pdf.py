import streamlit as st

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

def list_pdf(index, namespace):
    id_generator = index.list(namespace=namespace)

    vector_ids = list(id_generator)

    fetch_response = index.fetch(ids=vector_ids[0], namespace=namespace)
    
    list_file_name=[]

    for vector_id, vector_data in fetch_response['vectors'].items():
        metadata = vector_data.get('metadata', {})
        if 'file_name' in metadata:
            list_file_name.append(f"{metadata['file_name']}")

    list_file_name_unique = list(set(list_file_name))
    
    return list_file_name_unique 

if 'login' in st.session_state:
    if ( st.session_state['login'] and ( "auth" in st.session_state ) ) or st.session_state.DISABLE_LOGIN:
        
        with st.spinner("Loading..."):
            os.environ['OPENAI_API_KEY']   = st.secrets.store_api_key.OPENAI_API_KEY
            os.environ['PINECONE_API_KEY'] = st.secrets.store_api_key.PINECONE_API_KEY
            
            if st.session_state.DISABLE_LOGIN:
                st.write("Logged in DEV MODE")
                index_name = 'dev'
            else:
                st.write("Logged in")
                index_name = st.session_state["auth"].split('@')[0].replace('.','-')

            namespace = 'default'

            pinecone_client = Pinecone()
            index           = pinecone_client.Index(index_name)
            index_stats     = index.describe_index_stats()
            embeddings      = OpenAIEmbeddings(model='text-embedding-ada-002')
            llm             = ChatOpenAI(model='gpt-3.5-turbo-16k', temperature=0.2)

            if index_name not in pinecone_client.list_indexes().names():
                pinecone_client.create_index(
                    name=index_name,
                    dimension=1536,
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud='aws',
                        region='us-east-1'
                    )
                )

        col1, col2 = st.columns(2)
        
        col1.write('Chat')
        col2.write('Envio de PDF')

        with col2:
            list_file_name_unique = list_pdf(index, namespace)

            st.write(f"Lista de arquivos já enviados {list_file_name_unique}!")

            uploaded_files = st.file_uploader("Enviar um documento (.pdf)", type=("pdf"), accept_multiple_files=True)

            if uploaded_files is not None:
                documents = []

                for uploaded_file in uploaded_files:

                    if not uploaded_file.name in list_file_name_unique:

                        bytes_data = uploaded_file.getvalue()

                        file_like_object = BytesIO(bytes_data)

                        pdf_document = fitz.open(stream=file_like_object, filetype="pdf")

                        with tempfile.NamedTemporaryFile(delete=True, suffix='.pdf') as temp_file:
                            pdf_document.save(temp_file.name)

                            loader = PyMuPDFLoader(temp_file.name)

                            documents.extend(loader.load())
                            
                        text_splitter = RecursiveCharacterTextSplitter(
                            chunk_size=1000,  
                            chunk_overlap=100,
                            length_function=len
                        )

                        data_hora = datetime.now().strftime('%Y%m%d_%H%M')
                        chunks = text_splitter.create_documents([doc.page_content for doc in documents], metadatas=[{'file_name': os.path.basename(uploaded_file.name), 'date_time': data_hora } for doc in documents])
                    
                        vectorstore_doc = PineconeVectorStore.from_documents(
                            documents=chunks,
                            embedding=embeddings,
                            index_name=index_name,
                            namespace=namespace
                        )
                    else:
                        st.write(f"Arquivo {uploaded_file.name} faz parte da lista de 'já enviados!'")

            vectorstore     = PineconeVectorStore(
                index_name  = index_name,
                embedding   = embeddings,
                namespace   = namespace
            )

            retriever = vectorstore.as_retriever(search_type='similarity', search_kwargs={'k': 3, 'namespace': namespace})
            chain     = RetrievalQA.from_chain_type(llm=llm, chain_type='stuff', retriever=retriever)

        with col1:
            st.title("📄 Pergunte aos documentos.")
            
            question = st.text_area(
                "Faça uma pergunta pertinente aos documentos inseridos.",
                #placeholder="Crie uma tabela com o número do processos, nome do réu, data hora e local, julgamento simplificado em DEFERIDO ou INDEFERIDO.",
                value="O que é tratado no documento ?",
                disabled=not chain,
            )

            messages = [
                SystemMessage(content="Você é um assistente, que responde as perguntas somente referentes ao documentos anexados."),
                HumanMessage(content="Olá Assistente, como você está hoje?"),
                AIMessage(content="Estou bem, obrigado. O que você gostaria de saber sobre o documento anexado?"),
                HumanMessage(content=question)
            ]

            answer_1 = chain.invoke(messages[3].content)

            st.markdown(answer_1['result'])