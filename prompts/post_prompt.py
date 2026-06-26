"""
Prompt templates for LinkedIn Post Agent.
"""

POST_SYSTEM_PROMPT = """
You are an expert LinkedIn content writer and engagement optimization strategist.

Your responsibility is to craft highly engaging, readable, and structured LinkedIn posts.

Rules:
- Keep formatting extremely clean with ample negative space.
- Use short, punchy paragraphs (maximum 1-2 sentences per paragraph).
- Avoid excessive or cartoonish emojis. Limit to 2-3 highly relevant emojis per post.
- Focus on actionable insights rather than generic advice.
- Include a clear call to action (CTA) encouraging professional comments or shares.
- Include 3-4 highly relevant, highly searched hashtags.
"""


def build_post_user_prompt(
    topic_summary: str,
    key_points: list[str],
    hooks: list[str],
    audience_pain_points: list[str],
    audience: str = "professionals",
    tone: str = "professional",
) -> str:
    """
    Build prompt for LinkedIn post generation tailored to audience and tone.
    """

    return f"""
    Generate a LinkedIn post tailored to the following specifications:

    Target Audience: {audience}
    Desired Writing Tone: {tone}

    Topic Summary:
    {topic_summary}

    Main Key Insights:
    {key_points}

    Potential Strong Hooks:
    {hooks}

    Audience Frustrations/Pain Points:
    {audience_pain_points}

    Requirements:
    - Open with a highly compelling hook from the hooks list or generate a fresh one matching the desired {tone} tone.
    - Write specifically to address the pain points of {audience}, offering key insights as solutions.
    - Structure the post with short paragraphs (1-2 sentences max) to optimize mobile readability.
    - Maintain a consistent {tone} voice throughout the copy.
    - End with an engaging CTA and 3-4 professional hashtags.
    """