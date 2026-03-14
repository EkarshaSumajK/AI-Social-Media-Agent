from __future__ import annotations

import html
import inspect
import json
import re
from collections.abc import Awaitable, Callable
from functools import lru_cache
from pathlib import Path

import markdown
from langgraph.graph import END, StateGraph

from app.core.config import get_settings
from app.services.llm_service import LLMClient
from app.services.prompt_service import PromptCatalog, get_prompt_catalog
from app.workflows.types import ContentState, GeneratedDraft

settings = get_settings()
PROJECT_ROOT = Path(__file__).resolve().parents[2]
QUALITY_FIRST_CHECKLIST = (
    'Quality-first drafting rules:\n'
    '- Write as a clinician speaking directly to parents. Use first-person plural voice (we, our, us) regularly throughout — at least 3-4 times per section.\n'
    '- NEVER sound like a news report or press release. Do NOT summarize legislation, bills, or policy actions. Focus on child and family experience.\n'
    '- NEVER repeat or rephrase the topic title in your output. The topic is background context only.\n'
    '- Return section body text only: no markdown headings, no section labels, no template markers.\n'
    '- Keep readability at approximately 6th-8th grade with mostly 12-20 word sentences.\n'
    '- Preserve the required article structure and keep each section complete, specific, and useful.\n'
    '- CRITICAL anti-plagiarism rules: completely rewrite every idea from the source in your own words. '
    'Do not reproduce any phrase of 7 or more consecutive words from the source material. '
    'Change sentence structures, replace terminology with synonyms, and reorganize the order of ideas.\n'
    '- Avoid repeated 4-word phrase patterns, repeated sentences, and repetitive transition templates.\n'
    '- Reduce AI tone: vary sentence openings/lengths, use natural human rhythm, and include occasional contractions.\n'
    '- Include the focus keyword naturally without stuffing: in SEO title, meta description, first paragraph, and one relevant section heading.\n'
    '- Keep claims factual and cautious; do not invent data, quotes, or citations.\n'
)
def _get_template_heading_markers() -> frozenset[str]:
    clinic = settings.clinic_name.lower()
    return frozenset({
        'h1: seo optimized title',
        'seo optimized title',
        'introduction',
        'intro: summary of issue',
        'summary of issue',
        "understanding our children's experiences",
        'understanding our childrens experiences',
        'why this matters',
        'mental health implications',
        'professional insight',
        f'how {clinic} can help',
        'take the next step',
        'take the next step (cta)',
        'footer disclaimer',
        'author info',
        'citations',
        'internal links',
        'meta data',
    })


TEMPLATE_HEADING_MARKERS = _get_template_heading_markers()


