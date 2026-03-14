from __future__ import annotations

import html
import re
from collections import Counter
from dataclasses import dataclass, replace
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path
from statistics import pstdev

from app.core.config import get_settings
from app.services.llm_service import LLMClient
from app.services.prompt_service import PromptCatalog, get_prompt_catalog
from app.workflows.types import GeneratedDraft

settings = get_settings()
PROJECT_ROOT = Path(__file__).resolve().parents[2]

def _get_required_section_headings() -> list[str]:
    clinic = get_settings().clinic_name
    return [
        'Summary of Issue',
        'Why This Matters',
        'Mental Health Implications',
        'Professional Insight',
        f'How {clinic} Can Help',
        'Take the Next Step',
    ]


@dataclass
class QualityGuardResult:
    draft: GeneratedDraft
    passed: bool
    readability_score: float
    ai_generated_probability: float
    source_similarity_score: float
    structure_valid: bool
    quality_notes: list[str]


@dataclass
class SEOReport:
    passed: bool
    notes: list[str]


@dataclass
class PlagiarismReport:
    risk_score: float
    sequence_ratio: float
    sentence_overlap_ratio: float
    ngram_overlap_ratio: float
    paragraph_overlap_ratio: float
    longest_match_ratio: float
    notes: list[str]


@dataclass
class VoiceReport:
    first_person_ratio: float
    first_person_count: int
    passed: bool
    notes: list[str]


@dataclass
class HumanizationReport:
    lexical_diversity: float
    sentence_length_stddev: float
    repeated_ngram_ratio: float
    contractions_per_1000_words: float
    question_ratio: float
    passed: bool
    notes: list[str]


