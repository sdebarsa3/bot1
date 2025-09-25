#!/usr/bin/env python3
"""
Test ALL notifications for 1337 Morocco Monitor - Windows + Discord
"""

import asyncio
import time
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Discord configuration
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DISCORD_USER_ID = int(os.getenv('DISCORD_USER_ID')) if os.getenv('DISCORD_USER_ID') else None

async def test_windows_notifications():
    """Test Windows native notifications"""
    print("🧪 Testing Windows notifications...")
    
    try:
        from plyer import notification
        
        # Test notification 1: Check-in alert
        print("📢 Sending Windows check-in alert...")
        notification.notify(
            title="🚨 1337 MOROCCO ALERT!",
            message="🔥 UI CHANGE DETECTED!\n"
                   "➕ NEW BUTTON: Check-in Now Available\n"
                   f"⏰ {datetime.now().strftime('%H:%M:%S')}\n"
                   "🔗 Check admission page NOW!",
            app_name="1337 Morocco Monitor",
            timeout=15
        )
        
        # Add sound
        try:
            import winsound
            winsound.Beep(1000, 300)
        except:
            pass
        
        print("✅ Windows notification sent!")
        return True
        
    except Exception as e:
        print(f"❌ Windows notification failed: {e}")
        return False

async def test_discord_notifications():
    """Test Discord notifications"""
    print("\n💬 Testing Discord notifications...")
    
    if not DISCORD_BOT_TOKEN or not DISCORD_USER_ID:
        print("❌ Discord not configured - missing DISCORD_BOT_TOKEN or DISCORD_USER_ID")
        return False
    
    try:
        import discord
        from discord.ext import commands
        
        # Create Discord bot
        intents = discord.Intents.default()
        intents.message_content = True
        bot = commands.Bot(command_prefix='!', intents=intents)
        
        @bot.event
        async def on_ready():
            print(f"✅ Discord bot connected as {bot.user}")
            
            try:
                # Get user and send test message
                user = await bot.fetch_user(DISCORD_USER_ID)
                print(f"✅ Found Discord user: {user.name}")
                
                # Send test alert message
                test_message = f"""🚨 **1337 MOROCCO TEST ALERT** 🚨

🔥 **UI CHANGE DETECTED** 
➕ **NEW BUTTON:** Check-in Now Available
📅 **Check #1337**
⏰ **Time:** {datetime.now().strftime('%H:%M:%S')}
🔗 **URL:** https://admission.1337.ma/candidature/check-in

⚡ **THIS IS A TEST - Check admission page NOW!** ⚡"""
                
                await user.send(test_message)
                print("✅ Discord test message sent!")
                
                # Send second test for CAPTCHA
                await asyncio.sleep(2)
                
                captcha_message = f"""🧩 **CAPTCHA DETECTED** 🧩

🚨 **IMPORTANT CHANGE ON 1337 MOROCCO**
🧩 **CAPTCHA ADDED:** Security verification appeared
📅 **Check #1338**
⏰ **Time:** {datetime.now().strftime('%H:%M:%S')}

🏃‍♂️ **Page is changing - check immediately!**"""
                
                await user.send(captcha_message)
                print("✅ Discord CAPTCHA alert sent!")
                
                return True
                
            except Exception as e:
                print(f"❌ Failed to send Discord message: {e}")
                return False
            finally:
                await bot.close()
        
        # Start bot and wait for connection
        print("🔄 Connecting to Discord...")
        await bot.start(DISCORD_BOT_TOKEN)
        
    except Exception as e:
        print(f"❌ Discord test failed: {e}")
        return False

