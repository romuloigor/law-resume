import streamlit as st

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
import vector

import logging
logging.basicConfig(level=logging.INFO)

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

            # Verificar se o índice existe, caso contrário, criar um novo índice
            if index_name not in pinecone_client.list_indexes().names():
                pinecone_client.create_index(
                    name=index_name,
                    dimension=1536,  # Substitua pela dimensão correta dos seus embeddings
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud='aws',  # Substitua pela nuvem correta, se necessário
                        region='us-east-1'  # Substitua pela região correta, se necessário
                    )
                )

        col1, col2 = st.columns(2)
        
        col1.write('Chat')
        col2.write('Envio de PDF')

        with col2:
            uploaded_files = st.file_uploader(
                "Enviar um documento (.pdf) para o banco de dados.", type=("pdf"), accept_multiple_files=True
            )

            if uploaded_files is not None:
                documents = []

                for uploaded_file in uploaded_files:
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

                    #chunks = text_splitter.create_documents([doc.page_content for doc in documents], metadatas=metadatas)
                    chunks = text_splitter.create_documents([doc.page_content for doc in documents], metadatas=[{"file_name": os.path.basename(uploaded_file.name)} for doc in documents])
                
                    # Inserir o vetor no Pinecone se não existir
                    vectorstore_doc = PineconeVectorStore.from_documents(
                        documents=chunks,
                        embedding=embeddings,
                        index_name=index_name,
                        namespace=namespace
                    )

            vectorstore     = PineconeVectorStore(
                index_name  = index_name,
                embedding   = embeddings,
                namespace   = namespace
            )

            retriever = vectorstore.as_retriever(search_type='similarity', search_kwargs={'k': 3, 'namespace': namespace})
            chain     = RetrievalQA.from_chain_type(llm=llm, chain_type='stuff', retriever=retriever)

        with col1:
            st.title("📄 Pergunte aos documentos.")
            id_generator = index.list(namespace=namespace)
            vector_ids = list(id_generator)

            if not vector_ids:
                st.write("Nenhum vetor encontrado no namespace 'default'.")
            else:
                fetch_response = index.fetch(ids=vector_ids[0],namespace=namespace)
                
                #st.write(index_stats)
                #st.write(vector_ids[0])
                #st.write(fetch_response)

                # Exibe os metadados dos vetores
                for vector_id, vector_data in fetch_response['vectors'].items():
                    metadata = vector_data.get('metadata', {})
                    if 'codigo' in metadata:
                        st.write(f"Metadados do vetor {vector_id}: codigo={metadata['codigo']}")
            
            question = st.text_area(
                "Faça uma pergunta pertinente aos documentos inseridos.",
                #placeholder="Crie uma tabela com o número do processos, nome do réu, data hora e local, julgamento simplificado em DEFERIDO ou INDEFERIDO.",
                value="O que é tratado no documento ?",
                disabled=not chain,
            )

            # Mensagens para simular a conversa
            messages = [
                SystemMessage(content="Você é um assistente juríco, que responde as perguntas somente referentes ao documento anexado."),
                HumanMessage(content="Olá Assistente, como você está hoje?"),
                AIMessage(content="Estou bem, obrigado. Como posso ajudar?"),
                HumanMessage(content=question)
            ]

            answer_1 = chain.invoke(messages[3].content)

            st.markdown(answer_1['result'])