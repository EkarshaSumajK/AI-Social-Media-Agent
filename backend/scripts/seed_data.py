"""Seed the database with realistic WellNest Group content data."""
import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, text

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.enums import (
    ArticleStatus, CampaignPhase, CampaignStatus, Platform,
    SocialPlatform, SocialStatus, TopicCategory, TopicStatus, UserRole,
)
from app.models import (
    Article, AuditLog, Campaign, CampaignPiece, Competitor,
    HookTemplate, SocialPost, SwipeFile, Topic, User,
)

settings = get_settings()
NOW = datetime.now(timezone.utc)


async def _already_seeded(db) -> bool:
    r = await db.execute(select(User).where(User.email == "reviewer-connect@wellnestgroup.com"))
    return r.scalar_one_or_none() is not None


async def seed():
    async with SessionLocal() as db:
        await db.execute(text(f"SET search_path TO {settings.database_schema}, public"))

        if await _already_seeded(db):
            print("⏭  Seed data already exists — skipping.")
            return

        # ── Users ──────────────────────────────────────────────────
        admin = (await db.execute(select(User).where(User.email == settings.admin_email))).scalar_one_or_none()
        if not admin:
            admin = User(
                email=settings.admin_email, full_name=settings.admin_full_name,
                hashed_password=get_password_hash(settings.admin_password),
                role=UserRole.ADMIN, platform=Platform.HORIZON, is_active=True,
            )
            db.add(admin)
            await db.flush()

        reviewer_c = User(
            email="reviewer-connect@wellnestgroup.com", full_name="Priya Sharma",
            hashed_password=get_password_hash("Reviewer@Connect1"),
            role=UserRole.REVIEWER, platform=Platform.CONNECT, is_active=True,
        )
        reviewer_h = User(
            email="reviewer-horizons@wellnestgroup.com", full_name="Arjun Reddy",
            hashed_password=get_password_hash("Reviewer@Horizons1"),
            role=UserRole.REVIEWER, platform=Platform.HORIZON, is_active=True,
        )
        db.add_all([reviewer_c, reviewer_h])
        await db.flush()

        # ── Topics ─────────────────────────────────────────────────
        topic_data = [
            dict(title="CBSE Introduces Mandatory Mental Health Curriculum for Classes 6-12",
                 source_url="https://indianexpress.com/article/education/cbse-mental-health-curriculum-2025",
                 source_name="Indian Express", relevance_label="high", relevance_score=92,
                 age_group="adolescent", topic_type="education", mental_health_specific=True,
                 trust_score=85, is_trending=True, x_engagement_score=78.5, x_tweet_count=340,
                 topic_category=TopicCategory.HEALTH.value, region="india",
                 platform=Platform.CONNECT, status=TopicStatus.PROCESSED,
                 summary="CBSE has announced a new framework integrating mental health education into the core curriculum for secondary students."),
            dict(title="WHO Report: Teen Anxiety Rates Triple Post-Pandemic Globally",
                 source_url="https://www.who.int/news/teen-anxiety-rates-2025",
                 source_name="WHO", relevance_label="high", relevance_score=95,
                 age_group="teen", topic_type="research", mental_health_specific=True,
                 trust_score=98, is_trending=True, x_engagement_score=120.3, x_tweet_count=890,
                 topic_category=TopicCategory.HEALTH.value, region="global",
                 platform=Platform.HORIZON, status=TopicStatus.PROCESSED,
                 summary="A comprehensive WHO study reveals teen anxiety rates have tripled since the COVID-19 pandemic."),
            dict(title="Corporate Wellness Programs Reduce Burnout by 40% — McKinsey Study",
                 source_url="https://www.mckinsey.com/wellness-programs-burnout-2025",
                 source_name="McKinsey", relevance_label="high", relevance_score=88,
                 age_group="adult", topic_type="business", mental_health_specific=False,
                 trust_score=90, is_trending=False, topic_category=TopicCategory.BUSINESS.value,
                 region="global", platform=Platform.HORIZON, status=TopicStatus.PROCESSED,
                 summary="McKinsey research shows structured corporate wellness programs can reduce employee burnout by 40%."),
            dict(title="India's National Mental Health Policy 2025: Key Highlights",
                 source_url="https://pib.gov.in/mental-health-policy-2025",
                 source_name="PIB India", relevance_label="high", relevance_score=90,
                 age_group="all", topic_type="policy", mental_health_specific=True,
                 trust_score=95, is_trending=True, x_engagement_score=65.0, x_tweet_count=210,
                 topic_category=TopicCategory.POLITICS.value, region="india",
                 platform=Platform.HORIZON, status=TopicStatus.PROCESSED,
                 summary="India unveils a comprehensive national mental health policy with focus on school-based interventions."),
            dict(title="Screen Time and Child Development: New NIH Longitudinal Study Results",
                 source_url="https://www.nih.gov/news/screen-time-child-development-2025",
                 source_name="NIH", relevance_label="medium", relevance_score=75,
                 age_group="child", topic_type="research", mental_health_specific=True,
                 trust_score=96, is_trending=False, topic_category=TopicCategory.TECHNOLOGY.value,
                 region="usa", platform=Platform.CONNECT, status=TopicStatus.PROCESSED,
                 summary="NIH longitudinal data shows nuanced effects of screen time on child cognitive and emotional development."),
            dict(title="AI-Powered Therapy Apps: Promise and Ethical Concerns",
                 source_url="https://www.theguardian.com/technology/ai-therapy-apps-2025",
                 source_name="The Guardian", relevance_label="medium", relevance_score=70,
                 age_group="adult", topic_type="technology", mental_health_specific=True,
                 trust_score=80, is_trending=False, topic_category=TopicCategory.AI.value,
                 region="global", platform=Platform.HORIZON, status=TopicStatus.PROCESSED,
                 summary="Experts weigh in on the rise of AI therapy chatbots and the ethical implications for patient care."),
            dict(title="Parenting in the Digital Age: Managing Children's Online Anxiety",
                 source_url="https://timesofindia.indiatimes.com/parenting-digital-anxiety-2025",
                 source_name="Times of India", relevance_label="medium", relevance_score=68,
                 age_group="child", topic_type="parenting", mental_health_specific=True,
                 trust_score=72, is_trending=False, topic_category=TopicCategory.HEALTH.value,
                 region="india", platform=Platform.PARENTSHALA, status=TopicStatus.NEW,
                 summary="Rising concerns about children's digital exposure and its impact on anxiety levels."),
            dict(title="Startup Founder Mental Health Crisis: Investors Take Notice",
                 source_url="https://livemint.com/startups/founder-mental-health-2025",
                 source_name="Livemint", relevance_label="low", relevance_score=55,
                 age_group="adult", topic_type="business", mental_health_specific=True,
                 trust_score=75, is_trending=False, topic_category=TopicCategory.STARTUPS.value,
                 region="india", platform=Platform.HORIZON, status=TopicStatus.NEW,
                 summary="VCs are increasingly prioritizing founder wellbeing as burnout rates surge in the Indian startup ecosystem."),
            dict(title="NEP 2020 Progress Report: Mental Wellness Integration in Schools",
                 source_url="https://www.thehindu.com/education/nep-wellness-progress-2025",
                 source_name="The Hindu", relevance_label="high", relevance_score=82,
                 age_group="adolescent", topic_type="education", mental_health_specific=True,
                 trust_score=88, is_trending=False, topic_category=TopicCategory.HEALTH.value,
                 region="india", platform=Platform.CONNECT, status=TopicStatus.PROCESSED,
                 summary="Progress report on NEP 2020's mental wellness component shows mixed adoption across Indian states."),
            dict(title="Meditation Apps Market Reaches $5B — But Do They Actually Work?",
                 source_url="https://bbc.com/news/health/meditation-apps-effectiveness-2025",
                 source_name="BBC News", relevance_label="low", relevance_score=45,
                 age_group="adult", topic_type="technology", mental_health_specific=False,
                 trust_score=85, is_trending=False, topic_category=TopicCategory.MARKETING.value,
                 region="global", platform=Platform.HORIZON, status=TopicStatus.DUPLICATE_REJECTED,
                 summary="Analysis of the booming meditation app market and research on their clinical effectiveness."),
            dict(title="Speech Therapy Demand Surges 60% in Urban India",
                 source_url="https://hindustantimes.com/health/speech-therapy-demand-2025",
                 source_name="Hindustan Times", relevance_label="high", relevance_score=80,
                 age_group="child", topic_type="clinical", mental_health_specific=True,
                 trust_score=78, is_trending=True, x_engagement_score=42.0, x_tweet_count=150,
                 topic_category=TopicCategory.HEALTH.value, region="india",
                 platform=Platform.HORIZON, status=TopicStatus.PROCESSED,
                 summary="Urban India sees massive increase in demand for pediatric speech therapy services."),
            dict(title="Creator Economy and Mental Health: The Hidden Cost of Influencing",
                 source_url="https://reuters.com/lifestyle/creator-economy-mental-health-2025",
                 source_name="Reuters", relevance_label="medium", relevance_score=62,
                 age_group="young_adult", topic_type="social", mental_health_specific=True,
                 trust_score=92, is_trending=False, topic_category=TopicCategory.CREATOR_ECONOMY.value,
                 region="global", platform=Platform.HORIZON, status=TopicStatus.NEW,
                 summary="Reuters investigation into the mental health toll on content creators and influencers."),
        ]
        topics = [Topic(**d) for d in topic_data]
        db.add_all(topics)
        await db.flush()

        # ── Articles (linked to PROCESSED topics) ──────────────────
        processed = [t for t in topics if t.status == TopicStatus.PROCESSED]
        articles = []
        article_tpl = [
            dict(status=ArticleStatus.PUBLISHED, requires_review=False,
                 readability_score=82.5, ai_generated_probability=0.12,
                 source_similarity_score=0.15, structure_valid=True,
                 virality_score=8.2, clarity_score=9.0, hook_strength_score=7.8, conversion_score=7.5),
            dict(status=ArticleStatus.APPROVED, requires_review=False,
                 readability_score=78.3, ai_generated_probability=0.18,
                 source_similarity_score=0.22, structure_valid=True,
                 virality_score=7.5, clarity_score=8.5, hook_strength_score=7.0, conversion_score=7.0),
            dict(status=ArticleStatus.DRAFT, requires_review=True,
                 readability_score=75.0, ai_generated_probability=0.25,
                 source_similarity_score=0.30, structure_valid=True,
                 virality_score=6.5, clarity_score=7.8, hook_strength_score=6.5, conversion_score=6.0),
            dict(status=ArticleStatus.PUBLISHED, requires_review=False,
                 readability_score=85.0, ai_generated_probability=0.10,
                 source_similarity_score=0.12, structure_valid=True,
                 virality_score=8.8, clarity_score=9.2, hook_strength_score=8.5, conversion_score=8.0),
            dict(status=ArticleStatus.APPROVED, requires_review=False,
                 readability_score=80.0, ai_generated_probability=0.15,
                 source_similarity_score=0.20, structure_valid=True,
                 virality_score=7.0, clarity_score=8.0, hook_strength_score=7.2, conversion_score=7.0),
            dict(status=ArticleStatus.DRAFT, requires_review=True,
                 readability_score=72.0, ai_generated_probability=0.30,
                 source_similarity_score=0.35, structure_valid=False,
                 virality_score=5.5, clarity_score=7.0, hook_strength_score=5.8, conversion_score=5.5),
            dict(status=ArticleStatus.PUBLISHED, requires_review=False,
                 readability_score=88.0, ai_generated_probability=0.08,
                 source_similarity_score=0.10, structure_valid=True,
                 virality_score=9.0, clarity_score=9.5, hook_strength_score=8.8, conversion_score=8.5),
            dict(status=ArticleStatus.REJECTED, requires_review=False,
                 readability_score=60.0, ai_generated_probability=0.55,
                 source_similarity_score=0.60, structure_valid=False,
                 virality_score=3.0, clarity_score=5.0, hook_strength_score=4.0, conversion_score=3.5),
        ]
        for i, topic in enumerate(processed[:8]):
            tpl = article_tpl[i % len(article_tpl)]
            slug = topic.title.lower().replace(" ", "-").replace(":", "").replace("—", "")[:80]
            a = Article(
                topic_id=topic.id, content_html=f"<h1>{topic.title}</h1><p>{topic.summary or 'Content pending.'}</p>",
                seo_title=topic.title[:300], meta_description=(topic.summary or "")[:500],
                keywords=["mental health", "wellness", topic.topic_category or "health"],
                issue_summary=f"This article covers the key findings from: {topic.title}",
                why_it_matters="Mental health awareness is critical for early intervention and prevention.",
                mental_health_implications="Understanding these trends helps professionals design better support systems.",
                professional_insight="Experts recommend integrating mental wellness into everyday routines.",
                how_services_help="Wellnest Group provides therapy, counseling, and school wellness programs.",
                call_to_action="Book a free consultation at wellnesthorizons.com or learn more about Wellnest Connect.",
                source_url=topic.source_url, platform=topic.platform, slug=slug,
                created_by=admin.id,
                approved_by=admin.id if tpl["status"] in (ArticleStatus.APPROVED, ArticleStatus.PUBLISHED) else None,
                approved_at=NOW - timedelta(days=2) if tpl["status"] in (ArticleStatus.APPROVED, ArticleStatus.PUBLISHED) else None,
                published_at=NOW - timedelta(days=1) if tpl["status"] == ArticleStatus.PUBLISHED else None,
                published_url=f"https://wellnesthorizons.com/blog/{slug}" if tpl["status"] == ArticleStatus.PUBLISHED else None,
                **tpl,
            )
            db.add(a)
            articles.append(a)
        await db.flush()

        # ── Social Posts (2 per article) ───────────────────────────
        platforms_cycle = [SocialPlatform.INSTAGRAM, SocialPlatform.LINKEDIN,
                          SocialPlatform.TWITTER, SocialPlatform.FACEBOOK]
        statuses_cycle = [SocialStatus.POSTED, SocialStatus.READY, SocialStatus.DRAFT, SocialStatus.DRAFT]
        for i, art in enumerate(articles):
            for j in range(2):
                plat = platforms_cycle[(i * 2 + j) % 4]
                st = statuses_cycle[(i * 2 + j) % 4]
                db.add(SocialPost(
                    article_id=art.id, platform=plat,
                    caption=f"🧠 {art.seo_title[:100]}… Read more on our blog! #MentalHealth #Wellness",
                    edited_caption=f"✨ {art.seo_title[:80]} — Learn how this impacts you. Link in bio." if st == SocialStatus.POSTED else None,
                    status=st,
                    posted_at=NOW - timedelta(hours=12) if st == SocialStatus.POSTED else None,
                ))
        await db.flush()

        # ── Campaigns ──────────────────────────────────────────────
        campaigns_data = [
            dict(title="World Mental Health Day 2025", event_date=NOW + timedelta(days=60),
                 goal="Raise awareness and drive 500 consultations",
                 audience_description="Parents, teachers, and young adults aged 18-35 in urban India",
                 platforms=["instagram", "linkedin", "twitter"],
                 platform_entity="horizon", status=CampaignStatus.ACTIVE.value, created_by=admin.id),
            dict(title="Back-to-School Wellness Campaign", event_date=NOW + timedelta(days=30),
                 goal="Onboard 50 new schools onto Wellnest Connect",
                 audience_description="School administrators and counselors in Tier 1 and Tier 2 Indian cities",
                 platforms=["linkedin", "email"],
                 platform_entity="connect", status=CampaignStatus.DRAFT.value, created_by=reviewer_c.id),
            dict(title="Parenting Workshop Series Launch", event_date=NOW - timedelta(days=10),
                 goal="Drive registrations for 3-part parenting workshop",
                 audience_description="Parents of children aged 5-15",
                 platforms=["instagram", "facebook", "whatsapp"],
                 platform_entity="parentshala", status=CampaignStatus.COMPLETED.value, created_by=reviewer_h.id),
        ]
        campaigns = [Campaign(**d) for d in campaigns_data]
        db.add_all(campaigns)
        await db.flush()

        # ── Campaign Pieces ────────────────────────────────────────
        phases = [CampaignPhase.PRE.value, CampaignPhase.DURING.value, CampaignPhase.POST.value]
        content_types = ["email", "social", "ad"]
        for ci, camp in enumerate(campaigns):
            for pi, phase in enumerate(phases):
                db.add(CampaignPiece(
                    campaign_id=camp.id, phase=phase, content_type=content_types[pi],
                    platform=camp.platforms[0] if camp.platforms else None,
                    content=f"[{phase.upper()}] {camp.title} — {content_types[pi]} content.\n\nKey message: {camp.goal}",
                    scheduled_for=camp.event_date + timedelta(days=-7 + pi * 7) if camp.event_date else None,
                    status="posted" if camp.status == CampaignStatus.COMPLETED.value else "draft",
                ))
        await db.flush()

        # ── Competitors ────────────────────────────────────────────
        competitors_data = [
            ("Amaha Health", "instagram", "https://instagram.com/amahahealth", "horizon"),
            ("YourDOST", "linkedin", "https://linkedin.com/company/yourdost", "horizon"),
            ("MindPeers", "twitter", "https://twitter.com/mindpeers", "horizon"),
            ("Manah Wellness", "linkedin", "https://linkedin.com/company/manahwellness", "connect"),
            ("Lissun", "instagram", "https://instagram.com/lissunapp", "horizon"),
            ("InnerHour", "instagram", "https://instagram.com/innerhour", "horizon"),
        ]
        for name, plat, url, pe in competitors_data:
            db.add(Competitor(name=name, platform=plat, profile_url=url,
                              platform_entity=pe, created_by=admin.id))
        await db.flush()

        # ── Hook Templates ─────────────────────────────────────────
        hooks = [
            ("Did you know 1 in 4 teens experience clinical anxiety? Here's what parents can do →", "health", "instagram"),
            ("Your school's biggest risk isn't academics. It's student wellbeing.", "health", "linkedin"),
            ("Thread 🧵: 5 signs your child might be struggling silently with anxiety", "health", "twitter"),
            ("Stop scrolling. Your mental health matters more than this feed.", "health", "instagram"),
            ("Why India's top companies are investing ₹50Cr+ in employee wellness programs", "business", "linkedin"),
            ("3 CBT techniques you can practice at home today 👇", "health", "instagram"),
            ("The ROI of school counseling programs might surprise you 📊", "marketing", "linkedin"),
            ("Hot take: Most meditation apps don't work. Here's what does.", "technology", "twitter"),
            ("We asked 500 parents about their biggest parenting fear. The #1 answer?", "health", "facebook"),
            ("Your child's screen time is not the real problem. This is →", "technology", "instagram"),
            ("Burnout isn't a badge of honor. Here's how to actually recover.", "business", "linkedin"),
            ("Breaking: India's new mental health policy changes everything for schools", "health", "twitter"),
        ]
        for hook_text, cat, plat in hooks:
            db.add(HookTemplate(hook_text=hook_text, category=cat, platform=plat,
                                use_count=0, created_by=admin.id))
        await db.flush()

        # ── Swipe Files ────────────────────────────────────────────
        swipes = [
            ("Amaha's Viral Reel on Teen Anxiety", "instagram",
             "Hook: 'Your teen isn't lazy. They're overwhelmed.' — 2.3M views, 45K saves.",
             "https://instagram.com/p/example1", "Carousel format, emotional hook, CTA to DM",
             ["viral", "teen", "anxiety", "reels"]),
            ("YourDOST LinkedIn Thought Leadership Post", "linkedin",
             "Post about corporate wellness ROI with data visualization — 15K impressions, 800 reactions.",
             "https://linkedin.com/posts/example2", "Data-driven, visual charts, third-person proof",
             ["b2b", "corporate", "data", "thought-leadership"]),
            ("NIMHANS Awareness Twitter Thread", "twitter",
             "12-tweet thread on childhood ADHD myths — 5K retweets, 20K likes.",
             "https://twitter.com/nimhans/example3", "Thread format, myth-busting, expert authority",
             ["thread", "adhd", "myths", "education"]),
            ("Wellnest Connect School Success Story", "linkedin",
             "Case study post: How one Hyderabad school reduced student anxiety by 35% in 6 months.",
             None, "Case study format, specific metrics, testimonial quote",
             ["case-study", "school", "success", "connect"]),
        ]
        for title, plat, content, url, notes, tags in swipes:
            db.add(SwipeFile(created_by=admin.id, platform=plat, title=title,
                             content=content, source_url=url,
                             performance_notes=notes, tags=tags))
        await db.flush()

        # ── Audit Logs ─────────────────────────────────────────────
        log_entries = [
            (admin.id, "create_user", "User", str(reviewer_c.id), {"email": reviewer_c.email}),
            (admin.id, "create_user", "User", str(reviewer_h.id), {"email": reviewer_h.email}),
            (admin.id, "approve_article", "Article", str(articles[0].id), {"title": articles[0].seo_title[:50]}),
            (admin.id, "publish_article", "Article", str(articles[0].id), {"url": articles[0].published_url}),
            (admin.id, "approve_article", "Article", str(articles[1].id), {"title": articles[1].seo_title[:50]}),
            (admin.id, "create_campaign", "Campaign", str(campaigns[0].id), {"title": campaigns[0].title}),
            (reviewer_c.id, "create_campaign", "Campaign", str(campaigns[1].id), {"title": campaigns[1].title}),
            (admin.id, "reject_article", "Article", str(articles[7].id), {"reason": "High AI-generated probability"}),
            (reviewer_h.id, "create_campaign", "Campaign", str(campaigns[2].id), {"title": campaigns[2].title}),
            (admin.id, "add_competitor", "Competitor", "1", {"name": "Amaha Health"}),
        ]
        for actor_id, action, etype, eid, details in log_entries:
            db.add(AuditLog(actor_id=actor_id, action=action,
                            entity_type=etype, entity_id=eid, details=details))

        await db.commit()
        print("✅ Seed data inserted successfully!")
        print(f"   Users: 3 | Topics: {len(topics)} | Articles: {len(articles)}")
        print(f"   Social Posts: {len(articles)*2} | Campaigns: {len(campaigns)}")
        print(f"   Campaign Pieces: {len(campaigns)*3} | Competitors: {len(competitors_data)}")
        print(f"   Hook Templates: {len(hooks)} | Swipe Files: {len(swipes)} | Audit Logs: {len(log_entries)}")


if __name__ == "__main__":
    asyncio.run(seed())
