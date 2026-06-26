"""
LinkedIn Post Generation Agent.
"""

from app.core.logger import logger
from app.prompts.post_prompt import (
    POST_SYSTEM_PROMPT,
    build_post_user_prompt,
)
from app.schemas.research_schema import ResearchOutput
from app.services.openai_service import openai_service


class PostAgent:
    """
    Agent responsible for drafting high-quality, engaging LinkedIn posts.
    """

    async def run(
        self,
        research_data: ResearchOutput,
        audience: str = "professionals",
        tone: str = "professional",
    ) -> str:
        """
        Generate a LinkedIn post tailored to target audience, tone, and research insights.
        """

        logger.info(
            "post_agent_started",
            audience=audience,
            tone=tone,
        )

        system_prompt = POST_SYSTEM_PROMPT

        user_prompt = build_post_user_prompt(
            topic_summary=research_data.topic_summary,
            key_points=research_data.key_points,
            hooks=research_data.hooks,
            audience_pain_points=research_data.audience_pain_points,
            audience=audience,
            tone=tone,
        )

        response = await openai_service.generate_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7,
        )

        logger.info("post_agent_completed")

        return response.strip()


post_agent = PostAgent()