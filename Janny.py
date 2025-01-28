import discord
from discord.ext import commands, tasks
from datetime import datetime

# Bot setup with command prefix "-"
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="-", intents=intents)

# Replace this with your specific role ID
ROLE_ID = 1331524868834852904  # Put your role ID here
ROLE_ID2 = 1322671881232584835
channel_message_counts = {}
MESSAGE_LIMIT = 75
ROLE_ID3 = 1034276393338556456  # Replace with your desired role ID
DELETE_INTERVAL_HOURS = 20

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
member_count = {}

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

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    # Initialize message counts for all channels
    for guild in bot.guilds:
        for channel in guild.text_channels:
            try:
                messages = [msg async for msg in channel.history(limit=None)]
                channel_message_counts[1333281332456849540] = len(messages)
                print(f'Initialized {channel.name} with {len(messages)} messages')
            except Exception as e:
                print(f'Error accessing channel {channel.name}: {e}')
@bot.event
async def on_member_join(member):
    """Automatically assign role to new members"""
    try:
        role = member.guild.get_role(ROLE_ID3)
        if role:
            await member.add_roles(role)
            print(f'Assigned role to {member.name}')
        else:
            print(f'Role with ID {ROLE_ID3} not found')
    except Exception as e:
        print(f'Error assigning role: {e}')

@tasks.loop(hours=DELETE_INTERVAL_HOURS)
async def delete_old_messages():
    """Delete messages from all channels every 20 hours"""
    for guild in bot.guilds:
        for channel in guild.text_channels:
            try:
                # Check if bot has permission to manage messages in this channel
                if channel.permissions_for(guild.me).manage_messages:
                    deleted = await channel.purge(
                        limit=None,  # No limit on number of messages to delete
                        check=lambda m: not m.pinned  # Don't delete pinned messages
                    )
                    print(f'Deleted {len(deleted)} messages from {channel.name}')
            except Exception as e:
                print(f'Error deleting messages in {channel.name}: {e}')

@delete_old_messages.before_loop
async def before_delete():
    """Wait until the bot is ready before starting the deletion loop"""
    await bot.wait_until_ready()

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

# Error handling
@bot.event
async def on_error(event, *args, **kwargs):
    print(f'Error in {event}: {args[0]}')

@bot.command(name='fm')
@commands.has_permissions(manage_roles=True)
async def assign_role(ctx, user: discord.Member):
    """
    Silently assigns the specified role to a user
    Usage: -assignrole @user
    """
    try:
        role = ctx.guild.get_role(ROLE_ID)
        if role is not None:
            await user.add_roles(role)
    except:
        pass
    
@bot.command(name='d')
@commands.has_permissions(manage_roles=True)
async def assign_role(ctx, user: discord.Member):
    """
    Silently assigns the specified role to a user
    Usage: -assignrole @user
    """
    try:
        role = ctx.guild.get_role(ROLE_ID2)
        if role is not None:
            await user.add_roles(role)
    except:
        pass

@bot.command(name='ban')
@commands.has_permissions(ban_members=True)
async def ban_user(ctx, user_id: int):
    """
    Silently bans a user using their user ID
    Usage: -ban user_id
    """
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.ban(user)
    except:
        pass

# Replace 'YOUR_BOT_TOKEN' with your actual bot token
bot.run("")