class ContentGraphRunner:
    def __init__(
        self,
        llm_client: LLMClient | None = None,
        prompt_catalog: PromptCatalog | None = None,
    ) -> None:
        self.llm = llm_client or LLMClient()
        self.prompts = prompt_catalog or get_prompt_catalog()

        graph = StateGraph(ContentState)

        graph.add_node('understand_problem', self.understand_problem)
        graph.add_node('explain_to_parent', self.explain_to_parent)
        graph.add_node('research_backing', self.research_backing)
        graph.add_node('real_world_impact', self.real_world_impact)
        graph.add_node('professional_guidance', self.professional_guidance)
        graph.add_node('service_solution_mapping', self.service_solution_mapping)
        graph.add_node('reassurance_tone', self.reassurance_tone)
        graph.add_node('seo_generation', self.seo_generation)
        graph.add_node('social_generation', self.social_generation)

        graph.set_entry_point('understand_problem')
        graph.add_edge('understand_problem', 'explain_to_parent')
        graph.add_edge('explain_to_parent', 'research_backing')
        graph.add_edge('research_backing', 'real_world_impact')
        graph.add_edge('real_world_impact', 'professional_guidance')
        graph.add_edge('professional_guidance', 'service_solution_mapping')
        graph.add_edge('service_solution_mapping', 'reassurance_tone')
        graph.add_edge('reassurance_tone', 'seo_generation')
        graph.add_edge('seo_generation', 'social_generation')
        graph.add_edge('social_generation', END)

        self.graph = graph.compile()

    _NODE_PROGRESS: list[tuple[int, str]] = [
        (76, 'Writing problem overview…'),
        (77, 'Writing parent explanation…'),
        (78, 'Writing real-world impact…'),
        (79, 'Writing research backing…'),
        (80, 'Writing professional guidance…'),
        (81, 'Writing service solutions & reassurance…'),
        (83, 'Generating SEO metadata & social posts…'),
    ]

    async def _tick_progress(self) -> None:
        cb: Callable | None = getattr(self, '_run_progress_cb', None)
        if cb is None:
            return
        idx: int = getattr(self, '_run_node_idx', 0)
        if idx < len(self._NODE_PROGRESS):
            progress, message = self._NODE_PROGRESS[idx]
            self._run_node_idx = idx + 1
            outcome = cb('draft_generation', progress, message)
            if inspect.isawaitable(outcome):
                await outcome

    async def run(
        self,
        *,
        topic_title: str,
        topic_summary: str | None,
        focus_keyword: str | None = None,
        regions: list[str] | None = None,
        public_concerns: list[str] | None = None,
        trend_statements: list[str] | None = None,
        trend_sentiment: str | None = None,
        statistics: list[str] | None = None,
        humanization_guidance: str = (
            'Prioritize natural human clinician voice, strict SEO structure, strong readability, and low-plagiarism '
            'paraphrasing while avoiding repetitive AI-sounding phrasing.'
        ),
        progress_callback: Callable[..., Awaitable[None] | None] | None = None,
    ) -> GeneratedDraft:
        self._run_progress_cb = progress_callback
        self._run_node_idx = 0
        initial: ContentState = {
            'topic_title': topic_title,
            'topic_summary': topic_summary or '',
            'focus_keyword': (focus_keyword or _extract_focus_keyword(topic_title)).strip(),
            'regions': regions or ['International'],
            'public_concerns': public_concerns or [],
            'trend_statements': trend_statements or [],
            'trend_sentiment': trend_sentiment or 'awareness',
            'statistics': statistics or [],
            'service_links': settings.service_links,
            'services_reference': _load_services_reference(),
            'humanization_guidance': humanization_guidance,
            'trend_context': self._build_trend_context(
                regions=regions or ['International'],
                public_concerns=public_concerns or [],
                trend_statements=trend_statements or [],
                trend_sentiment=trend_sentiment or 'awareness',
            ),
            'keywords': [],
            'social_posts': {},
        }
        result = await self.graph.ainvoke(initial)
        self._run_progress_cb = None

        issue_summary = '\n\n'.join(
            filter(
                None,
                [
                    result.get('opening_scenario', ''),
                    result.get('child_experience', ''),
                    result.get('science_explanation', ''),
                ],
            )
        )
        why_it_matters = '\n\n'.join(
            filter(
                None,
                [
                    result.get('real_life_effects', ''),
                    result.get('parent_misunderstandings', ''),
                ],
            )
        )
        professional_insight = '\n\n'.join(
            filter(
                None,
                [
                    result.get('guidance_steps', ''),
                    result.get('when_to_seek_help', ''),
                ],
            )
        )

        generated = GeneratedDraft(
            seo_title=result['seo_title'],
            meta_description=result['meta_description'],
            keywords=result['keywords'],
            issue_summary=issue_summary,
            why_it_matters=why_it_matters,
            mental_health_implications=result.get('science_explanation', ''),
            professional_insight=professional_insight,
            how_services_help=result.get('services_help', ''),
            call_to_action=result.get('reassuring_close', ''),
            content_html=self._build_content_html(result),
            social_posts=result['social_posts'],
            opening_scenario=result.get('opening_scenario', ''),
            child_experience=result.get('child_experience', ''),
            science_explanation=result.get('science_explanation', ''),
            real_life_effects=result.get('real_life_effects', ''),
            parent_misunderstandings=result.get('parent_misunderstandings', ''),
            guidance_steps=result.get('guidance_steps', ''),
            when_to_seek_help=result.get('when_to_seek_help', ''),
            reassuring_close=result.get('reassuring_close', ''),
        )
        return generated

    async def understand_problem(self, state: ContentState) -> ContentState:
        system_prompt, prompt = self.prompts.get_prompt(
            bundle='content_generation/v2/prompts.yaml',
            key='understand_problem',
            context=state,
        )
        text = await self.llm.generate(
            system_prompt=self._with_quality_guardrails(system_prompt, state),
            prompt=prompt,
            model=settings.llm_model,
            temperature=0.5,
        )
        await self._tick_progress()
        return {'opening_scenario': text.strip()}

    async def explain_to_parent(self, state: ContentState) -> ContentState:
        system_prompt, prompt = self.prompts.get_prompt(
            bundle='content_generation/v2/prompts.yaml',
            key='explain_to_parent',
            context=state,
        )
        text = await self.llm.generate(
            system_prompt=self._with_quality_guardrails(system_prompt, state),
            prompt=prompt,
            model=settings.llm_model,
            temperature=0.45,
        )
        await self._tick_progress()
        return {'child_experience': text.strip()}

    async def real_world_impact(self, state: ContentState) -> ContentState:
        system_prompt, prompt = self.prompts.get_prompt(
            bundle='content_generation/v2/prompts.yaml',
            key='real_world_impact',
            context=state,
        )
        text = await self.llm.generate(
            system_prompt=self._with_quality_guardrails(system_prompt, state),
            prompt=prompt,
            model=settings.llm_model,
            temperature=0.45,
        )
        labeled = _parse_labeled_blocks(
            text,
            first_key='REAL_LIFE_EFFECTS',
            second_key='PARENT_MISUNDERSTANDINGS',
        )
        await self._tick_progress()
        return {
            'real_life_effects': labeled[0],
            'parent_misunderstandings': labeled[1],
        }

    async def research_backing(self, state: ContentState) -> ContentState:
        system_prompt, prompt = self.prompts.get_prompt(
            bundle='content_generation/v2/prompts.yaml',
            key='research_backing',
            context=state,
        )
        text = await self.llm.generate(
            system_prompt=self._with_quality_guardrails(system_prompt, state),
            prompt=prompt,
            model=settings.llm_model,
            temperature=0.35,
        )
        await self._tick_progress()
        return {'science_explanation': text.strip()}

    async def professional_guidance(self, state: ContentState) -> ContentState:
        system_prompt, prompt = self.prompts.get_prompt(
            bundle='content_generation/v2/prompts.yaml',
            key='professional_guidance',
            context=state,
        )
        text = await self.llm.generate(
            system_prompt=self._with_quality_guardrails(system_prompt, state),
            prompt=prompt,
            model=settings.llm_model,
            temperature=0.4,
        )
        labeled = _parse_labeled_blocks(
            text,
            first_key='PROFESSIONAL_GUIDANCE_STEPS',
            second_key='WHEN_TO_SEEK_HELP',
        )
        await self._tick_progress()
        return {
            'guidance_steps': labeled[0],
            'when_to_seek_help': labeled[1],
        }

    async def service_solution_mapping(self, state: ContentState) -> ContentState:
        system_prompt, prompt = self.prompts.get_prompt(
            bundle='content_generation/v2/prompts.yaml',
            key='service_solution_mapping',
            context=state,
        )
        text = await self.llm.generate(
            system_prompt=self._with_quality_guardrails(system_prompt, state),
            prompt=prompt,
            model=settings.llm_model,
            temperature=0.4,
        )
        await self._tick_progress()
        return {'services_help': text.strip()}

    async def reassurance_tone(self, state: ContentState) -> ContentState:
        system_prompt, prompt = self.prompts.get_prompt(
            bundle='content_generation/v2/prompts.yaml',
            key='reassurance_tone',
            context=state,
        )
        text = await self.llm.generate(
            system_prompt=self._with_quality_guardrails(system_prompt, state),
            prompt=prompt,
            model=settings.llm_model,
            temperature=0.45,
        )
        await self._tick_progress()
        return {'reassuring_close': text.strip()}

    async def seo_generation(self, state: ContentState) -> ContentState:
        article_summary = '\n\n'.join(
            filter(
                None,
                [
                    state.get('opening_scenario', ''),
                    state.get('child_experience', ''),
                    state.get('science_explanation', ''),
                    state.get('real_life_effects', ''),
                    state.get('guidance_steps', ''),
                ],
            )
        )
        system_prompt, prompt = self.prompts.get_prompt(
            bundle='content_generation/v2/prompts.yaml',
            key='seo_generation',
            context={
                **state,
                'article_summary': article_summary[:4000],
            },
        )
        payload = await self.llm.generate_json(
            system_prompt=self._with_quality_guardrails(system_prompt, state),
            prompt=prompt,
            model=settings.llm_model,
            temperature=0.2,
        )

        focus_keyword = str(state.get('focus_keyword') or state['topic_title']).strip()
        seo_title = str(payload.get('seo_title') or f"{focus_keyword} | Child Mental Health Guidance").strip()
        meta_description = str(payload.get('meta_description') or '').strip()
        if not meta_description:
            meta_description = (
                f"A practical parent guide to {focus_keyword} with child mental health insights, "
                'daily-life impact, and professional guidance.'
            )
        keywords = payload.get('keywords')
        if isinstance(keywords, list):
            normalized_keywords = [str(item).strip() for item in keywords if str(item).strip()]
        else:
            normalized_keywords = []
        if not normalized_keywords:
            normalized_keywords = [
                focus_keyword,
                'child mental health',
                'teen mental health',
                'parent guidance',
                'professional support',
            ]

        await self._tick_progress()
        return {
            'seo_title': seo_title,
            'meta_description': meta_description[:500],
            'keywords': normalized_keywords[:10],
        }

    async def social_generation(self, state: ContentState) -> ContentState:
        article_summary = '\n'.join(
            filter(
                None,
                [
                    state.get('opening_scenario', ''),
                    state.get('science_explanation', ''),
                    state.get('guidance_steps', ''),
                ],
            )
        )
        system_prompt, prompt = self.prompts.get_prompt(
            bundle='content_generation/v2/prompts.yaml',
            key='social_generation',
            context={
                **state,
                'article_summary': article_summary[:2000],
            },
        )
        payload = await self.llm.generate_json(
            system_prompt=self._with_quality_guardrails(system_prompt, state),
            prompt=prompt,
            model=settings.llm_model,
            temperature=0.4,
        )

        focus_kw = str(state.get('focus_keyword') or state['topic_title']).strip()
        posts = {
            'instagram': f"{focus_kw}: Parent-focused guidance from a child mental health perspective.",
            'linkedin': f"A professional child mental health briefing for parents on {focus_kw}.",
            'twitter': f"{focus_kw} impacts daily family life. Here is what parents can do next.",
            'facebook': f"Parents are asking about {focus_kw}. Here is a calm, practical guide.",
        }
        for key in posts:
            if isinstance(payload.get(key), str) and payload.get(key).strip():
                posts[key] = str(payload[key]).strip()

        await self._tick_progress()
        return {'social_posts': posts}

    def _build_content_html(self, state: ContentState) -> str:
        seo_title = html.escape(state.get('seo_title', state['topic_title']))
        intro_text = '\n\n'.join(
            filter(
                None,
                [
                    str(state.get('opening_scenario', '')).strip(),
                    str(state.get('child_experience', '')).strip(),
                ],
            )
        )
        why_it_matters_text = '\n\n'.join(
            filter(
                None,
                [
                    str(state.get('real_life_effects', '')).strip(),
                    str(state.get('parent_misunderstandings', '')).strip(),
                ],
            )
        )
        mental_implications_text = str(state.get('science_explanation', '')).strip()
        professional_insight_text = '\n\n'.join(
            filter(
                None,
                [
                    str(state.get('guidance_steps', '')).strip(),
                    str(state.get('when_to_seek_help', '')).strip(),
                ],
            )
        )
        services_text = str(state.get('services_help', '')).strip()
        cta_text = str(state.get('reassuring_close', '')).strip()

        sections = _fit_sections_to_word_target(
            sections={
                'intro': intro_text,
                'why': why_it_matters_text,
                'implications': mental_implications_text,
                'insight': professional_insight_text,
                'services': services_text,
                'cta': cta_text,
            },
            focus_keyword=str(state.get('focus_keyword') or state.get('topic_title') or '').strip(),
        )

        clinic_name = html.escape(settings.clinic_name)
        body = [f'<h1>{seo_title}</h1>']
        body.append(f"<section><h2>Summary of Issue</h2>{self._render_rich_text(sections['intro'])}</section>")
        body.append(f"<section><h2>Why This Matters</h2>{self._render_rich_text(sections['why'])}</section>")
        body.append(f"<section><h2>Mental Health Implications</h2>{self._render_rich_text(sections['implications'])}</section>")
        body.append(f"<section><h2>Professional Insight</h2>{self._render_rich_text(sections['insight'])}</section>")
        body.append(
            f'<section><h2>How {clinic_name} Can Help</h2>'
            f'{self._render_rich_text(sections["services"])}'
            '</section>'
        )
        body.append(f"<section><h2>Take the Next Step (CTA)</h2>{self._render_rich_text(sections['cta'])}</section>")
        return ''.join(body)

    def _render_rich_text(self, text: str) -> str:
        cleaned = re.sub(r'\r\n?', '\n', (text or '').strip())
        if not cleaned:
            return '<p>No content available.</p>'
        return markdown.markdown(
            cleaned,
            extensions=['extra', 'sane_lists', 'nl2br'],
            output_format='html5',
        )

    def _build_trend_context(
        self,
        *,
        regions: list[str],
        public_concerns: list[str],
        trend_statements: list[str],
        trend_sentiment: str,
    ) -> str:
        payload = {
            'regions': regions,
            'public_concerns': public_concerns,
            'trend_statements': trend_statements,
            'trend_sentiment': trend_sentiment,
        }
        return json.dumps(payload, ensure_ascii=True)

    def _with_quality_guardrails(self, base_system_prompt: str, state: ContentState) -> str:
        focus_keyword = str(state.get('focus_keyword') or '').strip()
        keyword_line = (
            f'Focus keyword to preserve naturally: "{focus_keyword}".\n'
            if focus_keyword
            else ''
        )
        return f'{base_system_prompt}\n\n{QUALITY_FIRST_CHECKLIST}{keyword_line}'.strip()


