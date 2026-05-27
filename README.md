# Network IT Troubleshooter for Linux

Offline, GUI-only Linux network troubleshooting helper with safe read-only checks and copyable IT summaries.

## What it does

- Runs safe read-only live network checks from a desktop GUI
- Helps interpret common network problems using offline rules/flowcharts
- Can optionally open JSON reports from Network Diagnostics Report Tool
- Shows likely problem, why, next step, and a copyable IT/support summary
- Includes Work Package buttons for safe checks such as DNS, gateway/router, HTTPS, and internet reachability

## What it does not do

- Does not change network settings
- Does not require AI
- Does not auto-repair the computer
- Does not upload reports anywhere

## Platform

Linux. Python 3.10+ recommended.

## Run from source

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
network-it-troubleshooter
```

Alternative local launcher after installing dependencies:

```bash
./run.sh
```

## Test

```bash
python3 -m pytest -q
```

Verified locally before public prep: **65 tests passed**.

## Privacy / safety

All Work Package checks are read-only. The app is designed to help users understand network problems and copy a summary for IT/support, not to change settings automatically.

## First-time prerequisite setup

If the app does not open, run:

```bash
./Setup_Prerequisites.sh
```

The setup script checks for Python and the app's Python dependencies. If common Linux system packages are missing, it asks before trying to install them.

Supported automatic system package managers:

- apt / apt-get
- dnf
- pacman
- zypper

If your distro uses a different package manager, install Python 3, venv/pip, and the app dependencies manually.

## Support development

These apps are free/pay-what-you-want so people can actually use them.

If this app helped you, a small tip helps me keep building and improving them.

- Cash App: $jaydubgtfo

## License

No open-source license has been selected yet. Unless a license is added later, all rights are reserved by the author.
