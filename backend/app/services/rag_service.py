import faiss
import os
import pickle


class RAGService:
    def __init__(self):
        self.model = None
        self.index = None
        self.metadata = []

        self.index_path = "app/data/faiss_index/index.faiss"
        self.meta_path = "app/data/faiss_index/meta.pkl"
        self.model_name = "all-MiniLM-L6-v2"

        self.load()

    def _load_model(self):
        if self.model is None:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)

    def load(self):
        self._load_model()
        if os.path.exists(self.index_path) and os.path.exists(self.meta_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.meta_path, "rb") as f:
                self.metadata = pickle.load(f)
        elif os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            self.metadata = []
        else:
            self.index = faiss.IndexFlatIP(384)
            self.metadata = []

    def save(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "wb") as f:
            pickle.dump(self.metadata, f)

    def add_documents(self, docs):
        self._load_model()
        texts = [doc["text"] for doc in docs]
        embeddings = self.model.encode(texts)

        self.index.add(embeddings)
        self.metadata.extend(docs)

        self.save()

    def query(self, query_text, k=5):
        self._load_model()
        query_embedding = self.model.encode([query_text])
        D, I = self.index.search(query_embedding, k)

        results = []
        for idx in I[0]:
            if idx < len(self.metadata):
                results.append(self.metadata[idx])

        return results


rag = RAGService()
