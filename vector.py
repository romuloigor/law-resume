import pinecone

#Importing OpenAIEmbeddings from langchain.embeddings is deprecated.
from langchain_community.embeddings import OpenAIEmbeddings

def vector_exists(index, vector, namespace=''):
    query_response = index.query(
        vector=vector,
        top_k=1,
        namespace=namespace
    )
    if query_response['matches']:
        # Verifica se a similaridade é alta o suficiente (ajuste conforme necessário)
        similarity_threshold = 0.99
        if query_response['matches'][0]['score'] > similarity_threshold:
            return True
    return False

def chunk_to_vector(chunk, embeddings):
    vector = embeddings.embed_query(chunk.page_content)
    return vector