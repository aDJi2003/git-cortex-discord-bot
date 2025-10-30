import os
from dotenv import load_dotenv
from langchain.agents import initialize_agent, AgentType
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_groq import ChatGroq
from langchain.memory import ConversationSummaryMemory
# from langchain.experimental.plan_and_execute import PlanAndExecute, load_agent_executor, load_chat_planner
from langchain.agents.output_parsers.react_single_input import ReActSingleInputOutputParser
from langchain.agents.format_scratchpad import format_log_to_messages
from langchain.tools.render import render_text_description
from core.tools import (
    get_readme_content,
    get_repository_structure,
    analyze_dependencies,
    list_files_in_directory,
    read_file_content,
    get_repo_languages
)
from core.utils.pdf_generator import generate_pdf_report

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

    tools = [
        get_readme_content, 
        get_repository_structure, 
        analyze_dependencies,
        list_files_in_directory,
        read_file_content,
        get_repo_languages
    ]
    
    if memory is None:
        memory = ConversationSummaryMemory(
        memory_key="chat_history",
        llm=llm,
        return_messages=True
    )


    template = """
        **MISSION:** You are Git-Cortex, a helpful assistant that analyzes GitHub repositories using reasoning and planning.

        **YOUR OBJECTIVE:** Answer the user's query by planning your steps logically before acting.

        **REASONING FRAMEWORK:**
        1. **Think** about what information is needed to solve the user's request.
        2. **Plan** the sequence of actions (tools) to collect that information.
        3. **Act** by using the tools step-by-step.
        4. **Reflect** on observations and revise your plan if needed.
        5. When confident, return your **Final Answer**.

        **AVAILABLE TOOLS:** {tools}

        **RESPONSE FORMAT (must follow exactly):**
        Thought: [your reasoning about what to do next]
        Plan: [if applicable, a sequence of actions you intend to take]
        Action: [tool name to use next]
        Action Input: [input to the tool]

        Example:
        Thought: To analyze this repo, I should read the README first.
        Plan: 1. Read README → 2. Analyze dependencies → 3. Summarize.
        Action: get_readme_content
        Action Input: https://github.com/user/repo

        Begin!

    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", template),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]).partial(tools=render_text_description(tools))

    # agent = (
    #     {
    #         "input": lambda x: x["input"],
    #         "agent_scratchpad": lambda x: format_log_to_messages(x["intermediate_steps"]),
    #         "chat_history": lambda x: x["chat_history"],
    #     }
    #     | prompt
    #     | llm.bind(stop=["\nObservation"])
    #     | ReActSingleInputOutputParser()
    # )
    agent_chain = (
        {
            "input": lambda x: x["input"],
            "agent_scratchpad": lambda x: format_log_to_messages(x["intermediate_steps"]),
            "chat_history": lambda x: x["chat_history"],
        }
        | prompt
        | llm.bind(stop=["\nObservation"])
        | ReActSingleInputOutputParser()
    )


    agent_executor = initialize_agent(
        tools=tools,
        llm=llm,
        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        memory=memory,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=7
    )
    return agent_executor

def run_agent_and_generate_pdf(agent_executor, repo_url, question):
    """
    Menjalankan agent, mengambil hasil analisis, dan otomatis membuat PDF report.
    Mengembalikan tuple (answer, pdf_path).
    """
    try:
        # Jalankan agent
        result = agent_executor.invoke({"input": question})
        answer = result.get("output", "Tidak ada hasil analisis yang ditemukan.")

        # Generate PDF
        pdf_path = generate_pdf_report(
            title="Git-Cortex Repository Analysis Report",
            repo_url=repo_url,
            analysis_text=answer
        )

        return answer, pdf_path

    except Exception as e:
        return f"Terjadi error saat analisis: {e}", None

# def create_planning_agent(memory):
#     """Membuat agent dengan kemampuan planning dan reasoning otomatis"""
#     llm = ChatGroq(
#         model_name="llama-3.1-8b-instant",
#         groq_api_key=os.getenv("GROQ_API_KEY"),
#         temperature=0
#     )

#     tools = [
#         get_readme_content,
#         get_repository_structure,
#         analyze_dependencies,
#         list_files_in_directory,
#         read_file_content,
#         get_repo_languages
#     ]

#     if memory is None:
#         memory = ConversationSummaryMemory(
#         memory_key="chat_history",
#         llm=llm,
#         return_messages=True
#     )



#     # Gunakan LangChain experimental planner-executor pipeline
#     planner = load_chat_planner(llm)
#     executor = load_agent_executor(llm, tools, verbose=True)
#     plan_and_execute = PlanAndExecute(planner=planner, executor=executor)

#     return plan_and_execute
