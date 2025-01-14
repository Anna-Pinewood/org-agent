ANALYZE_ERROR_PROMPT_BROWSER = """An agent is trying to perform some action with existing tools, but something went wrong OR the process wasn't completed (some step is missing). Analyze the failed step execution and suggest the next tool to use to fix problem gradually (or complete process). You must not suggest all the necessary tools at once. Give only one tool at a time.

Mind this:
1. If you filled some form with many inputs and then clicked on submit button and din't get expected result, you need to fill all inputs again, because the page was reloaded and all the data probably was lost.
2. Don't forget you are working with browser, so sometimes you need to click on some action items to acrually trigger the action, espicially if you filled some form and then didn't click on submit button or open some selector and then didn't pick the option, etc.

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
