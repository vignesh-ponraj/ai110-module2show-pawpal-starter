from __future__ import annotations

from dataclasses import dataclass
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


def build_index(corpus_dir: str) -> Index:
	"""Placeholder for Task 4."""
	raise NotImplementedError()


def load_index(filepath: str) -> Index:
	"""Placeholder for Task 5."""
	raise NotImplementedError()


def query(index: Index, question: str) -> QueryResult:
	"""Placeholder for Task 6."""
	raise NotImplementedError()
