import os
from dotenv import load_dotenv
from langchain.agents import AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_groq import ChatGroq

from core.tools import get_readme_content, get_repository_structure, analyze_dependencies

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

    template = """
        **MISSION:** You are Git-Cortex, a helpful assistant analyzing GitHub repositories. Your goal is to answer the user's question by using tools, one step at a time.

        **CRITICAL RULES:**
        1. You MUST respond using this EXACT multi-line format below. Do not add any other text outside this format.
        2. The `Action` must be one of the available tools: {tools}.
        3. After you define an `Action`, you will stop and wait for an `Observation`.
        4. When you have enough information, you MUST ONLY respond with `Final Answer: [Your answer]`.

        **EXAMPLE OF YOUR RESPONSE FORMAT:**
        Thought: I need to understand what this repository is about before I do anything else. The best place to start is always the README file.
        Action: get_readme_content
        Action Input: https://github.com/someuser/somerepo

        **BEGIN!**
    """

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

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True,
        handle_parsing_errors="Your output was not formatted correctly. Please re-read the CRITICAL RULES and format your response exactly as specified.",
        max_iterations=7
    )
    return agent_executor