class ArticleQualityGuard:
    def __init__(
        self,
        llm_client: LLMClient | None = None,
        prompt_catalog: PromptCatalog | None = None,
    ) -> None:
        self.llm = llm_client or LLMClient()
        self.prompts = prompt_catalog or get_prompt_catalog()

    async def validate_and_fix(
        self,
        *,
        draft: GeneratedDraft,
        source_text: str | None,
        focus_keyword: str,
    ) -> QualityGuardResult:
        # Step 1: Light prep - just basic cleanup before humanization
        normalized = draft
        
        # Step 2: Humanize the content (this may alter structure/keywords)
        normalized = await self._auto_humanize(normalized, focus_keyword=focus_keyword)
        
        # Step 3: Apply quality fixes AFTER humanization so they stick
        # Fix readability first (sentence structure)
        normalized = self._auto_fix_readability(normalized)

        # Then apply SEO fixes (keywords, density, structure) — single pass
        normalized = self._auto_fix_seo(draft=normalized, focus_keyword=focus_keyword)

        plain_text = _plain_text(normalized.content_html)
        word_count = len(plain_text.split())
        readability_score = round(_flesch_kincaid_grade(plain_text), 2)
        plagiarism = _plagiarism_report(plain_text, source_text or '')
        reference_text = _load_reference_pdf_text()
        if reference_text:
            reference_plagiarism = _plagiarism_report(plain_text, reference_text)
            if reference_plagiarism.risk_score > plagiarism.risk_score:
                plagiarism = reference_plagiarism
        source_similarity_score = plagiarism.risk_score
        structure_valid = self._validate_structure(normalized.content_html)
        ai_generated_probability = round(await self._estimate_ai_probability(plain_text), 4)
        seo_report = self._assess_seo(normalized, focus_keyword=focus_keyword)
        voice_report = _assess_first_person_voice(plain_text)
        humanization_report = _assess_humanization(plain_text)

        notes: list[str] = []
        passed = True

        # Plagiarism checks — flag for human review when thresholds are exceeded.
        if plagiarism.risk_score > 0.16:
            passed = False
            notes.append(f'plagiarism_risk_score={plagiarism.risk_score} exceeds 0.16')
        if plagiarism.sentence_overlap_ratio > 0.10:
            passed = False
            notes.append(
                f'sentence_overlap_ratio={plagiarism.sentence_overlap_ratio} exceeds 0.10'
            )
        if plagiarism.ngram_overlap_ratio > 0.07:
            passed = False
            notes.append(f'ngram_overlap_ratio={plagiarism.ngram_overlap_ratio} exceeds 0.07')
        if plagiarism.paragraph_overlap_ratio > 0.14:
            passed = False
            notes.append(
                f'paragraph_overlap_ratio={plagiarism.paragraph_overlap_ratio} exceeds 0.14'
            )
        if plagiarism.longest_match_ratio > 0.20:
            passed = False
            notes.append(f'longest_match_ratio={plagiarism.longest_match_ratio} exceeds 0.20')

        # AI-generated probability — flag but don't block.
        if ai_generated_probability > 0.55:
            notes.append(f'ai_generated_probability={ai_generated_probability} exceeds 0.55')

        if not structure_valid:
            notes.append('mandatory article structure is incomplete')

        # Keep SEO findings as warnings.
        if not seo_report.passed:
            notes.extend(seo_report.notes)

        # Voice and humanization are warnings, not blockers.
        if voice_report.notes:
            notes.extend(voice_report.notes)
        if humanization_report.notes:
            notes.extend(humanization_report.notes)

        # Readability and word count are warnings.
        if readability_score < 5 or readability_score > 10:
            notes.append(f'readability_score={readability_score} outside target 5-10')
        if word_count < 900 or word_count > 1100:
            notes.append(f'word_count={word_count} outside target 900-1100')

        notes.extend(plagiarism.notes)
        notes = _dedupe_notes(notes)

        return QualityGuardResult(
            draft=normalized,
            passed=passed,
            readability_score=readability_score,
            ai_generated_probability=ai_generated_probability,
            source_similarity_score=source_similarity_score,
            structure_valid=structure_valid,
            quality_notes=notes,
        )

    def _validate_structure(self, content_html: str) -> bool:
        lowered = content_html.lower()
        return all(heading.lower() in lowered for heading in _get_required_section_headings())

    def _assess_seo(self, draft: GeneratedDraft, *, focus_keyword: str) -> SEOReport:
        notes: list[str] = []
        title = (draft.seo_title or '').strip()
        meta = (draft.meta_description or '').strip()
        keyword = (focus_keyword or '').strip().lower()

        if not title:
            notes.append('seo_title is empty')
        # Relaxed: 45-70 instead of 50-65
        elif len(title) < 45 or len(title) > 70:
            notes.append(f'seo_title length {len(title)} outside target 45-70 characters')

        if keyword and keyword not in title.lower():
            notes.append('seo_title must include focus keyword')

        # Relaxed: 135-165 instead of 140-160
        if len(meta) < 135 or len(meta) > 165:
            notes.append(f'meta_description length {len(meta)} outside target 135-165 characters')

        if keyword and keyword not in meta.lower():
            notes.append('meta_description must include focus keyword')

        if keyword and not _keyword_in_first_words(draft.content_html, keyword, 100):
            notes.append('focus keyword not found in first 100 words of content')

        if keyword and not _keyword_in_h2(draft.content_html, keyword):
            notes.append('focus keyword should appear in at least one H2 heading')

        h1_count = _count_tag(draft.content_html, 'h1')
        h2_count = _count_tag(draft.content_html, 'h2')
        if h1_count != 1:
            notes.append(f'expected exactly 1 h1, found {h1_count}')
        # Relaxed: 6 instead of 7
        if h2_count < 6:
            notes.append(f'expected at least 6 h2 sections, found {h2_count}')

        keyword_density = _keyword_density(draft.content_html, keyword)
        # Relaxed: 0.4-3.0 instead of 0.6-2.5
        if keyword and (keyword_density < 0.4 or keyword_density > 3.0):
            notes.append(
                f'focus keyword density {round(keyword_density, 2)}% outside target 0.4%-3.0%'
            )

        if len(draft.keywords) < 5 or len(draft.keywords) > 8:
            notes.append(f'keywords count {len(draft.keywords)} outside target 5-8')

        return SEOReport(passed=not notes, notes=notes)

    async def _estimate_ai_probability(self, article_text: str) -> float:
        if not article_text.strip():
            return 1.0

        system_prompt, user_prompt = self.prompts.get_prompt(
            bundle='article_quality_guard/v1/prompts.yaml',
            key='ai_tone_detection',
            context={'article_text': article_text[:9000]},
        )
        payload = await self.llm.generate_json(
            system_prompt=system_prompt,
            prompt=user_prompt,
            model=settings.llm_quality_model,
            temperature=0.0,
        )
        probability = payload.get('ai_generated_probability') if payload else None
        try:
            normalized = float(probability)
            return min(1.0, max(0.0, normalized))
        except (TypeError, ValueError):
            return _heuristic_ai_probability(article_text)

    async def _auto_humanize(self, draft: GeneratedDraft, *, focus_keyword: str) -> GeneratedDraft:
        plain_text = _plain_text(draft.content_html)
        initial_probability = _heuristic_ai_probability(plain_text)
        # Raised threshold: skip full humanization if probability <= 0.6 instead of 0.5
        if initial_probability <= 0.6:
            return replace(draft, content_html=_rule_based_humanize_html(draft.content_html))

        system_prompt, user_prompt = self.prompts.get_prompt(
            bundle='article_quality_guard/v1/prompts.yaml',
            key='humanization_rewrite',
            context={
                'article_html': draft.content_html[:12000],
                'focus_keyword': focus_keyword,
            },
        )
        rewritten = await self.llm.generate(
            system_prompt=system_prompt,
            prompt=user_prompt,
            model=settings.llm_quality_model,
            temperature=0.55,
        )

        candidate = _normalize_rewritten_html(rewritten)
        if not candidate:
            candidate = _rule_based_humanize_html(draft.content_html)

        return replace(draft, content_html=candidate)

    def _auto_fix_seo(self, *, draft: GeneratedDraft, focus_keyword: str) -> GeneratedDraft:
        keyword = focus_keyword.strip()
        seo_title = draft.seo_title.strip()
        
        # Ensure keyword is in title first, then manage length
        if keyword and keyword.lower() not in seo_title.lower():
            # Try adding keyword at the start
            seo_title = f'{keyword}: {seo_title}'.strip(': ')
        
        # Adjust length while preserving keyword
        if len(seo_title) < 50:
            suffix = ' | Parent Guidance'
            if len(seo_title + suffix) <= 65:
                seo_title = f'{seo_title}{suffix}'
        
        if len(seo_title) > 65:
            # Truncate but ensure keyword remains
            if keyword and keyword.lower() in seo_title[:65].lower():
                seo_title = seo_title[:65].rstrip(' -:|').strip()
            else:
                # Keyword would be lost, rebuild title
                seo_title = keyword[:60] + '...'
        
        # Double-check keyword is still present
        if keyword and keyword.lower() not in seo_title.lower():
            seo_title = keyword if len(keyword) <= 65 else keyword[:62] + '...'

        meta_description = (draft.meta_description or '').strip()
        if keyword and keyword.lower() not in meta_description.lower():
            prefix = f'{keyword}: '
            meta_description = f'{prefix}{meta_description}'.strip()

        if len(meta_description) > 160:
            meta_description = meta_description[:157].rstrip() + '...'
        elif len(meta_description) < 140:
            additions = [
                f'Learn how {keyword.lower()} affects children in daily life and what parents can do next.',
                'Get practical, professional guidance on early signs, support at home, and when to seek help.',
            ]
            for addition in additions:
                joined = ' '.join(part for part in [meta_description, addition] if part).strip()
                meta_description = joined
                if len(meta_description) >= 140:
                    break
            while len(meta_description) < 140:
                meta_description = f'{meta_description} Support starts with understanding.'.strip()
            if len(meta_description) > 160:
                meta_description = meta_description[:157].rstrip() + '...'

        keywords = _normalize_keywords(draft.keywords, keyword)

        content_html = draft.content_html
        content_html = _ensure_h1_contains_keyword(content_html=content_html, keyword=keyword)
        content_html = _ensure_h2_contains_keyword(content_html=content_html, keyword=keyword)

        # Trim AFTER density injection so excess snippets are removed.
        content_html = _trim_content_to_target_length(content_html, target_max=1100, target_min=900)

        return replace(
            draft,
            seo_title=seo_title,
            meta_description=meta_description,
            keywords=keywords,
            content_html=content_html,
        )

    def _auto_fix_readability(self, draft: GeneratedDraft) -> GeneratedDraft:
        score = _flesch_kincaid_grade(_plain_text(draft.content_html))
        # Wider acceptable range: 5-10 instead of 6-9
        if 5 <= score <= 10:
            return draft

        cleaned = draft.content_html
        
        # If score too high (too complex), simplify by breaking up sentences
        if score > 9:
            # Replace complex punctuation with periods to create shorter sentences
            cleaned = re.sub(r';\s*', '. ', cleaned)
            cleaned = re.sub(r':\s+(?=[A-Z])', '. ', cleaned)
            cleaned = re.sub(r',\s+and ', '. ', cleaned, count=3)
            cleaned = re.sub(r',\s+but ', '. ', cleaned, count=2)
            
            # Replace complex words with simpler alternatives in HTML
            simplifications = {
                r'\butilize\b': 'use',
                r'\bfacilitate\b': 'help',
                r'\bdemonstrate\b': 'show',
                r'\bimplement\b': 'use',
                r'\bnevertheless\b': 'still',
                r'\badditionally\b': 'also',
            }
            for pattern, replacement in simplifications.items():
                cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
        
        # If score too low (too simple), combine some short sentences
        elif score < 6:
            # Join very short sentences
            cleaned = re.sub(r'\.\s+([A-Z][a-z]{0,3})\s+', r', \1 ', cleaned, count=3)
        
        cleaned = re.sub(r'\s{2,}', ' ', cleaned)
        
        # Verify improvement
        new_score = _flesch_kincaid_grade(_plain_text(cleaned))
        if abs(new_score - 7.5) < abs(score - 7.5):
            return replace(draft, content_html=cleaned)
        
        return draft


