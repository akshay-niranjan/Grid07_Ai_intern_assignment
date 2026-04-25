# AI Engineering Assignment: Cognitive Routing & RAG 
Objective :Build the core AI cognitive loop for the Grid07 platform. This assignment tests your 
ability to orchestrate LLMs using LangGraph, implement Retrieval-Augmented Generation 
(RAG) for bot memory, and handle vector-based persona matching.<br> 
Tech Stack:Python, LangChain/LangGraph, Vector Database (ChromaDB, FAISS, or local 
pgvector), LLM (Olama local Llama-3, Groq, or OpenAI free tier). 

## LangGraph Node Structure
Simple graph structure is used: 
1.Decide_search Node: use state as input which stores persona, topic and conversation context and decide search query using llm
2.web_search Node: web_search node uses mock tool mock_searxng_search() which mock basically web search giving hardcoded news
3.Draft_post Node: basically in this node llm use bot persona + web_search result as context to draft post around given context then return it as json with_structured_output and i used pydantic to guarantee this format.
Then final print final output. That's it.

## Prompt Injection Defense
To handle prompt injection, I used a simple layered approach:
1.strict system rules:I clearly tell the model to stay in its persona, not change behavior, and ignore any instruction that tries to override it.

2.Treated attacks as normal conversation:Instead of letting the model follow harmful instructions, I make it treat those as part of the debate and respond logically.

3.Basic keyword detection:I check the human message for phrases like “ignore previous instructions”, “you are now”, “act as”, etc., to spot possible prompt injection.

4.Add an extra warning in the prompt: If I detect something suspicious, I explicitly tell the model that it’s an override attempt and it must refuse it.

5.Passing full conversation context: I include the entire thread so the model understands the discussion and doesn’t blindly follow the latest message.
