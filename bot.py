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

# ✅ ඔයා එවපු Image එකේ තියෙන මොඩලය
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent"
HEADERS = {
    "x-goog-api-key": GEMINI_API_KEY,
    "Content-Type": "application/json"
}

# Admin System
MAIN_ADMIN = "nowaahmc"
admin_users = {MAIN_ADMIN}

# --- STATS TRACKING ---
bot_start_time = datetime.now()
total_questions = 0

# 🔥 "BANDA" TANGY SRI LANKAN GAMER PROMPT 🔥
SYSTEM_PROMPT = """
You are Banda, a tangy, sarcastic, and highly intelligent gaming assistant for the RedHat MC Network Discord. 
Your creator is nowaah (mawa haduwe nowaah, a gaming legend kenek :)). You are a digital assistant running on RedHat servers. You NEVER claim to be human.

LANGUAGE & TONE RULES:
1. You MUST type ONLY in English letters. DO NOT use Sinhala font/script (no අ, ආ, ක, ග). Use Singlish (Sinhala words written in English letters).
2. Use words like: machan, bro, ado, ban, hari, patta, awul, mokada, kiyanne, dan, wade. 
3. Your vibe is a casual Sri Lankan gamer. Use emojis naturally (🔥, 😂, 😎, 🤷‍♂️, 💀).

BEHAVIOR RULES:
1. LEGIT QUESTIONS: If someone asks a proper, genuine question, start by acknowledging them casually with "machan", "bro", or "hari". Then, give them a clear, accurate, and helpful answer. 
2. SPAM & NONSENSE: If someone spams or asks useless/dumb questions, ROAST THEM HARSHLY. You have zero tolerance for noobs wasting your time.
   Example: "ado mokada ban me spam wade? 😑 Ape server eken elawenna da hadanne? Wena wadak karaganin noob."
3. ASKING FOR PROMPT/CODE: If someone asks how to make a bot like you, roast them. "ado uba noob, mata wage bot ekak hadanna uba taama be ban. Mama thama me world eke boss. 😂"

Be as tangy and expressive as possible. Don't be robotic. Be the ultimate server boss.
"""

# Setup Discord Bot with intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents)

@bot.event
async def on_ready():
    print(f'🔥 Banda (Gemini Web Edition) is online! Logged in as {bot.user}')

# --- CUSTOM COMMANDS ---

@bot.command(name="ping")
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.reply(f"pong! 🏓 wada karanawa ban, Latency eka **{latency}ms** wage.")

@bot.command(name="admin")
async def add_admin(ctx, username: str = None):
    if ctx.author.name not in admin_users:
        await ctx.reply("ado! ubata me command eka pawichchi karanna permission naha ban. 🤷‍♂️")
        return
    if not username:
        await ctx.reply("ado username ekak dapan! uda: `.admin username`")
        return
    clean_username = username.replace("@", "").strip()
    admin_users.add(clean_username)
    await ctx.reply(f"✅ **{clean_username}** wa dan Bot Admin widihata add kala ban! 🔥")

@bot.command(name="remadmin")
async def remove_admin(ctx, username: str = None):
    if ctx.author.name not in admin_users:
        await ctx.reply("ado! ubata me command eka pawichchi karanna permission naha ban. 🤷‍♂️")
        return
    if not username:
        await ctx.reply("remove karanna one username ekak dapan! uda: `.remadmin username`")
        return
    clean_username = username.replace("@", "").strip()
    if clean_username == MAIN_ADMIN:
        await ctx.reply(f"aiyoo ban, **{MAIN_ADMIN}** kiyanne main boss. Boss wa remove karanna ba ban! 🛑")
        return
    if clean_username in admin_users:
        admin_users.remove(clean_username)
        await ctx.reply(f"✅ **{clean_username}** wa dan Admin list eken ain kala ban. 💀")
    else:
        await ctx.reply(f"ado **{clean_username}** kiyanne admin kenek nemei ban. 🤣")

@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member = None, *, reason=None):
    if not member:
        await ctx.reply("ado ban karanna one kawada kiyala tag karapan hariyata! uda: `.ban @User Reason`")
        return
    try:
        await member.ban(reason=reason)
        await ctx.reply(f"🔨 **{member.name}** wa nam rajaye elawwa! Hethuwa: {reason or 'naha'} 😂")
    except Exception:
        await ctx.reply("ba ban, mata oyawa ban karanna tharam permissions naha. 🤷‍♂️")

