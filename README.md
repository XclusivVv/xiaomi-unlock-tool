    # Xiaomi Unlock Tool

    This is an automated tool for submitting bootloader unlock requests to Xiaomi's servers.  
    Based on the original work by Vierta, I've rebuilt the interface with a cleaner dark theme,  
    better error handling, and proper timing synchronization.

    The tool handles all the tedious parts of the unlock process — synchronizing with Beijing  
    time servers, measuring network latency, calculating the exact submission window, and  
    sending the request at precisely the right moment. Without this, you'd be doing manual API  
    calls and timing everything yourself. Not ideal.

    ## What it does

    - Pulls accurate Beijing time from NTP servers for reliable synchronization  
    - Measures your network latency to Xiaomi's servers to calculate optimal submission timing  
    - Validates your authentication token and checks account eligibility  
    - Submits your unlock request at the exact second Xiaomi's servers accept it  
    - Logs everything so you know what's happening at each step  
    - Handles both automatic mode (measures ping and calculates timing) and manual mode (you pick the submission second)  
    - Shows real-time status and errors without cryptic output  

    ## How it works (roughly)

    You extract an authentication token from the Mi Community website (instructions built in).  
    The tool connects to time servers in China to get Beijing timezone, waits until **23:59:48**,  
    quickly measures ping to Xiaomi's servers, calculates the precise second you need to submit  
    based on network latency, then sends your request at exactly that moment.

    Xiaomi only accepts submissions in a narrow time window — usually the last couple seconds  
    of each minute — so timing is critical.

    If something goes wrong (cookie expired, account too new, already submitted, etc.) the tool  
    catches it and tells you exactly what the issue is instead of failing silently.

    ## Setup

    Install dependencies:
    ```
    bash
    python run_first.py
    ```

    That's it. The script creates a virtual environment, installs everything, and launches the tool.

    Or if you already have the venv set up:
    ```
    bash
    python app.py
    ```

    ## Requirements

    - Python 3.8+  
    - Windows, macOS, or Linux  
    - Internet connection  
    - A Mi account (30+ days old, Global region)  
    - A Xiaomi device you actually own  

    ## Before you start

    You need to meet these:

    - Account must be at least 30 days old  
    - Account region must be set to Global (not China)  
    - Your device must be a Global variant (not CN model)  
    - Device must be running HyperOS 1–3  
    - Device needs to be bound to your account in settings  

    ## How to get your token

    The tool has built-in instructions for Firefox, Chrome, Brave, and Safari.  
    Basically you log into Mi Community, use a Cookie Editor extension or a bookmarklet to grab  
    your authentication token, paste it into the tool, and go.

    The token is temporary — if you get errors later, just grab a fresh one.

    ## Credits

    Original concept and core logic by **Vierta**.  
    Current version built by:

    - **Space** (UI improvements, auto-update feature)  
    - **New Gen / QcomSnap8Gen1** (core functionality, request handling)  
    - **Zdarova ilia** (testing, optimization)

    ## Disclaimer

    Use this at your own risk. Bootloader unlocking may void your warranty.  
    The developers aren't responsible for bricked devices or banned accounts, though the latter  
    is very unlikely if you use this normally (once per account, not spamming requests).

    Always back up your data before messing with your bootloader.

    ## Links

    GitHub: https://github.com/AsInsideOut/miunlocktool  
    Telegram: https://t.me/miunlocktoolnew

    Questions or issues?  
    Check the troubleshooting section in the tool's instructions window or join the Telegram group.
