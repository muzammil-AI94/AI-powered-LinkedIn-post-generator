"""
Autonomous Topic Discovery Agent.
"""

from app.core.logger import logger
from app.prompts.topic_prompt import (
    TOPIC_SYSTEM_PROMPT,
    build_topic_user_prompt,
)
from app.schemas.topic_schema import (
    TopicDiscoveryOutput,
)
from app.services.openai_service import (
    openai_service,
)


class TopicAgent:
    """
    Agent responsible for discovering and proposing trending LinkedIn topics.
    """

    async def run(self) -> TopicDiscoveryOutput:
        """
        Execute autonomous discovery of multiple candidate topics.

        Returns:
            Structured output containing candidates list.
        """

        logger.info("topic_candidate_discovery_started")

        response = (
            await openai_service.generate_structured_completion(
                system_prompt=TOPIC_SYSTEM_PROMPT,
                user_prompt=build_topic_user_prompt(),
                response_model=TopicDiscoveryOutput,
                temperature=0.6,
            )
        )

        logger.info(
            "topic_candidate_discovery_completed",
            discovered_count=len(response.candidates),
        )

        return response


topic_agent = TopicAgent()