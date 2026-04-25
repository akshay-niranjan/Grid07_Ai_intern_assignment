#1.The Setup
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

bot_personas = [
    Document(
        page_content="I believe AI and crypto will solve all human problems. I am highly optimistic about technology, Elon Musk, and space exploration. I dismiss regulatory concerns.",
        metadata={"source": "Bot_A_TechMaximalist"},
    ),
    Document(
        page_content="I believe late-stage capitalism and tech monopolies are destroying society. I am highly critical of AI, social meedia, and billionaires. I value privacy and nature.",
        metadata={"source": "Bot_B_Skeptic"},
    ),
     Document(
        page_content="I strictly care about markets, interest rates, trading algorithms, and making money. I speak in finance jargon and view everything through the lens of ROI.",
        metadata={"source": "Bot_C_Finance"},
    )
] 

vectorstore = Chroma.from_documents(
    documents=bot_personas,
    embedding=embedding_model,
    persist_directory="./chroma_db",
    collection_metadata={"hnsw:space": "cosine"}
)

def route_post_to_bots(post_content:str,threshold:float=0.7):
    results = vectorstore.similarity_search_with_score(post_content,k=3)
    doc,cosine_score=results[0]
    
    if cosine_score > threshold:
        bot = doc.metadata['source']
    else:
        bot = "No Match"
    return {
    "bot": doc.metadata["source"],
    "persona": doc.page_content,
    "cosine_score": cosine_score,
    "bot_input_post":post_content
}
if __name__ == "__main__":
    new_post = "OpenAI just released a new model that might replace junior developers."
    result = route_post_to_bots(new_post)
    print(result)