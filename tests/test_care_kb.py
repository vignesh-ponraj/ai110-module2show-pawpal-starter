import numpy as np

from rag.care_kb import Index, Match, QueryResult, _get_model


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
