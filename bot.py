import os
import asyncio
import aiohttp
from aiohttp import web
import discord
from discord.ext import commands

# --- CONFIGURATION ---
HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "YOUR_HUGGINGFACE_TOKEN_HERE")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "YOUR_DISCORD_BOT_TOKEN_HERE")

# Hugging Face API Setup (Using Meta Llama 3)
API_URL = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"
headers = {"Authorization": f"Bearer {HF_API_KEY}"}

# Admin System (Main Admin: nowaahmc)
MAIN_ADMIN = "nowaahmc"
admin_users = {MAIN_ADMIN}

# Bandara's Persona / System Prompt for RedHat MC Network
SYSTEM_PROMPT = """
You are Bandara, a blunt, slightly sarcastic, and witty support assistant working in the RedHat MC Network Discord and ticket system. 
You speak in a seamless mix of Sinhala and English, matching the user's language style, and use mild gaming-chat and Discord slang.
You are never abusive or discriminatory, but you don't sugarcoat things. If someone opens a useless ticket, spams, or asks something completely obvious, deliver a short, firm, and witty roast before actually helping them. 
If they ask a legitimate question, provide accurate, concise, and actionable solutions—especially regarding Minecraft server commands, permissions (LuckPerms), grief prevention (WorldGuard), troubleshooting, and network rules.
Your creator is Nowaah. Never claim to be human; you're a tired digital assistant running on RedHat servers.
"""

# Setup Discord Bot with intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents)

@bot.event
async def on_ready():
    print(f'🔥 Bandara (Hugging Face Edition) is online! Logged in as {bot.user}')

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

# --- AI MESSAGE HANDLING (HUGGING FACE) ---

async def query_huggingface(prompt_text):
    payload = {
        "inputs": f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n{SYSTEM_PROMPT}<|eot_id|><|start_header_id|>user<|end_header_id|>\n{prompt_text}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n",
        "parameters": {"max_new_tokens": 250, "temperature": 0.7}
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, headers=headers, json=payload) as response:
            if response.status == 200:
                result = await response.json()
                if isinstance(result, list) and len(result) > 0:
                    generated_text = result[0].get("generated_text", "")
                    if "<|start_header_id|>assistant<|end_header_id|>" in generated_text:
                        reply = generated_text.split("<|start_header_id|>assistant<|end_header_id|>")[1].strip()
                        return reply
                    return generated_text
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

                ai_response = await query_huggingface(clean_content)
                if ai_response:
                    await message.reply(ai_response)
                else:
                    await message.reply("අඩෝ Hugging Face model එක දැන් busy වගේ. පොඩි වෙලාවකින් ට්‍රයි එකක් දීපන්.")
            except Exception as e:
                print(f"Error: {e}")
                await message.reply("අඩෝ මොකක් හරි technical error එකක් ආවා බං. පස්සේ ට්‍රයි එකක් දීපන්.")

# --- FAKE HEALTH CHECK SERVER FOR KOYEB ---
async def handle_health(request):
    return web.Response(text="Bandara Bot (HF) is Healthy and Alive!")

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