def _extract_focus_keyword(topic_title: str) -> str:
    """Extract a clean 2-3 word focus keyword from a topic title.

    Filters stop/filler words and headline verbs, then finds the best
    consecutive run of meaningful words to form a grammatically valid phrase.
    """
    _STOP_WORDS = {
        'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'from', 'up', 'about', 'into', 'through', 'new', 'law', 'laws',
        'bill', 'act', 'acts', 'how', 'why', 'what', 'when', 'where',
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do',
        'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'shall', 'can',
        'its', 'their', 'our', 'your', 'my', 'this', 'that', 'these', 'those', 'report',
        'study', 'says', 'shows', 'finds', 'as', 'after', 'over', 'under', 'between',
        'among', 'across', 'amid', 'contracts', 'contract',
        # headline verbs
        'announces', 'announce', 'announced', 'reveals', 'reveal', 'revealed',
        'show', 'showed', 'showing', 'found', 'launch', 'launches', 'launched',
        'highlight', 'highlights', 'highlighted', 'creates', 'create', 'created',
        'unveil', 'unveils', 'unveiled', 'propose', 'proposes', 'proposed',
        'approve', 'approves', 'approved', 'tackle', 'tackles', 'tackled',
        'boost', 'boosts', 'boosted', 'expand', 'expands', 'expanded',
        'save', 'saves', 'saved', 'suggest', 'suggests', 'suggested',
        'indicate', 'indicates', 'indicated', 'raise', 'raises', 'raised',
        'reduce', 'reduces', 'reduced', 'improve', 'improves', 'improved',
        'improvement', 'improvements', 'provide', 'provides', 'provided',
        'introduce', 'introduces', 'introduced',
    }
    words = [w.strip('.,!?:;()[]"\'') for w in topic_title.split()]

    mask = []
    for w in words:
        is_stop = w.lower() in _STOP_WORDS
        is_short = len(w) <= 2
        is_acronym = w.isupper() and len(w) >= 5
        mask.append(not is_stop and not is_short and not is_acronym)

    # Find consecutive runs of meaningful words.
    runs: list[tuple[int, int]] = []
    run_start = -1
    for i, is_meaningful in enumerate(mask):
        if is_meaningful:
            if run_start == -1:
                run_start = i
        else:
            if run_start != -1:
                run_len = i - run_start
                if run_len >= 2:
                    runs.append((run_start, run_len))
                run_start = -1
    if run_start != -1:
        run_len = len(mask) - run_start
        if run_len >= 2:
            runs.append((run_start, run_len))

    if runs:
        start, length = runs[0]
        take = length if length <= 3 else 2
        return ' '.join(words[start:start + take]).lower().strip()

    meaningful = [w for i, w in enumerate(words) if mask[i]]
    if len(meaningful) >= 2:
        return ' '.join(meaningful[:2]).lower().strip()
    if meaningful:
        return meaningful[0].lower().strip()

    long_words = [w for w in words if len(w) > 2]
    return ' '.join(long_words[:2]).lower().strip() or topic_title.lower()


