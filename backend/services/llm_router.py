from typing import Optional, List, Any, Dict, Type
import structlog
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

from ..config.settings import get_settings

logger = structlog.get_logger(__name__)

# Fallback sequence definitions
TIER_FALLBACK_CHAINS = {
    "power": ["power", "balanced", "flash"],
    "balanced": ["balanced", "power", "flash"],
    "flash": ["flash", "balanced", "power"],
}

AGENT_TIER_MAPPING = {
    "planner": "flash",
    "architect": "balanced",
    "coder": "power",
    "tester": "power",
    "reviewer": "balanced",
    "devops": "flash",
}


def get_llm(tier: str) -> BaseChatModel:
    """
    Instantiate BaseChatModel based on tier.
    Falls back gracefully to alternative models if specific provider key is absent.
    """
    settings = get_settings()

    if tier == "power":
        if settings.OPENAI_API_KEY:
            return ChatOpenAI(
                model="gpt-4o",
                api_key=settings.OPENAI_API_KEY,
                temperature=0.2,
                max_retries=2,
                timeout=90,
            )
        elif settings.ANTHROPIC_API_KEY:
            return ChatAnthropic(
                model="claude-3-5-sonnet-20241022",
                api_key=settings.ANTHROPIC_API_KEY,
                temperature=0.2,
                max_retries=2,
                timeout=90,
            )
        else:
            return ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=settings.GOOGLE_API_KEY or "dummy",
                temperature=0.2,
            )

    elif tier == "balanced":
        if settings.ANTHROPIC_API_KEY:
            return ChatAnthropic(
                model="claude-3-5-sonnet-20241022",
                api_key=settings.ANTHROPIC_API_KEY,
                temperature=0.2,
                max_retries=2,
                timeout=90,
            )
        elif settings.OPENAI_API_KEY:
            return ChatOpenAI(
                model="gpt-4o",
                api_key=settings.OPENAI_API_KEY,
                temperature=0.2,
                max_retries=2,
                timeout=90,
            )
        else:
            return ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=settings.GOOGLE_API_KEY or "dummy",
                temperature=0.2,
            )

    elif tier == "flash":
        if settings.GOOGLE_API_KEY:
            return ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=settings.GOOGLE_API_KEY,
                temperature=0.2,
            )
        elif settings.OPENAI_API_KEY:
            return ChatOpenAI(
                model="gpt-4o-mini",
                api_key=settings.OPENAI_API_KEY,
                temperature=0.2,
            )
        else:
            return ChatAnthropic(
                model="claude-3-5-haiku-20241022",
                api_key=settings.ANTHROPIC_API_KEY or "dummy",
                temperature=0.2,
            )
    else:
        raise ValueError(f"Unknown LLM tier: {tier}")


def get_llm_for_agent(agent_name: str) -> BaseChatModel:
    """Return model configured for the specific agent role."""
    tier = AGENT_TIER_MAPPING.get(agent_name.lower(), "balanced")
    return get_llm(tier)


async def call_with_fallback(
    messages: List[BaseMessage],
    primary_tier: str = "power",
    max_retries: int = 3,
    structured_output_schema: Optional[Type[Any]] = None,
) -> Any:
    """
    Invoke LLM with tenacity retries and tiered fallback.
    Tiers flow through TIER_FALLBACK_CHAINS on failure.
    """
    fallback_tiers = TIER_FALLBACK_CHAINS.get(primary_tier, [primary_tier])
    last_error: Optional[Exception] = None

    for tier in fallback_tiers:
        try:
            logger.info("llm_invocation_attempt", tier=tier)
            llm = get_llm(tier)

            if structured_output_schema:
                model_with_structure = llm.with_structured_output(structured_output_schema)
                # Tenacity retry block per tier
                @retry(
                    stop=stop_after_attempt(max_retries),
                    wait=wait_exponential(multiplier=1, min=2, max=10),
                    reraise=True,
                )
                async def _invoke_structured():
                    return await model_with_structure.ainvoke(messages)

                result = await _invoke_structured()
                return result
            else:
                @retry(
                    stop=stop_after_attempt(max_retries),
                    wait=wait_exponential(multiplier=1, min=2, max=10),
                    reraise=True,
                )
                async def _invoke_text():
                    return await llm.ainvoke(messages)

                response = await _invoke_text()
                return response

        except Exception as e:
            logger.warning(
                "llm_tier_call_failed",
                tier=tier,
                error=str(e),
                falling_back=tier != fallback_tiers[-1],
            )
            last_error = e
            continue

    logger.error("all_llm_tiers_failed", last_error=str(last_error))
    raise RuntimeError(f"All LLM tiers failed to generate response. Last error: {last_error}") from last_error
