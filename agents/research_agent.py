"""
Research Agent implementation.

Responsibilities:
-----------------
- analyze LinkedIn topics
- extract structured insights
- identify audience pain points
- generate hooks

This agent focuses on:
- low latency
- deterministic outputs
- structured orchestration
"""

from app.core.logger import logger
from app.prompts.research_prompt import (
    RESEARCH_SYSTEM_PROMPT,
    build_research_user_prompt,
)
from app.schemas.research_schema import (
    ResearchOutput,
)
from app.services.openai_service import (
    openai_service,
)


class ResearchAgent:
    """
    Agent responsible for topic research and insight extraction.
    """

    async def run(
        self,
        topic: str,
    ) -> ResearchOutput:
        """
        Execute research workflow.

        Args:
            topic:
                LinkedIn topic provided by user.

        Returns:
            Structured research output.
        """

        logger.info(
            "research_agent_started",
            topic=topic,
        )

        response = (
            await openai_service.generate_structured_completion(
                system_prompt=RESEARCH_SYSTEM_PROMPT,
                user_prompt=build_research_user_prompt(
                    topic=topic,
                ),
                response_model=ResearchOutput,
                temperature=0.5,
            )
        )

        logger.info(
            "research_agent_completed",
            topic=topic,
        )

        return response


research_agent = ResearchAgent()