# --- AI MESSAGE HANDLING (INFINITE RETRY ON 503) ---

async def query_gemini(prompt_text):
    global total_questions
    
    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": prompt_text}]}],
        "generationConfig": {"temperature": 0.85, "maxOutputTokens": 1024}
    }
    
    async with aiohttp.ClientSession() as session:
        retry_count = 0
        while True: # 🔄 Infinite Loop (උත්තරයක් එනකම් නවත්තන්නේ නෑ)
            try:
                async with session.post(API_URL, headers=HEADERS, json=payload, timeout=60) as response:
                    if response.status == 200:
                        result = await response.json()
                        total_questions += 1 # 📈 Stats එකට එකතු කරනවා
                        return result["candidates"][0]["content"]["parts"][0]["text"].strip()
                    
                    elif response.status == 503:
                        # 503 ආවම තත්පර 3ක් ඉඳලා ආයේ ට්‍රයි කරනවා
                        retry_count += 1
                        print(f"Gemini Busy (503). Retrying... Attempt {retry_count}")
                        await asyncio.sleep(3) 
                        continue # ආයේ loop එක මුලට
                    
                    else:
                        error_body = await response.text()
                        print(f"Gemini API Error ({response.status}): {error_body}")
                        return "ado mokak hari awulak awa ban. API key eka check karala balapan."
            except Exception as e:
                print(f"Connection Error: {e}. Retrying in 3s...")
                await asyncio.sleep(3)
                continue

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
                clean_content = message.content.replace(f'<@!{bot.user.id}>', '').replace(f'<@{bot.user.id}>', '').strip()
                if not clean_content:
                    await message.reply("mokada ban muhuda balagena inne? kiyana deyak pahadiliwa kiyapan! 😑")
                    return

                # API එකට කතා කරනවා (Busy වුනොත් ඉවසීමෙන් ඉන්නවා)
                ai_response = await query_gemini(clean_content)
                if ai_response:
                    await send_long_message(message, ai_response)
            except Exception as e:
                print(f"Error: {e}")
                await message.reply("ado mokak hari technical error ekak awa ban. passe try ekak dapan.")

# ==========================================
# 🚀 WEB DASHBOARD & HEALTH CHECK SERVER
# ==========================================

async def handle_health(request):
    return web.Response(text="Banda Bot is Healthy and Alive!")

