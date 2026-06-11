"""Okapi BM25 keyword index (pure Python)."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from phase_3_5.normalize import expand_facet_phrases, tokenize


@dataclass
class KeywordHit:
    chunk_id: str
    score: float
    scheme: str
    source_url: str
    section_title: str


class BM25Index:
    def __init__(
        self,
        *,
        k1: float = 1.5,
        b: float = 0.75,
        facet_phrases: list[str] | None = None,
    ) -> None:
        self.k1 = k1
        self.b = b
        self.facet_phrases = facet_phrases or []
        self._docs: dict[str, dict[str, Any]] = {}
        self._postings: dict[str, dict[str, int]] = {}
        self._doc_len: dict[str, int] = {}
        self._df: dict[str, int] = {}
        self._avg_dl = 0.0
        self._n_docs = 0

    @property
    def document_count(self) -> int:
        return self._n_docs

    def add_document(self, chunk_id: str, keyword_text: str, metadata: dict[str, Any]) -> None:
        expanded = expand_facet_phrases(keyword_text, self.facet_phrases)
        tokens = tokenize(expanded)
        if not tokens:
            return
        tf: dict[str, int] = {}
        for tok in tokens:
            tf[tok] = tf.get(tok, 0) + 1
        self._docs[chunk_id] = {**metadata, "chunk_id": chunk_id}
        self._doc_len[chunk_id] = len(tokens)
        for term, freq in tf.items():
            self._postings.setdefault(term, {})[chunk_id] = freq

    def finalize(self) -> None:
        self._n_docs = len(self._docs)
        self._df = {term: len(post) for term, post in self._postings.items()}
        if self._n_docs:
            self._avg_dl = sum(self._doc_len.values()) / self._n_docs
        else:
            self._avg_dl = 0.0

    def _idf(self, term: str) -> float:
        df = self._df.get(term, 0)
        if df == 0:
            return 0.0
        # BM25+ idf variant
        return math.log(1 + (self._n_docs - df + 0.5) / (df + 0.5))

    def search(
        self,
        query: str,
        *,
        top_k: int = 10,
        scheme: str | None = None,
        source_url: str | None = None,
    ) -> list[KeywordHit]:
        terms = tokenize(query)
        if not terms:
            return []

        scores: dict[str, float] = {}
        for term in terms:
            posting = self._postings.get(term)
            if not posting:
                continue
            idf = self._idf(term)
            for chunk_id, tf in posting.items():
                meta = self._docs[chunk_id]
                if scheme and str(meta.get("scheme")) != scheme:
                    continue
                if source_url and str(meta.get("source_url")) != source_url:
                    continue
                dl = self._doc_len[chunk_id]
                denom = tf + self.k1 * (1 - self.b + self.b * dl / (self._avg_dl or 1.0))
                score = idf * (tf * (self.k1 + 1)) / denom
                scores[chunk_id] = scores.get(chunk_id, 0.0) + score

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        hits: list[KeywordHit] = []
        for chunk_id, score in ranked:
            meta = self._docs[chunk_id]
            hits.append(
                KeywordHit(
                    chunk_id=chunk_id,
                    score=score,
                    scheme=str(meta.get("scheme") or ""),
                    source_url=str(meta.get("source_url") or ""),
                    section_title=str(meta.get("section_title") or ""),
                ),
            )
        return hits

    def to_dict(self) -> dict[str, Any]:
        return {
            "k1": self.k1,
            "b": self.b,
            "facet_phrases": self.facet_phrases,
            "n_docs": self._n_docs,
            "avg_dl": self._avg_dl,
            "docs": self._docs,
            "postings": self._postings,
            "doc_len": self._doc_len,
            "df": self._df,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BM25Index":
        idx = cls(
            k1=float(data.get("k1", 1.5)),
            b=float(data.get("b", 0.75)),
            facet_phrases=list(data.get("facet_phrases") or []),
        )
        idx._docs = dict(data.get("docs") or {})
        idx._postings = {k: dict(v) for k, v in (data.get("postings") or {}).items()}
        idx._doc_len = dict(data.get("doc_len") or {})
        idx._df = dict(data.get("df") or {})
        idx._n_docs = int(data.get("n_docs") or len(idx._docs))
        idx._avg_dl = float(data.get("avg_dl") or 0.0)
        return idx

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "BM25Index":
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))
