"""
Hallucination & Groundedness Evaluator
Deterministic claim-level faithfulness verifier comparing LLM responses against
grounding context documents. Detects fabricated numeric claims, unsupported named
entities, and negation polarity contradictions.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

_STOPWORDS: frozenset[str] = frozenset(
    {
        "a",
        "about",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "been",
        "being",
        "by",
        "for",
        "from",
        "had",
        "has",
        "have",
        "in",
        "into",
        "is",
        "it",
        "its",
        "may",
        "might",
        "of",
        "on",
        "or",
        "over",
        "should",
        "that",
        "the",
        "this",
        "through",
        "to",
        "using",
        "via",
        "was",
        "were",
        "will",
        "with",
        "would",
    }
)

_NEGATION_WORDS: frozenset[str] = frozenset(
    {
        "aren't",
        "can't",
        "cannot",
        "didn't",
        "doesn't",
        "don't",
        "isn't",
        "neither",
        "never",
        "no",
        "none",
        "nor",
        "not",
        "wasn't",
        "weren't",
        "without",
        "won't",
    }
)

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|\n+")
_BULLET_PREFIX_RE = re.compile(r"^\s*(?:[-*]|\d+[.)])\s+")
_TOKEN_RE = re.compile(r"[a-z0-9]+(?:'[a-z]+)?")
_NUMBER_RE = re.compile(r"(?<![a-zA-Z0-9])(\d[\d,]*(?:\.\d+)?%?)")
_ENTITY_RE = re.compile(r"\b([A-Z][a-zA-Z0-9-]{2,}|[A-Z]{2,}[0-9]*)\b")


@dataclass
class ClaimVerdict:
    """Groundedness assessment for an individual response claim."""

    claim: str
    supported: bool
    support_score: float
    missing_anchors: list[str] = field(default_factory=list)
    reason: str = "Grounded in context"


@dataclass
class HallucinationReport:
    """Aggregate faithfulness & hallucination report for an LLM response."""

    is_grounded: bool
    groundedness_score: float
    hallucination_risk: float
    total_claims: int
    grounded_claims: int
    ungrounded_claims: list[ClaimVerdict] = field(default_factory=list)


def _split_claims(text: str) -> list[str]:
    """Split text into non-empty normalized claim strings."""
    claims: list[str] = []
    for raw_part in _SENTENCE_SPLIT_RE.split(text.strip()):
        cleaned = _BULLET_PREFIX_RE.sub("", raw_part).strip()
        if not cleaned:
            continue
        tokens = _TOKEN_RE.findall(cleaned.lower())
        if len(tokens) >= 2 or bool(_NUMBER_RE.search(cleaned)):
            claims.append(cleaned)
    return claims


def _content_tokens(text: str) -> set[str]:
    """Extract lowercase content tokens excluding stopwords and negations."""
    return {
        tok
        for tok in _TOKEN_RE.findall(text.lower())
        if tok not in _STOPWORDS and tok not in _NEGATION_WORDS and len(tok) > 1
    }


def _skip_bigrams(tokens: list[str], max_gap: int = 2) -> set[tuple[str, str]]:
    """Construct token pairs within max_gap positions to tolerate light paraphrasing."""
    pairs: set[tuple[str, str]] = set()
    for i in range(len(tokens)):
        for j in range(i + 1, min(len(tokens), i + 1 + max_gap)):
            pairs.add((tokens[i], tokens[j]))
    return pairs


def _extract_numeric_anchors(text: str) -> set[str]:
    """Extract normalized numeric tokens (preserving '%' suffix)."""
    return {m.replace(",", "") for m in _NUMBER_RE.findall(text)}


def _extract_entity_anchors(text: str) -> set[str]:
    """Extract mid-sentence capitalized entities and all-caps acronyms."""
    anchors: set[str] = set()
    for match in _ENTITY_RE.finditer(text):
        word = match.group(1)
        is_acronym = word.isupper() and len(word) >= 2
        at_start = match.start() == 0
        if is_acronym or not at_start:
            anchors.add(word)
    return anchors


def _has_negation(text: str) -> bool:
    """Return True if any negation marker appears in text."""
    return bool(_NEGATION_WORDS.intersection(_TOKEN_RE.findall(text.lower())))


class HallucinationDetector:
    """Deterministic claim-level faithfulness evaluator against source context."""

    def __init__(self, min_claim_support: float = 0.5, min_groundedness: float = 0.6) -> None:
        if not 0.0 <= min_claim_support <= 1.0:
            raise ValueError("min_claim_support must be between 0.0 and 1.0")
        if not 0.0 <= min_groundedness <= 1.0:
            raise ValueError("min_groundedness must be between 0.0 and 1.0")
        self.min_claim_support = min_claim_support
        self.min_groundedness = min_groundedness

    def evaluate(
        self,
        context: str | list[str],
        response: str,
        min_groundedness: float | None = None,
    ) -> HallucinationReport:
        """Evaluate whether response claims are faithful to the provided context."""
        if not response or not response.strip():
            raise ValueError("response must be a non-empty string")

        threshold = self.min_groundedness if min_groundedness is None else min_groundedness
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("min_groundedness must be between 0.0 and 1.0")

        context_text = (
            "\n".join(doc for doc in context if doc and doc.strip())
            if isinstance(context, list)
            else context
        )
        claims = _split_claims(response)
        if not claims:
            claims = [response.strip()]

        if not context_text or not context_text.strip():
            verdicts = [
                ClaimVerdict(
                    claim=c,
                    supported=False,
                    support_score=0.0,
                    reason="No reference context provided",
                )
                for c in claims
            ]
            return HallucinationReport(
                is_grounded=False,
                groundedness_score=0.0,
                hallucination_risk=1.0,
                total_claims=len(claims),
                grounded_claims=0,
                ungrounded_claims=verdicts,
            )

        context_sentences = _split_claims(context_text) or [context_text]
        ctx_tokens = _content_tokens(context_text)
        ctx_seq = [t for t in _TOKEN_RE.findall(context_text.lower()) if t not in _STOPWORDS]
        ctx_bigrams = _skip_bigrams(ctx_seq)
        ctx_numbers = _extract_numeric_anchors(context_text)
        ctx_entities_lower = {e.lower() for e in _extract_entity_anchors(context_text)} | ctx_tokens

        sentence_profiles = [
            (_content_tokens(sent), _has_negation(sent)) for sent in context_sentences
        ]

        verdicts = [
            self._assess_claim(
                claim=claim,
                ctx_tokens=ctx_tokens,
                ctx_bigrams=ctx_bigrams,
                ctx_numbers=ctx_numbers,
                ctx_entities_lower=ctx_entities_lower,
                sentence_profiles=sentence_profiles,
            )
            for claim in claims
        ]

        grounded_count = sum(1 for v in verdicts if v.supported)
        avg_score = round(sum(v.support_score for v in verdicts) / len(verdicts), 4)
        ungrounded = [v for v in verdicts if not v.supported]
        has_hard_fabrication = any(bool(v.missing_anchors) for v in ungrounded)
        is_grounded = avg_score >= threshold and not has_hard_fabrication and len(ungrounded) == 0

        return HallucinationReport(
            is_grounded=is_grounded,
            groundedness_score=avg_score,
            hallucination_risk=round(1.0 - avg_score, 4),
            total_claims=len(verdicts),
            grounded_claims=grounded_count,
            ungrounded_claims=ungrounded,
        )

    def _assess_claim(
        self,
        *,
        claim: str,
        ctx_tokens: set[str],
        ctx_bigrams: set[tuple[str, str]],
        ctx_numbers: set[str],
        ctx_entities_lower: set[str],
        sentence_profiles: list[tuple[set[str], bool]],
    ) -> ClaimVerdict:
        claim_tokens = _content_tokens(claim)
        claim_numbers = _extract_numeric_anchors(claim)
        claim_entities = _extract_entity_anchors(claim)

        missing_numbers = sorted(n for n in claim_numbers if n not in ctx_numbers)
        missing_entities = sorted(
            e for e in claim_entities if e.lower() not in ctx_entities_lower
        )
        missing_anchors = missing_numbers + missing_entities

        if claim_tokens:
            token_recall = len(claim_tokens & ctx_tokens) / len(claim_tokens)
        else:
            token_recall = 1.0 if not missing_anchors else 0.0

        claim_seq = [t for t in _TOKEN_RE.findall(claim.lower()) if t not in _STOPWORDS]
        claim_bg = _skip_bigrams(claim_seq)
        bigram_recall = (len(claim_bg & ctx_bigrams) / len(claim_bg)) if claim_bg else token_recall

        # Check polarity alignment against the highest-overlap source sentence
        claim_neg = _has_negation(claim)
        best_overlap = 0.0
        best_sent_neg = claim_neg
        for sent_tokens, sent_neg in sentence_profiles:
            if not claim_tokens or not sent_tokens:
                continue
            overlap = len(claim_tokens & sent_tokens) / len(claim_tokens)
            if overlap > best_overlap:
                best_overlap = overlap
                best_sent_neg = sent_neg

        polarity_contradiction = best_overlap >= 0.45 and claim_neg != best_sent_neg

        base_score = 0.7 * token_recall + 0.3 * bigram_recall
        if missing_anchors:
            anchor_count = max(1, len(claim_numbers) + len(claim_entities))
            anchor_penalty = 0.65 * (len(missing_anchors) / anchor_count)
            base_score = max(0.0, base_score - anchor_penalty)
        if polarity_contradiction:
            base_score = min(base_score, 0.15)

        support_score = round(min(1.0, max(0.0, base_score)), 4)

        if polarity_contradiction:
            return ClaimVerdict(
                claim=claim,
                supported=False,
                support_score=support_score,
                missing_anchors=missing_anchors,
                reason="Polarity contradiction against source context",
            )
        if missing_anchors:
            return ClaimVerdict(
                claim=claim,
                supported=False,
                support_score=support_score,
                missing_anchors=missing_anchors,
                reason=f"Unsupported factual anchors: {', '.join(missing_anchors)}",
            )
        if support_score < self.min_claim_support:
            return ClaimVerdict(
                claim=claim,
                supported=False,
                support_score=support_score,
                reason="Insufficient semantic overlap with reference context",
            )
        return ClaimVerdict(
            claim=claim,
            supported=True,
            support_score=support_score,
            reason="Grounded in context",
        )


def evaluate_groundedness(
    context: str | list[str],
    response: str,
    min_groundedness: float = 0.6,
) -> HallucinationReport:
    """Convenience function evaluating response faithfulness against context."""
    return HallucinationDetector(min_groundedness=min_groundedness).evaluate(context, response)
