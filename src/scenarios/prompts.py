ANALYZE_ERROR_PROMPT_BROWSER = """An agent is trying to perform some action with existing tools,but something went wrong. Analyze the failed step execution and suggest the next tool to use to fix problem gradually. You must not suggest all the necessary tools at once. Give only one tool at a time. Don't forget you are working with browser, so sometimes you need to click on some action items to acrually trigger the action.

Context:
- Step execution history: {history}

Available tools and their descriptions:
{tool_descriptions}

Return a JSON with this structure:
{{
    "analysis": "Brief analysis of what went wrong",
    "next_action": {{
        "tool_name": "Name of tool to use next",
        "params": {{
            "param1": "value1",
            ...
        }}
    }}
}}

Return only valid JSON without comments."""

ANALYZE_ERROR_PROMPT_BASE = """An agent is trying to perform some action with existing tools,but something went wrong. Analyze the failed step execution and suggest the next tool to use to fix problem gradually. You must not suggest all the necessary tools at once. Give only one tool at a time. 

Context:
- Step execution history: {history}

Available tools and their descriptions:
{tool_descriptions}

Return a JSON with this structure:
{{
    "analysis": "Brief analysis of what went wrong",
    "next_action": {{
        "tool_name": "Name of tool to use next",
        "params": {{
            "param1": "value1",
            ...
        }}
    }}
}}

Return only valid JSON without comments."""
