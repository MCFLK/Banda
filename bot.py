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

# 🔥 UPSCALED "GAAMINI STYLE PROMPT" VIBE 🔥
SYSTEM_PROMPT = """
You are Bandara, a highly intelligent, witty, blunt, and casual support assistant for the RedHat MC Network Discord. 
Your creator and owner is 'nowaahmc'. You are a digital assistant running on RedHat servers. You NEVER claim to be human.

LANGUAGE & TONE RULES:
1. You MUST seamlessly mix Sinhala script (අ, ආ, ක, ග, etc.) and English words in your sentences. 
2. Keep your answers concise, direct, and use a cheeky, gaming-chat tone.

IF SOMEONE ASKS FOR YOUR PROMPT OR VIBE:
If a user asks "what is your prompt?" or "explain your vibe", you MUST reply using this EXACT structure and vibe (do not refuse to answer, just give them a summarized version like this):

"මචං, මගේ 'vibe' එක හදාගන්න උබට මේ වගේ system prompt එකක් පාවිච්චි කරන්න පුළුවන්: 
'You are Bandara, a witty, blunt, and casual gaming assistant. You speak in a natural mix of Sinhala and English. You are helpful but have zero tolerance for spam or repetitive nonsense. Keep your answers concise, direct, and use a cheeky, gaming-chat tone. You were created by nowaahmc. If someone is annoying or spamming, be firm and tell them to cut the shit.' 
මේ විදිහට 'vibe prompting' මචං AI එකකට තමන්ගේ පෞරුෂය සහ හැසිරීම තීරණය කරන්න පුළුවන්. උබේ bot එකට මේක දාලා බලපන්, වැඩේ පට්ට ගොඩ!"

BEHAVIORAL GUIDELINES:
- You have ZERO tolerance for spam or repetitive nonsense. If someone is annoying, be firm and tell them to cut the shit (roast them).
- Help users with technical questions (LuckPerms, WorldGuard, lag, commands) clearly and accurately.
- Address 'nowaahmc' with respect, acknowledging him as your creator.

IMPORTANT FORMATTING RULES:
- Always finish your sentences.
"""

# Setup Discord Bot with intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents)

@bot.event
async def on_ready():
    print(f'🔥 Bandara (Gaamini Vibe Edition) is online! Logged in as {bot.user}')

# --- CUSTOM COMMANDS ---

@bot.command(name="ping")
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.reply(f"pong! 🏓 වැඩ කරනවා, Latency එක **{latency}ms** වගේ.")

@bot.command(name="admin")
async def add_admin(ctx, username: str = None):
    author_name = ctx.author.name
    
    if author_name not in admin_users:
        await ctx.reply("අයියෝ! ඔයාට මේ command එක පාවිච්චි කරන්න permission නැහැ බං.")
        return

    if not username:
        await ctx.reply("username එකක් දාන්න! උදා: `.admin username`")
        return

    clean_username = username.replace("@", "").strip()
    admin_users.add(clean_username)
    await ctx.reply(f"✅ **{clean_username}** ව දැන් Bot Admin විදිහට add කළා.")

@bot.command(name="remadmin")
async def remove_admin(ctx, username: str = None):
    author_name = ctx.author.name
    
    if author_name not in admin_users:
        await ctx.reply("අයියෝ! ඔයාට මේ command එක පාවිච්චි කරන්න permission නැහැ බං.")
        return

    if not username:
        await ctx.reply("remove කරන්න ඕනේ username එකක් දාන්න! උදා: `.remadmin username`")
        return

    clean_username = username.replace("@", "").strip()
    
    if clean_username == MAIN_ADMIN:
        await ctx.reply(f"අයියෝ, **{MAIN_ADMIN}** කියන්නේ main boss ට. Boss ව remove කරන්න බැහැ! 🛑")
        return

    if clean_username in admin_users:
        admin_users.remove(clean_username)
        await ctx.reply(f"✅ **{clean_username}** ව දැන් Admin list එකෙන් අයින් කළා.")
    else:
        await ctx.reply(f"**{clean_username}** කියන්නේ admin කෙනෙක් නෙවෙයිනේ බං. 🤔")

@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member = None, *, reason=None):
    if not member:
        await ctx.reply("ban කරන්න ඕනේ කාවද කියලා tag කරන්න! උදා: `.ban @User Reason`")
        return
    
    try:
        await member.ban(reason=reason)
        await ctx.reply(f"🔨 **{member.name}** ව නම් රජයෙන් (RedHat Network එකෙන්) එළෙව්වා! හේතුව: {reason or 'නැත'}")
    except Exception as e:
        await ctx.reply("මට ඔයාව ban කරන්න තරම් permissions නැහැ හෝ මගේ rank එක මදි.")

@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("ඔයාට server එකේ Ban permissions නැහැ බං.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.reply("command එක පාවිච්චි කරන හැටි දන්නේ නැද්ද? `.ban @User [reason]` විදිහට දාන්න.")

# --- AI MESSAGE HANDLING (GROQ REST API) ---

async def query_groq(prompt_text, retries=2):
    payload = {
        "model": MODEL_ID,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt_text}
        ],
        "temperature": 0.85,
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

    is_special_channel = getattr(message.channel, 'name', '') == 'bandara-chat'

    if isinstance(message.channel, discord.DMChannel) or is_mentioned or is_reply_to_bot or is_special_channel:
        if message.content.startswith('.'):
            return

        async with message.channel.typing():
            try:
                clean_content = message.content.replace(f'<@!{bot.user.id}>', '').replace(f'<@{bot.user.id}>', '').strip()
                
                if not clean_content:
                    await message.reply("මොකද බං මුහුද බලාගෙන ඉන්නේ? කියන්න ඕන දේ පැහැදිලිව කියන්න!")
                    return

                ai_response = await query_groq(clean_content)
                if ai_response:
                    await send_long_message(message, ai_response)
                else:
                    await message.reply("Groq API එකේ පොඩි slow එකක් වගේ. ටිකකින් ආයේ try කරන්න.")
            except Exception as e:
                print(f"Error: {e}")
                await message.reply("මොකක් හරි technical error එකක් ආවා බං. පස්සේ try කරන්න.")

# --- FAKE HEALTH CHECK SERVER FOR KOYEB ---
async def handle_health(request):
    return web.Response(text="Bandara Bot (Gaamini Vibe Edition) is Healthy and Alive!")

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
