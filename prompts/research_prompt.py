"""
Prompt templates for the Research Agent.

Why this module exists:
------------------------
Separates prompt logic from agent logic.

Benefits:
- easier maintenance
- easier prompt iteration
- cleaner architecture
- reusable prompting
"""


RESEARCH_SYSTEM_PROMPT = """
Generate concise LinkedIn research insights.

Return:
- practical insights
- concise bullet points
- strong hooks
- actionable ideas

Keep outputs compact and structured.
"""


def build_research_user_prompt(topic: str) -> str:
    """
    Build user prompt for research generation.

    Args:
        topic:
            LinkedIn topic from user.

    Returns:
        Formatted prompt string.
    """

    return f"""
Analyze the following LinkedIn topic:

Topic:
{topic}

Generate a valid JSON response using this exact structure:

{{
    "topic_summary": "string",
    "key_points": [
        "point 1",
        "point 2",
        "point 3"
    ],
    "hooks": [
        "hook 1",
        "hook 2",
        "hook 3"
    ],
    "audience_pain_points": [
        "pain point 1",
        "pain point 2",
        "pain point 3"
    ]
}}

Rules:
- return ONLY valid JSON
- no markdown
- no explanations
- no extra text
- keep responses concise
"""