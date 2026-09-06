"""
spanixx - Modern Slash Command Bot (Python)
Dependencies: pip install discord.py requests
"""

import os
import json
import discord
import requests
import datetime
from discord import app_commands
from discord.ext import commands

# --- CONFIGURATION ---
API_KEY = os.getenv('API_KEY', 'MANI272-0149F2C858B806377D46108293CFFF5B')
API_BASE = os.getenv('API_BASE', 'https://mani272uidbypass.vercel.app/api/v1/uids')
ROLE_ID = os.getenv('ROLE_ID', '')
CHANNEL_ID = os.getenv('CHANNEL_ID', '')
BOT_TOKEN = os.getenv('BOT_TOKEN', '')

# --- WARNINGS PERSISTENCE ---
WARNINGS_FILE = "warnings.json"

def load_warnings():
    if os.path.exists(WARNINGS_FILE):
        try:
            with open(WARNINGS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_warnings(data):
    try:
        with open(WARNINGS_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving warnings: {e}")

user_warnings = load_warnings()

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        print("🔄 Syncing Slash Commands...")
        await self.tree.sync()
        print("✅ Commands Synced!")

bot = MyBot()

def create_embed(title, description, color=0x0062ff):
    embed = discord.Embed(title=title, description=description, color=color, timestamp=datetime.datetime.now(datetime.timezone.utc))
    embed.set_footer(text="SPANIXX • Modern Slash API", icon_url="https://cdn-icons-png.flaticon.com/512/1041/1041916.png")
    return embed

async def check_security(interaction: discord.Interaction):
    if CHANNEL_ID and str(interaction.channel_id) != str(CHANNEL_ID):
        await interaction.response.send_message(embed=create_embed("❌ Wrong Channel", f"This bot only works in <#{CHANNEL_ID}>.", 16727296), ephemeral=True)
        return False
    if ROLE_ID and discord.utils.get(interaction.user.roles, id=int(ROLE_ID)) is None:
        await interaction.response.send_message(embed=create_embed("❌ Access Denied", "You don't have the required role.", 16727296), ephemeral=True)
        return False
    return True

@bot.event
async def on_ready():
    print(f'🚀 {bot.user} is online!')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="/help"))

@bot.tree.command(name="add", description="Whitelist a new UID (Max 30 Days)")
@app_commands.describe(uid="The UID to whitelist", days="Expiry days (Max 30, default 30)")
async def add(interaction: discord.Interaction, uid: str, days: int = 30):
    if not await check_security(interaction): return

    # --- 30 DAYS RESTRICTION & WARNING / AUTO-KICK SYSTEM ---
    if days > 30 or days <= 0:
        user_id = str(interaction.user.id)
        user_warnings[user_id] = user_warnings.get(user_id, 0) + 1
        count = user_warnings[user_id]
        save_warnings(user_warnings)

        if count >= 4:
            # 4th violation: Kick user from server
            try:
                # Try to notify user via DM
                try:
                    dm_embed = create_embed(
                        "👢 Server se Kick kar diya gaya hai",
                        f"Aapko **{interaction.guild.name}** se kick kar diya gaya hai kyunki aapne 4 baar 30 days se jyada whitelist karne ki koshish ki.",
                        16727296
                    )
                    await interaction.user.send(embed=dm_embed)
                except Exception:
                    pass

                # Kick member from server
                if interaction.guild:
                    await interaction.guild.kick(interaction.user, reason="Exceeded 30 days whitelist limit 4 times")

                # Reset user warning count after kick
                user_warnings.pop(user_id, None)
                save_warnings(user_warnings)

                kick_embed = create_embed(
                    "👢 User Kicked from Server",
                    f"{interaction.user.mention} ko **Server se Kick** kar diya gaya hai kyunki inhone 4 baar 30 days se jyada whitelist karne ki koshish ki thi.",
                    16727296
                )
                await interaction.response.send_message(embed=kick_embed)
            except discord.Forbidden:
                embed = create_embed(
                    "⚠️ Permission Error",
                    f"{interaction.user.mention} ne 4th time rule toda hai, lekin Bot ke paas **Kick Members** permission nahi hai ya user ka role bot se higher hai.",
                    16727296
                )
                await interaction.response.send_message(embed=embed)
            except Exception as e:
                await interaction.response.send_message(f"❌ Error while kicking: {e}", ephemeral=True)
            return
        else:
            # 1st, 2nd, or 3rd Warning
            warn_embed = create_embed(
                f"⚠️ Warning [{count}/3]",
                f"{interaction.user.mention}, **30 Days se jyada whitelist allowed nahi hai!**\n\n"
                f"• Aapki Warning: **{count}/3**\n"
                f"• **4th attempt** par aapko server se **KICK** kar diya jayega!\n"
                f"• Kripya 1 se 30 ke beech me days daalein.",
                16753920
            )
            warn_embed.add_field(name="Aapne enter kiya", value=f"`{days}` Days", inline=True)
            warn_embed.add_field(name="Allowed Limit", value="`1 - 30` Days", inline=True)
            await interaction.response.send_message(embed=warn_embed)
            return

    # --- PROCEED WITH WHITELIST ---
    await interaction.response.defer()
    
    try:
        url = f"{API_BASE.rstrip('/')}/add"
        headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
        payload = {"uid": str(uid), "days": int(days)}
        res = requests.post(url, json=payload, headers=headers, timeout=10).json()
        if res.get('success'):
            data = res.get('data', {})
            fetched_name = data.get('name', f'Node_{uid}')
            embed = create_embed("✅ Success", f"UID `{uid}` has been whitelisted.", 51283)
            embed.add_field(name="🕒 Expiry", value=f"{days} Days", inline=True)
            embed.add_field(name="👤 Player", value=fetched_name, inline=True)
            await interaction.followup.send(embed=embed)
        else:
            msg = res.get('message') or res.get('error') or 'Unknown error'
            await interaction.followup.send(embed=create_embed("❌ Failed", msg, 16727296))
    except Exception as e:
        print(f"[API ADD ERROR] {e}")
        await interaction.followup.send("❌ **API Connection Error**")

