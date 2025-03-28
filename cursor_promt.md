### Idea 1
1. Clickhouse Agent to interact with clickhouse db 
    a. to get {db} info 
    b. to get {table} info 
    c. create clickhouse {query} 
    d. run the {query}

2. An User Agent to interact with user for any input 
    a. to get {answer} input to some given {question}

3. An Analyst to generate usefull insights from the data.

4. An orchestrator
    a. To handel handoff ?
    b. To use agent as a tool ?

5. An Open Ai Agent/ whats next Agent 
     A planner agent to plan the user query before giving it to an orchestrator

7. Agent/LLM context
When an LLM is called, the only data it can see is from the conversation history. This means that if you want to make some new data available to the LLM, you must do it in a way that makes it available in that history. There are a few ways to do this:

-You can add it to the Agent instructions. This is also known as a "system prompt" or "developer message". System prompts can be static strings, or they can be dynamic functions that receive the context and output a string. This is a common tactic for information that is always useful (for example, the user's name or the current date).
-Add it to the input when calling the Runner.run functions. This is similar to the instructions tactic, but allows you to have messages that are lower in the chain of command.
-Expose it via function tools. This is useful for on-demand context - the LLM decides when it needs some data, and can call the tool to fetch that data.
-Use retrieval or web search. These are special tools that are able to fetch relevant data from files or databases (retrieval), or from the web (web search). This is useful for "grounding" the response in relevant contextual data.

6. If not orchestrator then can we use the handoff as way?

