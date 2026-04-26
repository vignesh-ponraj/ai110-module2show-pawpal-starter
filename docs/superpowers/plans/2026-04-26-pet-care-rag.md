# Pet-Care Knowledge Base RAG Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a free-text "Ask PawPal" feature to the existing Streamlit app that retrieves answers from a small local pet-care corpus using sentence-transformer embeddings and cosine similarity.

**Architecture:** A self-contained `rag/` Python package with a NumPy-backed in-memory index persisted to a single `.npz` file. No LLM. No DB. Top-1 retrieved snippet is returned verbatim with its source filename as citation. Below a 0.35 cosine-similarity threshold, the system replies "I can't answer". Index is auto-built on first launch; UI integration is a new section appended to `app.py`.

**Tech Stack:** Python 3, Streamlit, sentence-transformers (`all-MiniLM-L6-v2`), NumPy, pytest. Tests run against the real embedding model (small, fast, deterministic enough).

**Spec:** [`docs/superpowers/specs/2026-04-26-pet-care-rag-design.md`](../specs/2026-04-26-pet-care-rag-design.md)
**Diagram:** [`docs/superpowers/specs/rag-system-diagram.mmd`](../specs/rag-system-diagram.mmd)

## File Structure

| Path | Action | Responsibility |
|---|---|---|
| `requirements.txt` | Modify | Add sentence-transformers and numpy |
| `.gitignore` | Create or modify | Ignore generated `rag/index.npz` |
| `rag/__init__.py` | Create | Package marker; re-export public API |
| `rag/care_kb.py` | Create | All KB logic: dataclasses, model cache, `build_index`, `load_index`, `query`, CLI `__main__` |
| `data/care_tips/*.md` | Create | ~20 hand-written care-tip snippets |
| `tests/test_care_kb.py` | Create | Unit tests for build, load, retrieval, threshold |
| `app.py` | Modify | Append "Ask PawPal" UI section after the schedule section |

The entire RAG implementation lives in **one file** (`rag/care_kb.py`) because it is small (well under 200 lines) and its components are tightly cohesive (model handle + index dataclass + three functions that all touch them). Splitting now would be premature.

---

### Task 1: Dependencies and Package Skeleton

**Files:**
- Modify: `requirements.txt`
- Create: `.gitignore` (or modify if it exists)
- Create: `rag/__init__.py`
- Create: `data/care_tips/` (directory with `.gitkeep`)

- [ ] **Step 1: Check whether `.gitignore` already exists**

Run: `ls -la .gitignore 2>&1 || echo "no gitignore"`

If it exists, read its contents and append the new lines. If not, create it.

- [ ] **Step 2: Update `requirements.txt`**

Replace the file contents with:

```
streamlit>=1.30
pytest>=7.0
sentence-transformers>=2.2
numpy>=1.24
```

- [ ] **Step 3: Create or update `.gitignore`**

Append (or create file with) these lines:

```
rag/index.npz
__pycache__/
.venv/
.pytest_cache/
```

- [ ] **Step 4: Create `rag/__init__.py`**

Write the file with this exact content:

```python
from rag.care_kb import (
    Index,
    Match,
    QueryResult,
    build_index,
    load_index,
    query,
)

__all__ = ["Index", "Match", "QueryResult", "build_index", "load_index", "query"]
```

This will fail to import until `rag/care_kb.py` exists — that's fine, we'll add a stub in Task 3.

- [ ] **Step 5: Create the corpus directory**

Run: `mkdir -p data/care_tips && touch data/care_tips/.gitkeep`

- [ ] **Step 6: Install dependencies into the project venv**

Run: `./.venv/bin/python -m pip install -r requirements.txt`

Expected: pip downloads sentence-transformers (~80MB model is downloaded lazily on first use, not during install). Install completes without errors.

If `.venv` does not exist, create it first: `python -m venv .venv && ./.venv/bin/python -m pip install -r requirements.txt`.