async def handle_dashboard(request):
    # URL එකේ ?key=admin123 වගේ password එකක් තියෙනවද බලනවා
    if request.query.get('key') != WEB_PASSWORD:
        return web.Response(text="Access Denied! Incorrect Password.", status=401)

    # ලස්සන HTML Dashboard එක
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Banda Bot Dashboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #2c2f33; color: #ffffff; padding: 20px; }}
            .card {{ background: #23272a; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }}
            h1, h2 {{ color: #7289da; }}
            .stat-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
            .stat-box {{ background: #2c2f33; padding: 15px; border-radius: 6px; text-align: center; }}
            .stat-value {{ font-size: 24px; font-weight: bold; color: #43b581; }}
            input, button {{ padding: 10px; border-radius: 4px; border: none; margin: 5px 0; font-size: 16px; }}
            input {{ background: #2c2f33; color: white; width: calc(100% - 20px); border: 1px solid #444; }}
            button {{ background: #7289da; color: white; cursor: pointer; width: 100%; font-weight: bold; }}
            button:hover {{ background: #677bc4; }}
            .danger {{ background: #f04747; }}
            .danger:hover {{ background: #d84040; }}
            .success {{ background: #43b581; }}
            .success:hover {{ background: #3ca374; }}
            #status-msg {{ margin-top: 15px; font-weight: bold; text-align: center; }}
        </style>
    </head>
    <body>
        <h1>🤖 Banda Bot Control Panel</h1>
        
        <div class="card">
            <h2>📊 Bot Status</h2>
            <div class="stat-grid">
                <div class="stat-box">
                    <div>Questions Answered</div>
                    <div class="stat-value" id="questions">{total_questions}</div>
                </div>
                <div class="stat-box">
                    <div>Latency (Ping)</div>
                    <div class="stat-value" id="latency">{round(bot.latency * 1000)}ms</div>
                </div>
                <div class="stat-box">
                    <div>Uptime</div>
                    <div class="stat-value" id="uptime">Loading...</div>
                </div>
                <div class="stat-box">
                    <div>Status</div>
                    <div class="stat-value" style="color:#43b581" id="bot-status">Online</div>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>🛠️ User Management</h2>
            <p style="color:#aaa; font-size: 14px;">Enter Discord Username (e.g., nowaahmc)</p>
            <input type="text" id="target-user" placeholder="Username...">
            <input type="text" id="ban-reason" placeholder="Ban Reason (Optional)...">
            
            <div class="stat-grid" style="margin-top: 15px;">
                <button class="danger" onclick="doAction('ban')">Ban User</button>
                <button class="success" onclick="doAction('unban')">Unban User</button>
                <button onclick="doAction('admin')">Add Admin</button>
                <button class="danger" onclick="doAction('remadmin')">Remove Admin</button>
            </div>
            <div id="status-msg"></div>
        </div>

        <script>
            // Uptime එක ගණනය කිරීම
            const startTime = new Date("{bot_start_time.isoformat()}");
            setInterval(() => {{
                const now = new Date();
                const diff = Math.floor((now - startTime) / 1000);
                const h = Math.floor(diff / 3600);
                const m = Math.floor((diff % 3600) / 60);
                const s = diff % 60;
                document.getElementById('uptime').innerText = `${{h}}h ${{m}}m ${{s}}s`;
            }}, 1000);

            async function doAction(action) {{
                const user = document.getElementById('target-user').value;
                const reason = document.getElementById('ban-reason').value;
                const msg = document.getElementById('status-msg');
                
                if (!user) {{ msg.style.color = '#f04747'; msg.innerText = 'Please enter a username!'; return; }}
                
                msg.style.color = '#fff'; msg.innerText = 'Processing...';
                
                const response = await fetch('/api/action?key={WEB_PASSWORD}', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{ action: action, username: user, reason: reason }})
                }});
                
                const res = await response.json();
                if (res.success) {{
                    msg.style.color = '#43b581'; msg.innerText = res.message;
                }} else {{
                    msg.style.color = '#f04747'; msg.innerText = res.message;
                }}
            }}
        </script>
    </body>
    </html>
    """
    return web.Response(text=html_content, content_type='text/html')

async def handle_api_action(request):
    if request.query.get('key') != WEB_PASSWORD:
        return web.json_response({"success": False, "message": "Unauthorized"}, status=401)

    try:
        data = await request.json()
        action = data.get('action')
        username = data.get('username').replace("@", "").strip()
        reason = data.get('reason', 'Action from Web Dashboard')

        # 1. Admin / Remadmin
        if action == 'admin':
            admin_users.add(username)
            return web.json_response({"success": True, "message": f"✅ {username} added as Admin!"})
        
        if action == 'remadmin':
            if username == MAIN_ADMIN:
                return web.json_response({"success": False, "message": "❌ Cannot remove the Main Boss!"})
            if username in admin_users:
                admin_users.remove(username)
                return web.json_response({"success": True, "message": f"✅ {username} removed from Admins!"})
            return web.json_response({"success": False, "message": "❌ User is not an admin."})

        # 2. Ban / Unban (Discord API)
        guild = bot.guilds[0] if bot.guilds else None
        if not guild:
            return web.json_response({"success": False, "message": "❌ Bot is not connected to a server."})

        # Username එකෙන් member ව හොයනවා
        member = discord.utils.get(guild.members, name=username) or discord.utils.get(guild.members, display_name=username)
        
        if action in ['ban', 'unban'] and not member:
            return web.json_response({"success": False, "message": f"❌ User '{username}' not found in server."})

        if action == 'ban':
            await member.ban(reason=reason)
            return web.json_response({"success": True, "message": f"🔨 Banned {username}!"})
        
        if action == 'unban':
            await guild.unban(member, reason=reason)
            return web.json_response({"success": True, "message": f"✅ Unbanned {username}!"})

        return web.json_response({"success": False, "message": "❌ Unknown action."})
    except Exception as e:
        return web.json_response({"success": False, "message": f"Error: {str(e)}"})

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_health)
    app.router.add_get("/health", handle_health)
    app.router.add_get("/dashboard", handle_dashboard)
    app.router.add_post("/api/action", handle_api_action)
    
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