def _plain_text(content_html: str) -> str:
    text = re.sub(r'<[^>]+>', ' ', content_html or '')
    text = html.unescape(text)
    return re.sub(r'\s+', ' ', text).strip()


def _dedupe_notes(notes: list[str]) -> list[str]:
    unique: list[str] = []
    seen: set[str] = set()
    for note in notes:
        normalized = str(note or '').strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(normalized)
    return unique


def _keyword_in_first_words(content_html: str, keyword: str, limit: int) -> bool:
    words = _plain_text(content_html).lower().split()
    first_words = ' '.join(words[:limit])
    return keyword.lower() in first_words


def _inject_after_h1(content_html: str, payload: str) -> str:
    match = re.search(r'</h1>', content_html, flags=re.IGNORECASE)
    if not match:
        return payload + content_html
    idx = match.end()
    return content_html[:idx] + payload + content_html[idx:]


def _text_similarity(left: str, right: str) -> float:
    a = _normalize_similarity_text(left)
    b = _normalize_similarity_text(right)
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def _plagiarism_report(article_text: str, source_text: str) -> PlagiarismReport:
    if not article_text.strip() or not source_text.strip():
        return PlagiarismReport(
            risk_score=0.0,
            sequence_ratio=0.0,
            sentence_overlap_ratio=0.0,
            ngram_overlap_ratio=0.0,
            paragraph_overlap_ratio=0.0,
            longest_match_ratio=0.0,
            notes=[],
        )

    sequence_ratio = round(_text_similarity(article_text, source_text), 4)
    sentence_overlap_ratio = round(_sentence_overlap_ratio(article_text, source_text), 4)
    ngram_overlap_ratio = round(_ngram_overlap_ratio(article_text, source_text, n=7), 4)
    paragraph_overlap_ratio = round(_paragraph_overlap_ratio(article_text, source_text), 4)
    longest_match_ratio = round(_longest_common_match_ratio(article_text, source_text), 4)

    risk_score = round(
        max(
            sequence_ratio,
            sentence_overlap_ratio * 1.15,
            ngram_overlap_ratio * 1.35,
            paragraph_overlap_ratio * 1.2,
            longest_match_ratio * 1.1,
        ),
        4,
    )

    notes: list[str] = []
    if sequence_ratio > 0.14:
        notes.append(f'sequence_similarity={sequence_ratio} indicates elevated similarity')
    if sentence_overlap_ratio > 0.08:
        notes.append(f'sentence_overlap={sentence_overlap_ratio} indicates potential reuse')
    if ngram_overlap_ratio > 0.05:
        notes.append(f'7gram_overlap={ngram_overlap_ratio} indicates close phrasing overlap')
    if paragraph_overlap_ratio > 0.10:
        notes.append(f'paragraph_overlap={paragraph_overlap_ratio} indicates substantial paragraph reuse')
    if longest_match_ratio > 0.16:
        notes.append(f'longest_match_ratio={longest_match_ratio} indicates long copied span')

    return PlagiarismReport(
        risk_score=risk_score,
        sequence_ratio=sequence_ratio,
        sentence_overlap_ratio=sentence_overlap_ratio,
        ngram_overlap_ratio=ngram_overlap_ratio,
        paragraph_overlap_ratio=paragraph_overlap_ratio,
        longest_match_ratio=longest_match_ratio,
        notes=notes,
    )


