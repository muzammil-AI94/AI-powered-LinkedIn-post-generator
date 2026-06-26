"""
Image Prompt Generation Agent.
"""

from app.core.logger import logger
from app.prompts.image_prompt import (
    IMAGE_PROMPT_SYSTEM_PROMPT,
    build_image_prompt_user_prompt,
)
from app.services.openai_service import openai_service


class ImagePromptAgent:
    """
    Agent responsible for generating art direction prompts for DALL-E.
    """

    async def run(
        self,
        post_content: str,
    ) -> str:
        """
        Generate DALL-E ready prompt from post contents.

        Args:
            post_content: Generated LinkedIn post text.

        Returns:
            Stunning image generation prompt.
        """
        logger.info("image_prompt_agent_started")

        system_prompt = IMAGE_PROMPT_SYSTEM_PROMPT
        user_prompt = build_image_prompt_user_prompt(post_content)

        response = await openai_service.generate_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.6,
        )

        logger.info("image_prompt_agent_completed")
        return response.strip()


image_prompt_agent = ImagePromptAgent()
