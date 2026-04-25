from langchain_ollama import OllamaLLM
from langchain_core.tools import tool
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from typing import TypedDict
import json
from phase1 import route_post_to_bots,embedding_model
from langgraph.graph import StateGraph
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from pydantic import BaseModel  # to validate json format
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.8
)

@tool
def mock_searxng_search(query:str):
    """returns hardcoded, recent news headlines based on keywords (e.g., if query contains "crypto", return 
        "Bitcoin hits new a l-time high amid regulatory ETF approvals")."""

    #creating vector store of hardcoded news for similarity search with query 
    news = [
    "Bitcoin hits new all-time high amid ETF approvals",
    "Ethereum surges after major network upgrade",
    "AI stocks rally after strong earnings reports",
    "OpenAI releases new reasoning model",
    "Global markets remain stable amid uncertainty"
    ]
    docs = [Document(page_content=n) for n in news]
    vectorstore2 = Chroma.from_documents(
        documents=docs,
        embedding=embedding_model,
        persist_directory="./news_chroma_db",
        collection_metadata={"hnsw:space": "cosine"}
    )
    # performing similarity search with news vector store and returning top similar result
    results = vectorstore2.similarity_search(query,k=1)
    return results[0].page_content.strip()  # returning only top news result content

# Using llama3 as our llm
#llm = OllamaLLM(model="llama3")

# creating graphstate for langgraph
class GraphState(TypedDict):
    bot: str
    persona: str
    query: str
    web_search_result: str
    final_output: dict
    cosine_score: float
    bot_input_post: str

# Node 1: Decide Search
def decide_search(state: GraphState):
    prompt_template = PromptTemplate(
    input_variables=["persona"],
    template="""You are a bot with this personality: {persona}
            Decide a topic you want to post about today related to your personality generate a short sensible search query.
            Do not overcomplicate query keep it simple and straighforward.
            Return ONLY the query.
        """
    )
    prompt = prompt_template.invoke({"persona":state['persona']})

    response = llm.invoke(prompt)
    return {"query":response.content}            # llm will return query based on persona -> web_search

# Node 2: Web Search
def web_search(state: GraphState):
    result = mock_searxng_search.invoke(state["query"])    # return any one hardcoded news from my custom news document
    return {"web_search_result": result}

# Node 3: Draft Post using llm  
# persona + context -> llm -> json( bot_id,topic,post_content
def draft_post(state: GraphState):
    # prompt = persona+context and instruction to return JSON
    prompt_template = PromptTemplate(
        input_variables=["persona","web_search_result"],
        template="""You are a bot with this personality: {persona} 
            and Context: {web_search_result}
            Write a highly opinionated post (max 280 characters).
            Add topic of this post to JSON topic
            Choose bot_id from these 3 Bot_A_TechMaximalist,Bot_B_Skeptic,Bot_C_Finance
            Return STRICT JSON in this format:{{
                "bot_id": "...",
                "topic": "...",
                "post_content": "..."
            }}"""
    )
    prompt = prompt_template.invoke({
        'persona':state['persona'],
        'web_search_result':state['web_search_result']
    })
    

    class FinalOutput(BaseModel):
        bot_id: str
        topic: str
        post_content: str
    structured_llm = llm.with_structured_output(FinalOutput)
    response_json = structured_llm.invoke(prompt)
    # try:
    #     output = json.loads(response)
    # except:
    #     output = {
    #         "bot_id": state["bot"],
    #         "topic": "Not able to get topic",
    #         "post_content": response.strip()
    #     }
    return {"final_output": response_json.model_dump_json()}

# Getting bot persona using phase1 route_post_to_bots function
# building simple graph structure  
# (__start__)->(decide_search using bot persona)->(web_search using mock tool)->(draft_post using llm(bot persona+web_search_result))->(__end__)
def build_graph():
    graph = StateGraph(GraphState)
    graph.add_node("decide_search", decide_search)  # Node1: decide_search
    graph.add_node("web_search", web_search)        # Node2: web_search
    graph.add_node("draft_post", draft_post)        # Node3: draft_post
    graph.set_entry_point("decide_search")          # __start__ = Node1: decide_search
    graph.add_edge("decide_search", "web_search")   # Node1: decide_search -> Node2: web_search
    graph.add_edge("web_search", "draft_post")      # Node2: web_search -> Node3: draft_post
    graph.set_finish_point("draft_post")            # __end__ = Node3: draft_post = Final Output as JSON

    return graph.compile()

if __name__ == "__main__":
    graph = build_graph()
    new_post = "OpenAI just released a new model that might replace junior developers."
    state = route_post_to_bots(new_post)
    result = graph.invoke(state)

    text = json.loads(result['final_output'])
    print(json.dumps(text,indent=4))