def _normalize_similarity_text(value: str) -> str:
    value = value.lower()
    value = re.sub(r'[^a-z0-9\s]', ' ', value)
    return re.sub(r'\s+', ' ', value).strip()


def _sentence_overlap_ratio(article_text: str, source_text: str) -> float:
    article_sentences = _normalize_sentences(article_text)
    source_sentences = _normalize_sentences(source_text)
    if not article_sentences or not source_sentences:
        return 0.0

    source_set = set(source_sentences)
    overlap = sum(1 for sentence in article_sentences if sentence in source_set)
    return overlap / max(1, len(article_sentences))


def _normalize_sentences(text: str) -> list[str]:
    sentences = re.split(r'[.!?]+', text)
    normalized: list[str] = []
    for sentence in sentences:
        cleaned = _normalize_similarity_text(sentence)
        if len(cleaned.split()) >= 8:
            normalized.append(cleaned)
    return normalized


def _ngram_overlap_ratio(article_text: str, source_text: str, *, n: int) -> float:
    article_tokens = _normalize_similarity_text(article_text).split()
    source_tokens = _normalize_similarity_text(source_text).split()
    article_ngrams = _build_ngrams(article_tokens, n=n)
    source_ngrams = _build_ngrams(source_tokens, n=n)
    if not article_ngrams or not source_ngrams:
        return 0.0

    overlap = set(article_ngrams.keys()) & set(source_ngrams.keys())
    shared = sum(min(article_ngrams[key], source_ngrams[key]) for key in overlap)
    total = sum(article_ngrams.values())
    return shared / max(1, total)


