# Research Log

**Trajectory-conditioned behavioral perception** · Updated 2026-09-01

We publish our full experiment record, including results that did not hold up.
Items still open are marked **TBD**.

---

## Setup

| | |
|---|---|
| **Dataset** | WildChat-1M (allenai) — 1M real user–assistant conversations |
| **Our subset** | 11,832 events · 478 English trajectories · 2,313 human transitions |
| **Representation model** | Qwen2.5-0.5B-Instruct, frozen |
| **Annotator models** | Qwen2.5-7B and Qwen2.5-14B, run locally |
| **Human labels** | 12 events annotated blind, without seeing model labels |
| **Inter-annotator agreement** | **TBD** — single annotator to date; κ/α cannot be computed |
| **Ontology** | Seven transition types: `continue`, `new_topic`, `clarify`, `repair`, `correct`, `disagree`, `resist` |
| **Evaluated on** | Three of the seven — the rest had too few examples to score (Finding 5) |

---

## Findings

### 1. A model saying it's 97% sure means nothing

Qwen2.5-7B reported an average confidence of **0.968** on its own labels. Measured
against human annotation, it agreed exactly **66.7%** of the time.

| Annotator | Error (MAE) | Exact agreement |
|---|---|---|
| Qwen2.5-7B | 0.1875 | 66.7% |
| Qwen2.5-14B | 0.10 | 80% |
| Qwen2.5-72B | **TBD** | **TBD** |

Two failures show the pattern. When a user rephrased a request to get around a
refusal, 7B called it neutral (humans: clear pushback). When a user corrected the
assistant on a technical fact, 7B called it maximum pushback (humans: not pushback at
all — just a correction). 14B got both right.

> **Takeaway.** If you are using an LLM to label data, its stated confidence is not a
> quality signal. Budget for human adjudication.

### 2. Off-the-shelf embeddings sort by topic, not behavior

We tested whether a general-purpose language model's internal representations could
tell *what a user is doing* apart from *what they are talking about*. They mostly
can't — two users both complaining about broken code look similar; two users both
requesting a retry, on different topics, do not.

| Approach | Result |
|---|---|
| Subtracting the previous turn's embedding from the current one | Noisier than the plain embedding. Rejected |
| Retrieving by similarity to labeled examples of each class | Matched adjudication on ~5 of 25. Rejected |
| Purpose-built embedding model (bge-m3) | **TBD** — not yet tested |

> **Takeaway.** Behavioral perception needs purpose-built representations. Semantic
> similarity is not a shortcut to it.

### 3. Interesting behavior is rarer than keyword search suggests

We tried to find examples of user pushback by searching for likely phrases and
letting a model label them. Among randomly sampled controls, 7B flagged **36 of 77**
as pushback. In a hand-checked benchmark, the true rate was **1 in 20**. When 14B
re-examined ten of 7B's positives, it kept **one**.

> **Takeaway.** Keyword and single-model mining inflate what you're looking for
> rather than finding it. Base rates have to be measured, not assumed.

### 4. Observable transitions are easier to label than abstract scores

We started by scoring each turn for "resistance" on a 0–1 scale. Annotators — human
and model — could not apply it consistently. Replacing it with seven concrete
transition types made labeling tractable.

> **Takeaway.** Ask what happened, not how much of something it was.

### 5. Seven classes was more than our labels could support

With 52 labeled examples, classifying all seven types did worse than always guessing
the most common class:

| | Accuracy | Balanced accuracy |
|---|---|---|
| Our classifier | 0.288 | 0.160 |
| Always guess most common | 0.346 | 0.143 |

The cause was thin coverage — `correct` had 2 examples, `clarify` had 3. You cannot
evaluate a class with two instances. We narrowed to the three best-represented types
(`continue`, `new_topic`, `repair`) for everything below.

> **Takeaway.** The ontology outran the label budget. Narrowing was a data
> constraint, not a change of view about what matters. Note that `repair` — the
> hardest and most behaviorally interesting of the three — was kept, not dropped.

---

## The open question

> Does knowing what came earlier in a conversation tell you something about the
> current turn that the current turn alone does not?

This is the premise the product rests on. **We have not established it.**

