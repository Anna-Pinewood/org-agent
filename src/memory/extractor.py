EXTRACT_PREFERENCE_PROMPT = """Analyze the interaction context and extract user preferences or facts if they exist. Focus on discovering stated or implied preferences about rooms, timings, processes etc.

Context:
User command or dialog: {user_text}
Scenario type: {scenario_type}

If NO preferences are found, return null.
If preferences ARE found, return them in the following JSON structure:
{
    "header": "Brief category name - e.g. Room preference, Time preference, Booking workflow preference",
    "text": "Complete fact in natural language that captures the preference context",
    "origins": "The exact text that contained this preference"
}

Examples:

Input: "Мне нужна аудитория 1405, но пойдёт и 1404, они рядом находятсяtoo - they are close to each other"
Output: {
    "header": "Room preference",
    "text": "User prefers room 1404, with room 1405 as acceptable alternative due to proximity",
    "origins": "I need room 1404, but if it's not available then 1405 would work too - they are close to each other"
}

Input: "I prefer morning bookings, they work better for me"
Output: {
    "header": "Time preference", 
    "text": "User prefers to book rooms in the morning",
    "origins": "I prefer morning bookings, they work better for me"
}

Input: "Can you book a room for next Thursday?"
Output: null

Return only valid JSON or null without additional explanations."""