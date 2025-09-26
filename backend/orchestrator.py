import os
from langchain_community.llms import Ollama
from langchain.agents import AgentExecutor, create_react_agent
from langchain import hub

# Import the tools we just defined
from .agents.agent_tools import get_company_data_snapshot, generate_esg_report

class MasterAgent:
    def __init__(self):
        llm = Ollama(model="llama3")
        tools = [get_company_data_snapshot, generate_esg_report]
        prompt = hub.pull("hwchase17/react")
        
        agent = create_react_agent(llm, tools, prompt)
        
        # --- THE FIX: Add error handling for LLM parsing mistakes ---
        self.executor = AgentExecutor(
            agent=agent, 
            tools=tools, 
            verbose=True,
            # This tells the agent to catch parsing errors and ask the LLM to fix them.
            handle_parsing_errors=True 
        )

    def run(self, query: str):
        """Runs the orchestrator to get a response."""
        return self.executor.invoke({"input": query})
    
if __name__ == '__main__':
    # Test the orchestrator
    agent = MasterAgent()
    
    # Test a query that should use the reporting tool
    result = agent.run("Compare the scope 1 emissions of BP and Shell")
    print("\n--- Orchestrator Result ---")
    print(result['output'])
    
    # Test a query that should use the snapshot tool
    result = agent.run("Get the data snapshot for Amazon.Com")
    print("\n--- Orchestrator Result ---")
    print(result['output'])