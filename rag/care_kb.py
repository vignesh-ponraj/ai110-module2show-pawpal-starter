from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

import numpy as np

_MODEL = None


def _get_model():
	global _MODEL
	if _MODEL is None:
		from sentence_transformers import SentenceTransformer
		_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
	return _MODEL


@dataclass
class Match:
	filename: str
	score: float
	text: str


@dataclass
class QueryResult:
	answer: str
	matches: List[Match]
	confident: bool


@dataclass
class Index:
	embeddings: np.ndarray
	filenames: np.ndarray
	texts: np.ndarray


def build_index(corpus_dir: Path, index_path: Path) -> None:
	corpus_dir = Path(corpus_dir)
	index_path = Path(index_path)

	md_files = sorted(corpus_dir.glob("*.md"))
	if not md_files:
		raise ValueError(f"no markdown files in {corpus_dir}")

	filenames = [p.name for p in md_files]
	texts = [p.read_text() for p in md_files]

	model = _get_model()
	embeddings = model.encode(texts, convert_to_numpy=True).astype(np.float32)
	norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
	norms[norms == 0] = 1.0
	embeddings = embeddings / norms

	index_path.parent.mkdir(parents=True, exist_ok=True)
	np.savez(
		index_path,
		embeddings=embeddings,
		filenames=np.array(filenames),
		texts=np.array(texts),
	)


def load_index(filepath: str) -> Index:
	"""Placeholder for Task 5."""
	raise NotImplementedError()


def query(index: Index, question: str) -> QueryResult:
	"""Placeholder for Task 6."""
	raise NotImplementedError()
