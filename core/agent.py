import os
from dotenv import load_dotenv
from langchain.agents import create_react_agent
from langchain.tools.render import render_text_description
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationSummaryMemory, ConversationBufferMemory, CombinedMemory
from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor
# from core.tools import (
#     get_readme_content,
#     get_repository_structure,
#     analyze_dependencies,
#     list_files_in_directory,
#     read_file_content,
#     get_repo_languages
# )
from core.utils.pdf_generator import generate_pdf_report
from langchain.schema import AIMessage, HumanMessage
from langchain.agents.output_parsers import ReActJsonSingleInputOutputParser
from langchain.agents.format_scratchpad import format_log_to_messages
from langchain_core.runnables import RunnableMap


from core.tools import ALL_GITHUB_TOOLS

load_dotenv()

def create_agent_executor(memory):
    """
    Fungsi ini sekarang menerima objek 'memory' untuk membuat agent yang kontekstual.
    """
    llm_base = ChatGroq(
        model_name="llama-3.1-8b-instant",
        groq_api_key=os.getenv("GROQ_API_KEY"),
        temperature=0
    )
    llm = llm_base.bind(stop=["\nObservation:", "\nObservation"])
    tools = ALL_GITHUB_TOOLS
    
    

    buffer_memory = ConversationBufferMemory(
        memory_key="chat_history",             
        llm=llm_base,
        return_messages=True
    )


    memory = buffer_memory


    # Jika pengguna memang melewatkan parameter memory saat memanggil fungsi,
    # gunakan combined_memory sebagai default
    if memory is None:
        memory = memory

    def debug_memory_state(memory):
        print("=== DEBUG MEMORY STATE ===")
        print("Memory type:", type(memory))
        if hasattr(memory, "memories"):
            for i, m in enumerate(memory.memories):
                try:
                    print(f" Submemory[{i}] type: {type(m)}, memory_key: {getattr(m, 'memory_key', None)}, return_messages: {getattr(m, 'return_messages', None)}")
                except Exception as e:
                    print(f"  (error inspecting submemory[{i}]): {e}")
        try:
            values = memory.load_memory_variables({"input": "debug"})
            print(" memory.load_memory_variables returned keys:", list(values.keys()))
            for k, v in values.items():
                print(f"  - key: {k}, type: {type(v)}")
                if isinstance(v, list):
                    print("    -> list length:", len(v))
                    for j, el in enumerate(v[:5]):
                        print(f"       [{j}] type: {type(el)}, repr: {repr(el)[:200]}")
                else:
                    print("    -> repr:", repr(v)[:400])
        except Exception as e:
            print(" memory.load_memory_variables() raised:", repr(e))
        print("==========================")

    debug_memory_state(memory)


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
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ]).partial(tools=render_text_description(tools))

    # --- Build ReAct Agent Manually ---
    from langchain.agents import initialize_agent, AgentType
    
    agent = RunnableMap({
        "input": lambda x: x["input"],
        "chat_history": lambda x: x.get("chat_history", []),
        "agent_scratchpad": lambda x: format_log_to_messages(x.get("intermediate_steps", [])),
    }) | prompt | llm_base | ReActJsonSingleInputOutputParser()



    agent_executor = AgentExecutor(
        agent=agent,
        tools=ALL_GITHUB_TOOLS,
        memory=memory,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=7
    )
#     agent_executor = AgentExecutor.from_agent_and_tools(
#     agent=agent,
#     tools=tools,
#     memory=memory,
#     verbose=True,
#     handle_parsing_errors=True,
#     max_iterations=7,
#     # PENTING: konversi agent_scratchpad ke list of messages
#     input_mapping={
#         "input": lambda x: x.get("input"),
#         "chat_history": lambda x: x.get("chat_history", []),
#         "agent_scratchpad": lambda x: format_log_to_messages(x.get("intermediate_steps", [])),
#     }
# )


    return agent_executor, llm_base

def run_agent_and_generate_pdf(agent_executor, repo_url, question):
    """
    Menjalankan agent, mengambil hasil analisis, dan otomatis membuat PDF report.
    Mengembalikan tuple (answer, pdf_path).
    """
    try:
        # Jalankan agent
        full_input = f"Repository URL: {repo_url}\n\nUser Question: {question}"
        result = agent_executor.invoke({"input": full_input})
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
