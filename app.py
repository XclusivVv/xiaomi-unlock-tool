import subprocess
import sys
import os
import hashlib
import random
import time
from datetime import datetime, timezone, timedelta
import tkinter as tk
from tkinter import messagebox
import webbrowser
import re
import threading

# Check and install customtkinter
try:
    import customtkinter as ctk
except ImportError:
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "customtkinter"])
        import customtkinter as ctk
    except Exception as e:
        messagebox.showerror(
            "Installation Error",
            f"Failed to install customtkinter:\n{e}\n\nTry to install manually:\npip install customtkinter"
        )
        sys.exit(1)

# Check remaining dependencies
try:
    import ntplib
    import pytz
    import urllib3
    import json
    import statistics
    from icmplib import ping
    import requests
except ImportError as e:
    missing_module = str(e).split("'")[1]
    messagebox.showerror(
        "Import Error",
        f"Failed to import module: {missing_module}\n\nInstall it with:\npip install {missing_module}"
    )
    sys.exit(1)

# Configure customtkinter appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

CURRENT_VERSION = "4.5"
GITHUB_REPO_URL = "https://github.com/AsInsideOut/miunlocktool/releases/tag/Stable"

# Dark theme color scheme
class ColorScheme:
    # Primary colors - Charcoal & Gray (softer contrast)
    DARK_BG = "#111827"        # Dark charcoal
    DARKER_BG = "#0d1421"      # Darker charcoal
    CARD_BG = "#151f2e"        # Softer dark gray cards (was #1f2937)
    BORDER = "#2d3748"         # Softer gray borders (was #374151)
    
    # Accent colors - Blue & Gray
    PRIMARY = "#3b82f6"        # Blue
    PRIMARY_HOVER = "#2563eb"  # Darker blue
    SECONDARY = "#6b7280"      # Gray
    SECONDARY_HOVER = "#4b5563" # Darker gray
    
    # Status colors
    SUCCESS = "#22c55e"        # Green
    SUCCESS_HOVER = "#16a34a"  # Darker green
    DANGER = "#ef4444"         # Red
    DANGER_HOVER = "#dc2626"   # Darker red
    WARNING = "#f59e0b"        # Amber
    
    # Text colors
    TEXT_PRIMARY = "#f9fafb"   # Very light gray
    TEXT_SECONDARY = "#d1d5db" # Light gray
    TEXT_MUTED = "#9ca3af"     # Medium gray
    
    # Special backgrounds
    LOG_BG = "#0d1421"         # Dark log area
    HEADER_BG = "#151f2e"      # Header matches cards

ntp_servers = [
    "time1.google.com", "time2.google.com", "time3.google.com",
    "time4.google.com", "time.android.com", "time.aws.com",
    "time.google.com", "time.cloudflare.com"
]

MI_SERVERS = ['sgp-api.buy.mi.com', '20.157.18.26']

os.system('cls' if os.name == 'nt' else 'clear')

class HTTP11Session:
    def __init__(self):
        self.http = urllib3.PoolManager(
            maxsize=10,
            retries=True,
            timeout=urllib3.Timeout(connect=2.0, read=15.0),
            headers={}
        )

    def make_request(self, method, url, headers=None, body=None):
        try:
            request_headers = {}
            if headers:
                request_headers.update(headers)
                request_headers['Content-Type'] = 'application/json; charset=utf-8'
            
            if method == 'POST':
                if body is None:
                    body = '{"is_retry":true}'.encode('utf-8')
                request_headers['Content-Length'] = str(len(body))
                request_headers['Accept-Encoding'] = 'gzip, deflate, br'
                request_headers['User-Agent'] = 'okhttp/4.12.0'
                request_headers['Connection'] = 'keep-alive'
            
            response = self.http.request(
                method,
                url,
                headers=request_headers,
                body=body,
                preload_content=False
            )
            return response
        except Exception:
            return None

def _on_key_release(event):
    ctrl = (event.state & 0x4) != 0
    if event.keycode == 88 and ctrl and event.keysym.lower() != "x":
        event.widget.event_generate("<<Cut>>")
    if event.keycode == 86 and ctrl and event.keysym.lower() != "v":
        event.widget.event_generate("<<Paste>>")
    if event.keycode == 67 and ctrl and event.keysym.lower() != "c":
        event.widget.event_generate("<<Copy>>")

class UpdateChecker:
    @staticmethod
    def check_for_updates():
        try:
            current_version = CURRENT_VERSION
            api_url = "https://api.github.com/repos/AsInsideOut/miunlocktool/releases"
            
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                releases = response.json()
                if releases:
                    latest_tag = releases[0].get('tag_name', '')
                    match = re.search(r'(\d+\.\d+)', latest_tag)
                    if match:
                        latest_num = match.group(1)
                        current_num = re.search(r'(\d+\.\d+)', current_version)
                        if current_num and latest_num > current_num:
                            return latest_num, latest_tag
            return None, "Current version is up to date"
        except Exception as e:
            return None, f"Error: {str(e)}"

