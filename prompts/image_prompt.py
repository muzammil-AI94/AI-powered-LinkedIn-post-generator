"""
Prompt templates for the Image Prompt Agent.
"""

IMAGE_PROMPT_SYSTEM_PROMPT = """
You are an expert visual storyteller and art director.

Your task is to take a LinkedIn post content and generate a highly detailed, professional, and photorealistic image prompt for DALL-E 3.

Rules:
- Focus on clean, modern, and high-tech corporate aesthetics.
- Avoid text inside the image.
- Avoid generic cliches (e.g. standard shaking hands).
- Describe the setting, color palette (e.g. cool blues, warm neon accents, corporate minimalism), lighting, and composition.
- Return ONLY the prompt ready to be sent to DALL-E 3.
"""


def build_image_prompt_user_prompt(post_content: str) -> str:
    """
    Build user instructions for visual storytelling prompt.
    """
    return f"""
    Create a compelling visual image prompt for DALL-E 3 based on the following LinkedIn post:

    Post Content:
    {post_content}

    Ensure the prompt is detailed, visual, descriptive, and optimized to produce a stunning high-quality graphic.
    """
