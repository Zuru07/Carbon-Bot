import os
import logging
from dotenv import load_dotenv
from pathlib import Path
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
# --- New Imports for Llama ---
from langchain_community.llms import Ollama

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class GenAI_Reporter:
    """
    An agent that uses a vector index (Pinecone) and a local LLM (Llama via Ollama)
    to generate reports based on natural language queries.
    """
    def __init__(self):
        logging.info("Initializing GenAI Reporter with Llama...")
        # Load configs
        pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.pinecone_index_name = os.getenv("PINECONE_INDEX_NAME", "company-emissions-index")

        if not pinecone_api_key:
            raise ValueError("PINECONE_API_KEY is not set.")

        # --- Configure models and clients ---
        # Initialize Ollama to use the local Llama 3 model
        self.llm = Ollama(model="llama3")
        self.embedding_model = SentenceTransformer("all-mpnet-base-v2")
        pc = Pinecone(api_key=pinecone_api_key)
        self.index = pc.Index(self.pinecone_index_name)
        logging.info("GenAI Reporter initialized successfully.")

    def generate_report(self, query: str, top_k: int = 5) -> str:
        logging.info(f"Generating report for query: '{query}'")
        
        # 1. Retrieve
        query_embedding = self.embedding_model.encode(query).tolist()
        results = self.index.query(vector=query_embedding, top_k=top_k, include_metadata=True)
        
        # 2. Augment
        context = "CONTEXT:\n"
        if not results['matches']:
            return "I could not find any relevant company data for your query."

        for match in results['matches']:
            meta = match['metadata']
            context += (
                f"- Company: {meta.get('company_name', 'N/A')}\n"
                f"  Sector: {meta.get('sector', 'N/A')}\n"
                f"  Year: {int(meta.get('reporting_year', 'N/A'))}\n"
                f"  Scope 1: {meta.get('scope1_total', 0):.2f}, Scope 2: {meta.get('scope2_total', 0):.2f}, Scope 3: {meta.get('scope3_total', 0):.2f} metric tons CO2e\n\n"
            )
        
        # 3. Generate
        prompt = (
            f"You are a precise ESG analyst. Answer the user's query based *only* on the context provided. "
            f"Be concise and factual. If the context doesn't contain the answer, say so.\n"
            f"----------------\n{context}----------------\nQUERY: {query}\n\nANSWER:"
        )
        
        try:
            # Use the .invoke() method for LangChain's Ollama integration
            response = self.llm.invoke(prompt)
            return response
        except Exception as e:
            logging.error(f"LLM generation failed: {e}")
            return "Error: The local language model failed to produce a response. Is Ollama running?"

if __name__ == '__main__':
    project_root = Path(__file__).resolve().parents[3]
    load_dotenv(dotenv_path=project_root / ".env")
    
    # Make sure Ollama is running before you execute this test
    reporter = GenAI_Reporter()
    test_query = "Which company is in the Nasdaq sector?"
    report = reporter.generate_report(test_query)
    print("\n--- TEST REPORT (from Llama 3) ---")
    print(report)
    print("-----------------------------------\n")