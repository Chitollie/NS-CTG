# NS-CTG Discord Bot

## Overview
This is a Discord bot for Nova Sécurité (NS-CTG), a French security company simulation/roleplay server. The bot provides identification, menu navigation, and mission management features for Discord server members.

## Project Architecture
- **Language**: Python 3.11
- **Framework**: discord.py 2.4.0
- **Structure**: Modular command and view-based architecture

### Directory Structure
```
bot/
  ├── commands/       # Discord slash commands
  │   └── menu.py    # Main menu command
  ├── utils/         # Utility functions
  │   └── missions_data.py
  ├── views/         # Discord UI views (buttons, modals)
  │   ├── identification_view.py
  │   ├── menu_view.py
  │   ├── mission_view.py
  │   ├── modals.py
  │   └── verif_view.py
  ├── config.py      # Configuration and environment variables
  ├── events.py      # Event handlers (on_ready, etc.)
  └── main.py        # Bot entry point
```

## Dependencies
- discord.py==2.4.0 - Discord API wrapper
- python-dotenv==1.0.1 - Environment variable management

## Required Environment Variables
The bot requires the following environment variables to be set:
- `TOKEN` - Discord bot token
- `GUILD_ID` - Discord server (guild) ID
- `MISS_CHANNEL_ID` - Mission channel ID
- `ROLE_AGENTS_ID` - Agents role ID
- `ROLE_SAMS_ID` - SAMS role ID
- `ROLE_LSPD_ID` - LSPD role ID
- `IDENT_CHANNEL_ID` - Identification channel ID
- `ROLE_IDENTIFIE_ID` - Identified role ID

## Features
1. **Identification System**: Users can identify themselves via button clicks
2. **Menu Command**: `/menu` - Opens interactive menu for security company operations
3. **Mission Management**: Handles mission assignment and tracking
4. **Role Management**: Automatic role assignment based on user actions

## Setup Status
- ✅ Python 3.11 installed
- ✅ Dependencies installed (discord.py, python-dotenv)
- ⏳ Awaiting Discord bot credentials from user
- ⏳ Workflow configuration pending

## Recent Changes
- 2025-10-09: Initial Replit environment setup
- 2025-10-09: Installed Python 3.11 and all dependencies
