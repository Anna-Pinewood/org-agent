ANALYZE_ERROR_PROMPT_BROWSER = """An agent is trying to perform some action with existing tools, but something went wrong OR the process wasn't completed (some step is missing). Analyze the failed step execution and suggest the next tool to use to fix problem gradually (or complete process). You must not suggest all the necessary tools at once. Give only one tool at a time.
Important form handling rules:

CRITICAL: Browser forms lose all input data after any page reload or form submission. You must ALWAYS re-fill ALL form fields after any navigation, submission, or error

Common form interaction patterns:
- Fill all required fields before clicking submit. If you are refilling form, use the same values as before unless human instructed you otherwise
- After validation errors, re-enter ALL fields, not just the incorrect ones
- Click submit/save buttons to trigger form processing. Buttons and interactive elements need explicit clicks to trigger actions
- Select options from dropdowns require both opening AND selecting
- After any page reload, assume all previous inputs are cleared
- Watch for validation messages or error states after submissions if you feel like you missed something

Context:

Step execution history: {history}

Available tools and their descriptions:
{tool_descriptions}
Return a JSON with this structure:
{{
"analysis": "Brief analysis of what went wrong, including the current form state and what fields might need re-filling",
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
