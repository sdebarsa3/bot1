#!/usr/bin/env python3
"""
Ultimate 1337 Morocco Monitor - Multi-Vector Bypass System
Uses every possible technique to bypass Cloudflare protection
"""

import asyncio
import json
import logging
import os
import random
import re
import time
from datetime import datetime
from typing import Dict, Optional, List
import subprocess
import tempfile
import pickle
import asyncio as aio_sleep
import base64
from io import BytesIO
from urllib.parse import urlparse
import webbrowser
import shutil

# Import all bypass libraries
import httpx
import requests
import cloudscraper
from curl_cffi import requests as cf_requests
# from requests_html import HTMLSession  # Disabled due to dependency issues
import aiofiles
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from twilio.rest import Client
import discord
from discord.ext import commands
from fake_useragent import UserAgent

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
os.makedirs("logs", exist_ok=True)

# Selenium imports for auto-login
try:
    import undetected_chromedriver as uc
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
    SELENIUM_AVAILABLE = True
    logger.info("🔧 Selenium auto-login capability available")
except ImportError as e:
    SELENIUM_AVAILABLE = False
    logger.warning(f"⚠️ Selenium not available - auto-login disabled: {e}")

# Load environment variables
load_dotenv()

# Configuration
STUDENT_EMAIL = os.getenv("STUDENT_EMAIL") or ""
STUDENT_PASSWORD = os.getenv("STUDENT_PASSWORD") or ""
REFRESH_INTERVAL = float(os.getenv("REFRESH_INTERVAL", 5))
SITE_URL = os.getenv("SITE_URL", "https://tickets.cafonline.com/overflow/index.html")

# Notification configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN") 
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
TARGET_PHONE_NUMBER = os.getenv("ADMIN_PHONE") or STUDENT_EMAIL

# Discord configuration
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_USER_ID = int(os.getenv("DISCORD_USER_ID", "0")) if os.getenv("DISCORD_USER_ID") else None

# CAPTCHA solving configuration
CAPTCHA_API_KEY = os.getenv("CAPTCHA_API_KEY") or os.getenv("ANTICAPTCHA_API_KEY") or os.getenv("2CAPTCHA_API_KEY")
CAPTCHA_SERVICE = os.getenv("CAPTCHA_SERVICE", "anticaptcha")  # anticaptcha, 2captcha

# CAPTCHA solving configuration
CAPTCHA_SERVICE_API_KEY = os.getenv("CAPTCHA_API_KEY") or os.getenv("ANTICAPTCHA_API_KEY") or os.getenv("2CAPTCHA_API_KEY")
CAPTCHA_SERVICE = os.getenv("CAPTCHA_SERVICE", "anticaptcha")  # anticaptcha, 2captcha, capsolver

# Auto-login control
DISABLE_AUTO_LOGIN = os.getenv("DISABLE_AUTO_LOGIN", "true").lower() == "true"
CHROME_GUEST_REFRESH_SECONDS = int(os.getenv("CHROME_GUEST_REFRESH_SECONDS", "0"))  # 0 disables visible auto-refresh
FAST_MODE = os.getenv("FAST_MODE", "true").lower() == "true"  # Aggressive speed
VISIBLE_REFRESH_SECONDS = int(os.getenv("VISIBLE_REFRESH_SECONDS", "0"))  # Use Selenium to refresh one tab

# Enforce faster interval in FAST_MODE
if FAST_MODE and REFRESH_INTERVAL > 1.0:
    REFRESH_INTERVAL = 1.0

# Initialize Discord bot
bot = None
if DISCORD_BOT_TOKEN:
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix='!', intents=intents)
    
    @bot.event
    async def on_ready():
        logger.info(f"Discord bot logged in as {bot.user}")

