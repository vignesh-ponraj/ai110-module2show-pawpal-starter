# PawPal+ Reflection (Module 4)

This reflection covers the Module 4 increment that added a knowledge-base RAG ("Ask PawPal") to the existing PawPal+ scheduling app.

## Limitations and biases

- **The corpus is small and hand-written.** Twenty ~120-word snippets cannot cover the breadth of real pet-care questions. Anything outside the topics I picked (walking, feeding, grooming, dental, nails, enrichment, socialization, common meds, toxic foods, illness signs, senior care, vaccinations, spay/neuter, house training, litter box, exercise safety) is correctly refused — but a user might mistake a refusal for the system being broken.
- **The corpus reflects my own biases as the author.** I drew from general pet-care knowledge in my own head, biased toward dogs and cats in temperate climates with average-income owners. Exotic pets, working dogs, very small or very large breeds with breed-specific conditions, and culturally specific care practices are underrepresented.
- **`all-MiniLM-L6-v2` is an English-only model trained on general web text.** Non-English questions, technical veterinary jargon, and dialect/slang ("zoomies", "FLUTD") may retrieve poorly even when the corpus would have a relevant answer.
- **The 0.35 confidence threshold is a single global number.** Some questions that score 0.34 are answerable from the corpus; some that score 0.36 are not. A more honest system would learn the threshold per-topic or expose calibrated probabilities.
- **No fact-checking.** If a snippet I wrote contains an error (e.g., a wrong dosage), the system will confidently cite that error. The "citation" gives the appearance of authority without an authoritative source.

## Could it be misused, and how would I prevent that?

The realistic misuse path is **medical reliance**: a user could ask about medication dosages, toxic-food intake amounts, or illness symptoms and treat the cited snippet as veterinary advice. Even though the snippets are written conservatively (e.g., "call your vet" appears in `signs_of_illness.md`, `toxic_foods.md`, `common_meds.md`), the appearance of a confident, cited answer can shift behavior.

Mitigations I would add if this were going beyond a class demo:

1. A persistent **"This is not veterinary advice"** banner above the answer area (not just at the bottom or in fine print).
2. **Topic-specific guardrails**: detect questions about dosing, ingestion amounts, or acute illness and force a "call your vet" preface even when the cosine score is high.
3. **A more conservative threshold for medical-adjacent files** (`common_meds.md`, `toxic_foods.md`, `signs_of_illness.md`) — say 0.55 instead of 0.35 — so borderline matches in those areas refuse rather than answer.
4. **Logging of refused queries** so I can see what users are actually asking that the system can't answer; some of those reveal real gaps to expand the corpus, others reveal misuse patterns to guard against.

## What surprised me while testing

The most surprising finding was how *unreliable* a simple cosine threshold is at the boundary. I'd assumed unrelated questions like "what's the capital of France?" would score near 0 — they don't. They score around 0.3 against this corpus, just because *any* English question shares some surface vocabulary with *any* English document. My initial test threshold of 0.5 was being silently passed by off-topic questions, which would have looked fine in tests but produced garbage answers in a real demo. I had to switch to a more obviously off-topic question (*"explain quantum mechanics in detail"*) and raise the test threshold to 0.6 to actually verify the refusal path.

The lesson was: **confidence scores from sentence embeddings are not probabilities**, and a fixed threshold without visible surfacing is a false sense of security. That's why the final UI shows the top-3 retrieved snippets with their cosine scores on every query — it makes the model's confidence (or lack of it) legible to a human in real time, rather than hiding it behind a gate.

## AI collaboration on this project

I worked through this project iteratively with an AI assistant, using it for design brainstorming, code generation, test writing, and code review. The collaboration was structured: a brainstorming pass to lock in requirements, a written design spec, an implementation plan broken into ten small tasks, and a TDD workflow with separate spec-compliance and code-quality reviews after each task.

**One helpful AI suggestion.** When I described the RAG feature, my first instinct was to use a small local LLM (e.g., Ollama llama3.2:3b) for answer synthesis. The AI suggested I consider a non-LLM "extractive" path instead — return the top-1 retrieved snippet verbatim with a citation, no synthesis. The trade-off it surfaced was sharp: an LLM gives more conversational answers, but adds a 2GB runtime dependency, slower responses, and the possibility of hallucinated content drifting from the cited source. For a class demo on a 20-document corpus, deterministic citation with zero hallucination was the right call. I would not have made that choice on my own — I would have over-built. The AI's framing of the trade-off let me make a smaller, better system.

**One flawed AI suggestion.** During implementation, the AI initially produced a `query` test that asked *"what is the capital of France?"* with `threshold=0.5` and asserted the system would refuse. On my corpus, this question scored *above* 0.5 because the embedding model finds incidental surface similarity between any English question and any English document. The test passed locally for the AI in its head-model but would have failed in CI — and worse, it gave the false impression that a 0.5 threshold was sufficient to block off-topic questions. The bug surfaced when the test was actually run against the real model. The fix was a more clearly off-topic question and a higher test threshold, plus a permanent UI feature (the top-3 score table) so the same kind of false confidence couldn't hide in production. The lesson: AI-suggested tests can confidently assert behavior that doesn't survive real execution; running the test, not just reading it, is non-optional.

## Key takeaway

For grounded AI features on small, well-defined domains, the most valuable design decisions are about **what *not* to do**: don't add an LLM if retrieval alone answers the question, don't hide confidence behind a single number, don't trust thresholds without seeing them in action, and don't let a "citation" stand in for an authoritative source. The visible-score expander in the UI and the "I can't answer" output are not features I added — they're features I refused to omit, and they are what make the system trustworthy enough to demo.
