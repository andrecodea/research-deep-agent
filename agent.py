"""Build the agent graph for the Deep Research Assistant"""

import os
from datetime import datetime
import logging
from dotenv import load_dotenv
from pathlib import Path

from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents.middleware import SummarizationMiddleware, ToolRetryMiddleware, FilesystemFileSearchMiddleware
from deepagents import create_deep_agent, Runnable
from tools import research, extract, crawl, think
from tavily import UsageLimitExceededError

load_dotenv()
log = logging.getLogger(__name__)
BASE_DIR = Path(__file__).parent

# Loader function
def _load_prompt(filename:str) -> str:
    with open(BASE_DIR / filename, 'r', encoding='utf-8') as file:
        file.read()

# Prompt Loading
try:
    RESEARCH_WORKFLOW_INSTRUCTIONS = load_prompt("research_workflow_instructions.md")
    SUBAGENT_DELEGATION_INSTRUCTIONS = load_prompt("research_workflow_instructions.md")
    CRAWLER_INSTRUCTIONS = load_prompt("crawler_agent_instructions.md")
    EXTRACTOR_INSTRUCTIONS = load_prompt("extraction_agent_instructions.md")
    RESEARCHER_INSTRUCTIONS = load_prompt("research_agent_instructions.md")
    TASK_DESCRIPTION_PREFIX = load_prompt("task_description_prefix.md")
except FileNotFoundError as e:
    log.error(f"Failed to load prompt: {e}", exc_info=True)
    raise


def build_agent() -> Runnable:
    """Initializes deepagent with subagents"""
    try:
        log.info("[AGENT] Initializing Deep Research Agent")

        # Init model parameters
        api_key = os.getenv("INCEPTION_API_KEY")
        base_url = os.getenv("BASE_URL", "https://api.inceptionlabs.ai/v1")
        model_name = os.getenv("MODEL_NAME", "mercury-2")

        # Init agent parameters
        max_concurrent_research_units = int(os.getenv("MAX_CONCURRENT_RESEARCH_UNITS", 5))
        max_subagent_iterations = int(os.getenv("MAX_SUBAGENTS_ITERATIONS", 3))
        summarizer_model = os.getenv("SUMMARIZER_MODEL", "gpt-4.1-mini")
        recursion_limit = int(os.getenv("RECURSION_LIMIT", 50))

        # Get current date
        current_date = datetime.now().strftime("%d-%m-%Y")

        # Fallback to OpenAI
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")
            base_url = 'https://api.openai.com/v1'
            model_name = 'gpt-5.2'
            if not api_key:
                raise EnvironmentError("No LLM API key found, please provide either an INCEPTION_API_KEY or OPENAI_API_KEY in the .env file")

        # Init model
        llm = init_chat_model(
            model=model_name,
            base_url=base_url,
            api_key=api_key
        )

        # --- INIT SUBAGENTS ---
        research_subagent = {
            "name": "research-agent",
            "description":  "Delegate research to the researcher sub-agent. Only give this researcher one topic at a time.",
            "system_prompt": RESEARCHER_INSTRUCTIONS.format(date=current_date),
            "tools": [research, think]
        }

        extract_subagent = {
            "name": "extract-agent",
            "description":  "Delegate web page extraction to the extracting sub-agent. Only give this extractor one topic at a time.",
            "system_prompt": EXTRACTOR_INSTRUCTIONS.format(date=current_date),
            "tools": [extract, think]
        }

        crawl_subagent = {
            "name": "crawling-agent",
            "description":  "Delegate multi web page crawling to the crawling sub-agent. Only give this crawler one topic at a time.",
            "system_prompt": CRAWLER_INSTRUCTIONS.format(date=current_date),
            "tools": [crawl, think]
        }

        tools = [research, extract, crawl, think]
        subagents = [research_subagent, extract_subagent, crawl_subagent]
        other_agents = [s['name'] for s in subagents]

        INSTRUCTIONS = (
            RESEARCH_WORKFLOW_INSTRUCTIONS
            + "\n\n"
            + "=" * 80
            + "\n\n"
            + "=" * 80
            + TASK_DESCRIPTION_PREFIX
            + "\n\n"
            + SUBAGENT_DELEGATION_INSTRUCTIONS.format(
                max_concurrent_research_units=max_concurrent_research_units,
                max_subagent_iterations=max_subagent_iterations,
                other_agents=other_agents,
            )
        )

        # --- INIT ORCHESTRATOR --- 
        agent_graph = create_deep_agent(
            model=llm,
            tools=tools,
            system_prompt=INSTRUCTIONS,
            subagents=subagents,
            checkpointer=InMemorySaver(),
            middleware=[
                ToolRetryMiddleware(
                    max_retries=3,
                    backoff_factor=2, # waits 2x the time on each retry
                    retry_on=[TimeoutError, ConnectionError, UsageLimitExceededError] # For tavily API errors
                ),

                # Context management middlewares
                SummarizationMiddleware( 
                    model=summarizer_model,
                    trigger=("fraction", 0.8),
                    keep=("fraction", 0.8) # removes 20% of context window
                ),
                FilesystemFileSearchMiddleware(
                    root_path="./workspace"
                )
            ]
        )

        log.info(f"[AGENT] Deep Research Agent created with model={model_name}")
        log.info(f"[AGENT] Main tools: {[t.name for t in tools]}")
        return agent_graph.with_config({"recursion_limit": recursion_limit})
    except Exception as e:
        log.error(f"build_agent function failed: {e}", exc_info=True)
        raise