from openai import AsyncOpenAI

from app.config import settings
from app.services.ai_service import cache_key, check_ai_rate_limit, chunk_text, get_cached_ai, set_cached_ai


class AIService:
    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    @property
    def enabled(self) -> bool:
        return settings.ai_enabled and self.client is not None

    async def process_note(
        self,
        psychologist_id: str,
        client_id: str,
        note_text: str,
        locale: str = "uk",
    ) -> dict[str, str | list[str]]:
        if not self.enabled:
            return {
                "summary": "",
                "homework": "",
                "next_plan": "",
                "chunks": chunk_text(note_text),
                "skipped": "ai_disabled",
            }

        if not await check_ai_rate_limit(psychologist_id):
            return {
                "summary": "",
                "homework": "",
                "next_plan": "",
                "chunks": chunk_text(note_text),
                "skipped": "rate_limit",
            }

        cache_id = cache_key("note", psychologist_id, client_id, note_text[:500])
        cached = await get_cached_ai(cache_id)
        if cached:
            import json
            return json.loads(cached)

        lang = "Ukrainian" if locale == "uk" else "English"
        prompt = f"""You are an assistant for a licensed psychologist. Analyze session notes.
Respond in {lang}. Do not diagnose. Provide:
1) short summary (3-5 bullets)
2) homework suggestion
3) plan for next session

Notes:
{note_text}
"""

        response = await self.client.chat.completions.create(
            model=settings.openai_summary_model,
            messages=[
                {"role": "system", "content": "You help psychologists organize clinical notes. Never replace clinical judgment."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )
        content = response.choices[0].message.content or ""
        parts = content.split("\n\n", 2)
        result = {
            "summary": parts[0] if parts else content,
            "homework": parts[1] if len(parts) > 1 else "",
            "next_plan": parts[2] if len(parts) > 2 else "",
            "chunks": chunk_text(note_text),
            "skipped": "",
        }

        import json
        await set_cached_ai(cache_id, json.dumps(result))
        return result

    async def embed_chunks(self, chunks: list[str]) -> list[list[float] | None]:
        if not self.enabled or not chunks:
            return [None for _ in chunks]

        response = await self.client.embeddings.create(
            model=settings.openai_embedding_model,
            input=chunks,
        )
        return [item.embedding for item in response.data]

    async def pre_session_brief(
        self,
        psychologist_id: str,
        client_id: str,
        recent_notes: list[str],
        locale: str = "uk",
    ) -> str:
        if not self.enabled or not recent_notes:
            return ""

        if not await check_ai_rate_limit(psychologist_id):
            return ""

        cache_id = cache_key("brief", psychologist_id, client_id, "|".join(recent_notes)[:1000])
        cached = await get_cached_ai(cache_id)
        if cached:
            return cached

        lang = "Ukrainian" if locale == "uk" else "English"
        joined = "\n---\n".join(recent_notes[-12:])
        prompt = f"""Prepare the psychologist for today's session in {lang}.
Include: main theme, missed topics, trend (improving/worsening/stable), suggested focus today.

Recent notes:
{joined}
"""

        response = await self.client.chat.completions.create(
            model=settings.openai_insight_model,
            messages=[
                {"role": "system", "content": "Clinical assistant for psychologists only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        brief = response.choices[0].message.content or ""
        await set_cached_ai(cache_id, brief)
        return brief