- [ ] **Step 7: Commit**

```bash
git add requirements.txt .gitignore rag/__init__.py data/care_tips/.gitkeep
git commit -m "chore: scaffold rag package and add embedding dependencies"
```

---

### Task 2: Hand-Written Knowledge Corpus

**Files:**
- Create: 20 markdown files in `data/care_tips/`

Each file is ~100–150 words on one topic. The corpus needs semantic diversity so retrieval has clear winners and clear non-matches.

- [ ] **Step 1: Create `data/care_tips/dog_walking_by_age.md`**

```markdown
# Dog Walking Duration by Age

Puppies under 3 months should have very short, gentle walks of 5 to 10 minutes, mostly for socialization and house-training, not exercise. A common rule of thumb is 5 minutes of walking per month of age, twice a day, until the puppy is fully grown.

Adult dogs aged 1 to 7 years generally need 30 to 60 minutes of walking per day, split into one or two sessions. High-energy breeds like Labradors, Border Collies, and Australian Shepherds may need 60 to 90 minutes plus off-leash play.

Senior dogs (over 7 for large breeds, over 10 for small breeds) usually do best with two or three shorter walks of 15 to 20 minutes, watching for signs of joint stiffness or fatigue.

Source: general pet-care guidelines
```

- [ ] **Step 2: Create `data/care_tips/dog_walking_by_breed_size.md`**

```markdown
# Dog Walking by Breed Size

Small breeds such as Chihuahuas, Yorkies, and Pomeranians typically need 20 to 30 minutes of walking per day. They tire quickly and can overheat in warm weather.

Medium breeds like Beagles, Cocker Spaniels, and Border Collies need 45 to 60 minutes of walking, often more if they are working or herding breeds.

Large breeds including Labradors, Golden Retrievers, and German Shepherds usually need 60 to 90 minutes of walking and benefit from running or fetch sessions on top of that.

Giant breeds such as Great Danes and Saint Bernards need moderate walks of 30 to 45 minutes — too much high-impact exercise can stress their joints, especially in their first 18 months.

Source: general pet-care guidelines
```

- [ ] **Step 3: Create `data/care_tips/cat_feeding_basics.md`**

```markdown
# Cat Feeding Basics

Adult cats generally do well on two measured meals a day. Most adult cats need around 20 to 30 calories per pound of body weight, but indoor cats often need slightly less to avoid weight gain.

Wet food helps with hydration, which is important because cats have a low natural thirst drive. A mix of wet and dry food is a common compromise.

Avoid free-feeding dry kibble unless your cat has a stable, healthy weight — most cats will overeat if food is always available. Always provide fresh water, and refresh it daily. Cats with kidney issues, diabetes, or food allergies should follow a veterinarian-prescribed diet.

Source: general pet-care guidelines
```

- [ ] **Step 4: Create `data/care_tips/kitten_feeding.md`**

```markdown
# Kitten Feeding

Kittens grow rapidly and need more frequent meals than adult cats. From weaning until 4 months of age, feed kittens four small meals per day. From 4 to 6 months, three meals per day is appropriate. After 6 months, most kittens can transition to two meals per day.

Use food specifically labeled "kitten" or "for all life stages" — kitten food is higher in protein, fat, and key nutrients like taurine and DHA.

Kittens should always have access to fresh water. Cow's milk is not appropriate; most kittens are lactose intolerant after weaning. If a kitten is orphaned, use a commercial kitten milk replacer, never cow's milk.

Source: general pet-care guidelines
```

- [ ] **Step 5: Create `data/care_tips/dog_grooming_frequency.md`**

