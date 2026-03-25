"""CodeBERT + GraphCodeBERT code similarity embeddings."""
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SimilarFunction:
    filepath: str
    function_name: str
    score: float
    code: str


@dataclass
class ClonePair:
    file_a: str
    func_a: str
    file_b: str
    func_b: str
    similarity: float


@dataclass
class Cluster:
    cluster_id: int
    functions: List[SimilarFunction] = field(default_factory=list)
    centroid: Optional[np.ndarray] = None


class CodeSimilarityEngine:
    """CodeBERT + GraphCodeBERT embeddings for code similarity."""

    def __init__(self):
        self.codebert = None
        self.graphcodebert = None
        self.tokenizer = None
        self._loaded = False

    def _load_models(self):
        if self._loaded:
            return
        try:
            import torch
            from transformers import AutoModel, AutoTokenizer

            logger.info("Loading CodeBERT model...")
            self.tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")
            self.codebert = AutoModel.from_pretrained("microsoft/codebert-base")
            self.codebert.eval()

            logger.info("Loading GraphCodeBERT model...")
            self.graphcodebert = AutoModel.from_pretrained("microsoft/graphcodebert-base")
            self.graphcodebert.eval()
            self._loaded = True
            logger.info("CodeBERT + GraphCodeBERT loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load transformer models: {e}. Using fallback.")
            self._loaded = False

    def embed_function(self, code: str, model: str = "codebert") -> np.ndarray:
        self._load_models()
        if not self._loaded or self.tokenizer is None:
            return self._tfidf_fallback(code)

        try:
            import torch
            tokens = self.tokenizer(
                code,
                max_length=512,
                truncation=True,
                padding="max_length",
                return_tensors="pt",
            )
            with torch.no_grad():
                chosen_model = self.codebert if model == "codebert" else self.graphcodebert
                outputs = chosen_model(**tokens)
            cls_embedding = outputs.last_hidden_state[:, 0, :].squeeze().numpy()
            return cls_embedding
        except Exception as e:
            logger.debug(f"Embedding failed: {e}")
            return self._tfidf_fallback(code)

    def _tfidf_fallback(self, code: str) -> np.ndarray:
        """Simple hash-based embedding fallback."""
        tokens = code.split()
        vec = np.zeros(768, dtype=np.float32)
        for i, tok in enumerate(tokens[:768]):
            vec[i % 768] += hash(tok) % 1000 / 1000.0
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec

    def cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    def find_similar_functions(
        self,
        query_code: str,
        codebase_functions: List[Tuple[str, str, str]],  # (filepath, func_name, code)
        top_k: int = 10,
    ) -> List[SimilarFunction]:
        query_emb = self.embed_function(query_code)
        results = []
        for filepath, func_name, code in codebase_functions:
            emb = self.embed_function(code)
            score = self.cosine_similarity(query_emb, emb)
            results.append(SimilarFunction(filepath=filepath, function_name=func_name, score=score, code=code))
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def detect_code_clones(
        self,
        codebase_functions: List[Tuple[str, str, str]],
        threshold: float = 0.9,
    ) -> List[ClonePair]:
        embeddings = []
        for filepath, func_name, code in codebase_functions:
            emb = self.embed_function(code)
            embeddings.append(emb)

        clones = []
        n = len(embeddings)
        for i in range(n):
            for j in range(i + 1, n):
                sim = self.cosine_similarity(embeddings[i], embeddings[j])
                if sim >= threshold:
                    clones.append(
                        ClonePair(
                            file_a=codebase_functions[i][0],
                            func_a=codebase_functions[i][1],
                            file_b=codebase_functions[j][0],
                            func_b=codebase_functions[j][1],
                            similarity=sim,
                        )
                    )
        return clones

    def cluster_functions(
        self,
        codebase_functions: List[Tuple[str, str, str]],
        n_clusters: int = 20,
    ) -> List[Cluster]:
        if not codebase_functions:
            return []

        try:
            from sklearn.cluster import KMeans
        except ImportError:
            logger.warning("sklearn not available; skipping clustering")
            return []

        embeddings = np.array([self.embed_function(code) for _, _, code in codebase_functions])
        n_clusters = min(n_clusters, len(codebase_functions))

        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(embeddings)

        clusters: dict = {}
        for idx, label in enumerate(labels):
            if label not in clusters:
                clusters[label] = Cluster(cluster_id=int(label), centroid=kmeans.cluster_centers_[label])
            filepath, func_name, code = codebase_functions[idx]
            clusters[label].functions.append(
                SimilarFunction(filepath=filepath, function_name=func_name, score=1.0, code=code[:200])
            )

        return list(clusters.values())
