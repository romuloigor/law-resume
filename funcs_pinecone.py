import pinecone

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

from langchain.embeddings import OpenAIEmbeddings

def chunk_to_vector(chunk):
    embeddings = OpenAIEmbeddings()
    vector = embeddings.embed(chunk)
    return vector