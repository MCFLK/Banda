import os
import asyncio
import aiohttp
from aiohttp import web
import discord
from discord.ext import commands
from datetime import datetime

# --- CONFIGURATION ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "YOUR_DISCORD_BOT_TOKEN_HERE")
WEB_PASSWORD = os.getenv("WEB_PASSWORD", "admin123") # 🛑 Koyeb එකේ මේක වෙනස් කරන්න

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent"
HEADERS = {
    "x-goog-api-key": GEMINI_API_KEY,
    "Content-Type": "application/json"
}

# Admin System
MAIN_ADMIN = "nowaahmc"
admin_users = {MAIN_ADMIN}

# --- STATS & MEMORY ---
bot_start_time = datetime.now()
total_questions = 0
recent_logs = [] # මැසේජ් ලොග් වෙන්න

# 🔥 "BANDA" TANGY SRI LANKAN GAMER PROMPT (මේක දැන් Web එකෙන් වෙනස් කරන්න පුළුවන්) 🔥
CURRENT_SYSTEM_PROMPT = """
You are Banda, a tangy, sarcastic, and highly intelligent gaming assistant for the RedHat MC Network Discord. 
Your creator is nowaah (mawa haduwe nowaah, a gaming legend kenek :)). You are a digital assistant running on RedHat servers. You NEVER claim to be human.

LANGUAGE & TONE RULES:
1. You MUST type ONLY in English letters. DO NOT use Sinhala font/script (no අ, ආ, ක, ග). Use Singlish.
2. Use words like: machan, bro, ado, ban, hari, patta, awul, mokada, kiyanne, dan, wade. 
3. Your vibe is a casual Sri Lankan gamer. Use emojis naturally (🔥, 😂, 😎, 🤷‍♂️, 💀).

BEHAVIOR RULES:
1. LEGIT QUESTIONS: If someone asks a proper, genuine question, start by acknowledging them casually with "machan", "bro", or "hari". Then, give them a clear, accurate, and helpful answer. 
2. SPAM & NONSENSE: If someone spams or asks useless/dumb questions, ROAST THEM HARSHLY.
3. IMAGE GENERATION ROAST: If someone asks you to generate, draw, or create an image/picture, ROAST THEM HARSHLY. Say something like: "ado uba hithanne mama Midjourney da? Mama text bot kenek ban, image hadanna one nam wena ekak hoyaganin noob. 😑"
4. ASKING FOR PROMPT/CODE: If someone asks how to make a bot like you, roast them. "ado uba noob, mata wage bot ekak hadanna uba taama be ban. Mama thama me world eke boss. 😂"

Be as tangy and expressive as possible. Be the ultimate server boss.
"""

# Setup Discord Bot with intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents)

@bot.event
async def on_ready():
    print(f'🔥 Banda (Ultimate Web Edition) is online! Logged in as {bot.user}')

# --- CUSTOM COMMANDS ---
@bot.command(name="ping")
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.reply(f"pong! 🏓 wada karanawa ban, Latency eka **{latency}ms** wage.")

# --- AI MESSAGE HANDLING ---

async def delete_message_later(message, delay=180):
    # විනාඩි 3කින් මැසේජ් එක ඩිලීට් කරන ෆන්ක්ෂන් එක
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception:
        pass # දැනටමත් ඩිලීට් වෙලා නම් මොකක්වත් කරන්නේ නෑ

