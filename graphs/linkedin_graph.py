"""
LangGraph workflow orchestration.

Responsibilities:
-----------------
- define workflow state including new tone, audience, and image options
- orchestrate agents in sequence
- integrate Topic Intelligence Service in discovery node
- manage execution flow and node connections
- push real-time workflow stage progress updates to Redis/Memory cache
"""

import asyncio
from typing import Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.post_agent import post_agent
from app.agents.research_agent import research_agent
from app.agents.topic_agent import topic_agent
from app.db.database import AsyncSessionLocal
from app.schemas.research_schema import ResearchOutput
from app.schemas.topic_schema import TopicDiscoveryOutput
from app.services.topic_intelligence_service import (
    topic_intelligence_service,
    ScoredTopic,
)
from app.utils.cache import cache


class LinkedInState(TypedDict):
    """
    Shared workflow state passed between all agent nodes.
    """

    topic: Optional[str]
    topic_reason: str
    niche: Optional[str]
    base_score: Optional[float]
    final_score: Optional[float]
    research_data: Optional[ResearchOutput]
    final_post: str

    # Direct parameters from HTTP request
    audience: Optional[str]
    tone: Optional[str]
    generate_image: Optional[bool]
    task_id: Optional[str]


def update_task_stage(task_id: str, stage: str) -> None:
    """
    Synchronous helper to run the async cache setter for stage tracking.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        # Schedule the coroutine on the running event loop
        asyncio.ensure_future(cache.set(f"task_stage:{task_id}", stage))
    else:
        loop.run_until_complete(cache.set(f"task_stage:{task_id}", stage))


# ---------------------------------------------------------------------------
# Node functions
# ---------------------------------------------------------------------------

async def topic_discovery_node(
    state: LinkedInState,
) -> LinkedInState:
    """
    Execute autonomous topic discovery, scoring, and freshness ranking.
    """
    if state.get("task_id"):
        update_task_stage(state["task_id"], "TOPIC_DISCOVERY")

    topic_result: TopicDiscoveryOutput = await topic_agent.run()

    # Map candidate schemas to ScoredTopic domain objects
    candidates = [
        ScoredTopic(
            topic=c.topic,
            reason=c.reason,
            niche=c.niche,
            base_score=c.base_score,
        )
        for c in topic_result.candidates
    ]

    async with AsyncSessionLocal() as session:
        best_candidate = (
            await topic_intelligence_service.rank_and_select_best_topic(
                db_session=session,
                candidates=candidates,
            )
        )

    if not best_candidate:
        raise ValueError("No viable topic candidate discovered or scored.")

    return {
        **state,
        "topic": best_candidate.topic,
        "topic_reason": best_candidate.reason,
        "niche": best_candidate.niche,
        "base_score": best_candidate.base_score,
        "final_score": best_candidate.final_score,
    }


async def research_node(
    state: LinkedInState,
) -> LinkedInState:
    """
    Execute Research Agent to extract structured insights.
    """
    if state.get("task_id"):
        update_task_stage(state["task_id"], "RESEARCHING")

    research_output = await research_agent.run(
        topic=state["topic"],
    )

    return {
        **state,
        "research_data": research_output,
    }


async def post_generation_node(
    state: LinkedInState,
) -> LinkedInState:
    """
    Execute LinkedIn Post Agent to generate final post tailored to audience and tone.
    """
    if state.get("task_id"):
        update_task_stage(state["task_id"], "POST_GENERATION")

    final_post = await post_agent.run(
        research_data=state["research_data"],
        audience=state.get("audience", "professionals"),
        tone=state.get("tone", "professional"),
    )

    return {
        **state,
        "final_post": final_post,
    }


# ---------------------------------------------------------------------------
# Routing logic
# ---------------------------------------------------------------------------

def route_from_start(
    state: LinkedInState,
) -> str:
    """
    Route the workflow based on whether a topic was provided.
    """

    if state.get("topic"):
        return "research_node"

    return "topic_discovery_node"


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

workflow = StateGraph(LinkedInState)

workflow.add_node("topic_discovery_node", topic_discovery_node)
workflow.add_node("research_node", research_node)
workflow.add_node("post_generation_node", post_generation_node)

workflow.add_conditional_edges(
    START,
    route_from_start,
    {
        "topic_discovery_node": "topic_discovery_node",
        "research_node": "research_node",
    },
)

workflow.add_edge("topic_discovery_node", "research_node")
workflow.add_edge("research_node", "post_generation_node")
workflow.add_edge("post_generation_node", END)

linkedin_graph = workflow.compile()