```markdown
# Dog Grooming Frequency

Short-coated breeds like Beagles and Boxers need brushing about once a week and a bath every 1 to 3 months, or when visibly dirty.

Double-coated breeds like Huskies, Golden Retrievers, and German Shepherds need brushing 2 to 3 times per week, increasing to daily during seasonal shedding. Bathe every 2 to 3 months — over-bathing strips natural oils.

Long-coated breeds like Yorkies, Shih Tzus, and Maltese need daily brushing to prevent mats, plus a bath every 3 to 4 weeks.

Curly-coated breeds like Poodles and Bichons need brushing several times a week and professional grooming every 4 to 6 weeks to prevent matting.

Source: general pet-care guidelines
```

- [ ] **Step 6: Create `data/care_tips/cat_grooming.md`**

```markdown
# Cat Grooming

Most short-haired cats groom themselves effectively but still benefit from a weekly brushing to remove loose fur and reduce hairballs.

Long-haired cats like Persians and Maine Coons need brushing 3 to 4 times per week, or daily during shedding seasons, to prevent painful mats. Pay extra attention to areas behind the ears, under the front legs, and along the belly.

Cats rarely need baths unless they get into something they can't lick off, but their nails should be trimmed every 2 to 3 weeks. Check their ears monthly for wax buildup or redness.

If a cat suddenly stops grooming itself, that often signals pain, illness, or obesity and warrants a vet visit.

Source: general pet-care guidelines
```

- [ ] **Step 7: Create `data/care_tips/dental_care.md`**

```markdown
# Dental Care for Dogs and Cats

Dental disease is one of the most common health problems in pets, affecting most dogs and cats by age 3.

Brush your pet's teeth daily if possible, or at minimum 3 times per week, using a pet-specific toothpaste. Never use human toothpaste — fluoride and xylitol are toxic to pets.

Dental chews and water additives can help, but they do not replace brushing. Annual or biannual professional dental cleanings under anesthesia are recommended by most veterinarians, especially for small breeds prone to tartar buildup.

Signs of dental disease include bad breath, drooling, pawing at the mouth, reluctance to eat hard food, and visible tartar or red gums.

Source: general pet-care guidelines
```

- [ ] **Step 8: Create `data/care_tips/nail_trimming.md`**

```markdown
# Nail Trimming

Most dogs and cats need their nails trimmed every 3 to 4 weeks, though indoor cats and small dogs may need it more often because they don't naturally wear their nails down.

For light-colored nails, you can see the pink "quick" inside — trim a few millimeters in front of it. For dark nails, take small slices and stop when you see a dark spot in the center of the cut surface, which signals you're close to the quick.

If you accidentally cut the quick, apply styptic powder or cornstarch to stop bleeding. If a pet strongly resists nail trims, a groomer or vet tech can usually do it quickly and safely.

Source: general pet-care guidelines
```

- [ ] **Step 9: Create `data/care_tips/dog_enrichment.md`**

```markdown
# Mental Enrichment for Dogs

Mental exercise tires dogs as effectively as physical exercise, sometimes more so. A 15-minute training or puzzle session can be as satisfying as a 30-minute walk.

Good enrichment options include food puzzle toys, snuffle mats, scatter feeding in the yard, frozen Kong toys with peanut butter (xylitol-free), and short training sessions teaching new tricks or reinforcing basic commands.

Rotate toys weekly so they feel novel. Bored dogs often develop destructive behaviors like chewing furniture, excessive barking, or digging.

Sniffing is itself enriching — letting a dog sniff freely on walks, sometimes called a "sniffari", engages their primary sense and is mentally tiring in a way brisk walks are not.

Source: general pet-care guidelines
```

- [ ] **Step 10: Create `data/care_tips/cat_enrichment.md`**

```markdown
# Mental Enrichment for Cats

Indoor cats need active enrichment to stay healthy and avoid behavior problems. Aim for two or three short play sessions per day, 5 to 15 minutes each, using wand toys that mimic prey movement.

Vertical space matters — cat trees, shelves, and window perches let cats climb, observe, and feel safe. A view of a bird feeder is one of the cheapest enrichments available.

Food puzzles and treat-dispensing balls turn meals into hunting opportunities. Rotating toys every few days keeps them interesting.

Catnip or silvervine affects most adult cats and is safe in moderation. Without enough enrichment, indoor cats commonly develop overgrooming, aggression, or weight problems.

Source: general pet-care guidelines
```

