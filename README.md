# Club Manager Assistant Agent

# Process Manager
## Core Functions

* **Natural language cli interface** – The primary input processor that handles user commands in natural language like "Забронируй 3 аудитории на след четверг". Uses basic NLP tools OR LLM to understand intent, extract key information (dates, quantities, locations), and handle variations in command formulation. In future – must be able to understand context and references to previous commands or states.

* **Task Planning** – Creates an execution plan by breaking it into subtasks that can be performed with existing tools. Determines the sequence of operations, whether clarifications are needed, collects info, consideres dependencies and waiting periods (like approval waiting time). Prepares tool configurations and handles resource allocation.

* **Tool management decisions** – Decides when to create new tools or modify existing ones based on encountered tasks and errors. Analyzes command patterns to identify needs for new tools and monitors tool performance to suggest improvements. Makes decisions about caching frequently used tool configurations and command patterns.

* **Error handling and routing** – Analyzes errors at both tool and process levels to determine the best resolution strategy. Can decide to retry operations, switch to alternative approaches, or request user clarification. Uses error patterns to improve tool reliability and process flow.

* **Memory access control** – Makes decisions about when to store new information or retrieve historical data. Manages process states for long-running operations and maintains context between system runs. Controls what information, scenarios, repeated commands should be cached for quick access versus stored in long-term memory. Retrieve details from memory if command was brief ("Забронируй аудиторию").

# Interface Layers

* **Browser Interface** – Manages all web interactions. Handles element identification, interaction sequences, and state verification. Contains specialized scripts for common operations like hall booking or memo creation, with error detection and recovery mechanisms.

* **Telegram Interface** – Controls all Telegram-related operations including channel posting, bot event management, and direct messaging. Maintains chat states, and manages response monitoring. 
[Previous sections remain as is...]

* **Storage Interface** – Controls data persistence and retrieval operations for all system components. Implements different storage strategies for various data types: quick access for current process states, reliable storage for preferences and configurations, and optimized storage for command history and patterns, cache. Manages data versioning and cleanup.

* **Email Interface ** – Monitors email communications for booking approvals and other official responses. Handles email composition, attachments, and automated response analysis. Can be configured to notify the process manager about important status changes that should trigger next steps.

# Toolbox

* **Toolbox Manager** – Central point for tool registration, organization and lifecycle management. Maintains tool metadata including dependencies, version information, and usage statistics. Provides interfaces for the Process Manager to request tools, register new ones, or modify existing tools based on learned patterns.

* **Basic Tools** – Collection of fundamental operation tools including natural language processors, command parsers, and pattern matchers. These tools are used by the Process Manager directly and can be combined into more complex tool chains for specific tasks. Basic tools are highly reusable and well-tested.

* **Browser Tools** – Set of Selenium/PyAutoGUI scripts handling specific web interactions. Each tool is focused on a particular operation (like finding available halls or submitting booking forms) and includes error handling and state verification. Browser tools maintain their state and can report detailed operation results.

* **Communication Tools** – Collection of tools for various communication channels (Telegram, email). Includes specialized formatters for different message types, event creators, and response handlers. These tools understand channel-specific requirements and handle proper formatting and timing.

# Feature Processes

* **Hall Booking Process** – Complex process that combines multiple tools to handle the complete booking workflow. Starts with availability checking, proceeds to booking execution, monitors approval status, and triggers follow-up actions like rebooking or event creation. Maintains state throughout the potentially long-running process.

* **Moderator Call-up Process** – Handles moderator communications and scheduling. Maintains moderator contact information and preferences, sends personalized messages, interprets responses, and optimizes hall assignments. Can adapt its communication style based on previous interactions with each moderator.

* **Event Anouncement Process** – Event creation and announcement. Generates appropriate descriptions based on context and history, configures bot events, posts announcements, and monitors registration progress. Can modify event parameters based on registration patterns or special circumstances.

* **Memo Management Process** – Automates the creation and processing of official memos for guest access. Collects required information, formats it according to university requirements, submits for approval, and tracks approval status. Handles follow-up actions based on approval results.

# Memory Systems

* **Knowledge Base** – Long-term storage for system knowledge including learned preferences, common patterns, and historical decisions. Uses optimized storage and retrieval mechanisms to provide quick access to relevant information. Regularly updated with new insights from system operations.

* **Process States** – Maintains current state information for all active processes. Includes waiting conditions, next steps, and dependency tracking. Critical for resuming operations after interruptions and coordinating multiple parallel processes.

* **Command History** – Archives past commands and their execution results for pattern learning and optimization. Helps in understanding user preferences and common operation sequences. Used by Process Manager for improving task planning and tool selection.
