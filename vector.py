import pinecone

import logging
logging.basicConfig(level=logging.DEBUG)

#from langchain.embeddings import OpenAIEmbeddings
#from langchain_community.embeddings import OpenAIEmbeddings
from langchain_openai import OpenAIEmbeddings

def vector_exists(index, vector, namespace=''):
    query_response = index.query(
        vector=vector,
        top_k=10,
        namespace=namespace
    )
    if query_response['matches']:
        # Verifica se a similaridade é alta o suficiente (ajuste conforme necessário)
        similarity_threshold = 0.99
        if query_response['matches'][0]['score'] > similarity_threshold:
            return True
    return query_response['matches'][0]['score'], False

def chunk_to_vector(chunk, embeddings):
    vector_chunk = embeddings.embed_documents(chunk, chunk_size=1000)
    return vector_chunk