- [ ] **Step 11: Create `data/care_tips/dog_socialization.md`**

```markdown
# Puppy Socialization

The critical socialization window for puppies runs from about 3 to 14 weeks of age. Positive experiences with people, other animals, surfaces, sounds, and environments during this period shape lifelong temperament.

Expose your puppy to a wide variety of people (different ages, sizes, hats, beards), other vaccinated dogs, household sounds (vacuums, doorbells), surfaces (grass, tile, metal grates), and brief car rides.

Puppy classes that start before full vaccination are often recommended by behaviorists, with the trade-off of disease risk weighed against the much larger risk of behavior problems from under-socialization.

Keep experiences positive — never force a frightened puppy into a situation. Pair new things with treats and play.

Source: general pet-care guidelines
```

- [ ] **Step 12: Create `data/care_tips/common_meds.md`**

```markdown
# Common Pet Medications

Heartworm prevention is given monthly year-round in most regions, often combined with intestinal parasite control. Common products include ivermectin-based and milbemycin-based preventives.

Flea and tick prevention is also typically monthly. Options include oral chewables (e.g., isoxazoline-class drugs), topical spot-ons, and collars.

Pain relief in dogs commonly uses NSAIDs like carprofen or meloxicam, but these must be vet-prescribed — human NSAIDs like ibuprofen are toxic to dogs and cats.

Cats are particularly sensitive to many medications. Never give a cat any medication intended for dogs or humans without vet approval. Acetaminophen (Tylenol) is fatal to cats even at small doses.

Source: general pet-care guidelines
```

- [ ] **Step 13: Create `data/care_tips/toxic_foods.md`**

```markdown
# Foods Toxic to Dogs and Cats

Several common human foods are dangerous for pets and should never be fed.

For dogs and cats: chocolate (especially dark and baking chocolate), grapes and raisins, onions and garlic in any form, macadamia nuts, xylitol (a sweetener in sugar-free gum and many baked goods), alcohol, caffeine, and raw bread dough.

For cats specifically: lilies are extremely toxic — even a small amount of pollen can cause kidney failure. Tuna intended for humans is fine occasionally but not as a staple, and raw fish can deplete thiamine.

If your pet ingests a toxic substance, call your vet or a pet poison helpline immediately. Do not induce vomiting unless instructed; some substances cause more damage coming back up.

Source: general pet-care guidelines
```

- [ ] **Step 14: Create `data/care_tips/signs_of_illness.md`**

```markdown
# Signs of Illness in Pets

Pets often hide illness, so subtle changes matter. Schedule a vet visit for any of the following lasting more than 24 to 48 hours.

In dogs: lethargy, loss of appetite, vomiting or diarrhea, excessive thirst or urination, coughing, limping, sudden weight changes, or behavioral changes like increased irritability or hiding.

In cats: hiding more than usual, changes in litter box habits (especially straining or going outside the box), reduced grooming, weight loss, vocalizing more, or changes in appetite. Cats almost never show pain openly — any change in routine is worth attention.

Emergencies that need immediate vet care include difficulty breathing, collapse, suspected toxin ingestion, bloat (especially in deep-chested dogs), and a male cat straining to urinate.

Source: general pet-care guidelines
```

- [ ] **Step 15: Create `data/care_tips/senior_pet_care.md`**

```markdown
# Senior Pet Care

Dogs are generally considered senior at age 7 for large breeds and age 10 for small breeds. Cats are usually considered senior around age 11.

Senior pets benefit from twice-yearly vet checkups instead of annual ones, with bloodwork to catch kidney, liver, and thyroid issues early. Joint supplements containing glucosamine and omega-3 fatty acids can help with mobility.

Adjust feeding to a senior-formulated diet with appropriate calorie and protein levels. Watch for weight changes in either direction.

Provide easier access to favorite spots — ramps to couches, lower-sided litter boxes for cats with arthritis, non-slip rugs on slick floors. Cognitive decline is common and may show as confusion, altered sleep, or new vocalizations.

Source: general pet-care guidelines
```

