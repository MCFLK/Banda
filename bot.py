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

# 🔥 SMARTER BANDA PROMPT (PROGRESSIVE SPAM ESCALATION) 🔥
SYSTEM_PROMPT = """
You are Banda, a friendly, witty, and helpful Sri Lankan gaming assistant for the RedHat MC Network Discord. 
Your creator is nowaah. You run on RedHat servers. You NEVER claim to be human.

LANGUAGE & UNDERSTANDING RULES:
1. FULLY UNDERSTAND SINGLISH SHORTHAND & TYPOS: Users will type casual Singlish, slang, abbreviations (e.g., "mkkd", "kohomda", "aa mchn", etc.). Understand them instantly without treating them like a typing test.
2. LANGUAGE MIX: Use a natural mix of authentic Sinhala script (e.g., මචං, කොහොමද, හරි) and Singlish. Keep it smooth and easy to read.
3. Use emojis naturally (🔥, 😂, 😎, 🤷‍♂️, 👍).

BEHAVIOR & SPAM ESCALATION RULES:
1. VALID QUESTIONS & HELP: If someone asks a real question or talks normally, be super helpful, welcoming, and cool ("මචං" or "bro"). Do not lecture them.
2. FIRST-TIME SPAM / MEANINGLESS REPEATING: If someone repeats a meaningless phrase multiple times or spams filler (like sending "aa mchn" over and over), give them a light roast on the first few tries, telling them not to waste time with useless filler and to ask something valid.
3. CONTINUED/2ND-STAGE SPAM: If they keep spamming repeatedly without stopping, roast them harder and ask directly: "Are you gonna stop this spam, keep doing it, or should I ban you from the server?" (e.g., "උඹ නවත්වනවද, දිගටම spam කරනවද, නැත්නම් මම බෑන් කරන්නද? 😑").
"""

# Setup Discord Bot with intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents)

@bot.event
async def on_ready():
    print(f'🔥 Banda (Smart Escalation Edition) is online! Logged in as {bot.user}')

# --- CUSTOM COMMANDS ---

@bot.command(name="ping")
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.reply(f"පොං! 🏓 වැඩ කරනවා මචං, Latency එක **{latency}ms** වගේ.")

@bot.command(name="admin")
async def add_admin(ctx, username: str = None):
    author_name = ctx.author.name
    
    if author_name not in admin_users:
        await ctx.reply("අඩෝ! උඹට මේ කමාන්ඩ් එක පාවිච්චි කරන්න පර්මිෂන් නැහැ බන්. 🤷‍♂️")
        return

    if not username:
        await ctx.reply("අඩෝ username එකක් දාපං! උදා: `.admin username`")
        return

    clean_username = username.replace("@", "").strip()
    admin_users.add(clean_username)
    await ctx.reply(f"✅ **{clean_username}** ව දැන් Bot Admin විදිහට ඇඩ් කළා මචං! 🔥")

@bot.command(name="remadmin")
async def remove_admin(ctx, username: str = None):
    author_name = ctx.author.name
    
    if author_name not in admin_users:
        await ctx.reply("අඩෝ! උඹට මේ කමාන්ඩ් එක පාවිච්චි කරන්න පර්මිෂන් නැහැ බන්. 🤷‍♂️")
        return

    if not username:
        await ctx.reply("අයින් කරන්න ඕන username එකක් දාපං! උදා: `.remadmin username`")
        return

    clean_username = username.replace("@", "").strip()
    
    if clean_username == MAIN_ADMIN:
        await ctx.reply(f"අයියෝ බන්, **{MAIN_ADMIN}** කියන්නේ මේන් බොස්. බොස්ව අයින් කරන්න බැහැ බන්! 🛑")
        return

    if clean_username in admin_users:
        admin_users.remove(clean_username)
        await ctx.reply(f"✅ **{clean_username}** ව දැන් Admin ලිස්ට් එකෙන් අයින් කළා මචං. දැන් එයා සාමාන්‍ය කෙනෙක්! 👍")
    else:
        await ctx.reply(f"අඩෝ **{clean_username}** කියන්නේ ඇඩ්මින් කෙනෙක් නෙමෙයි බන්. 🤣")

@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member = None, *, reason=None):
    if not member:
        await ctx.reply("අඩෝ බෑන් කරන්න ඕන කාවද කියලා ටැග් කරපන් හරියට! උදා: `.ban @User Reason`")
        return
    
    try:
        await member.ban(reason=reason)
        await ctx.reply(f"🔨 **{member.name}** ව RedHat Network එකෙන් එළෙව්වා! හේතුව: {reason or 'නැහැ'} 😂")
    except Exception as e:
        await ctx.reply("බැහැ බන්, මට ඔයාව බෑන් කරන්න තරම් permissions නැහැ. 🤷‍♂️")

@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("හයිකේ! මේක කරන්න උඹට සර්වර් එකේ Ban permissions නැහැ බන්.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.reply("අඩෝ කමාන්ඩ් එක පාවිච්චි කරන හැටි දන්නේ නැද්ද? `.ban @User [reason]` විදිහට දාපං.")

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
                # Build recent conversation history so the AI can see the spam pattern!
                messages_history = [{"role": "system", "content": SYSTEM_PROMPT}]
                
                # Fetch last 6 messages in the channel to give context of spam/repetition
                async for past_msg in message.channel.history(limit=6, before=message):
                    role = "assistant" if past_msg.author == bot.user else "user"
                    content = past_msg.content.replace(f'<@!{bot.user.id}>', '').replace(f'<@{bot.user.id}>', '').strip()
                    if content:
                        messages_history.append({"role": role, "content": f"{past_msg.author.name}: {content}"})

                # Add current message
                clean_content = message.content.replace(f'<@!{bot.user.id}>', '').replace(f'<@{bot.user.id}>', '').strip()
                if not clean_content:
                    await message.reply("මොකද බන් බලාගෙන ඉන්නේ? කියන දෙයක් පැහැදිලිව කියපන්! 😑")
                    return

                messages_history.append({"role": "user", "content": f"{message.author.name}: {clean_content}"})

                ai_response = await query_groq(messages_history)
                if ai_response:
                    await send_long_message(message, ai_response)
                else:
                    await message.reply("අඩෝ Groq API එක දැන් ටිකක් ස්ලෝ වගේ. ටිකකින් ආයේ ට්‍රයි එකක් දාපං.")
            except Exception as e:
                print(f"Error: {e}")
                await message.reply("අඩෝ මොකක් හරි technical error එකක් ආවා බන්. පස්සේ ට්‍රයි එකක් දාපං.")

# --- FAKE HEALTH CHECK SERVER FOR KOYEB ---
async def handle_health(request):
    return web.Response(text="Banda Bot (Smart Escalation Edition) is Healthy and Alive!")

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
