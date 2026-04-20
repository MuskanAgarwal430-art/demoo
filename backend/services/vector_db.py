import chromadb
from django.conf import settings


class ChromaDBService:
    _client = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            cls._client = chromadb.PersistentClient(path=settings.CHROMADB_PATH)
        return cls._client

    @classmethod
    def collection_name(cls, company_code: str) -> str:
        return f"company_{company_code.upper()}_faces"

    @classmethod
    def get_collection(cls, company_code: str):
        client = cls.get_client()
        return client.get_or_create_collection(
            name=cls.collection_name(company_code),
            metadata={"hnsw:space": "cosine"},
        )

    @classmethod
    def delete_collection(cls, company_code: str):
        client = cls.get_client()
        try:
            client.delete_collection(cls.collection_name(company_code))
        except Exception:
            pass

    @classmethod
    def add_embedding(cls, company_code: str, employee_code: str, embedding: list, index: int, employee_name: str = ""):
        """Store one face embedding for an employee."""
        collection = cls.get_collection(company_code)
        doc_id = f"{employee_code}_{index}"
        # Delete existing entry with same id to allow re-training
        try:
            collection.delete(ids=[doc_id])
        except Exception:
            pass
        collection.add(
            embeddings=[embedding],
            ids=[doc_id],
            metadatas=[{
                "employee_code": employee_code,
                "employee_name": employee_name,
                "company_code": company_code.upper(),
                "image_index": index,
            }],
        )

    @classmethod
    def delete_employee_embeddings(cls, company_code: str, employee_code: str):
        """Remove all embeddings for an employee (e.g., when re-training or deleting)."""
        collection = cls.get_collection(company_code)
        results = collection.get(where={"employee_code": employee_code})
        if results["ids"]:
            collection.delete(ids=results["ids"])

    @classmethod
    def recognize(cls, company_code: str, query_embedding: list, n_results: int = 1) -> dict:
        """
        Search for the closest face in the company collection.
        Returns: {employee_code, employee_name, distance, confidence}
        """
        collection = cls.get_collection(company_code)
        count = collection.count()
        if count == 0:
            return {"matched": False, "reason": "No enrolled employees."}

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(n_results, count),
        )

        distance = results["distances"][0][0]
        metadata = results["metadatas"][0][0]
        threshold = settings.FACE_MATCH_THRESHOLD

        if distance <= threshold:
            return {
                "matched": True,
                "employee_code": metadata["employee_code"],
                "employee_name": metadata["employee_name"],
                "distance": round(distance, 4),
                "confidence": round(1 - distance, 4),
            }

        return {
            "matched": False,
            "distance": round(distance, 4),
            "confidence": round(1 - distance, 4),
            "reason": "No match above threshold.",
        }