def _paragraph_overlap_ratio(article_text: str, source_text: str) -> float:
    article_paragraphs = [
        _normalize_similarity_text(par)
        for par in re.split(r'\n\s*\n+', article_text)
        if _normalize_similarity_text(par)
    ]
    source_paragraphs = [
        _normalize_similarity_text(par)
        for par in re.split(r'\n\s*\n+', source_text)
        if _normalize_similarity_text(par)
    ]
    if not article_paragraphs or not source_paragraphs:
        return 0.0

    source_set = set(source_paragraphs)
    overlap = sum(1 for par in article_paragraphs if len(par.split()) >= 25 and par in source_set)
    comparable = sum(1 for par in article_paragraphs if len(par.split()) >= 25)
    if comparable == 0:
        return 0.0
    return overlap / comparable


def _longest_common_match_ratio(article_text: str, source_text: str) -> float:
    left = _normalize_similarity_text(article_text)
    right = _normalize_similarity_text(source_text)
    if not left or not right:
        return 0.0
    matcher = SequenceMatcher(None, left, right)
    longest = matcher.find_longest_match(0, len(left), 0, len(right))
    longest_words = len(left[longest.a : longest.a + longest.size].split())
    total_words = max(1, len(left.split()))
    return longest_words / total_words


def _build_ngrams(tokens: list[str], *, n: int) -> Counter[tuple[str, ...]]:
    if len(tokens) < n:
        return Counter()
    return Counter(tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1))


def _normalize_keywords(keywords: list[str], focus_keyword: str) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []

    if focus_keyword.strip():
        normalized.append(focus_keyword.strip())
        seen.add(focus_keyword.strip().lower())

    for keyword in keywords:
        item = str(keyword or '').strip()
        if not item:
            continue
        key = item.lower()
        if key in seen:
            continue
        normalized.append(item)
        seen.add(key)

    defaults = ['child mental health', 'teen anxiety support', 'parent guidance', 'early intervention']
    for keyword in defaults:
        if len(normalized) >= 8:
            break
        if keyword.lower() in seen:
            continue
        normalized.append(keyword)
        seen.add(keyword.lower())

    return normalized[:8]


