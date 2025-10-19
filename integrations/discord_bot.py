# integrations/discord_bot.py
import os
import discord
from dotenv import load_dotenv
from core.agent import create_agent_executor
from langchain.memory import ConversationBufferWindowMemory

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Dictionary untuk menyimpan percakapan yang sedang berlangsung (satu per channel)
conversations = {}

# Setup intents untuk bot
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

    # Hanya merespons jika di-mention atau menggunakan perintah
    if client.user.mentioned_in(message) or message.content.startswith('!analyze'):
        
        # Ambil konten pertanyaan
        if message.content.startswith('!analyze '):
            question = message.content[len('!analyze '):].strip()
        else:
            # Hapus mention bot dari pesan
            question = message.content.replace(f'<@!{client.user.id}>', '').strip()

        if not question:
            await message.channel.send("Mohon berikan pertanyaan setelah memanggil saya.")
            return

        channel_id = message.channel.id

        # Periksa apakah sudah ada percakapan di channel ini
        if channel_id not in conversations:
            print(f"Membuat percakapan baru untuk channel ID: {channel_id}")
            # Buat memori baru yang mengingat 3 interaksi terakhir
            memory = ConversationBufferWindowMemory(
                k=3, 
                memory_key="chat_history", 
                return_messages=True
            )
            # Buat agent baru dengan memori tersebut
            conversations[channel_id] = create_agent_executor(memory)

        # Ambil agent yang sesuai untuk channel ini
        agent_executor = conversations[channel_id]

        async with message.channel.typing():
            try:
                # Jalankan agent dengan pertanyaan pengguna
                response = await client.loop.run_in_executor(
                    None, agent_executor.invoke, {"input": question}
                )
                answer = response.get('output', "Maaf, saya tidak bisa menemukan jawaban.")
                await message.channel.send(answer)
            except Exception as e:
                await message.channel.send(f"😭 **Terjadi Error!**\nMaaf, saya gagal memproses. Error: {e}")

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("Error: DISCORD_BOT_TOKEN tidak ditemukan.")
    else:
        client.run(DISCORD_TOKEN)