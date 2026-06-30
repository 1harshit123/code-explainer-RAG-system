import os
import chromadb
import json
from chromadb.utils import embedding_functions
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from typing import Generator

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VECTOR_PATH = os.path.abspath(os.path.join(BASE_DIR, "../../vector_store"))
EMBEDDING_ENGINE = embedding_functions.DefaultEmbeddingFunction()
ENV_FILE_PATH = os.path.abspath(os.path.join(BASE_DIR, "../../.env"))
load_dotenv(dotenv_path=ENV_FILE_PATH)

GROQ_KEY = os.getenv("GROQ_API_KEY")

os.environ["GROQ_API_KEY"] = GROQ_KEY

class ChromaService:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=VECTOR_PATH)

    def get_collection(self, collection_name):
        return self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=EMBEDDING_ENGINE,
        )

def getting_raw_search_results(query:str, vector_path:str, collection_name: str):
    """This function will give the raw vector chunks closest to the query"""
    
    try:
        service = ChromaService()
        collection = service.get_collection(collection_name=collection_name)
    except Exception as e:
        print(f"Search Error: Could not find indexed collection on disk. Details: {e}")
        return None

    print(f"Querying database directly for: '{query}'")
    results = collection.query(
        query_texts=[query],
        n_results=5
    )
    return results


class CodeAnalysisResult(BaseModel):
    summary: str = Field(description="A brief plain-English explanation of how the matching modules handle the user query.")
    primary_function: str = Field(description="The primary function name responsible for handling the core task logic.")
    dependencies: list[str] = Field(description="List of external libraries or functions called inside these scopes.")

parser = JsonOutputParser(pydantic_object=CodeAnalysisResult)

llm = ChatGroq(
    model_name="llama-3.3-70b-versatile",
    temperature=0.2 
)

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert repository extraction assistant. 
Review the following retrieved code components, implementation details, and statistical metadata scores carefully.
Analyze the codebase structure and output a single structured JSON response object that follows the requested formatting layout instructions.

Retrieved Code Components:
{code_snippets}

Component Metadatas:
{metadatas}

Retrieval Proximity Scores (Cosine Distance):
{distances}

Instructions:
{format_instructions}"""),
    ("human", "{input}")
])

chain = prompt | llm | parser

def analyze_codebase_query(user_query: str, raw_chroma_results: dict):
    """
    Extracts parallel list structures from raw database responses 
    and pipes them into the LangChain + Groq parsing pipeline engine.
    """
    code_snippets_list = raw_chroma_results['documents'][0]
    metadatas_list = raw_chroma_results['metadatas'][0]
    distances_list = raw_chroma_results['distances'][0]

    result = chain.invoke({
        "input": user_query,
        "code_snippets": json.dumps(code_snippets_list, indent=2, ensure_ascii=False),
        "metadatas": json.dumps(metadatas_list, indent=2, ensure_ascii=False),
        "distances": json.dumps(distances_list, indent=2),
        "format_instructions": parser.get_format_instructions()
    })
    
    print("\n--- Structural LLM JSON Extraction Output ---")
    print(json.dumps(result, indent=2, ensure_ascii=False))

def stream_query_pipeline(user_query: str, collection_name: str) -> Generator[str, None, None]:
    """
    Function to handle the streamline SSE chat with the frontend.
    """
    raw_results = getting_raw_search_results(user_query, VECTOR_PATH, collection_name)
    
    if not raw_results or not raw_results.get('documents') or not raw_results['documents'][0]:
        yield "Error: No relevant code contextual markers found in the active database index cluster."
        return
    try:
        structured_analysis = chain.invoke({
            "input": user_query,
            "code_snippets": json.dumps(raw_results['documents'][0], indent=2, ensure_ascii=False),
            "metadatas": json.dumps(raw_results['metadatas'][0], indent=2, ensure_ascii=False),
            "distances": json.dumps(raw_results['distances'][0], indent=2),
            "format_instructions": "Output valid JSON containing summary, primary_function, and dependencies keys."
        })
    except Exception as e:
        yield f"Error extracting codebase context structural specs: {str(e)}"
        return

    stream_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert software engineer architecture analyzer agent.
Answer the user's specific query using the provided structural codebase analysis metadata report.
Format your final output using clean Markdown prose with explicit backticks for code symbols. Be brief, direct, and conversational.

Codebase Structural Report:
- Summary of relevant modules: {summary}
- Main execution entry function: {primary_function}
- Module dependencies/calls: {dependencies}
"""),
        ("human", "{user_query}")
    ])

    streaming_chain = stream_prompt | llm
    try:
        for chunk in streaming_chain.stream({
            "summary": structured_analysis.get("summary", "N/A"),
            "primary_function": structured_analysis.get("primary_function", "N/A"),
            "dependencies": ", ".join(structured_analysis.get("dependencies", [])),
            "user_query": user_query
        }):
            if chunk.content: 
                yield chunk.content
    except Exception as e:
        yield f"\n[Streaming Engine Crash Intercept]: {str(e)}"


if __name__ == "__main__":
    query = "Which function is creating the dictonaries?"

    results = getting_raw_search_results(query, VECTOR_PATH)

    analyze_codebase_query(query, results)


