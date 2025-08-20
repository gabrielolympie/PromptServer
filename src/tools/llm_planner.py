from clients.prompt_client import PromptClient
import os

client = PromptClient()


async def llm_planner(tools: str, task: str) -> str:
    """
    Uses a large language model to plan a task given a set of tools.

    Args:
        tools (str): A json string describing the tools available for the task and their description
        task (str): A string describing the task to be performed.

    Returns:
        str: A string describing the planned task.
    """

    inputs = {
        "user_id" : "dont_care_who_need_money_anyways",
        "tools": tools,
        "task": task,
    }

    text = "Do as you wich"
    
    text, _, _ = await client.acall(inputs, route="/prompts/tool_planner", method="post")

    return text