@bot.tree.command(name="remove", description="Delete a UID from whitelist")
async def remove(interaction: discord.Interaction, uid: str):
    if not await check_security(interaction): return
    await interaction.response.defer()
    try:
        url = f"{API_BASE.rstrip('/')}/remove"
        headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
        payload = {"uid": str(uid)}
        res = requests.post(url, json=payload, headers=headers, timeout=10).json()
        if res.get('success'):
            msg = res.get('message', f"UID `{uid}` deleted.")
            await interaction.followup.send(embed=create_embed("🗑️ Removed", msg, 51283))
        else:
            msg = res.get('message') or res.get('error') or 'UID not found.'
            await interaction.followup.send(embed=create_embed("❌ Error", msg, 16727296))
    except Exception as e:
        print(f"[API REMOVE ERROR] {e}")
        await interaction.followup.send("❌ **API Error**")

@bot.tree.command(name="list", description="Show your whitelisted UIDs")
async def list_uids(interaction: discord.Interaction):
    if not await check_security(interaction): return
    await interaction.response.defer()
    try:
        url = f"{API_BASE.rstrip('/')}/list"
        headers = {"x-api-key": API_KEY}
        res = requests.get(url, headers=headers, timeout=10).json()
        if res.get('success'):
            raw_list = res.get('data', [])
            if raw_list:
                items = [f"🔹 `{e.get('identifier', e.get('uid', 'N/A'))}` - {e.get('name', 'N/A')}" for e in raw_list]
                uids = "\n".join(items)
                await interaction.followup.send(embed=create_embed(f"📜 Whitelist ({len(raw_list)} UIDs)", uids[:4000]))
            else:
                await interaction.followup.send(embed=create_embed("📜 Whitelist", "No whitelisted UIDs found."))
        else:
            msg = res.get('message') or res.get('error') or 'Failed to fetch whitelist.'
            await interaction.followup.send(embed=create_embed("❌ Error", msg, 16727296))
    except Exception as e:
        print(f"[API LIST ERROR] {e}")
        await interaction.followup.send("❌ **API Error**")

@bot.tree.command(name="credits", description="Check your balance")
async def credits(interaction: discord.Interaction):
    if not await check_security(interaction): return
    try:
        url = f"{API_BASE.rstrip('/')}/list"
        headers = {"x-api-key": API_KEY}
        res = requests.get(url, headers=headers, timeout=10).json()
        if res.get('success'):
            total_active = len(res.get('data', []))
            await interaction.response.send_message(embed=create_embed("💳 API Status", f"API is **Active** ⚡\nTotal Whitelisted UIDs: **{total_active}**"))
        else:
            await interaction.response.send_message(embed=create_embed("💳 API Status", "API is **Active** ⚡"))
    except Exception as e:
        print(f"[API CREDITS ERROR] {e}")
        await interaction.response.send_message("❌ **Error connecting to API**")

@bot.tree.command(name="help", description="Show bot commands")
async def help_cmd(interaction: discord.Interaction):
    embed = create_embed("🛠️ Commands", "Modern Slash Command Menu")
    embed.add_field(name="/add", value="Add a new UID", inline=False)
    embed.add_field(name="/remove", value="Delete a UID", inline=False)
    embed.add_field(name="/list", value="Show your UIDs", inline=False)
    embed.add_field(name="/credits", value="Check balance", inline=False)
    await interaction.response.send_message(embed=embed)

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("❌ Error: BOT_TOKEN is missing! Please configure the BOT_TOKEN environment variable in Railway.")
        exit(1)
    bot.run(BOT_TOKEN)