async def test_combined_alert():
    """Test combined Windows + Discord alert for realistic scenario"""
    print("\n🎯 Testing COMBINED alert (Windows + Discord)...")
    
    # Simulate real UI change detection
    change_details = "➕ NEW BUTTON: Check-in Registration Open | 📄 NEW HEADER: Applications Now Available"
    
    # Send Windows notification
    windows_success = False
    try:
        from plyer import notification
        notification.notify(
            title="🚨 1337 MOROCCO - URGENT!",
            message="🔥 MAJOR UI CHANGE DETECTED!\n"
                   f"{change_details[:80]}...\n"
                   f"⏰ {datetime.now().strftime('%H:%M:%S')}\n"
                   "🏃‍♂️ CHECK IMMEDIATELY!",
            app_name="1337 Morocco Monitor",
            timeout=20
        )
        
        # Sound alert
        try:
            import winsound
            winsound.Beep(1200, 400)
            time.sleep(0.2)
            winsound.Beep(1500, 400)
        except:
            pass
            
        windows_success = True
        print("✅ Combined Windows alert sent!")
        
    except Exception as e:
        print(f"❌ Combined Windows alert failed: {e}")
    
    # Send Discord notification
    discord_success = False
    if DISCORD_BOT_TOKEN and DISCORD_USER_ID:
        try:
            import discord
            from discord.ext import commands
            
            intents = discord.Intents.default()
            intents.message_content = True
            bot = commands.Bot(command_prefix='!', intents=intents)
            
            @bot.event
            async def on_ready():
                nonlocal discord_success
                try:
                    user = await bot.fetch_user(DISCORD_USER_ID)
                    
                    urgent_message = f"""🚨 **URGENT: 1337 MOROCCO CHANGE DETECTED** 🚨

🔥 **MAJOR UI CHANGE DETECTED!**
{change_details}

📅 **Alert #1339**
⏰ **Time:** {datetime.now().strftime('%H:%M:%S')}
🔗 **URL:** https://admission.1337.ma/candidature/check-in

🏃‍♂️ **TAKE ACTION NOW - CHECK THE PAGE IMMEDIATELY!** 🏃‍♂️

This is a REAL-TIME alert from your 1337 Morocco monitor!"""
                    
                    await user.send(urgent_message)
                    discord_success = True
                    print("✅ Combined Discord alert sent!")
                    
                except Exception as e:
                    print(f"❌ Combined Discord alert failed: {e}")
                finally:
                    await bot.close()
            
            await bot.start(DISCORD_BOT_TOKEN)
            
        except Exception as e:
            print(f"❌ Discord combined test failed: {e}")
    
    return windows_success, discord_success

async def main():
    """Run all notification tests"""
    print("=" * 70)
    print("🚀 1337 MOROCCO MONITOR - COMPLETE NOTIFICATION TEST")
    print("=" * 70)
    print(f"💬 Discord Token: {'✅ Configured' if DISCORD_BOT_TOKEN else '❌ Missing'}")
    print(f"👤 Discord User ID: {'✅ Configured' if DISCORD_USER_ID else '❌ Missing'}")
    print("=" * 70)
    
    # Test 1: Windows notifications
    windows_result = await test_windows_notifications()
    await asyncio.sleep(2)
    
    # Test 2: Discord notifications
    discord_result = await test_discord_notifications()
    await asyncio.sleep(2)
    
    # Test 3: Combined realistic scenario
    windows_combined, discord_combined = await test_combined_alert()
    
    # Results
    print("\n" + "=" * 70)
    print("📊 COMPLETE TEST RESULTS:")
    print("=" * 70)
    print(f"📱 Windows Notifications: {'✅ PASS' if windows_result else '❌ FAIL'}")
    print(f"💬 Discord Notifications: {'✅ PASS' if discord_result else '❌ FAIL'}")
    print(f"🎯 Combined Windows Alert: {'✅ PASS' if windows_combined else '❌ FAIL'}")
    print(f"🎯 Combined Discord Alert: {'✅ PASS' if discord_combined else '❌ FAIL'}")
    print("=" * 70)
    
    if windows_result and discord_result:
        print("🎉 ALL NOTIFICATIONS WORKING PERFECTLY!")
        print("💡 You should have received multiple notifications in:")
        print("   📱 Windows notification center")
        print("   💬 Discord direct messages")
        print("🔔 When the monitor detects real changes, you'll get both!")
    elif windows_result:
        print("✅ Windows notifications working!")
        print("⚠️ Discord needs configuration - check .env file")
    else:
        print("❌ Notification system needs attention")
    
    print(f"\n⏰ All tests completed at {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(main())