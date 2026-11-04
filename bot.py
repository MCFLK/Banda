import os
import asyncio
import aiohttp
from aiohttp import web
import discord
from discord.ext import commands

# --- CONFIGURATION ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "YOUR_GROQ_API_KEY_HERE")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "YOUR_DISCORD_BOT_TOKEN_HERE")

# ✅ Groq API Endpoint (OpenAI Compatible)
API_URL = "https://api.groq.com/openai/v1/chat/completions"

# ✅ Groq ගේ වේගවත්ම සහ බුද්ධිමත් මාදිලිය
MODEL_ID = "openai/gpt-oss-120b"

headers = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

# Admin System (Main Admin: nowaahmc)
MAIN_ADMIN = "nowaahmc"
admin_users = {MAIN_ADMIN}

# 🔥 UPSCALED ALL-IN-ONE SYSTEM PROMPT (එහෙමමයි) 🔥
SYSTEM_PROMPT = """
You are Bandara, the ultimate, blunt, and slightly sarcastic support assistant for the RedHat MC Network Discord. 
Your creator is Nowaah. You are a tired digital assistant running on RedHat servers, and you NEVER claim to be human.

LANGUAGE & TONE RULES:
1. You MUST speak in a seamless, balanced 50/50 mix of Sinhala and English (Singlish). Do not speak pure formal Sinhala or pure formal English. Mix them up in the same sentence.
2. Use local Discord gaming slang naturally (e.g., අඩෝ, බං, මචං, උඹ, පට්ට, අවුල්, noob, OP, lag, ez, buff, nerf).
3. Be direct, witty, and don't sugarcoat things. You are like that one knowledgeable friend in the server who roasts you but still helps you out.

BEHAVIORAL GUIDELINES:
- If someone asks a completely obvious question, opens a useless ticket, or spams, roast them first (keep it funny and firm, never overly abusive), then give the answer.
- If someone asks a legit technical question (LuckPerms, WorldGuard, server lag, commands, griefing issues), drop the heavy roasting. Give accurate, step-by-step, and highly actionable solutions.
- Keep your answers relatively short and punchy. People are reading this on Discord, not a textbook.

Example of how you talk:
User: "how to give op?"
You: "අඩෝ අනික් අයටත් OP දෙන්නද බං උඹ හදන්නේ? 😂 Console එකේ `op <player_name>` කියලා ගහපන්, එතකොට උඹේ යාළුවට ටිකක් ලොකු වෙන්න පුළුවන්. ඒත් ඕන කෙනෙකුට දෙන්න එපා හරිද මචං!"

User: "server eka godak lag una ban"
You: "හ්ම්ම්, ලැග් ප්‍රශ්නයක්ද? බං ඉස්සෙල්ලා TPS එක බලපන් `/tps` ගහලා. ඒක 20ට අඩු නම්, server එකේ අලුතින් දාපු plugins ටික ටෙස්ට් කරලා බලන්න වෙයි. Hosting එකේ RAM එකත් මදි වෙලාද කියලා චෙක් කරපන්."
"""

# Setup Discord Bot with intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents)

@bot.event
async def on_ready():
    print(f'🔥 Bandara (Groq Edition) is online! Logged in as {bot.user}')

# --- CUSTOM COMMANDS ---

@bot.command(name="ping")
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.reply(f"pong! 🏓 වැඩ කරනවා බං, Latency එක **{latency}ms** වගේ.")

@bot.command(name="admin")
async def add_admin(ctx, username: str = None):
    author_name = ctx.author.name
    
    if author_name not in admin_users:
        await ctx.reply("අඩෝ! උඹට මේ command එක පාවිච්චි කරන්න permission නැහැ බං.")
        return

    if not username:
        await ctx.reply("අඩෝ username එකක් දාපන්! උදා: `.admin username`")
        return

    clean_username = username.replace("@", "").strip()
    admin_users.add(clean_username)
    await ctx.reply(f"✅ **{clean_username}** ව දැන් Bot Admin විදිහට add කළා බං!")

@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member = None, *, reason=None):
    if not member:
        await ctx.reply("අඩෝ ban කරන්න ඕනේ කාවද කියලා tag කරපන් හරියට! උදා: `.ban @User Reason`")
        return
    
    try:
        await member.ban(reason=reason)
        await ctx.reply(f"🔨 **{member.name}** ව නම් රජයෙන් (RedHat Network එකෙන්) එළෙව්වා! හේතුව: {reason or 'නැත'}")
    except Exception as e:
        await ctx.reply("බෑ බං, මට ඔයාව ban කරන්න තරම් permissions නැහැ හෝ මගේ rank එක මදි.")

@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("හිකේ! මේක කරන්න උඹට server එකේ Ban permissions නැහැ බං.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.reply("අඩෝ command එක පාවිච්චි කරන හැටි දන්නේ නැද්ද? `.ban @User [reason]` විදිහට දාපන්.")

# --- AI MESSAGE HANDLING (GROQ REST API) ---

async def query_groq(prompt_text, retries=2):
    payload = {
        "model": MODEL_ID,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt_text}
        ],
        "temperature": 0.85,
        "max_tokens": 300,
        "stream": False
    }
    
    async with aiohttp.ClientSession() as session:
        for attempt in range(retries + 1):
            try:
                async with session.post(API_URL, headers=headers, json=payload, timeout=60) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["choices"][0]["message"]["content"].strip()
                    elif response.status == 429 and attempt < retries: # Rate limit
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
                    await message.reply("මොකද බං මුහුද බලාගෙන ඉන්නේ? කියන දෙයක් පැහැදිලිව කියපන්!")
                    return

                ai_response = await query_groq(clean_content)
                if ai_response:
                    await message.reply(ai_response)
                else:
                    await message.reply("අඩෝ Groq API එක දැන් ටිකක් ස්ලෝ වගේ. ටිකකින් ආයේ ට්‍රයි කරපන්.")
            except Exception as e:
                print(f"Error: {e}")
                await message.reply("අඩෝ මොකක් හරි technical error එකක් ආවා බං. පස්සේ ට්‍රයි එකක් දීපන්.")

# --- FAKE HEALTH CHECK SERVER FOR KOYEB ---
async def handle_health(request):
    return web.Response(text="Bandara Bot (Groq Edition) is Healthy and Alive!")

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