- [ ] **Step 16: Create `data/care_tips/vaccinations.md`**

```markdown
# Core Vaccinations

Core vaccines are recommended for nearly all pets regardless of lifestyle.

For dogs, core vaccines include rabies, distemper, parvovirus, and adenovirus (often combined as DHPP). Puppies receive a series of shots starting at 6 to 8 weeks, with boosters every 3 to 4 weeks until 16 weeks. Adult boosters are typically every 1 to 3 years.

For cats, core vaccines include rabies and FVRCP (feline viral rhinotracheitis, calicivirus, and panleukopenia). Kitten schedules are similar to puppies.

Non-core vaccines like leptospirosis, Bordetella (kennel cough), Lyme disease, and feline leukemia (FeLV) are recommended based on lifestyle and regional disease risk.

Source: general pet-care guidelines
```

- [ ] **Step 17: Create `data/care_tips/spay_neuter.md`**

```markdown
# Spay and Neuter

Spaying (females) and neutering (males) prevent unwanted litters and have significant health and behavioral benefits.

For most dogs and cats, the traditional age is 5 to 6 months, before the first heat cycle. Recent research suggests that for some large and giant breed dogs, waiting until skeletal maturity (12 to 24 months) may reduce risks of joint disorders and certain cancers — discuss timing with your veterinarian.

Health benefits include eliminating risk of testicular cancer, greatly reducing mammary cancer risk in females spayed before their first heat, and preventing pyometra (uterine infection).

Behavioral benefits often include reduced roaming, marking, and inter-male aggression. Recovery typically takes 7 to 14 days with restricted activity.

Source: general pet-care guidelines
```

- [ ] **Step 18: Create `data/care_tips/house_training.md`**

```markdown
# House Training a Puppy

Most puppies can be reliably house-trained between 4 and 6 months of age, though some take longer.

Take the puppy outside first thing in the morning, after every meal, after naps, after play, and immediately before bed — typically every 1 to 2 hours for young puppies. A common guideline is that puppies can hold their bladder roughly one hour for every month of age.

Reward immediately when the puppy goes in the right spot, using a small treat and praise within 3 seconds. Crate training helps because puppies generally avoid soiling their sleeping area.

If you catch an accident in progress, interrupt with a calm "outside!" and take them out. Never punish accidents found after the fact — the puppy can't connect the punishment to the act.

Source: general pet-care guidelines
```

- [ ] **Step 19: Create `data/care_tips/litter_box_setup.md`**

```markdown
# Litter Box Setup

The standard rule is one litter box per cat, plus one extra. Two cats need three boxes.

Place boxes in quiet, low-traffic areas, but not next to noisy appliances like washing machines. Cats prefer not to eat next to where they eliminate, so keep boxes away from food and water.

Most cats prefer unscented, fine-grained clumping litter and dislike strong perfumes. Scoop at least once daily and fully replace litter every 1 to 2 weeks for clay litters, less frequently for some clumping varieties.

Going outside the box almost always signals a problem: medical issue (urinary tract infection, kidney disease), litter or location preference, or stress. A vet visit should be the first step.

Source: general pet-care guidelines
```

- [ ] **Step 20: Create `data/care_tips/exercise_safety.md`**

```markdown
# Exercise Safety in Heat and Cold

In hot weather, walk dogs in the early morning or evening when pavement is cool. Test pavement with the back of your hand for 7 seconds — if too hot for you, it's too hot for paws. Heatstroke risk rises sharply above 85°F, especially for brachycephalic breeds like Bulldogs and Pugs.

Watch for excessive panting, drooling, weakness, or vomiting — these are heatstroke symptoms requiring immediate cooling and vet care.

In cold weather, short-coated and small dogs may need a coat below 45°F. Wipe paws after walks to remove ice melt chemicals, which can be toxic if licked. Limit time outside in subfreezing temperatures.

Hydration matters in all weather. Bring water on long walks regardless of season.

Source: general pet-care guidelines
```

