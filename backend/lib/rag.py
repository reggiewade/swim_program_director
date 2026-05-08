from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

# RAG retrieval function to get relevant workouts based on a query.
def retrieve_workouts(query: str, k: int = 3):
    embed_model = OllamaEmbeddings(model="mxbai-embed-large")
    vector_store = Chroma(collection_name='workouts',
                      embedding_function=embed_model,
                      persist_directory='lib/chroma_db')
    query_embed = embed_model.embed_query(query)
    peek = vector_store.get(limit=2)
    return vector_store.similarity_search_by_vector(embedding=query_embed, k=k)