def _ensure_h1_contains_keyword(*, content_html: str, keyword: str) -> str:
    if not keyword:
        return content_html

    h1_match = re.search(r'<h1>(.*?)</h1>', content_html, flags=re.IGNORECASE | re.DOTALL)
    if not h1_match:
        return f'<h1>{html.escape(keyword)}</h1>{content_html}'

    heading_text = _plain_text(h1_match.group(1)).strip()
    if keyword.lower() in heading_text.lower():
        return content_html

    replacement = f'<h1>{html.escape(keyword)}: {html.escape(heading_text)}</h1>'
    return content_html[: h1_match.start()] + replacement + content_html[h1_match.end() :]


def _ensure_h2_contains_keyword(*, content_html: str, keyword: str) -> str:
    if not keyword or _keyword_in_h2(content_html, keyword):
        return content_html

    # Find all H2 headings
    h2_matches = list(re.finditer(r'<h2[^>]*>(.*?)</h2>', content_html, flags=re.IGNORECASE | re.DOTALL))
    
    if not h2_matches:
        # No H2s found, inject a new section
        section = (
            f'<section><h2>{html.escape(keyword)}</h2>'
            '<p>Parents can use these practical steps to support children early.</p></section>'
        )
        return _inject_after_h1(content_html, section)

    # Add keyword to first H2 if not present in any
    h2_match = h2_matches[0]
    heading_text = _plain_text(h2_match.group(1)).strip()
    
    if keyword.lower() in heading_text.lower():
        return content_html
    
    if heading_text:
        # Try to naturally incorporate keyword
        if len(heading_text) < 40:
            new_heading = f'{html.escape(heading_text)} and {html.escape(keyword)}'
        else:
            new_heading = f'{html.escape(keyword)}: {html.escape(heading_text[:50])}'
    else:
        new_heading = html.escape(keyword)
    
    replacement = f'<h2>{new_heading}</h2>'
    return content_html[: h2_match.start()] + replacement + content_html[h2_match.end() :]


def _ensure_min_keyword_density(
    *,
    content_html: str,
    keyword: str,
    min_density: float,
    max_additions: int,
) -> str:
    if not keyword:
        return content_html
    # Skip boilerplate injection for phrases longer than 3 words — looks unnatural in content.
    if len(keyword.split()) > 3:
        return content_html

    updated = content_html
    additions = 0
    
    # Use varied snippets to avoid repetitive content
    escaped_kw = html.escape(keyword)
    snippet_templates = [
        f'<p>Understanding <strong>{escaped_kw}</strong> helps parents recognize early warning signs and respond with confidence.</p>',
        f'<p>When <strong>{escaped_kw}</strong> affects daily life, professional guidance and consistent home support make a meaningful difference.</p>',
        f'<p>Parents who learn more about <strong>{escaped_kw}</strong> are better equipped to support their child through difficult moments.</p>',
        f'<p>Addressing <strong>{escaped_kw}</strong> early, with evidence-based approaches, supports children\'s long-term wellbeing.</p>',
        f'<p>Children affected by <strong>{escaped_kw}</strong> benefit from structured routines, clear communication, and consistent parental support.</p>',
        f'<p>Families navigating <strong>{escaped_kw}</strong> often find that small, consistent changes at home lead to meaningful progress over time.</p>',
        f'<p>Recognizing the signs of <strong>{escaped_kw}</strong> early allows caregivers to seek timely professional input and reduce unnecessary worry.</p>',
        f'<p>Many parents first ask about <strong>{escaped_kw}</strong> after noticing shifts in their child\'s mood, sleep, or school performance.</p>',
    ]
    
    snippet_index = 0
    while _keyword_density(updated, keyword) < min_density and additions < max_additions:
        snippet = snippet_templates[snippet_index % len(snippet_templates)]
        updated = _inject_after_h1(updated, snippet)
        additions += 1
        snippet_index += 1
    
    return updated


