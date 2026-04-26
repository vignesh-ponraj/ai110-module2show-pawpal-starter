from pathlib import Path

import numpy as np
import pytest

from rag.care_kb import Index, Match, QueryResult, _get_model, build_index, load_index, query


def test_match_dataclass_holds_filename_score_text():
	match = Match(filename="dog.md", score=0.42, text="content")
	assert match.filename == "dog.md"
	assert match.score == 0.42
	assert match.text == "content"


def test_query_result_holds_answer_matches_confident():
	matches = [Match(filename="a.md", score=0.5, text="x")]
	result = QueryResult(answer="hello", matches=matches, confident=True)
	assert result.answer == "hello"
	assert result.matches == matches
	assert result.confident is True


def test_index_dataclass_holds_arrays_and_filenames():
	embeddings = np.zeros((2, 384), dtype=np.float32)
	filenames = np.array(["a.md", "b.md"])
	texts = np.array(["text a", "text b"])
	index = Index(embeddings=embeddings, filenames=filenames, texts=texts)
	assert index.embeddings.shape == (2, 384)
	assert list(index.filenames) == ["a.md", "b.md"]
	assert list(index.texts) == ["text a", "text b"]


def test_get_model_returns_cached_instance():
	m1 = _get_model()
	m2 = _get_model()
	assert m1 is m2


@pytest.fixture
def tiny_corpus(tmp_path: Path) -> Path:
	corpus = tmp_path / "care_tips"
	corpus.mkdir()
	(corpus / "walk.md").write_text(
		"# Walking\n\nDogs need 30 to 60 minutes of walking per day.\n"
	)
	(corpus / "feed.md").write_text(
		"# Feeding\n\nAdult cats need two measured meals per day.\n"
	)
	(corpus / "groom.md").write_text(
		"# Grooming\n\nLong-haired cats need brushing several times per week.\n"
	)
	return corpus


def test_build_index_creates_npz_file(tiny_corpus: Path, tmp_path: Path):
	index_path = tmp_path / "index.npz"

	build_index(tiny_corpus, index_path)

	assert index_path.exists()


def test_build_index_embeds_each_document_once(tiny_corpus: Path, tmp_path: Path):
	index_path = tmp_path / "index.npz"

	build_index(tiny_corpus, index_path)

	with np.load(index_path, allow_pickle=False) as data:
		assert data["embeddings"].shape == (3, 384)
		assert data["embeddings"].dtype == np.float32


def test_build_index_normalizes_embeddings(tiny_corpus: Path, tmp_path: Path):
	index_path = tmp_path / "index.npz"

	build_index(tiny_corpus, index_path)

	with np.load(index_path, allow_pickle=False) as data:
		norms = np.linalg.norm(data["embeddings"], axis=1)
		assert np.allclose(norms, 1.0, atol=1e-5)


def test_build_index_stores_filenames_and_texts(tiny_corpus: Path, tmp_path: Path):
	index_path = tmp_path / "index.npz"

	build_index(tiny_corpus, index_path)

	with np.load(index_path, allow_pickle=False) as data:
		filenames = sorted(data["filenames"].tolist())
		assert filenames == ["feed.md", "groom.md", "walk.md"]
		assert len(data["texts"]) == 3
		assert any("Walking" in t for t in data["texts"])


def test_build_index_raises_on_empty_corpus(tmp_path: Path):
	empty = tmp_path / "empty"
	empty.mkdir()
	index_path = tmp_path / "index.npz"

	with pytest.raises(ValueError, match="no markdown files"):
		build_index(empty, index_path)


def test_load_index_round_trip(tiny_corpus: Path, tmp_path: Path):
	index_path = tmp_path / "index.npz"
	build_index(tiny_corpus, index_path)

	index = load_index(index_path)

	assert index.embeddings.shape == (3, 384)
	assert index.embeddings.dtype == np.float32
	assert sorted(index.filenames.tolist()) == ["feed.md", "groom.md", "walk.md"]
	assert len(index.texts) == 3


def test_load_index_missing_file_raises(tmp_path: Path):
	with pytest.raises(FileNotFoundError):
		load_index(tmp_path / "does_not_exist.npz")


@pytest.fixture
def tiny_index(tiny_corpus: Path, tmp_path: Path) -> Index:
	index_path = tmp_path / "index.npz"
	build_index(tiny_corpus, index_path)
	return load_index(index_path)


def test_query_returns_top_match_for_walking_question(tiny_index: Index):
	result = query(tiny_index, "how long should I walk my dog?")

	assert result.matches[0].filename == "walk.md"


def test_query_returns_top_match_for_feeding_question(tiny_index: Index):
	result = query(tiny_index, "how much food does my cat need?")

	assert result.matches[0].filename == "feed.md"


def test_query_returns_top_k_matches(tiny_index: Index):
	result = query(tiny_index, "how long should I walk my dog?", top_k=3)

	assert len(result.matches) == 3


def test_query_top_k_capped_at_corpus_size(tiny_index: Index):
	result = query(tiny_index, "how long should I walk my dog?", top_k=10)

	assert len(result.matches) == 3


def test_query_scores_are_descending(tiny_index: Index):
	result = query(tiny_index, "how long should I walk my dog?", top_k=3)

	scores = [m.score for m in result.matches]
	assert scores == sorted(scores, reverse=True)


def test_query_scores_are_in_valid_cosine_range(tiny_index: Index):
	result = query(tiny_index, "how long should I walk my dog?", top_k=3)

	for match in result.matches:
		assert -1.0 <= match.score <= 1.0


def test_query_match_text_is_full_document(tiny_index: Index):
	result = query(tiny_index, "how long should I walk my dog?", top_k=1)

	assert "30 to 60 minutes" in result.matches[0].text


def test_query_raises_on_empty_index(tmp_path: Path):
	empty_index = Index(
		embeddings=np.zeros((0, 384), dtype=np.float32),
		filenames=np.array([]),
		texts=np.array([]),
	)
	with pytest.raises(ValueError, match="knowledge base is empty"):
		query(empty_index, "anything")
