import streamlit as st
from streamlit_oauth import OAuth2Component
from streamlit_cookies_controller import CookieController

from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings

#Importing OpenAIEmbeddings from langchain.embeddings is deprecated.
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_openai import OpenAIEmbeddings

from langchain_pinecone import PineconeVectorStore

from langchain_community.document_loaders import PyMuPDFLoader

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.schema import SystemMessage, HumanMessage, AIMessage

from pinecone import Pinecone, ServerlessSpec
import vector

import yaml
import os, time
import base64
import json
import fitz

import tempfile
import login_google

from io import BytesIO
from openai import OpenAI

import logging
logging.basicConfig(level=logging.INFO)

# Show title and description.
st.set_page_config(page_title = 'CTC-Tech LLM App', page_icon = 'media/ctc.png',layout="wide")

controller = CookieController()

with st.sidebar:
    st.session_state["login"] = login_google.login(controller)
    
    if st.session_state['login'] and ( "auth" in st.session_state ):
        st.write("Logged in")

        with st.spinner("Loading..."):
            os.environ['OPENAI_API_KEY']   = st.secrets.store_api_key.OPENAI_API_KEY
            os.environ['PINECONE_API_KEY'] = st.secrets.store_api_key.PINECONE_API_KEY
            index_name                     = st.session_state["auth"].split('@')[0]

            pinecone_client = Pinecone()
            index           = pinecone_client.Index(index_name)

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

            vectorstore     = PineconeVectorStore(
                index_name  = index_name,
                embedding   = embeddings
            )

            retriever       = vectorstore.as_retriever(search_type='similarity', search_kwargs={'k': 3})

            chain           = RetrievalQA.from_chain_type(llm=llm, chain_type='stuff', retriever=retriever)

            # Let the user upload a file via `st.file_uploader`.
            uploaded_files = st.file_uploader(
                "Enviar um documento (.pdf) para o banco de dados.", type=("pdf"), accept_multiple_files=True
            )

            if uploaded_files is not None:
                documents = []

                for uploaded_file in uploaded_files:            
                    # To read file as bytes:
                    bytes_data = uploaded_file.getvalue()

                    # Converte bytes_data para um objeto de arquivo em memória
                    file_like_object = BytesIO(bytes_data)

                    # Abre o PDF com PyMuPDF
                    pdf_document = fitz.open(stream=file_like_object, filetype="pdf")

                    # Salvar o documento em um arquivo temporário
                    with tempfile.NamedTemporaryFile(delete=True, suffix='.pdf') as temp_file:
                        # Salva o pymupdf.Document no arquivo temporário
                        pdf_document.save(temp_file.name)

                        # Agora você pode usar PyMuPDFLoader com o caminho do arquivo temporário
                        loader = PyMuPDFLoader(temp_file.name)
                        documents.extend(loader.load())
                        
                    text_splitter = RecursiveCharacterTextSplitter(
                        chunk_size=1000,  
                        chunk_overlap=100,
                        length_function=len
                    )

                    chunks = text_splitter.create_documents([doc.page_content for doc in documents])
                    #st.write(chunks)
                    
                    #vector_chunk = vector.chunk_to_vector(chunk=chunks[0].page_content, embeddings=embeddings)
                    #st.write(vector_chunk[0])

                    # Verificar se o vetor já existe
                    #similarity, existe = vector.vector_exists(index=index, vector=vector_chunk[0])
                    #if existe:
                    #    st.write(f'vector_chunk já existe! {similarity}')
                    #else:
                    #    st.write(f'vector_chunk não existe! {similarity}')

                    # Inserir o vetor no Pinecone se não existir
                    vector_docs = vectorstore.from_documents(chunks, embeddings, index_name=index_name)

            #st.write(pinecone_client.describe_index(index_name))
            #st.write(pinecone_client.list_collections())
            st.write(index.describe_index_stats())

            st.success('Página carregada!')

# Check if 'key' already exists in session_state
# If not, then initialize it
if 'login' in st.session_state:
    if st.session_state['login'] and ( "auth" in st.session_state):
        #col1, col2 = st.columns(2)
        
        #col1.write('Perguntas')
        #col2.write('Dados')

        #with col1:
        st.title("📄 Pergunte aos documentos.")
        
        question = st.text_area(
            "Faça uma pergunta pertinente aos documentos inseridos.",
            #placeholder="Crie uma tabela com o número do processos, nome do réu, data hora e local, julgamento simplificado em DEFERIDO ou INDEFERIDO.",
            value="Crie uma tabela com o número do processos, nome do réu, data hora e local, se foi julgado SIM ou NÃO, se não existir informação deixe em branco.",
            disabled=not chain,
        )

        # Mensagens para simular a conversa
        messages = [
            SystemMessage(content="Você é um assistente juríco, que responde as perguntas somente em Portugues do Brasil."),
            HumanMessage(content="Olá Assistente, como você está hoje?"),
            AIMessage(content="Estou bem, obrigado. Como posso ajudar?"),
            HumanMessage(content=question)
        ]

        answer_1 = chain.invoke(messages[3].content)

        st.markdown(answer_1['result'])

        #with col2:
            #st.write("RESULT")