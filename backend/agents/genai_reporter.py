import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from langchain_community.llms import Ollama
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from backend.utils.report_schema import ESGReportSchema, create_report_from_snapshot

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class GenAI_Reporter:
    """
    An agent that uses a vector index (Pinecone) and a local LLM (Llama via Ollama)
    to generate reports based on natural language queries.
    
    Supports both natural language responses and structured JSON output for
    regulatory submissions.
    """
    
    def __init__(self, llm_model: str = "llama3"):
        logging.info(f"Initializing GenAI Reporter with {llm_model}...")
        
        pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.pinecone_index_name = os.getenv("PINECONE_INDEX_NAME", "company-emissions-index")
        
        if not pinecone_api_key:
            raise ValueError("PINECONE_API_KEY is not set.")
        
        self.llm = Ollama(model=llm_model)
        self.embedding_model = SentenceTransformer("all-mpnet-base-v2")
        pc = Pinecone(api_key=pinecone_api_key)
        self.index = pc.Index(self.pinecone_index_name)
        logging.info("GenAI Reporter initialized successfully.")

    def generate_report(
        self,
        query: str,
        top_k: int = 5,
        output_format: Literal["text", "json", "both"] = "text"
    ) -> str | dict:
        """
        Generates a report based on the query.
        
        Args:
            query: Natural language query
            top_k: Number of relevant companies to retrieve
            output_format: Output format - 'text', 'json', or 'both'
        
        Returns:
            Report in requested format
        """
        logging.info(f"Generating report for query: '{query}'")
        
        query_embedding = self.embedding_model.encode(query).tolist()
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        if not results['matches']:
            return "I could not find any relevant company data for your query."
        
        context = "CONTEXT:\n"
        for match in results['matches']:
            meta = match['metadata']
            context += (
                f"- Company: {meta.get('company_name', 'N/A')}\n"
                f"  Sector: {meta.get('sector', 'N/A')}\n"
                f"  Year: {int(meta.get('reporting_year', 'N/A'))}\n"
                f"  Scope 1: {meta.get('scope1_total', 0):.2f}, "
                f"Scope 2: {meta.get('scope2_total', 0):.2f}, "
                f"Scope 3: {meta.get('scope3_total', 0):.2f} metric tons CO2e\n\n"
            )
        
        prompt = (
            f"You are a precise ESG analyst. Answer the user's query based *only* "
            f"on the context provided. Be concise and factual. "
            f"If the context doesn't contain the answer, say so.\n"
            f"----------------\n{context}----------------\n"
            f"QUERY: {query}\n\nANSWER:"
        )
        
        try:
            response = self.llm.invoke(prompt)
            
            if output_format == "text":
                return response
            elif output_format == "json":
                return self._generate_structured_response(query, results, response)
            else:
                return {
                    "text": response,
                    "structured": self._generate_structured_response(query, results, response)
                }
        except Exception as e:
            logging.error(f"LLM generation failed: {e}")
            return "Error: The local language model failed to produce a response. Is Ollama running?"

    def _generate_structured_response(
        self,
        query: str,
        results: dict,
        llm_response: str
    ) -> dict:
        """Generates structured JSON response from query and results."""
        primary_match = results['matches'][0] if results['matches'] else None
        
        if not primary_match:
            return {"error": "No matching companies found"}
        
        meta = primary_match['metadata']
        
        structured_response = {
            "query": query,
            "llm_analysis": llm_response,
            "matched_companies": [],
            "summary": {
                "total_companies_matched": len(results['matches']),
                "total_emissions_tCO2e": sum(
                    m['metadata'].get('scope1_total', 0) +
                    m['metadata'].get('scope2_total', 0) +
                    m['metadata'].get('scope3_total', 0)
                    for m in results['matches']
                )
            }
        }
        
        for match in results['matches']:
            meta = match['metadata']
            company_data = {
                "company_name": meta.get('company_name'),
                "sector": meta.get('sector'),
                "reporting_year": meta.get('reporting_year'),
                "scope1_tCO2e": meta.get('scope1_total', 0),
                "scope2_tCO2e": meta.get('scope2_total', 0),
                "scope3_tCO2e": meta.get('scope3_total', 0),
                "total_tCO2e": (
                    meta.get('scope1_total', 0) +
                    meta.get('scope2_total', 0) +
                    meta.get('scope3_total', 0)
                ),
                "similarity_score": match.get('score', 0)
            }
            structured_response["matched_companies"].append(company_data)
        
        return structured_response

    def generate_structured_esg_report(
        self,
        company_name: str,
        snapshot: dict,
        alerts: list[dict] | None = None,
        report_type: Literal["annual", "quarterly", "spot"] = "annual"
    ) -> ESGReportSchema:
        """
        Generates a fully structured ESG report using the report schema.
        
        Args:
            company_name: Name of the company
            snapshot: Company data snapshot
            alerts: Optional deviation alerts
            report_type: Type of report
            
        Returns:
            ESGReportSchema instance
        """
        logging.info(f"Generating structured ESG report for {company_name}")
        
        report = create_report_from_snapshot(
            company_name=company_name,
            snapshot=snapshot,
            report_type=report_type,
            alerts=alerts
        )
        
        return report

    def generate_comparative_analysis(
        self,
        query: str,
        company_names: list[str],
        snapshots: list[dict]
    ) -> dict:
        """
        Generates a comparative analysis across multiple companies.
        
        Args:
            query: Analysis query
            company_names: List of company names
            snapshots: List of company data snapshots
            
        Returns:
            Comparative analysis dictionary
        """
        logging.info(f"Generating comparative analysis for {len(company_names)} companies")
        
        comparisons = []
        for name, snapshot in zip(company_names, snapshots):
            total = (
                (snapshot.get('scope1_total') or 0) +
                (snapshot.get('scope2_total') or 0) +
                (snapshot.get('scope3_total') or 0)
            )
            
            electricity_kwh = snapshot.get('electricity_kwh', 0)
            employees = snapshot.get('employee_count', 0)
            
            comparisons.append({
                "company_name": name,
                "total_emissions_tCO2e": total,
                "electricity_kwh": electricity_kwh,
                "employees": employees,
                "emissions_per_employee": total / employees if employees > 0 else 0,
                "emissions_intensity": total / electricity_kwh if electricity_kwh > 0 else 0,
                "sector": snapshot.get('sector'),
                "energy_mix": {
                    "renewable_pct": snapshot.get('energy_mix_renewable_pct', 0),
                    "fossil_pct": snapshot.get('energy_mix_fossil_pct', 0),
                    "nuclear_pct": snapshot.get('energy_mix_nuclear_pct', 0)
                }
            })
        
        total_emissions = sum(c['total_emissions_tCO2e'] for c in comparisons)
        
        return {
            "query": query,
            "companies_analyzed": len(company_names),
            "comparisons": comparisons,
            "aggregate": {
                "total_combined_emissions_tCO2e": total_emissions,
                "average_emissions_tCO2e": total_emissions / len(comparisons) if comparisons else 0
            },
            "generated_at": datetime.now().isoformat(),
            "generated_by": "Carbon-bot"
        }


if __name__ == '__main__':
    import sys
    project_root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(project_root))
    load_dotenv(dotenv_path=project_root / ".env")
    
    print("=== Testing GenAI Reporter ===\n")
    print("Note: This requires Ollama to be running with llama3 model")
    print("Skipping LLM call test - run with Ollama for full test\n")
    
    reporter = GenAI_Reporter()
    
    structured = reporter._generate_structured_response(
        "Compare emissions of major tech companies",
        {
            'matches': [
                {
                    'metadata': {
                        'company_name': 'Company A',
                        'sector': 'Technology',
                        'reporting_year': 2024,
                        'scope1_total': 100000,
                        'scope2_total': 50000,
                        'scope3_total': 500000
                    },
                    'score': 0.95
                },
                {
                    'metadata': {
                        'company_name': 'Company B',
                        'sector': 'Technology',
                        'reporting_year': 2024,
                        'scope1_total': 200000,
                        'scope2_total': 80000,
                        'scope3_total': 1000000
                    },
                    'score': 0.88
                }
            ]
        },
        "Company A has lower total emissions at 650,000 tCO2e compared to Company B at 1,280,000 tCO2e."
    )
    
    print("Structured Response:")
    import json
    print(json.dumps(structured, indent=2))