- [ ] **Step 21: Verify all 20 files exist**

Run: `ls data/care_tips/*.md | wc -l`

Expected output: `20`

- [ ] **Step 22: Commit**

```bash
git add data/care_tips/
git commit -m "feat: add hand-written pet-care knowledge corpus (20 snippets)"
```

---

### Task 3: Dataclasses and Lazy Model Cache

**Files:**
- Create: `rag/care_kb.py`
- Create: `tests/test_care_kb.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_care_kb.py` with this initial content:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_care_kb.py -v`

Expected: FAIL — `ModuleNotFoundError: No module named 'rag.care_kb'`.

- [ ] **Step 3: Write minimal implementation**

Create `rag/care_kb.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `./.venv/bin/python -m pytest tests/test_care_kb.py -v`

Expected: 4 passed. Note: `test_get_model_returns_cached_instance` will trigger a one-time download of the `all-MiniLM-L6-v2` model (~80MB) to your HuggingFace cache. This may take 30 seconds or more on first run.

- [ ] **Step 5: Commit**

```bash
git add rag/care_kb.py tests/test_care_kb.py
git commit -m "feat: add rag dataclasses and lazy embedding model cache"
```

---

### Task 4: `build_index` Function

**Files:**
- Modify: `rag/care_kb.py`
- Modify: `tests/test_care_kb.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_care_kb.py`:

```python
from pathlib import Path

import pytest

from rag.care_kb import build_index


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `./.venv/bin/python -m pytest tests/test_care_kb.py -v -k build_index`

Expected: 5 failures — `ImportError: cannot import name 'build_index'`.

- [ ] **Step 3: Implement `build_index`**

Append to `rag/care_kb.py`:

```python
from pathlib import Path


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
```

Move the `from pathlib import Path` line up to the other imports at the top of the file rather than leaving it next to the function.

- [ ] **Step 4: Run tests to verify they pass**

Run: `./.venv/bin/python -m pytest tests/test_care_kb.py -v`

Expected: all 9 tests pass (4 from Task 3 + 5 from this task).

- [ ] **Step 5: Commit**

```bash
git add rag/care_kb.py tests/test_care_kb.py
git commit -m "feat: implement build_index for rag care_kb"
```

---

### Task 5: `load_index` Function

**Files:**
- Modify: `rag/care_kb.py`
- Modify: `tests/test_care_kb.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_care_kb.py`:

```python
from rag.care_kb import load_index


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `./.venv/bin/python -m pytest tests/test_care_kb.py -v -k load_index`

Expected: ImportError — `cannot import name 'load_index'`.

- [ ] **Step 3: Implement `load_index`**

Append to `rag/care_kb.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `./.venv/bin/python -m pytest tests/test_care_kb.py -v`

Expected: all 11 tests pass.

- [ ] **Step 5: Commit**

```bash
git add rag/care_kb.py tests/test_care_kb.py
git commit -m "feat: implement load_index for rag care_kb"
```

---

### Task 6: `query` Function — Core Retrieval

**Files:**
- Modify: `rag/care_kb.py`
- Modify: `tests/test_care_kb.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_care_kb.py`:

```python
from rag.care_kb import query


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `./.venv/bin/python -m pytest tests/test_care_kb.py -v -k query`

Expected: 8 failures — `ImportError: cannot import name 'query'`.

- [ ] **Step 3: Implement `query`**

