from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path
from langchain_core.documents import Document
import uuid

# define embedding model
embed_model = OllamaEmbeddings(model="mxbai-embed-large")

# define the chroma database to store embeddings
vector_store = Chroma(collection_name='workouts',
                      embedding_function=embed_model,
                      persist_directory='chroma_db')

text_splitter = RecursiveCharacterTextSplitter(separators="---WORKOUT---",
                                               chunk_size=2000,
                                               chunk_overlap=0)

documents = []

p = Path('./structured')
for file in p.glob('*.json'):
    with file.open("r", encoding="utf-8") as f:
        content = f.read()
        chunks = text_splitter.split_text(content)
        for chunk in chunks:
            documents.append(Document(page_content=chunk, metadata={"source": file.name, "title": file.name}))

doc_ids = [str(uuid.uuid4()) for _ in range(len(documents))]

vector_store.add_documents(documents=documents, ids=doc_ids)