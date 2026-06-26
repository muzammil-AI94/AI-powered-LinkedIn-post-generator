"""
Centralized OpenAI service layer.

Responsibilities:
-----------------
- manage OpenAI API communication
- provide reusable AI generation methods
- enforce structured outputs
- centralize observability
- optimize token usage
"""

from typing import Type

from openai import AsyncOpenAI
from pydantic import BaseModel

from app.core.config import settings
from app.core.logger import logger


class OpenAIService:
    """
    Centralized OpenAI service.
    """

    def __init__(self) -> None:

        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
        )

    async def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate plain text response.

        Args:
            system_prompt:
                AI system instructions.

            user_prompt:
                User query.

            temperature:
                Creativity level.

        Returns:
            Generated text response.
        """

        logger.info(
            "openai_text_generation_started",
        )

        response = await self.client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            temperature=temperature,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
        )

        logger.info(
            "openai_text_generation_completed",
        )

        return response.choices[0].message.content

    async def generate_structured_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[BaseModel],
        temperature: float = 0.3,
    ) -> BaseModel:
        """
        Generate structured JSON output.

        Args:
            system_prompt:
                AI instructions.

            user_prompt:
                User input.

            response_model:
                Pydantic response schema.

            temperature:
                Creativity level.

        Returns:
            Structured validated response.
        """

        logger.info(
            "structured_openai_request_started",
        )

        response = (
            await self.client.beta.chat.completions.parse(
                model=settings.OPENAI_MODEL,
                temperature=temperature,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                response_format=response_model,
            )
        )

        logger.info(
            "structured_openai_request_completed",
        )

        return response.choices[0].message.parsed

    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
    ) -> str:
        """
        Generate image using DALL-E 3 model.

        Args:
            prompt: Visual storytelling prompt.
            size: Dimension size of the image.

        Returns:
            URL of the generated image.
        """
        logger.info("dalle_image_generation_started")

        response = await self.client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size=size,
            quality="standard",
        )

        logger.info("dalle_image_generation_completed")
        return response.data[0].url


openai_service = OpenAIService()