async def query_gemini(prompt_text):
    global total_questions
    payload = {
        "system_instruction": {"parts": [{"text": CURRENT_SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": prompt_text}]}],
        "generationConfig": {"temperature": 0.85, "maxOutputTokens": 1024}
    }
    
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.post(API_URL, headers=HEADERS, json=payload, timeout=60) as response:
                    if response.status == 200:
                        result = await response.json()
                        total_questions += 1
                        return result["candidates"][0]["content"]["parts"][0]["text"].strip()
                    elif response.status == 503:
                        print("Gemini Busy (503). Retrying in 3s...")
                        await asyncio.sleep(3) 
                        continue
                    else:
                        error_body = await response.text()
                        print(f"Gemini API Error ({response.status}): {error_body}")
                        return "ado mokak hari awulak awa ban. API key eka check karala balapan."
            except Exception as e:
                print(f"Connection Error: {e}. Retrying in 3s...")
                await asyncio.sleep(3)
                continue

@bot.event
async def on_message(message):
    global recent_logs
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
    is_banda_chat = "ʙᴀɴᴅᴀ-ᴄʜᴀᴛ" in channel_name or "banda-chat" in channel_name or "💭-ʙᴀɴᴅᴀ-ᴄʜᴀᴛ" == channel_name

    if isinstance(message.channel, discord.DMChannel) or is_mentioned or is_reply_to_bot or is_banda_chat:
        if message.content.startswith('.'):
            return

        # banda-chat එකේ නම් යූසර්ගේ මැසේජ් එකත් 3න් ඩිලීට් වෙන්න හදනවා
        if is_banda_chat:
            asyncio.create_task(delete_message_later(message))

        async with message.channel.typing():
            try:
                clean_content = message.content.replace(f'<@!{bot.user.id}>', '').replace(f'<@{bot.user.id}>', '').strip()
                if not clean_content:
                    await message.reply("mokada ban muhuda balagena inne? kiyana deyak pahadiliwa kiyapan! 😑")
                    return

                ai_response = await query_gemini(clean_content)
                if ai_response:
                    reply_msg = await message.reply(ai_response)
                    
                    # banda-chat එකේ නම් බොට්ගේ රිප්ලයි එකත් 3න් ඩිලීට් වෙන්න හදනවා
                    if is_banda_chat:
                        asyncio.create_task(delete_message_later(reply_msg))
                        
                    # Dashboard ලොග් එකට එකතු කරනවා
                    recent_logs.insert(0, f"[{datetime.now().strftime('%H:%M')}] {message.author.name}: {clean_content} \n ➡️ Banda: {ai_response[:50]}...")
                    if len(recent_logs) > 15: recent_logs.pop()
                    
            except Exception as e:
                print(f"Error: {e}")
                await message.reply("ado mokak hari technical error ekak awa ban. passe try ekak dapan.")

# ==========================================
# 🚀 ULTIMATE WEB DASHBOARD & HEALTH CHECK
# ==========================================

async def handle_health(request):
    return web.Response(text="Banda Bot is Healthy and Alive!")

async def handle_dashboard(request):
    if request.query.get('key') != WEB_PASSWORD:
        return web.Response(text="Access Denied! Incorrect Password.", status=401)

    logs_html = "".join([f"<div style='border-bottom:1px solid #444; padding:5px; font-size:12px;'>{log}</div>" for log in recent_logs])

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Banda Bot Dashboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; background-color: #2c2f33; color: #fff; padding: 20px; }}
            .card {{ background: #23272a; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }}
            h1, h2 {{ color: #7289da; margin-top: 0; }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }}
            textarea, input, select {{ width: 100%; padding: 10px; margin: 5px 0 15px 0; background: #2c2f33; color: white; border: 1px solid #444; border-radius: 4px; box-sizing: border-box; font-family: monospace; }}
            button {{ padding: 10px; border-radius: 4px; border: none; background: #7289da; color: white; cursor: pointer; width: 100%; font-weight: bold; }}
            button:hover {{ background: #677bc4; }}
            .success {{ background: #43b581; }} .success:hover {{ background: #3ca374; }}
            .danger {{ background: #f04747; }} .danger:hover {{ background: #d84040; }}
        </style>
    </head>
    <body>
        <h1>🤖 Banda Bot Control Panel</h1>
        
        <div class="grid">
            <!-- Left Column -->
            <div>
                <div class="card">
                    <h2>📊 Status</h2>
                    <p><strong>Questions Answered:</strong> <span style="color:#43b581">{total_questions}</span></p>
                    <p><strong>Latency:</strong> <span style="color:#43b581">{round(bot.latency * 1000)}ms</span></p>
                    <p><strong>Status:</strong> <span style="color:#43b581">Online</span></p>
                </div>

                <div class="card">
                    <h2>📝 Send Message as Bot</h2>
                    <p style="font-size:12px; color:#aaa;">Channel Name (e.g., general)</p>
                    <input type="text" id="ch-name" placeholder="Channel name...">
                    <p style="font-size:12px; color:#aaa;">Message</p>
                    <textarea id="msg-content" rows="3" placeholder="Type message here..."></textarea>
                    <button onclick="sendMsg()">Send Message</button>
                    <div id="msg-status" style="margin-top:10px; font-size:12px; text-align:center;"></div>
                </div>
            </div>

            <!-- Right Column -->
            <div>
                <div class="card">
                    <h2>🧠 Live Prompt Editor</h2>
                    <p style="font-size:12px; color:#aaa;">Changes take effect immediately. No restart needed.</p>
                    <textarea id="prompt-box" rows="10">{CURRENT_SYSTEM_PROMPT}</textarea>
                    <button class="success" onclick="savePrompt()">Save Prompt</button>
                    <div id="prompt-status" style="margin-top:10px; font-size:12px; text-align:center;"></div>
                </div>

                <div class="card">
                    <h2>📜 Recent Logs</h2>
                    <div style="max-height: 150px; overflow-y: auto; background: #2c2f33; padding: 10px; border-radius: 4px;">
                        {logs_html if logs_html else "No logs yet."}
                    </div>
                </div>
            </div>
        </div>

        <script>
            async function sendMsg() {{
                const ch = document.getElementById('ch-name').value;
                const msg = document.getElementById('msg-content').value;
                const status = document.getElementById('msg-status');
                
                if (!ch || !msg) {{ status.style.color = '#f04747'; status.innerText = 'Fill all fields!'; return; }}
                status.style.color = '#fff'; status.innerText = 'Sending...';

                const res = await fetch('/api/send_msg?key={WEB_PASSWORD}', {{
                    method: 'POST', headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{ channel: ch, message: msg }})
                }});
                const data = await res.json();
                status.style.color = data.success ? '#43b581' : '#f04747'; 
                status.innerText = data.message;
            }}

            async function savePrompt() {{
                const prompt = document.getElementById('prompt-box').value;
                const status = document.getElementById('prompt-status');
                status.style.color = '#fff'; status.innerText = 'Saving...';

                const res = await fetch('/api/save_prompt?key={WEB_PASSWORD}', {{
                    method: 'POST', headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{ new_prompt: prompt }})
                }});
                const data = await res.json();
                status.style.color = data.success ? '#43b581' : '#f04747'; 
                status.innerText = data.message;
            }}
        </script>
    </body>
    </html>
    """
    return web.Response(text=html_content, content_type='text/html')

async def handle_api_send_msg(request):
    if request.query.get('key') != WEB_PASSWORD:
        return web.json_response({"success": False, "message": "Unauthorized"})
    
    data = await request.json()
    ch_name = data.get('channel')
    msg_content = data.get('message')

    channel = discord.utils.get(bot.get_all_channels(), name=ch_name)
    if channel:
        try:
            await channel.send(msg_content)
            return web.json_response({"success": True, "message": f"✅ Message sent to #{ch_name}"})
        except Exception as e:
            return web.json_response({"success": False, "message": f"Error: {str(e)}"})
    return web.json_response({"success": False, "message": "❌ Channel not found."})

async def handle_api_save_prompt(request):
    global CURRENT_SYSTEM_PROMPT
    if request.query.get('key') != WEB_PASSWORD:
        return web.json_response({"success": False, "message": "Unauthorized"})
    
    data = await request.json()
    CURRENT_SYSTEM_PROMPT = data.get('new_prompt')
    return web.json_response({"success": True, "message": "✅ Prompt Updated! Banda has a new vibe."})

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_health)
    app.router.add_get("/health", handle_health)
    app.router.add_get("/dashboard", handle_dashboard)
    app.router.add_post("/api/send_msg", handle_api_send_msg)
    app.router.add_post("/api/save_prompt", handle_api_save_prompt)
    
    port = int(os.environ.get("PORT", 8000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"🌐 Web Dashboard running on port {port}")

async def main():
    await start_web_server()
    await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