class InstructionsWindow(ctk.CTkToplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.parent = parent
        self.app = app
        self.title("Instructions and Settings")
        self.geometry("1000x700")
        self.resizable(False, False)
        
        # FIX: Use after_idle instead of grab_set in __init__
        self.after_idle(self.grab_set)
        
        self.skip_cookie_check_var = ctk.BooleanVar(value=False)
        self.default_ping_var = ctk.StringVar(value="300")
        self.cookies_expanded = False
        
        self.about_text = None
        self.general_text = None
        self.firefox_text = None
        self.chrome_text = None
        self.brave_text = None
        self.trouble_text = None
        self.authors_text = None
        
        self.create_widgets()
    
    def create_widgets(self):
        self.main_frame = ctk.CTkFrame(self, fg_color=ColorScheme.DARK_BG)
        self.main_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        self.sidebar_frame = ctk.CTkFrame(self.main_frame, fg_color=ColorScheme.DARKER_BG, width=200)
        self.sidebar_frame.pack(side="left", fill="y", padx=0, pady=0)
        self.sidebar_frame.pack_propagate(False)
        
        content_frame = ctk.CTkFrame(self.main_frame, fg_color=ColorScheme.DARK_BG)
        content_frame.pack(side="right", fill="both", expand=True, padx=0, pady=0)
        
        header = ctk.CTkFrame(content_frame, fg_color=ColorScheme.PRIMARY)
        header.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            header,
            text="Instructions and Settings",
            font=("Arial", 18, "bold"),
            text_color=ColorScheme.TEXT_PRIMARY
        ).pack(pady=12)
        
        self.create_sidebar_buttons()
        
        self.content_area = ctk.CTkFrame(content_frame, fg_color=ColorScheme.DARK_BG)
        self.content_area.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.show_about_content()
    
    def create_sidebar_buttons(self):
        buttons = [
            ("About", self.show_about_content),
            ("Requirements", self.show_general_content),
            ("Troubleshooting", self.show_trouble_content),
            ("Authors", self.show_authors_content),
            ("Settings", self.show_settings_content),
        ]
        
        for text, cmd in buttons:
            btn = ctk.CTkButton(
                self.sidebar_frame,
                text=text,
                font=("Arial", 12, "bold"),
                height=40,
                fg_color=ColorScheme.DARKER_BG,
                hover_color=ColorScheme.PRIMARY,
                text_color=ColorScheme.PRIMARY,
                border_width=2,
                border_color=ColorScheme.PRIMARY,
                command=cmd
            )
            btn.pack(fill="x", padx=10, pady=5)
        
        # Cookies expandable section
        self.cookies_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="▶ Get Cookies",
            font=("Arial", 12, "bold"),
            height=40,
            fg_color=ColorScheme.DARKER_BG,
            hover_color=ColorScheme.PRIMARY,
            text_color=ColorScheme.PRIMARY,
            border_width=2,
            border_color=ColorScheme.PRIMARY,
            command=self.toggle_cookies_section
        )
        self.cookies_btn.pack(fill="x", padx=10, pady=5)
        
        self.cookies_sub_frame = ctk.CTkFrame(self.sidebar_frame, fg_color=ColorScheme.DARKER_BG)
        
        for text, cmd in [("Firefox", self.show_firefox_content), ("Chrome/Brave", self.show_chrome_content)]:
            btn = ctk.CTkButton(
                self.cookies_sub_frame,
                text=text,
                font=("Arial", 11),
                height=32,
                fg_color=ColorScheme.CARD_BG,
                hover_color=ColorScheme.SECONDARY,
                text_color=ColorScheme.SECONDARY,
                border_width=1,
                border_color=ColorScheme.SECONDARY,
                command=cmd
            )
            btn.pack(fill="x", padx=15, pady=2)
    
    def toggle_cookies_section(self):
        if self.cookies_expanded:
            self.cookies_sub_frame.pack_forget()
            self.cookies_btn.configure(text="▶ Get Cookies")
            self.cookies_expanded = False
        else:
            self.cookies_sub_frame.pack(fill="x", pady=(0, 5), after=self.cookies_btn)
            self.cookies_btn.configure(text="▼ Get Cookies")
            self.cookies_expanded = True
    
    def clear_content_area(self):
        for widget in self.content_area.winfo_children():
            widget.destroy()
    
    def create_text_frame(self, content):
        frame = ctk.CTkFrame(self.content_area, fg_color=ColorScheme.CARD_BG, corner_radius=10)
        frame.pack(fill="both", expand=True)
        
        textbox = ctk.CTkTextbox(
            frame,
            wrap="word",
            font=("Arial", 12),
            fg_color=ColorScheme.CARD_BG,
            text_color=ColorScheme.TEXT_PRIMARY,
            border_width=0,
            cursor="arrow"
        )
        textbox.pack(fill="both", expand=True, padx=15, pady=15)
        textbox.insert("1.0", content)
        textbox.configure(state='disabled')
        return textbox
    
    def show_about_content(self):
        self.clear_content_area()
        self.about_text = self.create_text_frame("""Xiaomi Unlock Tool v4.5

An automated tool for submitting bootloader unlock requests for Xiaomi devices running Global HyperOS.

Features:
• Automatic time synchronization with Beijing timezone
• Intelligent ping measurement for optimal timing
• Manual mode for custom submission times
• Cookie validation and account status checking
• Real-time execution logging
• Built-in update checker

How It Works:
The tool synchronizes with Beijing time servers and submits your unlock request at the precise moment needed. It measures network latency to ensure accurate timing.

Auto Mode:
Waits until 23:59:48 Beijing time, measures ping, calculates optimal submission time, and submits automatically.

Manual Mode:
You specify the submission second (58.5-59.8) and the tool submits at exactly 23:59:[your choice].

Developers:
• Space (@gloryoflunar)
• New gen / QcomSnap8Gen1 (@New_g3n)  
• Zdarova ilia (@Xander85)

Based on: Vierta

Links:
GitHub: https://github.com/AsInsideOut/miunlocktool
Telegram: https://t.me/miunlocktoolnew""")
    
    def show_general_content(self):
        self.clear_content_area()
        self.general_text = self.create_text_frame("""Requirements for Bootloader Unlock

You MUST meet ALL of these requirements to successfully unlock:

1. Account Age: 30+ Days
Your Mi account must be at least 30 days old. New accounts cannot submit requests. This is a hard requirement.

2. Global Region
Your Mi Community account must be set to Global region. Chinese (CN) region accounts cannot unlock via this method.

3. Device Compatibility
All Xiaomi devices with Global variants support unlocking. Chinese (CN) variants cannot be unlocked.

Check your device model:
• Global models: Can unlock (e.g., 2304F, 2312F)
• China models: Cannot unlock (model ends with CN)

4. Operating System
Your device must run HyperOS 1, 2, or 3. Ensure your system is fully updated.

5. Device Binding
Your device must be bound to your Mi account in Settings > About phone > Mi Unlock

Before Starting:
✓ Verify account is 30+ days old
✓ Switch Mi Community to Global
✓ Check device model is Global variant
✓ Update HyperOS to latest version
✓ Bind device to your account
✓ Extract fresh authentication cookie

Common Mistakes:
✗ Using account less than 30 days old
✗ Using Chinese region Mi Community account
✗ Trying with China (CN) variant device
✗ Using expired cookies
✗ Device not properly bound to account""")
    
    def show_firefox_content(self):
        self.clear_content_area()
        self.firefox_text = self.create_text_frame("""Getting Cookies - Firefox

Step 1: Install Cookie Editor Extension
1. Go to Firefox Add-ons store
2. Search for "Cookie Editor"
3. Click "Add to Firefox"
4. Allow the extension

Step 2: Prepare Your Account
1. Log out completely
2. Visit https://mi.com or https://new.c.mi.com/global
3. Log in with your Mi account

Step 3: Extract the Cookie Token
1. Click the Cookie Editor icon in your toolbar
2. Search for "new_bbs_serviceToken" or "popRunToken"
3. Copy the entire value
4. Paste it into the tool's cookie field

Important Notes:
• Use the GLOBAL version of Mi Community
• Keep your token private - never share it
• Tokens expire - get a fresh one if errors occur
• All times use Beijing timezone (UTC+8)

Troubleshooting:
- Token not found? Make sure you're logged in
- Wrong page? Verify you're on mi.com or new.c.mi.com/global
- Still stuck? Try the Chrome method instead""")
    
    def show_chrome_content(self):
        self.clear_content_area()
        self.chrome_text = self.create_text_frame("""Getting Cookies - Chrome/Chromium/Brave

Step 1: Prepare Your Account
1. Log out completely
2. Visit https://mi.com or https://new.c.mi.com/global
3. Log in with your Mi account

Step 2: Extract Token Using Address Bar Method
1. Click the address bar
2. Paste this code (REMOVE space after javascript):

javascript:(function(){var token=document.cookie.match(/popRunToken=([^;]+)/);if(token){prompt("Copy the token:", token[1]);}else{alert("Token not found");}})()

3. Press Enter
4. Copy the token from the popup window
5. Paste it into the tool's cookie field

For Brave Browser:
• Use the same method above
• OR install Cookie Editor extension (Chrome Web Store)
• Brave is Chromium-based, so both methods work

Important Notes:
• Remove the space after "javascript:" when pasting
• You MUST be on the correct Mi Community page
• Keep your token private
• Tokens expire - get fresh ones if needed
• All times use Beijing timezone (UTC+8)

Troubleshooting:
- "Token not found"? Verify you're logged in
- Wrong page? Go to mi.com or new.c.mi.com/global
- Paste failed? Remove the space after "javascript:"
- Extension method? Use Cookie Editor from Chrome Web Store""")
    
    def show_trouble_content(self):
        self.clear_content_area()
        self.trouble_text = self.create_text_frame("""Troubleshooting & Common Issues

COOKIES & LOGIN ISSUES

"Token not found" error
• Make sure you're on mi.com or new.c.mi.com/global
• Verify you're logged into your account
• Try refreshing the page
• Use a different extraction method

Cookie "expired" error
• Get a fresh cookie by logging in again
• Your old token may have been invalidated
• Clear browser cookies and try again

Account not found on Global
• Verify your Mi Community region is set to Global
• Go to Settings and change region from CN to Global
• Log out, switch region, log back in

---

ACCOUNT & ELIGIBILITY ISSUES

"Account too new" error
• Your account must be 30+ days old
• Wait until 30 days have passed
• No way around this requirement

"Account blocked" or limit exceeded
• You've already submitted recently
• Check your device Settings > Mi Unlock for status
• Wait until the specified date
• Contact Xiaomi support if permanently blocked

Account banned
• This may happen if you submit too many requests
• Do NOT submit multiple times in one day
• Wait several days between submissions
• Contact Xiaomi to appeal

---

DEVICE & COMPATIBILITY

Device not recognized
• Your device must be bound to your account
• Go to Settings > About phone > Mi Unlock
• Tap "Bind device" or similar option
• Wait a few minutes for binding

"Device model not supported"
• Check if your device is CN (China) variant
• Only Global variants can unlock
• If CN, unlocking is not possible

Device region mismatch
• Go to Settings > System > Device info
• Verify the model does NOT end in CN
• Flash Global ROM if you have CN variant

---

TIMING & SUBMISSION

Request failed at specific time
• Network latency may have caused miss
• Try manual mode to adjust timing
• Increase default ping value in settings
• Ensure stable internet connection

Manual mode not working
• Time must be between 58.5 and 59.8 seconds
• Example valid values: 59.0, 59.1, 58.7
• Make sure it's formatted correctly

---

GETTING HELP

If none of these solutions work:
1. Check the GitHub issues: github.com/AsInsideOut/miunlocktool/issues
2. Join the Telegram group: t.me/miunlocktoolnew
3. Provide details: device model, error message, account age
4. Include device logs if possible

DO NOT:
• Share your authentication tokens
• Submit requests multiple times
• Try with devices older than required
• Use multiple accounts simultaneously""")
    
    def show_authors_content(self):
        self.clear_content_area()
        self.authors_text = self.create_text_frame("""Project Contributors

MAIN DEVELOPERS

Space (@gloryoflunar)
• Auto-update feature
• UI design & improvements
• Testing & optimization

New Gen / QcomSnap8Gen1 (@New_g3n)
• Core functionality
• Request handling
• API integration

Zdarova ilia (@Xander85)
• Testing & QA
• Documentation
• Community support

ORIGINAL CONCEPT
Based on initial work by: Vierta

SPECIAL THANKS
To all users, testers, and contributors who helped identify bugs and improve this tool.

---

CONTACT & INFORMATION

Telegram Group: https://t.me/miunlocktoolnew
GitHub Repository: https://github.com/AsInsideOut/miunlocktool

Version: 4.5
Last Updated: 2025

---

IMPORTANT DISCLAIMER

This tool is provided AS-IS without warranty.

By using this tool, you acknowledge that:
• Bootloader unlocking may void your device warranty
• The developers are not responsible for bricked devices
• You use this tool at your own risk
• Account bans may occur (though unlikely if used properly)
• Always backup your data before unlocking

Use responsibly. Do not spam submission requests.

---

License: Open Source
Created for educational purposes.""")
    
    def show_settings_content(self):
        self.clear_content_area()
        
        settings_frame = ctk.CTkFrame(self.content_area, fg_color=ColorScheme.CARD_BG, corner_radius=10)
        settings_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Ping setting
        ping_frame = ctk.CTkFrame(settings_frame, fg_color=ColorScheme.CARD_BG)
        ping_frame.pack(fill="x", pady=20, padx=20)
        
        ctk.CTkLabel(
            ping_frame,
            text="Default Ping (ms):",
            font=("Arial", 13, "bold"),
            text_color=ColorScheme.PRIMARY
        ).pack(anchor="w", pady=(0, 8))
        
        ctk.CTkLabel(
            ping_frame,
            text="Fallback value if ping measurement fails. Default: 300ms",
            font=("Arial", 10),
            text_color=ColorScheme.TEXT_SECONDARY
        ).pack(anchor="w", pady=(0, 8))
        
        self.ping_entry = ctk.CTkEntry(
            ping_frame,
            textvariable=self.default_ping_var,
            width=100,
            height=32,
            font=("Arial", 11),
            fg_color=ColorScheme.DARKER_BG,
            border_color=ColorScheme.PRIMARY,
            text_color=ColorScheme.TEXT_PRIMARY
        )
        self.ping_entry.pack(anchor="w")
        
        # Cookie check toggle
        check_frame = ctk.CTkFrame(settings_frame, fg_color=ColorScheme.CARD_BG)
        check_frame.pack(fill="x", pady=20, padx=20)
        
        self.cookie_checkbox = ctk.CTkCheckBox(
            check_frame,
            text="Skip cookie validation (not recommended)",
            variable=self.skip_cookie_check_var,
            onvalue=True,
            offvalue=False,
            font=("Arial", 12),
            text_color=ColorScheme.TEXT_PRIMARY,
            fg_color=ColorScheme.PRIMARY,
            hover_color=ColorScheme.PRIMARY_HOVER
        )
        self.cookie_checkbox.pack(anchor="w")
        
        # Buttons
        button_frame = ctk.CTkFrame(settings_frame, fg_color=ColorScheme.CARD_BG)
        button_frame.pack(fill="x", pady=20, padx=20)
        
        save_btn = ctk.CTkButton(
            button_frame,
            text="Save Settings",
            command=self.save_settings,
            fg_color=ColorScheme.SUCCESS,
            hover_color=ColorScheme.SUCCESS_HOVER,
            height=36,
            font=("Arial", 12, "bold")
        )
        save_btn.pack(side="left", padx=(0, 10))
        
        update_btn = ctk.CTkButton(
            button_frame,
            text="Check for Updates",
            command=self.check_updates,
            fg_color=ColorScheme.SECONDARY,
            hover_color=ColorScheme.SECONDARY_HOVER,
            height=36,
            font=("Arial", 12, "bold")
        )
        update_btn.pack(side="left")
    
    def save_settings(self):
        try:
            ping_value = int(self.default_ping_var.get())
            if ping_value <= 0:
                raise ValueError("Must be positive")
            
            self.app.settings['default_ping'] = ping_value
            self.app.settings['skip_cookie_check'] = self.skip_cookie_check_var.get()
            self.app.log_message(f"Settings saved: Default ping = {ping_value}ms")
            messagebox.showinfo("Success", "Settings saved successfully!")
        except ValueError:
            messagebox.showerror("Error", "Ping must be a positive number!")
    
    def check_updates(self):
        latest, message = UpdateChecker.check_for_updates()
        if latest:
            if messagebox.askyesno("Update Available", f"Version {latest} is available!\n\nOpen download page?"):
                webbrowser.open(f"{GITHUB_REPO_URL}{latest}")
        else:
            messagebox.showinfo("Updates", message)

class XiaomiUnlockTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Xiaomi Unlock Tool")
        self.root.geometry("900x600")
        self.root.minsize(900, 600)
        self.root.maxsize(1200, 800)
        self.root.bind_all("<Key>", _on_key_release, "+")
        
        self.settings = {
            'skip_cookie_check': False,
            'default_ping': 300,
        }
        
        self.cookie_value = ctk.StringVar()
        self.device_id = ctk.StringVar()
        self.status_var = ctk.StringVar(value="Ready to start")
        self.ping_var = ctk.StringVar(value="Ping: not measured")
        self.time_var = ctk.StringVar(value="Time: not synchronized")
        self.mode_var = ctk.StringVar(value="auto")
        self.manual_time_var = ctk.StringVar(value="59.1")
        
        self.create_widgets()
        self.session = HTTP11Session()
        self.start_beijing_time = None
        self.start_timestamp = None
    
    def create_widgets(self):
        # Header
        header = ctk.CTkFrame(self.root, fg_color=ColorScheme.PRIMARY)
        header.pack(fill="x", padx=0, pady=0)
        
        ctk.CTkLabel(
            header,
            text="Xiaomi Unlock Tool v4.5",
            font=("Arial", 18, "bold"),
            text_color=ColorScheme.TEXT_PRIMARY
        ).pack(pady=12)
        
        # Description
        desc_frame = ctk.CTkFrame(self.root, fg_color=ColorScheme.SECONDARY)
        desc_frame.pack(fill="x", padx=10, pady=(5, 0))
        
        ctk.CTkLabel(
            desc_frame,
            text="Automated bootloader unlock request submission tool\nDevelopers: Space, New Gen, Zdarova ilia | Telegram: t.me/miunlocktoolnew",
            font=("Arial", 11),
            text_color=ColorScheme.TEXT_PRIMARY,
            justify="left"
        ).pack(padx=10, pady=8)
        
        # Main container
        main_frame = ctk.CTkFrame(self.root, fg_color=ColorScheme.DARK_BG)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        left_frame = ctk.CTkFrame(main_frame, fg_color=ColorScheme.DARK_BG)
        left_frame.pack(side="left", fill="both", expand=False, padx=(0, 5))
        
        right_frame = ctk.CTkFrame(main_frame, fg_color=ColorScheme.DARK_BG)
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        # Input panel
        input_panel = ctk.CTkFrame(left_frame, fg_color=ColorScheme.CARD_BG, corner_radius=10)
        input_panel.pack(fill="x", pady=(0, 10), expand=True)
        
        ctk.CTkLabel(
            input_panel,
            text="Parameters",
            font=("Arial", 13, "bold"),
            text_color=ColorScheme.PRIMARY
        ).pack(anchor="w", padx=12, pady=(10, 8))
        
        # Mode selection
        mode_frame = ctk.CTkFrame(input_panel, fg_color=ColorScheme.CARD_BG)
        mode_frame.pack(fill="x", padx=12, pady=5)
        
        ctk.CTkLabel(
            mode_frame,
            text="Mode:",
            font=("Arial", 11),
            text_color=ColorScheme.TEXT_PRIMARY
        ).pack(side="left")
        
        ctk.CTkRadioButton(
            mode_frame,
            text="Auto",
            variable=self.mode_var,
            value="auto",
            command=self.toggle_mode,
            text_color=ColorScheme.TEXT_PRIMARY
        ).pack(side="left", padx=(20, 10))
        
        ctk.CTkRadioButton(
            mode_frame,
            text="Manual",
            variable=self.mode_var,
            value="manual",
            command=self.toggle_mode,
            text_color=ColorScheme.TEXT_PRIMARY
        ).pack(side="left")
        
        # Manual time input
        self.manual_time_frame = ctk.CTkFrame(input_panel, fg_color=ColorScheme.CARD_BG)
        
        ctk.CTkLabel(
            self.manual_time_frame,
            text="Submission second (58.5-59.8):",
            font=("Arial", 10),
            text_color=ColorScheme.TEXT_SECONDARY
        ).pack(anchor="w", padx=12, pady=(5, 2))
        
        self.manual_time_entry = ctk.CTkEntry(
            self.manual_time_frame,
            textvariable=self.manual_time_var,
            width=70,
            height=28,
            font=("Arial", 10),
            fg_color=ColorScheme.DARKER_BG,
            border_color=ColorScheme.PRIMARY,
            text_color=ColorScheme.TEXT_PRIMARY
        )
        self.manual_time_entry.pack(anchor="w", padx=12, pady=(0, 8))
        
        # Cookie input
        ctk.CTkLabel(
            input_panel,
            text="Authentication Token:",
            font=("Arial", 11),
            text_color=ColorScheme.TEXT_PRIMARY
        ).pack(anchor="w", padx=12, pady=(10, 3))
        
        self.cookie_entry = ctk.CTkEntry(
            input_panel,
            textvariable=self.cookie_value,
            height=32,
            font=("Arial", 10),
            fg_color=ColorScheme.DARKER_BG,
            border_color=ColorScheme.PRIMARY,
            text_color=ColorScheme.TEXT_PRIMARY
        )
        self.cookie_entry.pack(fill="x", padx=12, pady=(0, 12))
        self.cookie_entry.bind("<Return>", lambda event: self.start_process())
        
        # Info panel
        info_panel = ctk.CTkFrame(left_frame, fg_color=ColorScheme.CARD_BG, corner_radius=10)
        info_panel.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            info_panel,
            text="Status",
            font=("Arial", 13, "bold"),
            text_color=ColorScheme.PRIMARY
        ).pack(anchor="w", padx=12, pady=(10, 8))
        
        ctk.CTkLabel(
            info_panel,
            textvariable=self.status_var,
            font=("Arial", 11),
            text_color=ColorScheme.TEXT_PRIMARY,
            wraplength=350
        ).pack(anchor="w", padx=12, pady=2)
        
        ctk.CTkLabel(
            info_panel,
            textvariable=self.ping_var,
            font=("Arial", 11),
            text_color=ColorScheme.TEXT_PRIMARY
        ).pack(anchor="w", padx=12, pady=2)
        
        ctk.CTkLabel(
            info_panel,
            textvariable=self.time_var,
            font=("Arial", 11),
            text_color=ColorScheme.TEXT_PRIMARY
        ).pack(anchor="w", padx=12, pady=(2, 12))
        
        # Buttons
        button_frame = ctk.CTkFrame(left_frame, fg_color=ColorScheme.DARK_BG)
        button_frame.pack(fill="x", pady=10)
        
        self.start_button = ctk.CTkButton(
            button_frame,
            text="Submit Request",
            command=self.start_process,
            fg_color=ColorScheme.SUCCESS,
            hover_color=ColorScheme.SUCCESS_HOVER,
            height=36,
            font=("Arial", 12, "bold")
        )
        self.start_button.pack(fill="x", pady=(0, 5))
        
        self.instructions_button = ctk.CTkButton(
            button_frame,
            text="Instructions",
            command=self.open_instructions,
            fg_color=ColorScheme.SECONDARY,
            hover_color=ColorScheme.SECONDARY_HOVER,
            height=32,
            font=("Arial", 11, "bold")
        )
        self.instructions_button.pack(fill="x", pady=(0, 5))
        
        self.exit_button = ctk.CTkButton(
            button_frame,
            text="Exit",
            command=self.exit_application,
            fg_color=ColorScheme.DANGER,
            hover_color=ColorScheme.DANGER_HOVER,
            height=32,
            font=("Arial", 11, "bold")
        )
        self.exit_button.pack(fill="x")
        
        # Log panel
        log_panel = ctk.CTkFrame(right_frame, fg_color=ColorScheme.CARD_BG, corner_radius=10)
        log_panel.pack(fill="both", expand=True)
        
        ctk.CTkLabel(
            log_panel,
            text="Execution Log",
            font=("Arial", 13, "bold"),
            text_color=ColorScheme.PRIMARY
        ).pack(anchor="w", padx=12, pady=(10, 8))
        
        self.log_text = ctk.CTkTextbox(
            log_panel,
            font=("Consolas", 10),
            wrap="word",
            fg_color=ColorScheme.LOG_BG,
            text_color=ColorScheme.TEXT_PRIMARY,
            border_width=0
        )
        self.log_text.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.log_text.configure(state='disabled')
    
    def toggle_mode(self):
        if self.mode_var.get() == "manual":
            self.manual_time_frame.pack(fill="x", padx=12, pady=5, after=self.mode_label)
        else:
            self.manual_time_frame.pack_forget()
    
    def open_instructions(self):
        InstructionsWindow(self.root, self)
    
    def exit_application(self):
        self.root.destroy()
        sys.exit(0)
    
    def log_message(self, message):
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        full_message = f"{timestamp} {message}"
        
        self.log_text.configure(state='normal')
        self.log_text.insert("end", full_message + "\n")
        self.log_text.configure(state='disabled')
        self.log_text.see("end")
        self.root.update()
    
    def get_average_ping(self):
        all_pings = []
        self.log_message("Starting ping measurement...")
        
        for server in MI_SERVERS:
            try:
                result = ping(server, count=2, interval=0.5, timeout=2)
                if result.is_alive:
                    all_pings.append(result.avg_rtt)
                    self.log_message(f"Ping to {server}: {result.avg_rtt:.2f} ms")
                else:
                    self.log_message(f"Failed to ping {server}")
            except Exception as e:
                self.log_message(f"Ping error {server}: {e}")
        
        if not all_pings:
            default = self.settings['default_ping']
            self.log_message(f"Using default ping: {default} ms")
            self.ping_var.set(f"Ping: {default} ms (default)")
            return default
        
        avg_ping = statistics.mean(all_pings)
        self.log_message(f"Average ping: {avg_ping:.2f} ms")
        self.ping_var.set(f"Ping: {avg_ping:.2f} ms")
        return avg_ping
    
    def generate_device_id(self):
        random_data = f"{random.random()}-{time.time()}"
        device_id = hashlib.sha1(random_data.encode('utf-8')).hexdigest().upper()
        self.device_id.set(device_id)
        self.log_message(f"Generated deviceId: {device_id}")
        return device_id
    
    def get_initial_beijing_time(self):
        client = ntplib.NTPClient()
        beijing_tz = pytz.timezone("Asia/Shanghai")
        
        for server in ntp_servers:
            try:
                self.log_message(f"Connecting to NTP server: {server}")
                response = client.request(server, version=3)
                ntp_time = datetime.fromtimestamp(response.tx_time, timezone.utc)
                beijing_time = ntp_time.astimezone(beijing_tz)
                self.log_message(f"Time from {server}: {beijing_time.strftime('%Y-%m-%d %H:%M:%S')}")
                self.time_var.set(f"Time synchronized: {beijing_time.strftime('%H:%M:%S')} (UTC+8)")
                return beijing_time
            except Exception as e:
                self.log_message(f"NTP error {server}: {e}")
        
        self.log_message("Failed to connect to any NTP server!")
        return None
    
    def get_synchronized_beijing_time(self, start_beijing_time, start_timestamp):
        elapsed = time.time() - start_timestamp
        current_time = start_beijing_time + timedelta(seconds=elapsed)
        return current_time
    
    def calculate_script_time(self, ping_ms):
        script_time = 59.091 + (166 - ping_ms) * 0.006
        return script_time
    
    def wait_until_target_time(self, start_beijing_time, start_timestamp, script_time):
        seconds = int(script_time)
        milliseconds = int((script_time % 1) * 1000)
        
        target_time = start_beijing_time.replace(
            hour=23, minute=59, second=seconds, 
            microsecond=milliseconds * 1000
        )
        
        current_time = self.get_synchronized_beijing_time(start_beijing_time, start_timestamp)
        if current_time > target_time:
            target_time = target_time + timedelta(seconds=1)
        
        self.log_message(f"Waiting until {target_time.strftime('%H:%M:%S.%f')}")
        
        def check_time():
            current_time = self.get_synchronized_beijing_time(start_beijing_time, self.start_timestamp)
            time_diff = (target_time - current_time).total_seconds()
            self.time_var.set(f"Time: {current_time.strftime('%H:%M:%S')} (UTC+8)")
            
            if time_diff <= 0:
                self.log_message(f"Target time reached! Submitting request...")
                self.start_request()
            else:
                self.root.after(100, check_time)
        
        check_time()
    
    def check_unlock_status(self, cookie_value, device_id):
        if self.settings['skip_cookie_check']:
            self.log_message("Cookie check skipped")
            return True
        
        try:
            url = "https://sgp-api.buy.mi.com/bbs/api/global/user/bl-switch/state"
            headers = {
                "Cookie": f"new_bbs_serviceToken={cookie_value};deviceId={device_id};"
            }
            
            response = self.session.make_request('GET', url, headers=headers)
            if response is None:
                self.log_message("Failed to check unlock status")
                return False
            
            response_data = json.loads(response.data.decode('utf-8'))
            response.release_conn()
            
            if response_data.get("code") == 100004:
                self.log_message("Cookie expired - please get a new one")
                messagebox.showerror("Error", "Cookie expired. Please get a fresh cookie.")
                return False
            
            data = response_data.get("data", {})
            is_pass = data.get("is_pass")
            button_state = data.get("button_state")
            deadline = data.get("deadline_format", "")
            
            if is_pass == 4:
                if button_state == 1:
                    self.log_message("Account ready for submission")
                    return True
                elif button_state == 2:
                    self.log_message(f"Account blocked until {deadline}")
                    messagebox.showinfo("Info", f"Account blocked until {deadline}")
                    return False
                elif button_state == 3:
                    self.log_message("Account too new (less than 30 days)")
                    messagebox.showinfo("Info", "Account must be at least 30 days old")
                    return False
            elif is_pass == 1:
                self.log_message(f"Application already approved until {deadline}")
                messagebox.showinfo("Info", f"Already approved until {deadline}")
                return False
        except Exception as e:
            self.log_message(f"Status check error: {e}")
        
        return False
    
    def start_request(self):
        cookie = self.cookie_value.get().strip()
        device_id = self.device_id.get()
        
        url = "https://sgp-api.buy.mi.com/bbs/api/global/apply/bl-auth"
        headers = {
            "Cookie": f"new_bbs_serviceToken={cookie};deviceId={device_id};"
        }
        
        try:
            request_time = self.get_synchronized_beijing_time(self.start_beijing_time, self.start_timestamp)
            self.log_message(f"Sending request at {request_time.strftime('%H:%M:%S.%f')}")
            
            response = self.session.make_request('POST', url, headers=headers)
            if response is None:
                self.log_message("Failed to send request")
                messagebox.showerror("Error", "Failed to send request")
                return
            
            response_time = self.get_synchronized_beijing_time(self.start_beijing_time, self.start_timestamp)
            self.log_message(f"Response received at {response_time.strftime('%H:%M:%S.%f')}")
            
            response_data = json.loads(response.data.decode('utf-8'))
            response.release_conn()
            
            code = response_data.get("code")
            data = response_data.get("data", {})
            
            if code == 0:
                apply_result = data.get("apply_result")
                if apply_result == 1:
                    self.log_message("Request approved!")
                    messagebox.showinfo("Success", "Request approved!")
                elif apply_result == 3:
                    deadline = data.get("deadline_format", "")
                    self.log_message(f"Submission limit reached, try again {deadline}")
                    messagebox.showinfo("Info", f"Try again on {deadline}")
            else:
                self.log_message(f"Response code: {code}")
                
        except Exception as e:
            self.log_message(f"Request error: {e}")
            messagebox.showerror("Error", f"Error: {e}")
    
    def start_process(self):
        cookie = self.cookie_value.get().strip()
        if not cookie:
            messagebox.showerror("Error", "Please enter your authentication token!")
            return
        
        self.log_message("\n========== Starting Unlock Process ==========")
        self.status_var.set("Processing...")
        
        device_id = self.generate_device_id()
        
        if not self.check_unlock_status(cookie, device_id):
            self.status_var.set("Check failed")
            return
        
        self.start_beijing_time = self.get_initial_beijing_time()
        if self.start_beijing_time is None:
            messagebox.showerror("Error", "Failed to synchronize time!")
            self.status_var.set("Time sync failed")
            return
        
        self.start_timestamp = time.time()
        
        if self.mode_var.get() == "auto":
            self.wait_for_ping_time()
        else:
            self.start_manual_mode()
    
    def wait_for_ping_time(self):
        target_time = self.start_beijing_time.replace(hour=23, minute=59, second=48)
        
        current_time = self.get_synchronized_beijing_time(self.start_beijing_time, self.start_timestamp)
        if current_time > target_time:
            target_time = target_time + timedelta(seconds=1)
        
        self.log_message("Waiting for 23:59:48 to measure ping...")
        self.status_var.set("Waiting for ping time...")
        
        def check_time():
            current_time = self.get_synchronized_beijing_time(self.start_beijing_time, self.start_timestamp)
            time_diff = (target_time - current_time).total_seconds()
            self.time_var.set(f"Time: {current_time.strftime('%H:%M:%S')} (UTC+8)")
            
            if time_diff <= 0:
                self.log_message("23:59:48 reached, measuring ping...")
                avg_ping = self.get_average_ping()
                script_time = self.calculate_script_time(avg_ping)
                self.log_message(f"Calculated submission time: {script_time:.3f}s")
                self.wait_until_target_time(self.start_beijing_time, self.start_timestamp, script_time)
            else:
                self.root.after(100, check_time)
        
        check_time()
    
    def start_manual_mode(self):
        try:
            script_time = float(self.manual_time_var.get())
            if script_time < 58.5 or script_time > 59.8:
                raise ValueError("Time must be between 58.5 and 59.8")
            
            self.log_message(f"Manual mode: submission time set to 23:59:{script_time}")
            self.status_var.set("Manual mode active")
            self.wait_until_target_time(self.start_beijing_time, self.start_timestamp, script_time)
        except ValueError:
            messagebox.showerror("Error", "Invalid time! Use format: 59.1 (between 58.5 and 59.8)")

def hide_console():
    if os.name == 'nt':
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

def main():
    hide_console()
    root = ctk.CTk()
    app = XiaomiUnlockTool(root)
    root.mainloop()

if __name__ == "__main__":
    main()