We compared three conditions: the current turn alone, the current turn with a
*shuffled* (wrong) history, and the current turn with its *correct* history.

**First run — 36 examples**

| Condition | Accuracy |
|---|---|
| Current turn only | 0.417 |
| Wrong history | 0.417 |
| Correct history | **0.583** |

**Second run — 94 examples, split so no conversation appears in both training and
testing**

| Condition | Accuracy |
|---|---|
| Current turn only | 0.532 |
| Wrong history | 0.521 |
| Correct history | **0.447** |
| Keyword baseline (bag-of-words) | 0.521 |

The correct-history condition, which should have been best, came last.

**Third run — properly sized benchmark: TBD.** Not yet built. See Next, item 4.

### What the reanalysis showed

The results above were originally recorded without error bars. Adding them (Wilson
95% confidence intervals; random guessing = 0.333):

| Condition | 36 examples | 94 examples |
|---|---|---|
| Current turn only | 0.417 [0.271, 0.578] | 0.532 [0.432, 0.630] |
| Correct history | 0.583 [0.422, 0.729] | 0.447 [0.350, 0.547] |

The ranges overlap heavily in both runs. At this sample size, detecting a 20-point
difference needs ~95 examples; a 10-point difference needs ~389; a 5-point difference
needs ~1,565.

> **Correction.** We first recorded this as "the positive result failed to
> replicate." That overstates it. Neither run was large enough to tell a real effect
> from noise. Both are consistent with a genuine advantage and with none.

These intervals treat each prediction as independent, which understates uncertainty
because cross-validation folds share training data. The correct test is a paired
McNemar comparison over per-item predictions — **TBD**, requires re-running with
predictions retained.

**Two things we got wrong in the setup:**

The 94-example benchmark was compromised. A plain keyword model scored 0.521 — as
well as anything else — because we had selected `repair` examples by searching for
phrases like *didn't work*, *error*, and *fix*. The current turn already gave away
the answer, so history had nothing left to contribute.

The 36-example run doesn't record how it split training from test data. If the same
conversation appeared on both sides, the history features could have leaked the
answer — and only in the correct-history condition. That would explain the result
entirely. **Re-run with correct splitting: TBD** — one hour of work, not yet done.

---

## Open measurements

Numbers we do not have, and cannot honestly estimate until we do:

| Measurement | Status | Why it matters |
|---|---|---|
| **Base rate of history-dependence** | TBD | What fraction of real turns change label once history is visible. Determines whether the premise is worth pursuing at all |
| **Inter-annotator agreement (κ / α)** | TBD | Without it, no ground truth here has an error bar |
| **Grouped-CV re-run at n=36** | TBD | Resolves whether the original positive was leakage |
| **Paired McNemar test** | TBD | The statistically correct comparison |
| **Per-turn latency** | TBD | Not yet measured on any hardware |
| **Purpose-built embeddings (bge-m3)** | TBD | Whether the `repair` failure is the representation or the phenomenon |

---

## Not demonstrated

- Any reliable advantage from trajectory context over current-turn scoring
- Calibrated behavioral scores of any kind
- Production latency or multi-plane scoring

---

## Next

1. **Re-run the 36-example experiment with correct data splitting** — one hour,
   resolves the confound above
2. **Measure the base rate** — annotate blind to history, re-annotate with history
   after a washout, count how often the label changes
3. **Add a second annotator** — agreement can't be measured alone
4. **Build a properly sized benchmark** — several hundred examples across 300+
   conversations, constructed so the current turn is genuinely ambiguous
5. **Preregister the analysis** before the next redesign

---

## How we report

Every result includes the full comparison set — majority class, keyword baseline,
current-turn-only, wrong-history, correct-history. Every number carries a confidence
interval. Data is always split so no conversation appears in both training and test.
Model-generated labels are never treated as truth without human checking. Negative
results appear here with the same prominence as positive ones. Open items are marked
TBD rather than estimated.

Taxonomies are frozen and hashed: `resistance_v1.json` (`0f488b2a…`),
`behavioral_primitives_v1.json` (`63ee4d21…`).

Copyright 2026 Temperans AI.
