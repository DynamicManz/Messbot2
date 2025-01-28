import discord
from discord.ext import commands
import os
from datetime import datetime

# Function to convert numbers to Roman numerals
def to_roman(num):
    roman_values = [
        (1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'),
        (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'),
        (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')
    ]
    
    roman = ''
    for value, numeral in roman_values:
        while num >= value:
            roman += numeral
            num -= value
    return roman

# Bot setup
intents = discord.Intents.all()
intents.members = True  # Enable member intents
bot = commands.Bot(command_prefix='!', intents=intents)

# Store the current member count
member_count = {}
ROLE_ID3 = 1034276393338556456
channel_message_counts = {}
MESSAGE_LIMIT = 75

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    # Initialize member count for each guild
    for guild in bot.guilds:
        member_count[guild.id] = count_non_bot_members(guild)

def count_non_bot_members(guild):
    return len([member for member in guild.members if not member.bot])

@bot.event
async def on_member_join(member):
    if member.bot:
        return
        
    try:
        guild = member.guild
        # Update member count and get the new member's number
        member_count[guild.id] = member_count.get(guild.id, 0) + 1
        new_number = member_count[guild.id]
        
        # Convert to Roman numeral and set nickname
        new_name = to_roman(new_number)
        await member.edit(nick=new_name)
        
        # Send welcome message in system channel if it exists
        if guild.system_channel:
            await guild.system_channel.send(f"Welcome {member.mention}! You have been assigned the number {new_name}.")
            
    except discord.Forbidden:
        if guild.system_channel:
            await guild.system_channel.send(f"Failed to rename {member.mention}. Missing permissions.")
    except Exception as e:
        print(f"Error handling new member {member.name}: {str(e)}")

    try:
        role = member.guild.get_role(ROLE_ID3)
        if role:
            await member.add_roles(role)
            print(f'Assigned role to {member.name}')
        else:
            print(f'Role with ID {ROLE_ID3} not found')

    except Exception as e:
        print(f'Error assigning role: {e}')

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    channel_id = message.channel.id
    
    # Initialize count if channel is not in dictionary
    if channel_id not in channel_message_counts:
        messages = [msg async for msg in message.channel.history(limit=None)]
        channel_message_counts[1325703127747395584] = len(messages)
    else:
        channel_message_counts[1325703127747395584] += 1


    # Check if channel has reached the message limit
    if channel_message_counts[1325703127747395584] > MESSAGE_LIMIT:
        try:
             async for oldest_message in message.channel.history(limit=1, oldest_first=True):
                await oldest_message.delete()
                channel_message_counts[1325703127747395584] -= 1
                print(f'Deleted oldest message in {message.channel.name}')
                break
        except Exception as e:
            print(f'Error deleting message: {e}')

    await bot.process_commands(message)

@bot.command(name='renameall')
@commands.has_permissions(administrator=True)
async def rename_members(ctx):
    try:
        # Get all members and sort them by join date
        members = sorted(ctx.guild.members, key=lambda m: m.joined_at or datetime.max)
        
        # Reset member count for this guild
        member_count[ctx.guild.id] = 0
        
        # Send initial message
        status_message = await ctx.send('Starting to rename members...')
        
        # Track successful and failed renames
        success_count = 0
        failed_count = 0
        failed_members = []

        for member in members:
            try:
                # Skip bots
                if member.bot:
                    continue
                    
                # Increment counter and update guild's member count
                member_count[ctx.guild.id] += 1
                new_name = to_roman(member_count[ctx.guild.id])
                
                # Attempt to rename the member
                await member.edit(nick=new_name)
                success_count += 1
                
                # Update status message every 5 members
                if success_count % 5 == 0:
                    await status_message.edit(content=f'Progress: {success_count} members renamed...')
                    
            except discord.Forbidden:
                failed_count += 1
                failed_members.append(member.name)
                continue
            except Exception as e:
                failed_count += 1
                failed_members.append(member.name)
                print(f"Error renaming {member.name}: {str(e)}")
                continue
                
        # Send completion message
        completion_message = f"Renaming complete!\n"
        completion_message += f"Successfully renamed: {success_count} members\n"
        completion_message += f"Failed to rename: {failed_count} members"
        
        if failed_members:
            completion_message += "\nFailed members (first 10):"
            for name in failed_members[:10]:
                completion_message += f"\n- {name}"
            if len(failed_members) > 10:
                completion_message += f"\n...and {len(failed_members) - 10} more"
                
        await ctx.send(completion_message)
        
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

@bot.command(name='fixcount')
@commands.has_permissions(administrator=True)
async def fix_member_count(ctx):
    """Fix the member count if it gets out of sync"""
    try:
        guild = ctx.guild
        actual_count = count_non_bot_members(guild)
        member_count[guild.id] = actual_count
        await ctx.send(f"Member count reset to {actual_count}")
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

# Replace 'YOUR_TOKEN_HERE' with your bot's token
bot.run("")