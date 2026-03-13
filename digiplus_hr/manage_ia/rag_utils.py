import os
from django.conf import settings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

FAISS_STORE_PATH = os.path.join(settings.BASE_DIR, "faiss_index")

# Initialisation différée pour ne pas bloquer au démarrage
_embeddings = None

def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = FastEmbedEmbeddings()
    return _embeddings

def get_vector_store():
    embeddings = get_embeddings()
    if os.path.exists(FAISS_STORE_PATH):
        # Allow dangerous deserialization car le fichier est créé localement par notre code
        return FAISS.load_local(FAISS_STORE_PATH, embeddings, allow_dangerous_deserialization=True)
    return None

def add_document_to_index(company_document):
    """
    Extrait le texte d'un PDF, le découpe et l'ajoute à l'index FAISS local.
    """
    # 1. Charger le fichier PDF
    file_path = company_document.file.path
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Fichier non trouvé: {file_path}")

    loader = PyPDFLoader(file_path)
    documents = loader.load()

    # On ajoute des metadata pour savoir d'où vient ce texte
    for doc in documents:
        doc.metadata["source_id"] = company_document.id
        doc.metadata["title"] = company_document.title

    # 2. Découper en morceaux de 1000 caractères avec chevauchement
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""]
    )
    docs_chunks = text_splitter.split_documents(documents)

    # 3. Vectoriser et stocker
    embeddings = get_embeddings()
    vector_store = get_vector_store()

    if vector_store is None:
        # Créer un nouvel index si c'est le premier document
        vector_store = FAISS.from_documents(docs_chunks, embeddings)
    else:
        # Ajouter à l'index existant
        vector_store.add_documents(docs_chunks)
    
    # 4. Sauvegarder localement
    vector_store.save_local(FAISS_STORE_PATH)


def search_context_for_query(query, k=3):
    """
    Recherche k passages pertinents pour la question posée.
    """
    vector_store = get_vector_store()
    if vector_store is None:
        return "" # Aucun document indexé
        
    results = vector_store.similarity_search(query, k=k)
    context_text = "\n\n---\n\n".join(
        [f"Source: {res.metadata.get('title', 'Document inconnu')}\n{res.page_content}" for res in results]
    )
    return context_text
