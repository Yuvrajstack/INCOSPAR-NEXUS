import os
import re
import json
import numpy as np
from typing import List, Dict, Any, Tuple

# Try importing scikit-learn for high-quality tf-idf vector search fallback
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# Try importing ChromaDB or FAISS if user installs it later
try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

class DocumentLoader:
    """Loads markdown runbooks and configurations from local files."""
    
    def __init__(self, directory_path: str):
        self.directory_path = directory_path

    def load_documents(self) -> List[Dict[str, Any]]:
        documents = []
        if not os.path.exists(self.directory_path):
            os.makedirs(self.directory_path, exist_ok=True)
            
        for filename in os.listdir(self.directory_path):
            if filename.endswith(".md") or filename.endswith(".txt"):
                filepath = os.path.join(self.directory_path, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                documents.append({
                    "source": filename,
                    "content": content
                })
        return documents

class TextChunker:
    """Splits loaded text documents into logical chunks with overlaps."""
    
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def split_document(self, doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        content = doc["content"]
        source = doc["source"]
        
        # Split logically by headers first if available, else by word count
        headers = re.split(r'(?=\n#+\s+)', content)
        chunks = []
        
        for idx, sec in enumerate(headers):
            sec = sec.strip()
            if not sec:
                continue
            
            # Sub-split long sections
            if len(sec) > self.chunk_size:
                words = sec.split()
                sub_chunks = []
                for i in range(0, len(words), self.chunk_size - self.overlap):
                    sub_text = " ".join(words[i:i + self.chunk_size])
                    sub_chunks.append(sub_text)
                for s_idx, sc in enumerate(sub_chunks):
                    chunks.append({
                        "source": source,
                        "chunk_id": f"{source}-h{idx}-s{s_idx}",
                        "content": sc
                    })
            else:
                chunks.append({
                    "source": source,
                    "chunk_id": f"{source}-h{idx}",
                    "content": sec
                })
        return chunks

class LocalVectorDB:
    """
    Unified swappable Vector Database client.
    Supports ChromaDB/FAISS drivers, falling back to a pre-installed
    NumPy and Scikit-Learn Cosine similarity matrix model to run completely offline.
    """
    def __init__(self):
        self.chunks: List[Dict[str, Any]] = []
        self.vectorizer = None
        self.tfidf_matrix = None
        self.chroma_client = None
        self.chroma_collection = None
        
        if CHROMADB_AVAILABLE:
            try:
                # Initialize local ChromaDB client (persistent)
                self.chroma_client = chromadb.PersistentClient(path="data/chroma_db")
                self.chroma_collection = self.chroma_client.get_or_create_collection("runbooks")
                print("ChromaDB persistent vector store initialized.")
            except Exception as e:
                print(f"ChromaDB startup warning: {e}. Falling back to NumPy Vector Store.")
                self.chroma_client = None

    def index_chunks(self, chunks: List[Dict[str, Any]]):
        self.chunks = chunks
        if not chunks:
            return

        # 1. Index using ChromaDB if active
        if self.chroma_collection:
            try:
                ids = [c["chunk_id"] for c in chunks]
                documents = [c["content"] for c in chunks]
                metadatas = [{"source": c["source"]} for c in chunks]
                
                # ChromaDB has built-in sentence-transformers or handles string embedding defaults
                self.chroma_collection.add(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )
                return
            except Exception as e:
                print(f"ChromaDB indexing failed: {e}. Falling back to TF-IDF.")

        # 2. Offline Fallback: TF-IDF Embedding Vectorization
        if SKLEARN_AVAILABLE:
            self.vectorizer = TfidfVectorizer(stop_words='english')
            texts = [c["content"] for c in chunks]
            self.tfidf_matrix = self.vectorizer.fit_transform(texts)
            
    def similarity_search(self, query: str, top_k: int = 3) -> List[Tuple[Dict[str, Any], float]]:
        if not self.chunks:
            return []

        # 1. Search using ChromaDB if active
        if self.chroma_collection:
            try:
                results = self.chroma_collection.query(
                    query_texts=[query],
                    n_results=top_k
                )
                matched = []
                if results and 'documents' in results and results['documents']:
                    docs = results['documents'][0]
                    metas = results['metadatas'][0]
                    ids = results['ids'][0]
                    distances = results['distances'][0] if 'distances' in results else [0.0] * len(docs)
                    
                    for i in range(len(docs)):
                        matched.append(({
                            "chunk_id": ids[i],
                            "content": docs[i],
                            "source": metas[i]["source"]
                        }, round(1.0 - distances[i], 3)))
                return matched
            except Exception as e:
                print(f"ChromaDB query warning: {e}. Falling back to TF-IDF search.")

        # 2. Search using TF-IDF and Cosine similarity fallback
        if SKLEARN_AVAILABLE and self.vectorizer and self.tfidf_matrix is not None:
            query_vec = self.vectorizer.transform([query])
            similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                score = float(similarities[idx])
                if score > 0.05: # Minimum match threshold
                    results.append((self.chunks[idx], round(score, 3)))
            return results
            
        # 3. Keyword intersection fallback if scikit-learn is absent
        results = []
        q_words = set(query.lower().split())
        for chunk in self.chunks:
            c_words = set(chunk["content"].lower().split())
            intersection = q_words.intersection(c_words)
            score = len(intersection) / max(1, len(q_words))
            if score > 0.0:
                results.append((chunk, round(score, 3)))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

class RetrievalEngine:
    """Coordinates loader, chunker and vector DB searches."""
    
    def __init__(self, runbooks_dir: str):
        self.loader = DocumentLoader(runbooks_dir)
        self.chunker = TextChunker()
        self.vector_db = LocalVectorDB()
        self.initialize_index()

    def initialize_index(self):
        docs = self.loader.load_documents()
        all_chunks = []
        for doc in docs:
            all_chunks.extend(self.chunker.split_document(doc))
        self.vector_db.index_chunks(all_chunks)

    def retrieve_context(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        matches = self.vector_db.similarity_search(query, top_k)
        retrieved = []
        for chunk, score in matches:
            retrieved.append({
                "chunk_id": chunk["chunk_id"],
                "source": chunk["source"],
                "content": chunk["content"],
                "score": score
            })
        return retrieved

# Initialize global singleton instance mapping to runbooks directory
rag_retrieval_engine = RetrievalEngine("data/runbooks")
