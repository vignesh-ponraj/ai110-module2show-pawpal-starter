from __future__ import annotations

import warnings
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


def load_index(index_path: Path) -> Index:
	index_path = Path(index_path)
	if not index_path.exists():
		raise FileNotFoundError(f"index file not found: {index_path}")
	with np.load(index_path, allow_pickle=False) as data:
		return Index(
			embeddings=data["embeddings"].copy(),
			filenames=data["filenames"].copy(),
			texts=data["texts"].copy(),
		)


def query(
	index: Index,
	question: str,
	top_k: int = 3,
	threshold: float = 0.35,
) -> QueryResult:
	if index.embeddings.shape[0] == 0:
		raise ValueError("knowledge base is empty")

	model = _get_model()
	q_vec = model.encode([question], convert_to_numpy=True).astype(np.float32)[0]
	q_norm = np.linalg.norm(q_vec)
	if q_norm > 0:
		q_vec = q_vec / q_norm

	with warnings.catch_warnings():
		warnings.simplefilter("ignore", RuntimeWarning)
		scores = index.embeddings @ q_vec
	k = min(top_k, scores.shape[0])
	top_idx = np.argsort(-scores)[:k]

	matches = [
		Match(
			filename=str(index.filenames[i]),
			score=float(scores[i]),
			text=str(index.texts[i]),
		)
		for i in top_idx
	]

	confident = matches[0].score >= threshold
	if confident:
		top = matches[0]
		answer = f"Based on `{top.filename}`:\n\n{top.text.strip()}"
	else:
		answer = (
			"I can't answer that — I don't have information on that topic "
			"in my pet-care knowledge base."
		)

	return QueryResult(answer=answer, matches=matches, confident=confident)


def _cli_build(corpus_dir: str = "data/care_tips", index_path: str = "rag/index.npz") -> None:
	build_index(Path(corpus_dir), Path(index_path))
	print(f"built index at {index_path}")


if __name__ == "__main__":
	import sys

	if len(sys.argv) >= 2 and sys.argv[1] == "build":
		_cli_build()
	else:
		print("usage: python -m rag.care_kb build", file=sys.stderr)
		sys.exit(2)