class UltimateBypassMonitor:
    def __init__(self):
        self.previous_content = None
        self.previous_url_key = None
        self.ua = UserAgent()
        self.success_method = None
        self.proxy_list = []
        
        # Initialize Twilio
        self.twilio_client = None
        if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
            try:
                self.twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
                logger.info("Twilio client initialized")
            except Exception as e:
                logger.error(f"Twilio init failed: {e}")
        
        # Initialize browser for auto-login
        self.browser = None
        self.cookies_file = "session_cookies.pkl"
        
        # Initialize all bypass methods
        self.init_bypass_methods()
        
        # Open in Chrome Guest on startup if requested
        if os.getenv("OPEN_CHROME_GUEST", "true").lower() == "true":
            try:
                self.open_in_chrome_guest(SITE_URL)
            except Exception as e:
                logger.warning(f"Could not open Chrome Guest: {e}")

        # Optionally keep a single visible browser tab and refresh it
        self.visible_refresh_ready = False
        if VISIBLE_REFRESH_SECONDS > 0 and SELENIUM_AVAILABLE:
            try:
                if not self.browser:
                    ok = self.init_browser()
                    if not ok:
                        raise RuntimeError("Selenium init failed")
                self.browser.get(SITE_URL)
                self.visible_refresh_ready = True
                logger.info(f"🧭 Visible tab opened for periodic refresh every {VISIBLE_REFRESH_SECONDS}s")
            except Exception as e:
                logger.warning(f"Visible refresh disabled (init error): {e}")
        
    def init_bypass_methods(self):
        """Initialize all bypass methods"""
        logger.info("🔧 Initializing multi-vector bypass system...")
        
        # Method 1: CloudScraper with custom settings
        self.cloudscraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False},
            delay=random.uniform(1, 3)
        )
        
        # Method 2: curl-cffi (Go HTTP implementation)
        self.cf_session = cf_requests.Session()
        
        # Method 3: HTTPX with custom settings - SPEED OPTIMIZED
        self.httpx_client = httpx.AsyncClient(
            timeout=(3.0 if FAST_MODE else 8.0),
            follow_redirects=True,
            verify=False,
            limits=httpx.Limits(max_connections=(30 if FAST_MODE else 10), max_keepalive_connections=(15 if FAST_MODE else 5))
        )
        
        # Method 4: requests-html (Disabled due to dependencies)
        # self.html_session = HTMLSession()
        
        # Method 5: Raw curl commands
        self.curl_available = True
        
        logger.info("✅ All bypass methods initialized")
    
    def open_in_chrome_guest(self, url: str):
        """Open URL in Google Chrome Guest mode on Windows"""
        # Common Chrome paths
        possible_paths = [
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        ]
        chrome_path = next((p for p in possible_paths if os.path.exists(p)), None)
        if not chrome_path:
            # Fallback to default browser if Chrome not found
            webbrowser.open(url)
            return
        subprocess.Popen([chrome_path, "--guest", url])
        
    def init_browser(self):
        """Initialize browser for auto-login"""
        if not SELENIUM_AVAILABLE:
            logger.warning("⚠️ Cannot initialize browser - Selenium not available")
            return False
            
        try:
            logger.info("🌐 Initializing stealth browser for auto-login...")
            
            # Chrome options for stealth (Fixed for compatibility)
            chrome_options = uc.ChromeOptions()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')
            # Remove problematic experimental options that cause errors
            
            # Create undetected Chrome instance with minimal options
            self.browser = uc.Chrome(options=chrome_options, version_main=None)
            
            # Apply anti-detection after browser creation
            self.browser.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("✅ Browser initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Browser initialization failed: {e}")
            self.browser = None
            return False
    
    async def detect_and_solve_captcha(self) -> bool:
        """Detect and solve CAPTCHA if present"""
        try:
            # Look for hCaptcha iframe
            hcaptcha_elements = [
                "iframe[src*='hcaptcha.com']",
                "[data-hcaptcha-widget-id]",
                ".h-captcha",
                "#h-captcha",
                "iframe[title*='hCaptcha']"
            ]
            
            captcha_found = False
            site_key = None
            
            for selector in hcaptcha_elements:
                try:
                    element = self.browser.find_element(By.CSS_SELECTOR, selector)
                    captcha_found = True
                    logger.info(f"🧩 hCaptcha detected using selector: {selector}")
                    
                    # Try to extract site key
                    if 'iframe' in selector:
                        src = element.get_attribute('src')
                        if 'sitekey=' in src:
                            site_key = src.split('sitekey=')[1].split('&')[0]
                    else:
                        site_key = element.get_attribute('data-sitekey')
                    break
                except:
                    continue
            
            if not captcha_found:
                logger.info("✅ No CAPTCHA detected")
                return True
                
            logger.info("🧩 hCaptcha detected - attempting to solve...")
            
            # For now, just wait and hope user solves manually
            logger.warning("⚠️ CAPTCHA detected! Please solve it manually within 30 seconds...")
            await aio_sleep.sleep(30)  # Give user time to solve
            
            return True  # Assume solved for now
            
        except Exception as e:
            logger.error(f"CAPTCHA detection error: {e}")
            return True  # Continue anyway
    
    def save_cookies(self):
        """Save browser cookies for session persistence"""
        if not self.browser:
            return
        try:
            cookies = self.browser.get_cookies()
            with open(self.cookies_file, 'wb') as f:
                pickle.dump(cookies, f)
            logger.info(f"🍪 Cookies saved to {self.cookies_file}")
        except Exception as e:
            logger.error(f"Cookie save error: {e}")
    
    def load_cookies(self):
        """Load saved cookies for session persistence"""
        if not self.browser or not os.path.exists(self.cookies_file):
            return False
        try:
            with open(self.cookies_file, 'rb') as f:
                cookies = pickle.load(f)
            for cookie in cookies:
                self.browser.add_cookie(cookie)
            logger.info(f"🍪 Cookies loaded from {self.cookies_file}")
            return True
        except Exception as e:
            logger.error(f"Cookie load error: {e}")
            return False
    
    async def auto_login(self, target_url: str) -> bool:
        """Automatically login to 1337 Morocco"""
        if not STUDENT_EMAIL or not STUDENT_PASSWORD:
            logger.error("❌ Cannot auto-login: Missing email or password")
            return False
            
        logger.info("🔑 Starting automatic login process...")
        
        try:
            # Initialize browser if needed
            if not self.browser and not self.init_browser():
                return False
            
            # Stay on the main check-in page - login form is on the same page
            logger.info(f"🌐 Navigating to: {target_url}")
            self.browser.get(target_url)
            await aio_sleep.sleep(1.5)  # Reduced for faster login
            
            # Try to load existing cookies first
            if self.load_cookies():
                logger.info("🍪 Trying with saved session...")
                self.browser.refresh()
                await aio_sleep.sleep(2)
                
                # Check if already logged in
                if await self.check_if_logged_in():
                    logger.info("✅ Already logged in with saved session!")
                    return True
            
            # Look for login form elements
            email_selectors = [
                "input[type='email']",
                "input[name='email']", 
                "input[name='username']",
                "input[id*='email']",
                "input[id*='user']",
                "input[placeholder*='email']",
                "input[placeholder*='Email']"
            ]
            
            password_selectors = [
                "input[type='password']",
                "input[name='password']",
                "input[id*='password']",
                "input[placeholder*='password']",
                "input[placeholder*='Password']"
            ]
            
            # Find and fill email field
            email_field = None
            for selector in email_selectors:
                try:
                    email_field = WebDriverWait(self.browser, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    break
                except TimeoutException:
                    continue
                    
            if not email_field:
                logger.error("❌ Could not find email field")
                return False
                
            # Find and fill password field  
            password_field = None
            for selector in password_selectors:
                try:
                    password_field = self.browser.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
                    
            if not password_field:
                logger.error("❌ Could not find password field")
                return False
            
            # Fill credentials
            logger.info(f"📧 Filling email: {STUDENT_EMAIL[:3]}***@{STUDENT_EMAIL.split('@')[1]}")
            email_field.clear()
            email_field.send_keys(STUDENT_EMAIL)
            await aio_sleep.sleep(0.3)  # Faster form filling
            
            logger.info("🔑 Filling password: ****")
            password_field.clear()
            password_field.send_keys(STUDENT_PASSWORD)
            await aio_sleep.sleep(0.3)  # Faster form filling
            
            # Check and solve CAPTCHA if present
            captcha_solved = await self.detect_and_solve_captcha()
            if not captcha_solved:
                logger.warning("⚠️ CAPTCHA detected but could not solve - continuing anyway...")
            
            # Find and click login button (prioritize login over signup)
            login_button_selectors = [
                # Specific login button selectors (highest priority)
                "button[type='submit']",  # Most common login submit button
                "input[type='submit'][value*='login']",
                "input[type='submit'][value*='Login']",
                "input[type='submit'][value*='Log in']",
                "input[type='submit'][value*='Sign in']",
                "input[type='submit'][value*='Connexion']",
                "button:contains('Login')",
                "button:contains('Log in')",
                "button:contains('Sign in')",
                "button:contains('Connexion')",
                # Text-based selectors
                "button[class*='login']",
                "button[id*='login']",
                "input[class*='login']",
                "input[id*='login']",
                # Form-based selectors
                "form[class*='login'] button[type='submit']",
                "form[id*='login'] button[type='submit']",
                "form button[type='submit']",  # Generic form submit
                # Generic fallbacks (lowest priority)
                "input[type='submit']",
                "button[type='submit']"
            ]
            
            submit_button = None
            button_text = ""
            
            # Try to find login-specific buttons first
            for selector in login_button_selectors:
                try:
                    if ':contains(' in selector:
                        # Use XPath for text-based selectors
                        xpath_selector = selector.replace('button:contains(', "//button[contains(text(), ").replace("')", "')]")
                        submit_button = self.browser.find_element(By.XPATH, xpath_selector)
                    else:
                        submit_button = self.browser.find_element(By.CSS_SELECTOR, selector)
                    
                    # Check button text to avoid signup buttons
                    button_text = submit_button.text.lower()
                    logger.info(f"🔍 Found button with text: '{button_text}' using selector: {selector}")
                    
                    # Skip if it's clearly a signup button
                    if any(signup_word in button_text for signup_word in ['sign up', 'signup', 'register', 'create', 'inscription']):
                        logger.info(f"⚠️  Skipping signup button: '{button_text}'")
                        submit_button = None
                        continue
                    
                    # Found a good login button
                    if submit_button:
                        logger.info(f"✅ Selected login button: '{button_text}'")
                        break
                        
                except (NoSuchElementException, Exception) as e:
                    continue
            
            # If we still don't have a button, try to find all buttons and pick the best one
            if not submit_button:
                try:
                    all_buttons = self.browser.find_elements(By.TAG_NAME, "button")
                    all_buttons.extend(self.browser.find_elements(By.CSS_SELECTOR, "input[type='submit']"))
                    
                    for button in all_buttons:
                        try:
                            btn_text = button.text.lower() if button.text else button.get_attribute('value', '').lower()
                            
                            # Prioritize login-related buttons
                            if any(login_word in btn_text for login_word in ['login', 'log in', 'sign in', 'connexion', 'submit']):
                                if not any(signup_word in btn_text for signup_word in ['sign up', 'signup', 'register', 'create']):
                                    submit_button = button
                                    button_text = btn_text
                                    logger.info(f"✅ Found login button from all buttons: '{btn_text}'")
                                    break
                        except:
                            continue
                except:
                    pass
                    
            if submit_button:
                logger.info(f"🚀 Clicking login button: '{button_text}'")
                # Scroll to button to ensure it's visible
                self.browser.execute_script("arguments[0].scrollIntoView(true);", submit_button)
                await aio_sleep.sleep(0.2)  # Faster button interaction
                
                # Try clicking the button
                try:
                    submit_button.click()
                    logger.info("✅ Login button clicked successfully")
                except Exception as e:
                    logger.warning(f"⚠️  Regular click failed, trying JavaScript click: {e}")
                    self.browser.execute_script("arguments[0].click();", submit_button)
                    logger.info("✅ Login button clicked via JavaScript")
            else:
                logger.warning("⚠️  No suitable login button found - trying Enter key submission")
                password_field.send_keys("\n")
            
            # Wait for login to complete - OPTIMIZED
            await aio_sleep.sleep(2)  # Faster login verification
            
            # Check if login was successful
            if await self.check_if_logged_in():
                logger.info("✅ AUTO-LOGIN SUCCESS!")
                self.save_cookies()
                return True
            else:
                logger.error("❌ Auto-login failed - check credentials or CAPTCHA")
                return False
                
        except Exception as e:
            logger.error(f"❌ Auto-login error: {e}")
            return False
    
    async def check_if_logged_in(self) -> bool:
        """Check if currently logged in using browser"""
        if not self.browser:
            return False
            
        try:
            current_url = self.browser.current_url
            page_source = self.browser.page_source
            
            # URL-based checks
            if 'login' in current_url.lower() or 'signin' in current_url.lower():
                return False
                
            # Content-based checks
            login_required = any(indicator in page_source.lower() for indicator in [
                'sign in', 'login', 'connexion', 'mot de passe'
            ])
            
            authenticated = any(indicator in page_source.lower() for indicator in [
                'logout', 'déconnexion', 'dashboard', 'candidature', 'profile'
            ])
            
            return authenticated and not login_required
            
        except Exception as e:
            logger.error(f"Login check error: {e}")
            return False

    def get_random_headers(self) -> dict:
        """Generate realistic browser headers"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': random.choice(['en-US,en;q=0.9', 'fr-FR,fr;q=0.9', 'ar-MA,ar;q=0.9']),
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'Pragma': 'no-cache'
        }

    async def method_cloudscraper(self, url: str) -> tuple[str, int, str]:
        """Method 1: Enhanced CloudScraper - OPTIMIZED FOR SPEED"""
        try:
            self.cloudscraper.headers.update(self.get_random_headers())
            # Reduced delay for faster response
            if not FAST_MODE:
                await asyncio.sleep(random.uniform(0.1, 0.3))
            
            response = self.cloudscraper.get(url, timeout=10, allow_redirects=True)
            final_url = response.url if hasattr(response, 'url') else url
            return response.text, response.status_code, str(final_url)
        except Exception as e:
            logger.debug(f"CloudScraper failed: {e}")
            return "", 403, url

    async def method_curl_cffi(self, url: str) -> tuple[str, int, str]:
        """Method 2: curl-cffi (Go HTTP implementation) - OPTIMIZED"""
        try:
            headers = self.get_random_headers()
            if not FAST_MODE:
                await asyncio.sleep(random.uniform(0.1, 0.2))
            
            response = self.cf_session.get(
                url,
                headers=headers,
                timeout=8,
                impersonate="chrome110",  # Impersonate Chrome 110
                verify=False,
                allow_redirects=True
            )
            final_url = response.url if hasattr(response, 'url') else url
            return response.text, response.status_code, str(final_url)
        except Exception as e:
            logger.debug(f"curl-cffi failed: {e}")
            return "", 403, url

    async def method_httpx(self, url: str) -> tuple[str, int, str]:
        """Method 3: HTTPX with custom TLS - SPEED OPTIMIZED"""
        try:
            headers = self.get_random_headers()
            if not FAST_MODE:
                await asyncio.sleep(random.uniform(0.05, 0.15))
            
            response = await self.httpx_client.get(url, headers=headers)
            final_url = str(response.url) if hasattr(response, 'url') else url
            return response.text, response.status_code, final_url
        except Exception as e:
            logger.debug(f"HTTPX failed: {e}")
            return "", 403, url

    async def method_requests_html(self, url: str) -> tuple[str, int, str]:
        """Method 4: requests-html with JavaScript rendering (disabled)"""
        return "", 403, url  # Disabled due to dependency issues

    async def method_raw_curl(self, url: str) -> tuple[str, int, str]:
        """Method 5: Raw curl with randomized parameters"""
        try:
            headers = self.get_random_headers()
            if not FAST_MODE:
                await asyncio.sleep(random.uniform(0.5, 2))
            
            # Build curl command with randomized options - SPEED OPTIMIZED
            curl_cmd = [
                'curl', '-s', '-L', '--max-time', '8', '-w', '%{url_effective}\\n',
                '--user-agent', headers['User-Agent'],
                '--header', f"Accept: {headers['Accept']}",
                '--header', f"Accept-Language: {headers['Accept-Language']}",
                '--header', 'Connection: keep-alive',
                '--compressed',
                '--http2',
                '--tlsv1.2',
                url
            ]
            
            # Add random delays and retries
            if random.choice([True, False]):
                curl_cmd.extend(['--retry', '2', '--retry-delay', '1'])
            
            # Execute curl
            process = await asyncio.create_subprocess_exec(
                *curl_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                output = stdout.decode('utf-8', errors='ignore')
                # Split content and final URL (curl -w adds the URL at the end)
                lines = output.strip().split('\n')
                final_url = lines[-1] if lines else url
                content = '\n'.join(lines[:-1]) if len(lines) > 1 else output
                
                # Estimate status code from content
                status = 200 if len(content) > 1000 and "cloudflare" not in content.lower() else 403
                return content, status, final_url
            else:
                return "", 403, url
                
        except Exception as e:
            logger.debug(f"Raw curl failed: {e}")
            return "", 403, url

    async def method_distributed_requests(self, url: str) -> tuple[str, int, str]:
        """Method 6: Distributed requests through multiple endpoints"""
        try:
            # Try using public proxy APIs or different request patterns
            endpoints = [
                # Different approach: try through different domains/paths
                url.replace('admission.1337.ma', 'www.admission.1337.ma'),
                url.replace('https://', 'http://'),  # Try HTTP
                f"{url}?t={int(time.time())}",  # Add timestamp
                f"{url}?v={random.randint(1, 999)}",  # Add version param
            ]
            
            for endpoint in endpoints:
                try:
                    headers = self.get_random_headers()
                    await asyncio.sleep(random.uniform(1, 2))
                    
                    response = await self.httpx_client.get(endpoint, headers=headers)
                    if response.status_code == 200:
                        final_url = str(response.url) if hasattr(response, 'url') else endpoint
                        return response.text, response.status_code, final_url
                except:
                    continue
                    
            return "", 403, url
        except Exception as e:
            logger.debug(f"Distributed requests failed: {e}")
            return "", 403, url

    async def bypass_attempt(self, url: str) -> tuple[str, int, str, str]:
        """Try all bypass methods simultaneously"""
        logger.debug(f"🚀 Launching bypass request...")  # Reduced logging for routine checks
        
        # List of all methods to try - PRIORITIZED BY SPEED
        methods = [
            ("HTTPX", self.method_httpx),           # Fastest - async native
            ("CloudScraper", self.method_cloudscraper),  # Fast and reliable
            ("curl-cffi", self.method_curl_cffi),   # Good balance
            ("Raw curl", self.method_raw_curl),     # System native
            ("Distributed", self.method_distributed_requests),
            ("requests-html", self.method_requests_html)  # Slowest - disabled
        ]
        
        # If we had a successful method before, try it first
        if self.success_method:
            methods = [m for m in methods if m[0] == self.success_method] + \
                     [m for m in methods if m[0] != self.success_method]
        
        # ULTRA SPEED OPTIMIZATION: Use only the working method
        if self.success_method:
            # Use the proven working method directly
            working_method = next((m for m in methods if m[0] == self.success_method), None)
            if working_method:
                method_name, method_func = working_method
                try:
                    logger.debug(f"⚡ DIRECT: Using {method_name} (proven working)...")
                    content, status, final_url = await method_func(url)
                    
                    if status == 200 and len(content) > 500:
                        if not any(block_indicator in content.lower() for block_indicator in [
                            "attention required", "cloudflare", "please enable javascript",
                            "ddos protection", "security check", "just a moment"
                        ]):
                            logger.debug(f"✅ {method_name} SUCCESS! Got real content ({len(content)} chars)")
                            logger.debug(f"🎯 Final URL: {final_url}")
                            return content, status, method_name, final_url
                except Exception as e:
                    logger.warning(f"⚠️ {method_name} failed, trying alternatives: {e}")
                    # Method failed, clear success method and try others
                    self.success_method = None
        
        # Only try other methods if no proven method or it failed
        logger.info("🔄 Finding working method...")
        if FAST_MODE:
            # Run methods concurrently for fastest success
            tasks = [method_func(url) for _, method_func in methods]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for (method_name, _), result in zip(methods, results):
                try:
                    if isinstance(result, Exception):
                        continue
                    content, status, final_url = result
                    if status == 200 and len(content) > 500 and not any(b in content.lower() for b in [
                        "attention required", "cloudflare", "please enable javascript",
                        "ddos protection", "security check", "just a moment"
                    ]):
                        logger.info(f"✅ {method_name} SUCCESS! Got real content ({len(content)} chars)")
                        logger.info(f"🎯 Final URL: {final_url}")
                        self.success_method = method_name
                        logger.info(f"💾 Saved {method_name} as preferred method for future requests")
                        return content, status, method_name, final_url
                except Exception:
                    continue
        else:
            for method_name, method_func in methods:
                try:
                    logger.info(f"🔄 Trying {method_name}...")
                    content, status, final_url = await method_func(url)
                    
                    if status == 200 and len(content) > 500:
                        if not any(block_indicator in content.lower() for block_indicator in [
                            "attention required", "cloudflare", "please enable javascript",
                            "ddos protection", "security check", "just a moment"
                        ]):
                            logger.info(f"✅ {method_name} SUCCESS! Got real content ({len(content)} chars)")
                            logger.info(f"🎯 Final URL: {final_url}")
                            self.success_method = method_name  # Remember this works
                            logger.info(f"💾 Saved {method_name} as preferred method for future requests")
                            return content, status, method_name, final_url
                            
                except Exception as e:
                    logger.debug(f"❌ {method_name} error: {e}")
                
        logger.warning("🚱 All bypass methods failed")
        return "", 403, "all_failed", url

    def extract_meaningful_content(self, html_content: str) -> str:
        """Extract meaningful content, ignoring dynamic/random elements"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove dynamic elements
            for element in soup(["script", "style", "noscript", "meta"]):
                element.decompose()
            
            # Remove CSRF tokens and session data
            import re
            for element in soup.find_all(attrs={'name': re.compile(r'csrf|token|session', re.I)}):
                element.decompose()
            
            text = soup.get_text(separator=' ', strip=True)
            
            # Clean the text - remove tokens, random strings
            import re
            # Remove hex tokens (like CSRF tokens)
            text = re.sub(r'\b[a-f0-9]{16,}\b', '', text, flags=re.I)
            # Remove numeric tokens
            text = re.sub(r'\b\d{10,}\b', '', text)
            # Clean whitespace
            text = ' '.join(text.split())
            
            return text.lower()
            
        except Exception as e:
            logger.error(f"Content extraction error: {e}")
            return html_content.lower() if html_content else ""
    
    def check_login_status(self, content: str, current_url: str = None) -> bool:
        """Check if we're properly logged in"""
        # Check URL patterns first
        if current_url:
            logger.debug(f"📱 Current URL: {current_url}")  # Less verbose for routine checks
            if 'login' in current_url.lower() or 'signin' in current_url.lower():
                logger.warning("❌ REDIRECTED TO LOGIN PAGE - Not logged in!")
                return False
            else:
                logger.debug(f"🌐 Staying on target URL: {current_url.split('/')[-1]}")  # Less verbose
        
        # Look for login indicators in content
        login_required = any(indicator in content.lower() for indicator in [
            'login', 'connexion', 'sign in', 'authenticate', 'mot de passe', 'password',
            'se connecter', 'identifiant', 'email', 'username', 'log in'
        ])
        
        # Look for authenticated user indicators  
        authenticated = any(indicator in content.lower() for indicator in [
            'dashboard', 'profile', 'logout', 'déconnexion', 'candidature', 'check-in',
            'bienvenue', 'welcome', 'mon compte', 'my account', 'book online', 'booking',
            'appointment', 'schedule'
        ])
        
        # Look for 1337 Morocco specific content or general authenticated indicators
        site_indicators = any(indicator in content.lower() for indicator in [
            '1337', 'ecole 42', 'piscine', 'student', 'étudiant', 'candidature',
            'admission', 'morocco', 'maroc', 'check-in', 'school 42'
        ])
        
        # More detailed content analysis
        logger.info(f"🔍 Content analysis: login_required={login_required}, authenticated={authenticated}, site_indicators={site_indicators}")
        
        if login_required and not authenticated:
            logger.warning("❌ LOGIN REQUIRED - Login form/fields detected")
            logger.info("🔍 Content contains login indicators but no authenticated content")
            return False
        elif authenticated or site_indicators:
            logger.info("✅ LOGGED IN - Authenticated content detected")
            return True
        elif len(content) < 500:
            logger.warning("❌ SUSPICIOUS - Very short page content (likely error/login page)")
            return False
        else:
            logger.warning("🤔 LOGIN STATUS UNCLEAR - No clear login or auth indicators")
            logger.warning("🚨 ASSUME NOT LOGGED IN - Better safe than sorry!")
            return False  # Changed to assume NOT logged in if unclear
    
    def check_for_checkin_availability(self, content: str) -> bool:
        """Check if check-in is actually available"""
        content_lower = content.lower()
        
        # CAF ticketing overflow specific logic
        if 'tickets.cafonline.com' in SITE_URL or 'cafonline' in content_lower:
            caf_unavailable_phrases = [
                'ticketing temporarily unavailable',
                'billetterie temporairement inaccessible',
                'due to high demand, all available tickets are already being purchased'
            ]
            if any(p in content_lower for p in caf_unavailable_phrases):
                return False
            if any(word in content_lower for word in ['ticket', 'tickets', 'billet', 'billets', 'purchase', 'acheter']):
                return True
            # Fall through to generic heuristics below
        
        # Positive indicators (check-in is available)
        positive_indicators = [
            'check-in available', 'check-in ouvert', 'inscription disponible',
            'places disponibles', 'spots available', 'you can check-in',
            'procéder au check-in', 'check-in now'
        ]
        
        # Negative indicators (check-in is closed)
        negative_indicators = [
            'check-in closed', 'check-in fermé', 'pas de places',
            'no spots available', 'complet', 'full', 'check-in pas encore',
            'not yet open', 'coming soon'
        ]
        
        # Check for positive indicators
        has_positive = any(indicator in content_lower for indicator in positive_indicators)
        has_negative = any(indicator in content_lower for indicator in negative_indicators)
        
        if has_positive and not has_negative:
            return True
        elif has_negative:
            return False
        else:
            # Look for general check-in keywords with availability context
            checkin_mentioned = any(word in content_lower for word in ['check-in', 'checkin', 'inscription'])
            available_mentioned = any(word in content_lower for word in ['available', 'disponible', 'open', 'ouvert'])
            
            return checkin_mentioned and available_mentioned

    async def monitor_page(self):
        """Monitor the page using all available methods"""
        try:
            # Announce checking steps
            logger.info("🔎 Checking availability and changes...")
            # Try bypass
            content, status, method, final_url = await self.bypass_attempt(SITE_URL)
            
            if status != 200 or not content:
                logger.error(f"❌ All methods failed - Status: {status}")
                return False
            
            # Normalize URL for change detection (ignore query/fragment)
            def _url_key(u: str) -> str:
                try:
                    parsed = urlparse(u)
                    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                except Exception:
                    return u

            current_url_key = _url_key(final_url)

            # Show current status (reduced logging for routine checks)
            if not hasattr(self, '_status_shown') or self._status_shown != method:
                logger.info(f"🌐 ===== CURRENT STATUS ======")
                logger.info(f"🎯 Target URL: {SITE_URL}")
                logger.info(f"🎯 Final URL: {final_url}")
                logger.info(f"🔧 Method used: {method}")
                self._status_shown = method
            
            # Check login status with URL info
            is_logged_in = self.check_login_status(content, final_url)
            if not is_logged_in:
                if DISABLE_AUTO_LOGIN:
                    logger.info("ℹ️ Not logged in; auto-login disabled. Continuing read-only monitoring.")
                else:
                    logger.error("❌ LOGIN REQUIRED - Attempting auto-login...")
                    
                    # Try automatic login if credentials are available
                    if STUDENT_EMAIL and STUDENT_PASSWORD and SELENIUM_AVAILABLE:
                        logger.info("🔑 Auto-login credentials available - attempting login...")
                        login_success = await self.auto_login(SITE_URL)
                        
                        if login_success:
                            logger.info("🎉 AUTO-LOGIN SUCCESS! Continuing monitoring...")
                            # Recheck the page after successful login
                            content, status, method, final_url = await self.bypass_attempt(SITE_URL)
                            if status == 200 and content:
                                is_logged_in = True
                        else:
                            logger.error("❌ AUTO-LOGIN FAILED - Manual login may be required")
                    else:
                        logger.warning("⚠️ No auto-login credentials or Selenium unavailable")
                        logger.info("ℹ️ Continuing read-only monitoring.")
            else:
                logger.info("✅ LOGIN STATUS: Successfully authenticated!")
            
            logger.info(f"🌐 =============================\n")
            
            # Extract meaningful content (ignore tokens/dynamic elements)
            meaningful_content = self.extract_meaningful_content(content)
            
            # Log success
            logger.info(f"📄 Page fetched via {method} - Content: {len(meaningful_content)} chars")
            logger.info(f"🔗 Current page: {final_url}")
            
            # Check for changes
            if self.previous_content is None:
                self.previous_content = meaningful_content
                self.previous_url_key = current_url_key
                logger.info("🎯 Initial content captured - monitoring for changes...")
                logger.info(f"🔍 Monitoring 1337 Morocco via {method} bypass")
                
                # Check if check-in is currently available
                if self.check_for_checkin_availability(meaningful_content):
                    urgent_msg = "🚨 CHECK-IN MIGHT BE AVAILABLE NOW! Verify manually: " + SITE_URL
                    logger.critical(urgent_msg)
                    await self.send_all_notifications(urgent_msg, urgent=True)
                    # Open browser for immediate action
                    try:
                        self.open_in_chrome_guest(SITE_URL)
                    except Exception as e:
                        logger.warning(f"Failed to open Chrome Guest: {e}")
                    
            elif self.previous_content != meaningful_content or (self.previous_url_key and self.previous_url_key != current_url_key):
                changes = self.find_meaningful_changes(self.previous_content, meaningful_content)
                # Add URL change note if path changed
                if self.previous_url_key and self.previous_url_key != current_url_key:
                    changes = (changes + " || " if changes else "") + f"URL changed: {self.previous_url_key} → {current_url_key}"
                
                if changes:
                    logger.info(f"📝 Content changed: {changes}")
                    
                    # Check if this indicates check-in availability
                    if self.check_for_checkin_availability(meaningful_content):
                        urgent_msg = "🚨 CHECK-IN APPEARS AVAILABLE! Check website NOW: " + SITE_URL
                        logger.critical(urgent_msg)
                        await self.send_all_notifications(urgent_msg, urgent=True)
                        # Open browser for immediate action
                        try:
                            self.open_in_chrome_guest(SITE_URL)
                        except Exception as e:
                            logger.warning(f"Failed to open Chrome Guest: {e}")
                    else:
                        # Only send non-urgent alerts for significant changes
                        if len(changes) > 50:  # Only for substantial changes
                            change_msg = f"Minor page update detected via {method}"
                            logger.info(change_msg)
                            # Don't send notifications for minor changes
                        
                    # Save change log
                    await self.log_change(changes, method, final_url)
                        
                self.previous_content = meaningful_content
                self.previous_url_key = current_url_key
            else:
                logger.debug(f"✅ No meaningful changes detected via {method}")
            
            logger.info("✅ Check completed. Waiting for next cycle...")
            return True
            
        except Exception as e:
            logger.error(f"Monitor error: {e}")
            return False

    def find_meaningful_changes(self, old_content: str, new_content: str) -> str:
        """Find meaningful changes between content, ignoring noise"""
        try:
            # Split into sentences for better context
            old_sentences = set(s.strip() for s in old_content.split('.') if len(s.strip()) > 10)
            new_sentences = set(s.strip() for s in new_content.split('.') if len(s.strip()) > 10)
            
            added_sentences = new_sentences - old_sentences
            removed_sentences = old_sentences - new_sentences
            
            # Filter out noise (short changes, technical stuff)
            import re
            def is_meaningful_sentence(sentence):
                # Skip very short changes
                if len(sentence) < 15:
                    return False
                # Skip technical/random strings
                if re.match(r'^[a-f0-9\s\-_]+$', sentence.lower()):
                    return False
                # Skip if it's mostly numbers/symbols
                if len(re.sub(r'[^a-zA-Z]', '', sentence)) < len(sentence) * 0.3:
                    return False
                return True
            
            meaningful_added = {s for s in added_sentences if is_meaningful_sentence(s)}
            meaningful_removed = {s for s in removed_sentences if is_meaningful_sentence(s)}
            
            changes = []
            if meaningful_added:
                # Show first 2 most relevant additions
                relevant_added = sorted(meaningful_added, key=len, reverse=True)[:2]
                changes.append(f"Added: {' | '.join(relevant_added)}")
            if meaningful_removed:
                # Show first 2 most relevant removals
                relevant_removed = sorted(meaningful_removed, key=len, reverse=True)[:2]
                changes.append(f"Removed: {' | '.join(relevant_removed)}")
                
            return " || ".join(changes) if changes else ""
            
        except Exception as e:
            logger.error(f"Change detection error: {e}")
            return "Change detected (parsing error)"

    async def log_change(self, changes: str, method: str, final_url: str = None):
        """Log changes to file"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "changes": changes,
                "method": method,
                "target_url": SITE_URL,
                "final_url": final_url or SITE_URL
            }
            
            async with aiofiles.open("logs/changes.json", "a") as f:
                await f.write(json.dumps(log_entry) + "\n")
                
        except Exception as e:
            logger.error(f"Log error: {e}")

    async def send_all_notifications(self, message: str, urgent: bool = False):
        """Send notifications through all channels"""
        try:
            tasks = []
            if self.twilio_client:
                tasks.append(self.send_sms(message, urgent))
            if bot:
                tasks.append(self.send_discord(message, urgent))
                
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
                
        except Exception as e:
            logger.error(f"Notification error: {e}")

    async def send_sms(self, message: str, urgent: bool = False):
        """Send SMS notification - ONLY for urgent check-in alerts to avoid daily limit"""
        try:
            # Only send SMS for truly urgent check-in alerts to avoid hitting daily limit
            if not urgent:
                logger.info("📱 SMS skipped (non-urgent) - saving for check-in alerts only")
                return
                
            if self.twilio_client and TWILIO_PHONE_NUMBER and TARGET_PHONE_NUMBER:
                sms_body = f"🚨 URGENT 1337 ALERT 🚨\n{message}\nURL: {SITE_URL}"
                
                msg = self.twilio_client.messages.create(
                    body=sms_body[:1600],  # SMS length limit
                    from_=TWILIO_PHONE_NUMBER,
                    to=TARGET_PHONE_NUMBER
                )
                logger.info(f"📱 SMS sent: {msg.sid}")
                
                # Make phone call for urgent alerts
                if urgent:
                    try:
                        call = self.twilio_client.calls.create(
                            twiml=f'<Response><Say voice="woman">Urgent 1337 Morocco alert. {message}. Check the website immediately.</Say></Response>',
                            to=TARGET_PHONE_NUMBER,
                            from_=TWILIO_PHONE_NUMBER
                        )
                        logger.info(f"📞 Call initiated: {call.sid}")
                    except Exception as e:
                        logger.error(f"Call failed: {e}")
                        
        except Exception as e:
            error_msg = str(e)
            if "exceeded the 9 daily messages limit" in error_msg or "63038" in error_msg:
                logger.warning(f"⚠️  Twilio daily SMS limit exceeded - SMS notifications disabled until tomorrow")
                logger.info("💬 Discord notifications still active for alerts")
            else:
                logger.error(f"SMS error: {e}")

    async def send_discord(self, message: str, urgent: bool = False):
        """Send Discord notification"""
        try:
            if not bot or not DISCORD_USER_ID:
                return
                
            user = bot.get_user(DISCORD_USER_ID)
            if user:
                discord_msg = f"🚨 **URGENT 1337 ALERT** 🚨\n{message}\n\n🔗 {SITE_URL}\n⚡ **CHECK NOW** ⚡" if urgent else f"📢 1337 Monitor\n{message}\n🔗 {SITE_URL}"
                await user.send(discord_msg[:2000])  # Discord length limit
                logger.info("💬 Discord DM sent")
                
        except Exception as e:
            logger.error(f"Discord error: {e}")

    async def cleanup(self):
        """Cleanup resources"""
        try:
            if hasattr(self, 'httpx_client'):
                await self.httpx_client.aclose()
            # if hasattr(self, 'html_session'):
            #     self.html_session.close()
            
            # Cleanup browser
            if hasattr(self, 'browser') and self.browser:
                try:
                    logger.info("🔄 Closing browser...")
                    self.browser.quit()
                except Exception as e:
                    logger.error(f"Browser cleanup error: {e}")
                    
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

async def test_single_check():
    """Test function - single check to show current status"""
    monitor = UltimateBypassMonitor()
    
    try:
        logger.info("🎆 === 1337 MOROCCO STATUS CHECK ===")
        logger.info(f"📡 Target: {SITE_URL}")
        logger.info("🛡️  Testing all bypass methods...\n")
        
        success = await monitor.monitor_page()
        
        if success:
            logger.info("✨ Status check completed successfully!")
        else:
            logger.error("❌ Status check failed - all methods blocked")
            
    except Exception as e:
        logger.error(f"Test error: {e}")
    finally:
        await monitor.cleanup()

async def main():
    """Main monitoring loop"""
    monitor = UltimateBypassMonitor()
    
    try:
        logger.info("🚀 Starting Ultimate 1337 Morocco Monitor")
        logger.info(f"📡 Target: {SITE_URL}")
        logger.info(f"⏱️  Interval: {REFRESH_INTERVAL}s")
        logger.info("🛡️  Multi-vector bypass system active")
        
        # Start Discord bot if configured
        if bot and DISCORD_BOT_TOKEN:
            asyncio.create_task(bot.start(DISCORD_BOT_TOKEN))
            await asyncio.sleep(2)
        
        # Main monitoring loop with optional Chrome guest refresh
        consecutive_failures = 0
        last_chrome_open = 0.0
        last_visible_refresh = 0.0
        while True:
            try:
                now = time.time()
                if CHROME_GUEST_REFRESH_SECONDS > 0 and now - last_chrome_open >= CHROME_GUEST_REFRESH_SECONDS:
                    try:
                        monitor.open_in_chrome_guest(SITE_URL)
                        last_chrome_open = now
                        logger.info(f"🧭 Refreshed visible Chrome Guest tab (every {CHROME_GUEST_REFRESH_SECONDS}s)")
                    except Exception as e:
                        logger.warning(f"Chrome Guest refresh failed: {e}")

                if VISIBLE_REFRESH_SECONDS > 0 and monitor.visible_refresh_ready and now - last_visible_refresh >= VISIBLE_REFRESH_SECONDS:
                    try:
                        monitor.browser.refresh()
                        last_visible_refresh = now
                        logger.info(f"🔁 Refreshed visible Selenium tab (every {VISIBLE_REFRESH_SECONDS}s)")
                    except Exception as e:
                        logger.warning(f"Selenium visible refresh failed: {e}")

                success = await monitor.monitor_page()
                
                if success:
                    consecutive_failures = 0
                    logger.info(f"✅ Monitor cycle completed - next check in {REFRESH_INTERVAL}s")
                else:
                    consecutive_failures += 1
                    logger.warning(f"❌ Monitor failed ({consecutive_failures} consecutive failures)")
                    
                    # Increase delay after failures
                    if consecutive_failures > 3:
                        delay = REFRESH_INTERVAL * 2
                        logger.info(f"⏳ Extended delay: {delay}s due to failures")
                        await asyncio.sleep(delay)
                        continue
                
                await asyncio.sleep(REFRESH_INTERVAL)
                
            except KeyboardInterrupt:
                logger.info("🛑 Monitor stopped by user")
                break
            except Exception as e:
                logger.error(f"Main loop error: {e}")
                await asyncio.sleep(REFRESH_INTERVAL * 2)
                
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        await monitor.cleanup()
        if bot:
            await bot.close()

if __name__ == "__main__":
    import sys
    
    # Check for test mode
    test_mode = len(sys.argv) > 1 and sys.argv[1] == '--test'
    
    # If auto-login is disabled, allow running without credentials
    if not DISABLE_AUTO_LOGIN and (not STUDENT_EMAIL or not STUDENT_PASSWORD):
        logger.error("❌ Missing STUDENT_EMAIL or STUDENT_PASSWORD and auto-login is enabled")
        exit(1)
    
    try:
        if test_mode:
            asyncio.run(test_single_check())
        else:
            asyncio.run(main())
    except Exception as e:
        logger.error(f"Application error: {e}")
