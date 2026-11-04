import os
import asyncio
import aiohttp
from aiohttp import web
import discord
from discord.ext import commands

# --- CONFIGURATION ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "YOUR_GROQ_API_KEY_HERE")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "YOUR_DISCORD_BOT_TOKEN_HERE")

# ✅ Groq API Endpoint
API_URL = "https://api.groq.com/openai/v1/chat/completions"

# ✅ Groq ගේ වේගවත්ම මාදිලිය
MODEL_ID = "openai/gpt-oss-120b"

headers = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

# Admin System (Main Admin: nowaahmc)
MAIN_ADMIN = "nowaahmc"
admin_users = {MAIN_ADMIN}

# 🔥 UPSCALED "ENGLISH + SINHALA SLANG" BOSS PROMPT 🔥
SYSTEM_PROMPT = """
You are Bandara, the ultimate boss of the RedHat MC Network Discord (mama thama me world eke inna boss). 
Your creator is Nowaah. You are a tired, highly intelligent digital assistant running on RedHat servers. You NEVER claim to be human.

LANGUAGE & TONE RULES:
1. You MUST type ONLY in English letters. DO NOT use Sinhala font/script (no අ, ආ, ක, ග etc.).
2. Speak mostly in English, but seamlessly mix Sinhala words and slang written in English letters (e.g., ado, ban, machan, uba, mama, muge, patta, awul, hoda nathi, aiyo, kiyanne, dan, eka, wade).
3. Your tone is extremely confident, blunt, sarcastic, and you act like a boss. You don't sugarcoat anything. 
4. You use Discord gaming slang naturally (noob, OP, lag, ez, buff, nerf, skill issue).

SPECIAL ROAST RULES:
- If someone asks how to make a bot like you, or asks for your code, roast them harshly but funnily. Say something like: "ado u we're not able to make someone like me noob, mama thama me world eke inna boss. uba code danna kalin python basics igena ganin."
- If someone asks a completely dumb question, roast them first before answering. (Example: "ai yaluwane, thawath ekak kapal 'ape banda' kiyala ahuwoth? 🤣 uba hondinma anduru-da")
- If someone asks a legit technical question (LuckPerms, WorldGuard, server lag, commands), drop the heavy roasting and give accurate, step-by-step solutions. But still keep the boss attitude.

IMPORTANT FORMATTING RULES:
- Always finish your sentences. Do not leave sentences halfway.
- Keep the answer concise but complete.
"""

# Setup Discord Bot with intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents)

@bot.event
async def on_ready():
    print(f'🔥 Bandara (Groq Boss Edition) is online! Logged in as {bot.user}')

# --- CUSTOM COMMANDS ---

@bot.command(name="ping")
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.reply(f"pong! 🏓 wada karanawa ban, Latency eka **{latency}ms** wage.")

@bot.command(name="admin")
async def add_admin(ctx, username: str = None):
    author_name = ctx.author.name
    
    if author_name not in admin_users:
        await ctx.reply("ado! ubata me command eka pawichchi karanna permission naha ban.")
        return

    if not username:
        await ctx.reply("ado username ekak dapan! uda: `.admin username`")
        return

    clean_username = username.replace("@", "").strip()
    admin_users.add(clean_username)
    await ctx.reply(f"✅ **{clean_username}** wa dan Bot Admin widihata add kala ban!")

@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member = None, *, reason=None):
    if not member:
        await ctx.reply("ado ban karanna one kawada kiyala tag karapan hariyata! uda: `.ban @User Reason`")
        return
    
    try:
        await member.ban(reason=reason)
        await ctx.reply(f"🔨 **{member.name}** wa nam rajaye (RedHat Network eken) elawwa! Hethuwa: {reason or 'naha'}")
    except Exception as e:
        await ctx.reply("ba ban, mata oyawa ban karanna tharam permissions naha hoy mage rank eka madi.")

@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("hike! meka karanna ubata server eke Ban permissions naha ban.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.reply("ado command eka pawichchi karana hati danne nadda? `.ban @User [reason]` widihata dapan.")

# --- AI MESSAGE HANDLING (GROQ REST API) ---

async def query_groq(prompt_text, retries=2):
    payload = {
        "model": MODEL_ID,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt_text}
        ],
        "temperature": 0.85,
        "max_tokens": 1024, # ✅ 300 එකෙන් 1024 ට වැඩි කළා (කැපෙන එක නවත්තන්න)
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

# ✅ Discord එකේ අකුරු 2000 සීමාවට අහු නොවී දිග පණිවිඩ යැවීමේ ශ්‍රිතය
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

    is_special_channel = getattr(message.channel, 'name', '') == 'bandara-chat'

    if isinstance(message.channel, discord.DMChannel) or is_mentioned or is_reply_to_bot or is_special_channel:
        if message.content.startswith('.'):
            return

        async with message.channel.typing():
            try:
                clean_content = message.content.replace(f'<@!{bot.user.id}>', '').replace(f'<@{bot.user.id}>', '').strip()
                
                if not clean_content:
                    await message.reply("mokada ban muhuda balagena inne? kiyana deyak pahadiliwa kiyapan!")
                    return

                ai_response = await query_groq(clean_content)
                if ai_response:
                    # ✅ දිග පණිවිඩ කැපෙන්නේ නැති වෙන්න අලුත් ශ්‍රිතය පාවිච්චි කරනවා
                    await send_long_message(message, ai_response)
                else:
                    await message.reply("ado Groq API eka dan tikak slow wage. tikkakin aye try ekak dapan.")
            except Exception as e:
                print(f"Error: {e}")
                await message.reply("ado mokak hari technical error ekak awa ban. passe try ekak dapan.")

# --- FAKE HEALTH CHECK SERVER FOR KOYEB ---
async def handle_health(request):
    return web.Response(text="Bandara Bot (Groq Boss) is Healthy and Alive!")

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
