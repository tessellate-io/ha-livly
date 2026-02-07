# Livly Integration for Home Assistant

A Home Assistant integration to track pending packages from the Livly resident app.

## Features

- **Package Tracking**: Shows the number of packages awaiting pickup
- **Sync Control**: Switch to enable/disable automatic updates
- **30-minute Polling**: Automatically checks for new packages

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots menu → "Custom repositories"
3. Add this repository URL and select "Integration" as the category
4. Click "Install"
5. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/livly` folder to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for "Livly"
3. Enter your phone number (select country code from dropdown)
4. Enter the 6-digit verification code sent via SMS
5. Done!

## Entities

| Entity | Type | Description |
|--------|------|-------------|
| `sensor.livly_pending_packages` | Sensor | Number of packages awaiting pickup |
| `switch.livly_sync_enabled` | Switch | Enable/disable automatic syncing |

### Sensor Attributes

- `last_checked`: ISO timestamp of the last successful update

## Privacy

- Phone numbers are stored locally (required for re-authentication) but only the last 4 digits are displayed in the UI
- Authentication tokens are stored in Home Assistant's secure storage
- No data is sent to third parties (only communicates with Livly's API)