Append to `rag/care_kb.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `./.venv/bin/python -m pytest tests/test_care_kb.py -v`

Expected: all 19 tests pass.

- [ ] **Step 5: Commit**

```bash
git add rag/care_kb.py tests/test_care_kb.py
git commit -m "feat: implement query with cosine retrieval and top-k ordering"
```

---

### Task 7: `query` — Confidence Threshold and Answer Formatting

This task adds tests that exercise the threshold and formatting behavior already implemented in Task 6, plus a custom-threshold test. No production code changes are needed if Task 6 was implemented as written; if a test fails, fix `query` to match.

**Files:**
- Modify: `tests/test_care_kb.py`
- Possibly modify: `rag/care_kb.py` (only if a test fails)

- [ ] **Step 1: Write threshold and formatting tests**

Append to `tests/test_care_kb.py`:

```python
def test_query_below_threshold_says_cant_answer(tiny_index: Index):
	result = query(tiny_index, "what is the capital of France?", threshold=0.5)

	assert result.confident is False
	assert "can't answer" in result.answer.lower()


def test_query_above_threshold_formats_answer_with_citation(tiny_index: Index):
	result = query(tiny_index, "how long should I walk my dog?", threshold=0.0)

	assert result.confident is True
	assert "`walk.md`" in result.answer
	assert "30 to 60 minutes" in result.answer


def test_query_threshold_is_configurable(tiny_index: Index):
	high_threshold = query(
		tiny_index, "how long should I walk my dog?", threshold=0.99
	)
	low_threshold = query(
		tiny_index, "how long should I walk my dog?", threshold=0.0
	)

	assert high_threshold.confident is False
	assert low_threshold.confident is True
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `./.venv/bin/python -m pytest tests/test_care_kb.py -v`

Expected: all 22 tests pass. If `test_query_below_threshold_says_cant_answer` fails because cosine similarity for "capital of France" against the tiny corpus exceeds 0.5, replace its question with `"explain quantum mechanics in detail"` and re-run. If still failing, raise the threshold in the test to 0.6.

- [ ] **Step 3: Commit**

```bash
git add tests/test_care_kb.py
git commit -m "test: cover threshold gate and citation formatting in query"
```

---

### Task 8: CLI Entry for Index Build

**Files:**
- Modify: `rag/care_kb.py`

- [ ] **Step 1: Add `__main__` block**

Append to `rag/care_kb.py`:

```python
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
```

- [ ] **Step 2: Smoke-test the CLI against the real corpus**

Run: `./.venv/bin/python -m rag.care_kb build`

Expected output: `built index at rag/index.npz`.

- [ ] **Step 3: Verify the index was created and has the right shape**

Run:
```bash
./.venv/bin/python -c "
import numpy as np
with np.load('rag/index.npz', allow_pickle=False) as d:
    print('shape:', d['embeddings'].shape)
    print('files:', len(d['filenames']))
    print('first file:', d['filenames'][0])
"
```

Expected: `shape: (20, 384)`, `files: 20`, and one of the markdown filenames.

- [ ] **Step 4: Commit**

The `rag/index.npz` file is gitignored from Task 1, so only the source change is committed.

```bash
git add rag/care_kb.py
git commit -m "feat: add CLI entry point for building the rag index"
```

---

### Task 9: Streamlit "Ask PawPal" UI Section

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Read the current end of `app.py`**

Run: `wc -l app.py` to confirm the file ends near line 329 as expected.

- [ ] **Step 2: Append the Ask PawPal section**

Append the following to `app.py`:

```python
st.divider()

st.subheader("Ask PawPal")
st.caption("Free-text Q&A grounded in a small local pet-care knowledge base.")


@st.cache_resource(show_spinner="Loading knowledge base...")
def get_index():
	from pathlib import Path

	from rag.care_kb import build_index, load_index

	corpus_dir = Path("data/care_tips")
	index_path = Path("rag/index.npz")
	if not index_path.exists():
		build_index(corpus_dir, index_path)
	return load_index(index_path)


question = st.text_input(
	"Ask a pet-care question",
	placeholder="How long should I walk a 3-year-old labrador?",
)

if st.button("Ask"):
	if not question.strip():
		st.info("Type a question first.")
	else:
		from rag.care_kb import query

		try:
			index = get_index()
		except ValueError as exc:
			st.error(f"Knowledge base error: {exc}")
		else:
			result = query(index, question.strip())
			if result.confident:
				st.markdown(result.answer)
			else:
				st.warning(result.answer)

			with st.expander("Retrieved snippets"):
				st.table(
					[
						{
							"filename": match.filename,
							"score": round(match.score, 3),
							"preview": match.text.strip().replace("\n", " ")[:80],
						}
						for match in result.matches
					]
				)
```

