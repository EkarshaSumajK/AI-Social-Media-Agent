from fastapi import APIRouter
from pydantic import BaseModel

from app.services.llm_service import LLMClient

router = APIRouter()

# Per-template instructions telling OpenAI how to rewrite the content
_TEMPLATE_INSTRUCTIONS: dict[str, str] = {
    # Twitter
    'tip-card':           'Extract one clear health tip. Max 2 sentences.',
    'myth-vs-fact':       'Rewrite as: MYTH: [the wrong belief]\nFACT: [the correct truth].',
    'health-reminder':    'Extract the key health reminder. Max 2 sentences.',
    'quick-statistic':    'Start with the exact number/percentage statistic, then 1 sentence of context.',
    'checklist-tip':      'List 4-5 key points, one per line starting with a dash (-).',
    'awareness-message':  'Write a powerful awareness message. Max 3 sentences.',
    'daily-health-habit': 'Extract the daily habit recommendation. Max 2 sentences.',
    # LinkedIn
    'insight-card':          'Extract the core professional insight. Max 3 sentences.',
    'statistic-card':        'Lead with the key statistic, then 1-2 sentences of professional context.',
    'expert-quote':          'Rewrite as a single quotable expert statement. Max 30 words, no quotation marks.',
    'industry-trend':        'Summarize the healthcare industry trend. Max 3 sentences.',
    'research-finding':      'State the research finding clearly and professionally. Max 3 sentences.',
    'innovation-highlight':  'Highlight the healthcare innovation concisely. Max 3 sentences.',
    'case-study-snapshot':   'Summarize the case study key outcome. Max 3 sentences.',
    # Instagram
    'carousel-cover':     'Write a bold, compelling 1-line carousel title. Max 8 words.',
    'health-tips':        'List 4-5 health tips, one per line starting with a dash (-).',
    'symptoms-explainer': 'List 4-5 symptoms, one per line starting with a dash (-).',
    'do-vs-dont':         'Rewrite as: DO: [what to do]\nDON\'T: [what not to do].',
    'checklist-guide':    'List 5-6 checklist items, one per line starting with a dash (-).',
    'nutrition-tips':     'Extract 2-3 sentences of specific nutrition advice.',
    'wellness-routine':   'List 4-5 daily routine steps, one per line starting with a dash (-).',
    'prevention-tips':    'Write 2-3 sentences of actionable prevention advice.',
    # Threads
    'quote-card':           'Extract the single most quotable sentence. Max 25 words.',
    'simple-tip':           'Write one clear, actionable health tip. Max 2 sentences.',
    'health-reminder':      'Extract the key reminder as a direct, friendly message. Max 2 sentences.',
    'quick-fact':           'State one surprising or important health fact. Max 2 sentences.',
    'conversation-starter': 'Rewrite as an engaging question that invites replies. End with ?',
    'daily-wellness-tip':   'Write one practical daily wellness tip. Max 2 sentences.',
    # YouTube
    'number-list':       'Write a bold YouTube title starting with a number (e.g. "5 Reasons Why..."). Max 10 words.',
    'warning-thumbnail': 'Write a bold, attention-grabbing YouTube warning title. Max 8 words.',
    'myth-busting':      'Write a bold myth-busting YouTube title. Max 8 words.',
    'symptoms-guide':    'List exactly 4 key symptoms, one per line starting with a dash (-).',
    'doctor-explains':   'Write a YouTube title in the format "Doctor Explains: [topic]". Max 8 words.',
    'before-vs-after':   'Rewrite as: BEFORE: [old habit or situation]\nAFTER: [improved result].',
    'top-mistakes':      'Write a bold YouTube title about common mistakes. Max 8 words.',
}

_SYSTEM_PROMPT = (
    'You are an expert social media image copywriter. '
    'Reformat post content into concise, punchy text for image cards. '
    'Return only a JSON object with key "image_text". No markdown, no explanation.'
)


class ImageTextRequest(BaseModel):
    content: str
    platform: str
    template_type: str | None = None


class ImageTextResponse(BaseModel):
    image_text: str


@router.post('/extract', response_model=ImageTextResponse)
async def extract_image_text(req: ImageTextRequest) -> ImageTextResponse:
    instruction = _TEMPLATE_INSTRUCTIONS.get(
        req.template_type or '',
        'Summarize the key message in 2-3 punchy sentences for a social media image card.',
    )

    prompt = (
        f'Platform: {req.platform}\n'
        f'Template: {req.template_type or "general"}\n'
        f'Task: {instruction}\n\n'
        f'Source post:\n{req.content}\n\n'
        'Return JSON: {"image_text": "..."}'
    )

    llm = LLMClient()
    data = await llm.generate_json(
        prompt=prompt,
        system_prompt=_SYSTEM_PROMPT,
        model='gpt-4o-mini',
        temperature=0.3,
    )

    image_text = str(data.get('image_text') or '').strip()
    if not image_text:
        # Fallback: first 200 chars of original content
        image_text = req.content[:200].strip()

    return ImageTextResponse(image_text=image_text)
