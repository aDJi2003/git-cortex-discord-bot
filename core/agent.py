# core/agent.py
import os
from dotenv import load_dotenv
from langchain.agents import AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_groq import ChatGroq

# Impor tools
from core.tools import get_readme_content, get_repository_structure, analyze_dependencies

# Impor komponen yang dibutuhkan untuk merakit agent
from langchain.agents.output_parsers.react_single_input import ReActSingleInputOutputParser
from langchain.agents.format_scratchpad import format_log_to_messages
from langchain.tools.render import render_text_description

load_dotenv()

def create_agent_executor(memory):
    """
    Fungsi ini sekarang menerima objek 'memory' untuk membuat agent yang kontekstual.
    """
    llm = ChatGroq(
        model_name="llama-3.1-8b-instant",
        groq_api_key=os.getenv("GROQ_API_KEY"),
        temperature=0
    )

    tools = [get_readme_content, get_repository_structure, analyze_dependencies]

    # Prompt sekarang memiliki placeholder baru untuk riwayat obrolan
    template = """
**MISSION:** You are Git-Cortex, a helpful assistant that analyzes GitHub repositories. Your job is to answer the user's question using the tools provided. You have access to the conversation history.

**CRITICAL RULES - FOLLOW THESE EXACTLY:**
1. Your response MUST follow the format: Thought, Action, Action Input, Observation.
2. The `Action:` line must contain ONLY the tool's name.
3. The `Action Input:` line must contain ONLY the input for the tool (e.g., a single URL).
4. After you get an `Observation`, you MUST have a new `Thought:` to decide what to do next.
5. If the `Observation` gives you enough information to answer the user's `Question`, you MUST immediately respond with `Final Answer:`.

**TOOLS:**
{tools}

**BEGIN!**
"""
    
    # Menggunakan ChatPromptTemplate untuk mengakomodasi riwayat pesan
    prompt = ChatPromptTemplate.from_messages([
        ("system", template),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]).partial(tools=render_text_description(tools))
    
    agent = (
        {
            "input": lambda x: x["input"],
            "agent_scratchpad": lambda x: format_log_to_messages(x["intermediate_steps"]),
            "chat_history": lambda x: x["chat_history"],
        }
        | prompt
        | llm.bind(stop=["\nObservation"])
        | ReActSingleInputOutputParser()
    )

    # Agent Executor sekarang diinisialisasi dengan memori
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory, # <-- Memori diintegrasikan di sini
        verbose=True,
        handle_parsing_errors="Your output was not formatted correctly. Please re-read the CRITICAL RULES and format your response exactly as specified.",
        max_iterations=7
    )
    return agent_executor