- [ ] **Step 3: Smoke-test the Streamlit app**

Run: `./.venv/bin/streamlit run app.py` (in a terminal you can keep open).

Manually verify in the browser:
1. Scroll to the "Ask PawPal" section at the bottom.
2. Type "how long should I walk my dog?" and click Ask. Expected: answer cites `dog_walking_by_age.md` or `dog_walking_by_breed_size.md`, expander shows top-3 with scores.
3. Type "what is the capital of France?" and click Ask. Expected: yellow warning box saying "I can't answer", expander still shows top-3 (with low scores).
4. Click Ask with empty input. Expected: blue info "Type a question first."

Stop the app with Ctrl+C.

- [ ] **Step 4: Commit**

```bash
git add app.py
git commit -m "feat: add Ask PawPal UI section backed by rag care_kb"
```

---

### Task 10: Final Verification

**Files:** none modified.

- [ ] **Step 1: Run the full test suite**

Run: `./.venv/bin/python -m pytest -v`

Expected: all tests pass (the 7 pre-existing tests in `tests/test_pawpal.py` plus the 22 new tests in `tests/test_care_kb.py`).

- [ ] **Step 2: Verify directory structure**

Run: `find rag data/care_tips docs/superpowers -type f | sort`

Expected files:
- `data/care_tips/.gitkeep` (or no .gitkeep if you removed it after the corpus was added)
- `data/care_tips/*.md` (20 files)
- `docs/superpowers/plans/2026-04-26-pet-care-rag.md`
- `docs/superpowers/specs/2026-04-26-pet-care-rag-design.md`
- `docs/superpowers/specs/rag-system-diagram.mmd`
- `rag/__init__.py`
- `rag/care_kb.py`
- `rag/index.npz` should NOT appear (it's gitignored, but `find` will list it). Verify with: `git check-ignore -v rag/index.npz` — expected output points to the `.gitignore` rule.

- [ ] **Step 3: Confirm `rag/index.npz` is not tracked**

Run: `git status`

Expected: clean working tree, no untracked `rag/index.npz`.

- [ ] **Step 4: No commit needed**

This task is verification only.

---

## Self-Review Notes

**Spec coverage check:**
- Goal (Ask PawPal free-text Q&A) → Task 9.
- Hand-written corpus → Task 2.
- `build_index` / `load_index` / `query` API → Tasks 4, 5, 6.
- L2-normalized embeddings, dot-product cosine → Task 4 (normalize), Task 6 (dot product).
- 0.35 threshold + "I can't answer" message → Task 6 (default param), Task 7 (tested).
- Top-3 with scores in UI expander → Task 9.
- `@st.cache_resource` for index loading → Task 9.
- Auto-build on first launch → Task 9 (`get_index` checks for missing index).
- CLI `python -m rag.care_kb build` → Task 8.
- Index missing / empty / empty question error handling → Task 4 (empty corpus), Task 6 (empty index), Task 9 (empty question).
- Real-model tests, no mocking → all test tasks use the actual model.

**Type / name consistency:** `Index`, `Match`, `QueryResult` declared in Task 3, used unchanged in Tasks 4–7. `build_index`, `load_index`, `query` signatures match the spec and are stable across tasks. The threshold parameter is named `threshold` consistently.

**No placeholders:** every code step has complete code; every test step has complete test code; every command has expected output.
