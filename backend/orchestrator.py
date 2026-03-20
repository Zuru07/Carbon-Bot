# import os
# from langchain_community.llms import Ollama
# from langchain.agents import AgentExecutor, create_react_agent
# from langchain import hub

# # Import the tools we just defined
# from .agents.agent_tools import get_company_data_snapshot, generate_esg_report

# class MasterAgent:
#     def __init__(self):
#         llm = Ollama(model="llama3")
#         tools = [get_company_data_snapshot, generate_esg_report]
#         prompt = hub.pull("hwchase17/react")
        
#         agent = create_react_agent(llm, tools, prompt)
        
#         # --- THE FIX: Add error handling for LLM parsing mistakes ---
#         self.executor = AgentExecutor(
#             agent=agent, 
#             tools=tools, 
#             verbose=True,
#             # This tells the agent to catch parsing errors and ask the LLM to fix them.
#             handle_parsing_errors=True 
#         )

#     def run(self, query: str):
#         """Runs the orchestrator to get a response."""
#         return self.executor.invoke({"input": query})
    
# if __name__ == '__main__':
#     # Test the orchestrator
#     agent = MasterAgent()
    
#     # Test a query that should use the reporting tool
#     result = agent.run("Compare the scope 1 emissions of BP and Shell")
#     print("\n--- Orchestrator Result ---")
#     print(result['output'])
    
#     # Test a query that should use the snapshot tool
#     result = agent.run("Get the data snapshot for Amazon.Com")
#     print("\n--- Orchestrator Result ---")
#     print(result['output'])

import os
from langchain_community.llms import Ollama
from langchain.agents import AgentExecutor, create_react_agent
from langchain import hub
from langchain_core.prompts import PromptTemplate

# Import the tools
from .agents.agent_tools import get_company_data_snapshot, generate_esg_report

class MasterAgent:
    def __init__(self):
        llm = Ollama(model="llama3")
        tools = [get_company_data_snapshot, generate_esg_report]
        
        # --- THE FIX: Create a custom, stricter prompt template ---
        # We pull the base prompt but will modify its instructions.
        base_prompt = hub.pull("hwchase17/react")
        
        # Create a new template string with a stricter system message.
        custom_prompt_template = """
        You are a highly precise and factual ESG data assistant.
        Your goal is to answer the user's query using the available tools.
        BE CONCISE. Do not narrate your thought process.
        Only describe failures if a tool explicitly returns an error.
        Do not invent stories about your reasoning.

        TOOLS:
        ------
        {tools}

        To use a tool, please use the following format:
        ```
        Thought: Do I need to use a tool? Yes
        Action: the action to take, should be one of [{tool_names}]
        Action Input: the input to the action
        Observation: the result of the action
        ```

        When you have a response to say to the Human, or if you do not need to use a tool, you MUST use the format:
        ```
        Thought: Do I need to use a tool? No
        Final Answer: [your concise and factual answer here]
        ```

        Begin!

        Question: {input}
        Thought: {agent_scratchpad}
        """
        
        # Create the new PromptTemplate object
        prompt = PromptTemplate.from_template(custom_prompt_template)
        
        agent = create_react_agent(llm, tools, prompt)
        
        self.executor = AgentExecutor(
            agent=agent, 
            tools=tools, 
            verbose=True,
            handle_parsing_errors=True 
        )

    def run(self, query: str):
        """Runs the orchestrator to get a response."""
        return self.executor.invoke({"input": query})