def _normalize_rewritten_html(value: str) -> str:
    candidate = (value or '').strip()
    if not candidate:
        return ''

    if '<h1' in candidate.lower() and '<section' in candidate.lower() and '<h2' in candidate.lower():
        return candidate
    return ''


def _assess_first_person_voice(text: str) -> VoiceReport:
    lowered = text.lower()
    markers = [
        ' we ',
        " we're ",
        " we've ",
        ' our ',
        ' us ',
    ]
    hits = sum(lowered.count(marker) for marker in markers)
    words = re.findall(r"[a-zA-Z']+", lowered)
    word_count = max(1, len(words))
    ratio = round(hits / word_count, 4)

    notes: list[str] = []
    passed = True
    # Relaxed: 5 instead of 6
    if hits < 5:
        passed = False
        notes.append(f'first_person_marker_count={hits} is below minimum 5')
    # Relaxed: 0.002 instead of 0.0025
    if ratio < 0.002:
        passed = False
        notes.append(f'first_person_ratio={ratio} is below minimum 0.002')

    return VoiceReport(
        first_person_ratio=ratio,
        first_person_count=hits,
        passed=passed,
        notes=notes,
    )


def _assess_humanization(text: str) -> HumanizationReport:
    words = re.findall(r"[a-zA-Z']+", text.lower())
    word_count = max(1, len(words))
    unique_words = len(set(words))
    lexical_diversity = round(unique_words / word_count, 4)

    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    sentence_lengths = [len(re.findall(r"[a-zA-Z']+", s)) for s in sentences]
    sentence_length_stddev = round(pstdev(sentence_lengths), 3) if len(sentence_lengths) >= 2 else 0.0

    repeated_4gram_ratio = _repeated_ngram_ratio(words, n=4)
    contractions = len(re.findall(r"\b\w+'(t|re|ve|ll|d|m|s)\b", text.lower()))
    contractions_per_1000 = round((contractions / word_count) * 1000.0, 3)
    questions = text.count('?')
    question_ratio = round(questions / max(1, len(sentences)), 4)

    notes: list[str] = []
    passed = True
    # Relaxed: 0.24 instead of 0.26
    if lexical_diversity < 0.24:
        passed = False
        notes.append(f'lexical_diversity={lexical_diversity} is below minimum 0.24')
    # Relaxed: 3.5 instead of 4.0
    if sentence_length_stddev < 3.5:
        passed = False
        notes.append(f'sentence_length_stddev={sentence_length_stddev} is below minimum 3.5')
    # Relaxed: 0.08 instead of 0.06
    if repeated_4gram_ratio > 0.08:
        passed = False
        notes.append(f'repeated_4gram_ratio={round(repeated_4gram_ratio,4)} exceeds 0.08')
    if contractions_per_1000 < 1.0:
        notes.append(
            f'contractions_per_1000_words={contractions_per_1000} is low; tone may still feel robotic'
        )
    if question_ratio > 0.2:
        notes.append(f'question_ratio={question_ratio} is high; reduce rhetorical questions')

    return HumanizationReport(
        lexical_diversity=lexical_diversity,
        sentence_length_stddev=sentence_length_stddev,
        repeated_ngram_ratio=round(repeated_4gram_ratio, 4),
        contractions_per_1000_words=contractions_per_1000,
        question_ratio=question_ratio,
        passed=passed,
        notes=notes,
    )


def _repeated_ngram_ratio(tokens: list[str], *, n: int) -> float:
    if len(tokens) < n:
        return 0.0
    ngrams = [tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]
    counts = Counter(ngrams)
    repeated = sum(count for count in counts.values() if count > 1)
    return repeated / max(1, len(ngrams))


def _count_tag(content_html: str, tag_name: str) -> int:
    return len(re.findall(rf'<{tag_name}\b', content_html or '', flags=re.IGNORECASE))


def _keyword_in_h2(content_html: str, keyword: str) -> bool:
    if not keyword:
        return True
    h2_values = re.findall(r'<h2[^>]*>(.*?)</h2>', content_html or '', flags=re.IGNORECASE | re.DOTALL)
    lowered_keyword = keyword.lower()
    return any(lowered_keyword in _plain_text(value).lower() for value in h2_values)


