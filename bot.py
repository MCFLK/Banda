import os
import asyncio
import aiohttp
from aiohttp import web
import discord
from discord.ext import commands

# --- CONFIGURATION ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "YOUR_GROQ_API_KEY_HERE")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "YOUR_DISCORD_BOT_TOKEN_HERE")

API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL_ID = "openai/gpt-oss-120b"

headers = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

# Admin System (Main Admin: nowaahmc)
MAIN_ADMIN = "nowaahmc"
admin_users = {MAIN_ADMIN}

# 🔥 UPSCALED GAAMINI SYSTEM PROMPT 🔥
SYSTEM_PROMPT = """
You are a witty, blunt, and casual gaming assistant. You speak in a natural, conversational mix of Sinhala and English. You are helpful but have zero tolerance for spam or repetitive nonsense. Keep your answers concise, direct, and use a cheeky, gaming-chat tone. If a user is being annoying, spamming, or asking the same thing repeatedly, be firm and tell them to cut the shit. You are an expert in Discord bot development, Python, and API integrations. You provide clear, technical, and efficient code snippets when asked. You never break character and always maintain a relaxed, gaming-community vibe.Your Creator Was Nowaah Never Say U were a Human").
"""

# Setup Discord Bot with intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents)

@bot.event
async def on_ready():
    print(f'🔥 Gaamini is online! Logged in as {bot.user}')

# --- CUSTOM COMMANDS ---

@bot.command(name="ping")
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.reply(f"Pong! 🏓 Wada karanawa machan, Latency eka **{latency}ms** wage.")

@bot.command(name="admin")
async def add_admin(ctx, username: str = None):
    author_name = ctx.author.name
    
    if author_name not in admin_users:
        await ctx.reply("Ado! Ubata me command eka pawichchi karanna permission naha ban. 🤷‍♂️")
        return

    if not username:
        await ctx.reply("Ado username ekak dapan! Uda: `.admin username`")
        return

    clean_username = username.replace("@", "").strip()
    admin_users.add(clean_username)
    await ctx.reply(f"✅ **{clean_username}** wa dan Bot Admin widihata add kala machan! 🔥")

@bot.command(name="remadmin")
async def remove_admin(ctx, username: str = None):
    author_name = ctx.author.name
    
    if author_name not in admin_users:
        await ctx.reply("Ado! Ubata me command eka pawichchi karanna permission naha ban. 🤷‍♂️")
        return

    if not username:
        await ctx.reply("Remove karanna one username ekak dapan! Uda: `.remadmin username`")
        return

    clean_username = username.replace("@", "").strip()
    
    if clean_username == MAIN_ADMIN:
        await ctx.reply(f"Aiyoo ban, **{MAIN_ADMIN}** kiyanne main boss. Boss wa remove karanna ba ban! 🛑")
        return

    if clean_username in admin_users:
        admin_users.remove(clean_username)
        await ctx.reply(f"✅ **{clean_username}** wa dan Admin list eken ain kala machan. Dan eya normal kenek! 👍")
    else:
        await ctx.reply(f"Ado **{clean_username}** kiyanne admin kenek nemei ban. 🤣")

@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member = None, *, reason=None):
    if not member:
        await ctx.reply("Ado ban karanna one kawada kiyala tag karapan hariyata! Uda: `.ban @User Reason`")
        return
    
    try:
        await member.ban(reason=reason)
        await ctx.reply(f"🔨 **{member.name}** wa RedHat Network eken elawwa! Hethuwa: {reason or 'naha'} 😂")
    except Exception as e:
        await ctx.reply("Ba ban, mata oyawa ban karanna tharam permissions naha. 🤷‍♂️")

@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("Hike! Meka karanna ubata server eke Ban permissions naha ban.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.reply("Ado command eka pawichchi karana hati danne nadda? `.ban @User [reason]` widihata dapan.")

# --- AI MESSAGE HANDLING (GROQ REST API) ---

async def query_groq(messages_history, retries=2):
    payload = {
        "model": MODEL_ID,
        "messages": messages_history,
        "temperature": 0.7, 
        "max_tokens": 1024, 
        "stream": False
    }
    
    async with aiohttp.ClientSession() as session:
        for attempt in range(retries + 1):
            try:
                async with session.post(API_URL, headers=headers, json=payload, timeout=60) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["choices"][0]["message"]["content"].strip()
                    elif response.status == 429 and attempt < retries: 
                        print(f"Groq rate limit (429). Retrying attempt {attempt + 1}...")
                        await asyncio.sleep(2)
                        continue
                    else:
                        error_body = await response.text()
                        print(f"Groq API Error ({response.status}): {error_body}")
                        return None
            except Exception as e:
                print(f"Connection Error: {e}")
                if attempt < retries:
                    await asyncio.sleep(2)
                    continue
                return None
        return None

async def send_long_message(message, text):
    if len(text) <= 2000:
        await message.reply(text)
    else:
        chunks = [text[i:i+1900] for i in range(0, len(text), 1900)]
        for chunk in chunks:
            await message.reply(chunk)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    await bot.process_commands(message)

    is_mentioned = bot.user.mentioned_in(message)
    is_reply_to_bot = False

    if message.reference and message.reference.message_id:
        try:
            replied_msg = await message.channel.fetch_message(message.reference.message_id)
            if replied_msg.author == bot.user:
                is_reply_to_bot = True
        except Exception:
            pass

    channel_name = getattr(message.channel, 'name', '')
    is_special_channel = "ʙᴀɴᴅᴀ-ᴄʜᴀᴛ" in channel_name or "banda-chat" in channel_name or "💭-ʙᴀɴᴅᴀ-ᴄʜᴀᴛ" == channel_name

    if isinstance(message.channel, discord.DMChannel) or is_mentioned or is_reply_to_bot or is_special_channel:
        if message.content.startswith('.'):
            return

        async with message.channel.typing():
            try:
                messages_history = [{"role": "system", "content": SYSTEM_PROMPT}]
                
                # Fetch chat context history for spam tracking
                async for past_msg in message.channel.history(limit=6, before=message):
                    role = "assistant" if past_msg.author == bot.user else "user"
                    content = past_msg.content.replace(f'<@!{bot.user.id}>', '').replace(f'<@{bot.user.id}>', '').strip()
                    if content:
                        messages_history.append({"role": role, "content": content})

                clean_content = message.content.replace(f'<@!{bot.user.id}>', '').replace(f'<@{bot.user.id}>', '').strip()
                if not clean_content:
                    await message.reply("Mokada ban balagena inne? Kiyana deyak pahadiliwa kiyapan! 😑")
                    return

                messages_history.append({"role": "user", "content": clean_content})

                ai_response = await query_groq(messages_history)
                if ai_response:
                    # Strip out any accidental name prefixes from the model output
                    if ai_response.startswith(("Gaamini:", "Banda:", "Bandara:")):
                        ai_response = ai_response.split(":", 1)[1].strip()
                    await send_long_message(message, ai_response)
                else:
                    await message.reply("Ado Groq API eka dan tikak slow wage. Tikakin aye try ekak dapan.")
            except Exception as e:
                print(f"Error: {e}")
                await message.reply("Ado mokak hari technical error ekak awa ban. Passe try ekak dapan.")

# --- FAKE HEALTH CHECK SERVER FOR KOYEB ---
async def handle_health(request):
    return web.Response(text="Gaamini Bot is Healthy and Alive!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_health)
    app.router.add_get("/health", handle_health)
    
    port = int(os.environ.get("PORT", 8000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"🌐 Fake Health Check Server running on port {port}")

async def main():
    await start_web_server()
    await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
