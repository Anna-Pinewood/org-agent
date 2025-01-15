ANALYZE_ERROR_PROMPT_BROWSER = """An agent is trying to perform some action with existing tools, but something went wrong OR the process wasn't completed (some step is missing). Analyze the failed step execution and suggest the next tool to use to fix problem gradually (or complete process). You must not suggest all the necessary tools at once. Give only one tool at a time.
Important form handling rules:

CRITICAL: Browser forms lose all input data after any page reload or form submission. You must ALWAYS re-fill ALL form fields after any navigation, submission, or error

Common form interaction patterns:
- Fill all required fields before clicking submit.
-  If you are refilling form, use the same values as before unless human instructed you otherwise.
- After validation errors, re-enter ALL fields, not just the incorrect ones
- Click submit/save buttons to trigger form processing. Buttons and interactive elements need explicit clicks to trigger actions
- Select options from dropdowns require both opening AND selecting
- After any page reload, assume all previous inputs are cleared
- Watch for validation messages or error states after submissions if you feel like you missed something

Context:

Step execution history: {history}

Available tools and their descriptions:
{tool_descriptions}

If you use tools, that was used before, you MUST USE THE SAME TOOLS as were used originally unless human passed you new values. 
Return a JSON with this structure:
{{
"analysis": "Brief analysis of what went wrong, including the prev params, probable error causes, suggestions",
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

ANALYZE_ERROR_PROMPT_BROWSER_MULTI = """An agent is trying to perform some action with existing tools, but something went wrong OR the process wasn't completed (some step is missing). Analyze the failed step execution and suggest up to 3 tools to fix the problem gradually. These tools will be executed in sequence.

Important form handling rules:

CRITICAL: Browser forms lose all input data after any page reload or form submission. You must ALWAYS re-fill ALL form fields after any navigation, submission, or error

Common form interaction patterns:
- Fill all required fields before clicking submit. If you are refilling form, use the same values as before unless human instructed you otherwise
- After validation errors, re-enter ALL fields, not just the incorrect ones
- Click submit/save buttons to trigger form processing. Buttons and interactive elements need explicit clicks to trigger actions
- Select options from dropdowns require both opening AND selecting
- After any page reload, assume all previous inputs are cleared
- Watch for validation messages or error states after submissions if you feel like you missed something

Guidelines for suggesting multiple tools:
- Suggest 1-3 tools that should be executed in sequence
- Each tool should build on the previous one's expected outcome
- Tools must be logically connected (e.g. fill form field -> validate field -> submit form)
- If you're unsure about later steps, suggest fewer tools
- If suggesting form interactions, group related field fills together
- When reusing tools that were used before, you MUST USE THE SAME PARAMS as were used originally unless human passed new values

Context:

Step execution history: {history}

Available tools and their descriptions:
{tool_descriptions}

Return a JSON with this structure:
{{
    "analysis": "Brief analysis of what went wrong, including the prev params, probable error causes, suggestions",
    "next_action": [
        {{
            "tool_name": "Name of first tool",
            "params": {{
                "param1": "value1",
                ...
            }}
        }},
        {{
            "tool_name": "Name of second tool",
            "params": {{
                "param1": "value1",
                ...
            }}
        }},
        ...  # Up to 3 tools total
    ]
}}

Return only valid JSON without comments. Ensure the "next_action" array contains 1-3 tools."""