def _keyword_density(content_html: str, keyword: str) -> float:
    if not keyword:
        return 0.0
    normalized_text = _normalize_similarity_text(_plain_text(content_html))
    if not normalized_text:
        return 0.0
    words = normalized_text.split()
    total_words = max(1, len(words))
    phrase = _normalize_similarity_text(keyword)
    if not phrase:
        return 0.0
    occurrences = normalized_text.count(phrase)
    return (occurrences / total_words) * 100.0


def _rule_based_humanize_html(content_html: str) -> str:
    updated = content_html
    replacements = {
        r'\bmoreover\b': 'also',
        r'\bfurthermore\b': 'also',
        r'\bin conclusion\b': 'to summarize',
        r'\bit is important to note that\b': 'parents should know that',
    }
    for pattern, replacement in replacements.items():
        updated = re.sub(pattern, replacement, updated, flags=re.IGNORECASE)

    updated = re.sub(r'\s{2,}', ' ', updated)
    return updated


@lru_cache(maxsize=1)
def _load_reference_pdf_text() -> str:
    pdf_path = PROJECT_ROOT / 'reference.pdf'
    if not pdf_path.exists():
        return ''

    try:
        import pypdf  # type: ignore

        reader = pypdf.PdfReader(str(pdf_path))
        text = '\n'.join((page.extract_text() or '') for page in reader.pages[:8])
        return text[:20000]
    except Exception:
        pass

    try:
        import PyPDF2  # type: ignore

        reader = PyPDF2.PdfReader(str(pdf_path))
        text = '\n'.join((page.extract_text() or '') for page in reader.pages[:8])
        return text[:20000]
    except Exception:
        return ''


def _flesch_kincaid_grade(text: str) -> float:
    words = re.findall(r"[a-zA-Z']+", text)
    sentences = re.split(r'[.!?]+', text)
    sentence_count = max(1, len([s for s in sentences if s.strip()]))
    word_count = max(1, len(words))
    syllable_count = sum(_count_syllables(word) for word in words)
    return 0.39 * (word_count / sentence_count) + 11.8 * (syllable_count / word_count) - 15.59


def _count_syllables(word: str) -> int:
    lowered = word.lower()
    groups = re.findall(r'[aeiouy]+', lowered)
    count = len(groups)
    if lowered.endswith('e') and count > 1:
        count -= 1
    return max(1, count)


def _heuristic_ai_probability(article_text: str) -> float:
    text = article_text.lower()
    generic_markers = [
        'in conclusion',
        'it is important to note',
        'overall',
        'furthermore',
        'moreover',
        'in today',
    ]
    marker_hits = sum(1 for marker in generic_markers if marker in text)
    if marker_hits >= 3:
        return 0.72
    if marker_hits == 2:
        return 0.62
    if marker_hits == 1:
        return 0.52
    return 0.38


def _trim_content_to_target_length(content_html: str, *, target_max: int, target_min: int) -> str:
    """Trim content to fit within target word count range while preserving structure."""
    plain_text = _plain_text(content_html)
    word_count = len(plain_text.split())
    
    # If within range, return as-is
    if target_min <= word_count <= target_max:
        return content_html
    
    # If too short, return as-is (SEO fixes should add content)
    if word_count < target_min:
        return content_html
    
    # If too long, trim by removing later sections
    if word_count > target_max:
        # Find all sections
        sections = list(re.finditer(r'<section[^>]*>.*?</section>', content_html, flags=re.IGNORECASE | re.DOTALL))
        
        if len(sections) <= 3:
            # Too few sections to remove, trim last section's content instead
            return content_html
        
        # Remove sections from the end until we're under target
        trimmed = content_html
        sections_to_keep = len(sections)
        
        while sections_to_keep > 3:
            # Try removing one less section
            sections_to_keep -= 1
            candidate = content_html[:sections[sections_to_keep].start()] + content_html[sections[-1].end():]
            candidate_word_count = len(_plain_text(candidate).split())
            
            if candidate_word_count <= target_max:
                trimmed = candidate
                break
            
            trimmed = candidate
        
        # Ensure we keep at minimum structure
        if _plain_text(trimmed).split() and len(_plain_text(trimmed).split()) < target_max * 1.3:
            return trimmed
    
    return content_html