def _parse_labeled_blocks(text: str, *, first_key: str, second_key: str) -> tuple[str, str]:
    normalized = text.replace('\r\n', '\n')
    first_pattern = re.compile(rf'{re.escape(first_key)}\s*:\s*', flags=re.IGNORECASE)
    second_pattern = re.compile(rf'{re.escape(second_key)}\s*:\s*', flags=re.IGNORECASE)

    first_match = first_pattern.search(normalized)
    second_match = second_pattern.search(normalized)
    if not first_match or not second_match:
        lines = [line.strip() for line in normalized.splitlines() if line.strip()]
        midpoint = max(1, len(lines) // 2)
        first_part = '\n'.join(lines[:midpoint]).strip()
        second_part = '\n'.join(lines[midpoint:]).strip()
        return first_part or normalized.strip(), second_part or normalized.strip()

    if first_match.start() < second_match.start():
        first_value = normalized[first_match.end():second_match.start()].strip()
        second_value = normalized[second_match.end():].strip()
    else:
        second_value = normalized[second_match.end():first_match.start()].strip()
        first_value = normalized[first_match.end():].strip()
    return first_value or normalized.strip(), second_value or normalized.strip()


def _fit_sections_to_word_target(*, sections: dict[str, str], focus_keyword: str) -> dict[str, str]:
    normalized = {
        key: _normalize_section_text(value)
        for key, value in sections.items()
    }

    max_words = {
        'intro': 300,
        'why': 260,
        'implications': 180,
        'insight': 280,
        'services': 170,
        'cta': 120,
    }
    min_words = {
        'intro': 180,
        'why': 160,
        'implications': 120,
        'insight': 180,
        'services': 120,
        'cta': 70,
    }

    for key, limit in max_words.items():
        normalized[key] = _truncate_to_words(normalized.get(key, ''), limit)

    total_words = _combined_word_count(normalized)
    target_min = 950
    target_max = 1050

    if total_words > target_max:
        overflow = total_words - target_max
        trim_order = ['intro', 'why', 'insight', 'services', 'implications', 'cta']
        for key in trim_order:
            if overflow <= 0:
                break
            current_words = _word_count(normalized.get(key, ''))
            floor = min_words[key]
            removable = max(0, current_words - floor)
            if removable <= 0:
                continue
            cut = min(removable, overflow)
            normalized[key] = _truncate_to_words(normalized.get(key, ''), current_words - cut)
            overflow -= cut

    elif total_words < target_min:
        deficit = target_min - total_words
        clinic_name = get_settings().clinic_name
        expansion_chunks = [
            (
                'insight',
                'In our clinical practice, we convert observations into small, repeatable '
                'steps families can follow each day with confidence.',
            ),
            (
                'why',
                'When these concerns are left unaddressed, stress can affect sleep, concentration, learning, and '
                'family communication in ways that compound over time.',
            ),
            (
                'services',
                f'At {clinic_name}, we coordinate parent coaching, child-focused support, and school-aligned '
                'guidance so care stays consistent across home and classroom settings.',
            ),
            (
                'cta',
                'A timely consultation helps families choose practical next steps, reduce uncertainty, and build a clear '
                'support plan that can start immediately.',
            ),
        ]

        idx = 0
        used_chunks: set[str] = set()
        while deficit > 0 and idx < len(expansion_chunks):
            key, chunk = expansion_chunks[idx]
            if key not in used_chunks:
                normalized[key] = f"{normalized.get(key, '').strip()}\n\n{chunk}".strip()
                deficit -= _word_count(chunk)
                used_chunks.add(key)
            idx += 1

    return normalized


def _ensure_first_person_sections(sections: dict[str, str]) -> dict[str, str]:
    first_person_openers = {
        'intro': 'In our clinical experience, we see these patterns in many families.',
        'why': 'From our perspective, we know these effects can grow when support is delayed.',
        'implications': 'We explain these implications so families can recognize warning signs earlier.',
        'insight': 'In our practice, we guide parents through practical step-by-step support.',
        'services': 'At Horizon Therapy Centre, we provide coordinated support for each family.',
        'cta': 'We encourage families to take the next step with timely, informed support.',
    }

    out: dict[str, str] = {}
    for key, text in sections.items():
        raw = str(text or '').strip()
        if _contains_first_person(raw):
            out[key] = raw
            continue
        opener = first_person_openers.get(key, 'In our experience, we support families through this concern.')
        out[key] = f'{opener}\n\n{raw}'.strip()
    return out


def _contains_first_person(text: str) -> bool:
    lowered = str(text or '').lower()
    return bool(re.search(r"\b(we|our|us|we're|we've|we'll|we'd)\b", lowered))


def _normalize_section_text(value: str) -> str:
    text = re.sub(r'\r\n?', '\n', str(value or '').strip())
    text = _strip_render_artifacts(text)
    text = _dedupe_repetitive_content(text)
    if text:
        return text
    return 'Content is being prepared for this section.'


def _strip_render_artifacts(text: str) -> str:
    lines = [line.rstrip() for line in str(text or '').split('\n')]
    cleaned_lines: list[str] = []
    previous_key = ''

    for raw_line in lines:
        line = raw_line.strip()

        # Remove orphan markdown marker lines like "**", "__", "---".
        if line and re.fullmatch(r'[\*_`\-~\s]{2,}', line):
            continue

        candidate = re.sub(r'^[#>\s]+', '', line).strip()
        candidate = candidate.strip('*').strip()
        candidate_key = re.sub(r'\s+', ' ', candidate).strip().lower().rstrip(':')

        # Drop repeated template headings accidentally generated into body text.
        if candidate_key in TEMPLATE_HEADING_MARKERS:
            continue

        # Drop immediate duplicate lines to prevent doubled heading/body rows.
        current_key = re.sub(r'\s+', ' ', line).strip().lower()
        if current_key and current_key == previous_key:
            continue

        cleaned_lines.append(raw_line)
        previous_key = current_key

    merged = '\n'.join(cleaned_lines).strip()
    merged = re.sub(r'\n{3,}', '\n\n', merged)
    return merged


def _dedupe_repetitive_content(text: str) -> str:
    paragraphs = [part.strip() for part in re.split(r'\n{2,}', str(text or '')) if part.strip()]
    if not paragraphs:
        return ''

    seen_paragraphs: set[str] = set()
    cleaned_paragraphs: list[str] = []
    for paragraph in paragraphs:
        normalized_paragraph = _normalize_for_dedupe(paragraph)
        if normalized_paragraph in seen_paragraphs:
            continue
        seen_paragraphs.add(normalized_paragraph)
        if re.search(r'(?m)^\s*(?:\d+\.|[-*+])\s+', paragraph):
            cleaned_paragraphs.append(_dedupe_repeated_list_lines(paragraph))
        else:
            cleaned_paragraphs.append(_dedupe_repeated_sentences(paragraph))

    merged = '\n\n'.join(cleaned_paragraphs).strip()
    merged = re.sub(r'\n{3,}', '\n\n', merged)
    return merged


def _dedupe_repeated_sentences(paragraph: str) -> str:
    sentences = re.split(r'(?<=[.!?])\s+', str(paragraph or '').strip())
    if len(sentences) <= 1:
        return paragraph.strip()

    seen_sentences: set[str] = set()
    deduped: list[str] = []
    for sentence in sentences:
        raw = sentence.strip()
        if not raw:
            continue
        normalized = _normalize_for_dedupe(raw)
        if normalized and normalized in seen_sentences:
            continue
        if normalized:
            seen_sentences.add(normalized)
        deduped.append(raw)

    return ' '.join(deduped).strip()


def _normalize_for_dedupe(value: str) -> str:
    normalized = re.sub(r'[^a-z0-9\s]', ' ', str(value or '').lower())
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized


def _dedupe_repeated_list_lines(value: str) -> str:
    lines = str(value or '').split('\n')
    seen: set[str] = set()
    out: list[str] = []
    for line in lines:
        raw = line.rstrip()
        if not raw.strip():
            out.append(raw)
            continue
        key = _normalize_for_dedupe(raw)
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        out.append(raw)
    return '\n'.join(out).strip()


def _truncate_to_words(text: str, limit: int) -> str:
    if limit <= 0:
        return ''
    cleaned = str(text or '').strip()
    words = cleaned.split()
    if len(words) <= limit:
        return cleaned

    sentences = re.split(r'(?<=[.!?])\s+', cleaned)
    kept_sentences: list[str] = []
    used_words = 0
    for sentence in sentences:
        candidate = sentence.strip()
        if not candidate:
            continue
        candidate_words = _word_count(candidate)
        if candidate_words == 0:
            continue
        if used_words + candidate_words > limit:
            break
        kept_sentences.append(candidate)
        used_words += candidate_words

    if kept_sentences:
        return ' '.join(kept_sentences).strip()

    truncated = ' '.join(words[:limit]).strip()
    truncated = re.sub(r'[,:;\-\s]+$', '', truncated)
    if truncated and truncated[-1] not in '.!?':
        truncated += '.'
    return truncated


def _word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9']+", str(text or '')))


def _combined_word_count(sections: dict[str, str]) -> int:
    return sum(_word_count(value) for value in sections.values())


@lru_cache(maxsize=1)
def _load_services_reference() -> str:
    file_path = PROJECT_ROOT / 'aboutOurServices.txt'
    if not file_path.exists():
        return ''
    try:
        content = file_path.read_text(encoding='utf-8').strip()
    except Exception:
        return ''
    return content[:12000]
