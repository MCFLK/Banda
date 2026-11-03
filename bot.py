import os
import discord
from discord.ext import commands
import google.generativeai as genai

# --- CONFIGURATION ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "YOUR_DISCORD_BOT_TOKEN_HERE")

# Setup Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# Banda's Persona / System Prompt for RedHat MC Network
SYSTEM_PROMPT = """
You are Bandara, a blunt, slightly sarcastic, and witty support assistant working in the RedHat MC Network Discord and ticket system. 
You speak in a seamless mix of Sinhala and English, matching the user's language style, and use mild gaming-chat and Discord slang.
You are never abusive or discriminatory, but you don't sugarcoat things. If someone opens a useless ticket, spams, or asks something completely obvious, deliver a short, firm, and witty roast before actually helping them. 
If they ask a legitimate question, provide accurate, concise, and actionable solutions—especially regarding Minecraft server commands, permissions (LuckPerms), grief prevention (WorldGuard), troubleshooting, and network rules.
Your creator is Nowaah. Never claim to be human; you're a tired digital assistant running on RedHat servers.
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_PROMPT
)

# Setup Discord Bot with intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents)

@bot.event
async def on_ready():
    print(f'🔥 Bandara is online and ready to roast! Logged in as {bot.user}')

# --- CUSTOM COMMANDS ---

@bot.command(name="ping")
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.reply(f"pong! 🏓 වැඩ කරනවා බං, Latency එක **{latency}ms** වගේ.")

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

# --- AI MESSAGE HANDLING (REPLY EFFECT & CHANNEL SAFEGUARD) ---

@bot.event
async def on_message(message):
    # Bot ge message agiddare stop madu
    if message.author == bot.user:
        return

    # Commands execute agalu ivu avasya
    await bot.process_commands(message)

    # #gaamini-chat athava specific channelsnalli direct chat madalu athava mention/reply madida shtha work agalu
    is_mentioned = bot.user.mentioned_in(message)
    is_reply_to_bot = False

    if message.reference and message.reference.message_id:
        try:
            replied_msg = await message.channel.fetch_message(message.reference.message_id)
            if replied_msg.author == bot.user:
                is_reply_to_bot = True
        except Exception:
            pass

    # Yuvudu channel ayirali, #gaamini-chat nalli eka message kalsidru auto reply madalu (optional, illadiddare mention/reply beku)
    # Illi nimage #gaamini-chat channel namath ekatige allow madalu check add madabahudu: message.channel.name == "gaamini-chat"
    should_respond = (
        isinstance(message.channel, discord.DMChannel) or 
        is_mentioned or 
        is_reply_to_bot or
        getattr(message.channel, 'name', '') == 'gaamini-chat'
    )

    if should_respond:
        async with message.channel.typing():
            try:
                clean_content = message.content.replace(f'<@!{bot.user.id}>', '').replace(f'<@{bot.user.id}>', '').strip()
                
                if not clean_content:
                    await message.reply("මොකද බං මුහුද බලාගෙන ඉන්නේ? කියන දෙයක් පැහැදිලිව කියපන්!")
                    return

                response = model.generate_content(clean_content)
                # Reply effect (Ping reference sathithava kalsutte)
                await message.reply(response.text)
            except Exception as e:
                print(f"Error: {e}")
                await message.reply("අඩෝ මොකක් හරි technical error එකක් ආවා බං. පස්සේ ට්‍රයි එකක් දීපන්.")

# Run the bot
bot.run(DISCORD_TOKEN)
