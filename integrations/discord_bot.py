import os
import discord
from dotenv import load_dotenv
from core.agent import create_agent_executor
# from langchain.memory import ConversationBufferWindowMemory
from langchain.memory import ConversationSummaryMemory
from core.agent import run_agent_and_generate_pdf
# from core.agent import create_planning_agent
import re


load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

conversations = {}

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Bot {client.user} telah online dan siap menganalisis! 🚀')
    print('---------------------------------------------------------')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    # if message.content.startswith("!plan "):
    #     question = message.content[len("!plan "):].strip()
    #     agent = create_planning_agent()

    #     async with message.channel.typing():
    #         try:
    #             result = await client.loop.run_in_executor(
    #                 None, agent.run, question
    #             )
    #             await message.channel.send(f"🧠 **Planned Analysis Result:**\n{result}")
    #         except Exception as e:
    #             await message.channel.send(f"❌ Error in planning agent: {e}")

    if client.user.mentioned_in(message) or message.content.startswith('!analyze'):
        
        if message.content.startswith('!analyze '):
            question = message.content[len('!analyze '):].strip()
        else:
            question = message.content.replace(f'<@!{client.user.id}>', '').strip()

        if not question:
            await message.channel.send("Mohon berikan pertanyaan setelah memanggil saya.")
            return
        
        match = re.match(r'(https?://github\.com/[^\s]+)\s*(.*)', question)
        if match:
            repo_url = match.group(1).strip()
            question = match.group(2).strip() or "Jelaskan tentang repositori ini."
        else:
            await message.channel.send("⚠️ Format salah. Harap tulis seperti:\n`!analyze https://github.com/user/repo Apa yang dilakukan proyek ini?`")
            return


        channel_id = message.channel.id

        if channel_id not in conversations:
            print(f"Membuat percakapan baru untuk channel ID: {channel_id}")
            # memory = ConversationBufferWindowMemory(
            #     k=3, 
            #     memory_key="chat_history", 
            #     return_messages=True
            # )
            agent_executor, llm = create_agent_executor(None)

            memory = ConversationSummaryMemory(
                llm=llm,
                memory_key="chat_history",
                return_messages=True
            )
            conversations[channel_id] = agent_executor

        agent_executor = conversations[channel_id]

        async with message.channel.typing():
            try:
                # response = await client.loop.run_in_executor(
                #     None, agent_executor.invoke, {"input": question}
                # )
                # answer = response.get('output', "Maaf, saya tidak bisa menemukan jawaban.")
                # await message.channel.send(answer)
                answer, pdf_path = await client.loop.run_in_executor(
                    None, run_agent_and_generate_pdf, agent_executor, repo_url, question
                )
                await message.channel.send(answer)

                if pdf_path:
                    await message.channel.send(
                        content="📄 Laporan analisis otomatis telah dibuat:",
                        file=discord.File(pdf_path)
                    )


            except Exception as e:
                await message.channel.send(f"**Terjadi Error!**\nMaaf, saya gagal memproses. Error: {e}")

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("Error: DISCORD_BOT_TOKEN tidak ditemukan.")
    else:
        client.run(DISCORD_TOKEN)