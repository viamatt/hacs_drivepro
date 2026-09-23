# DrivePro Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

A custom [Home Assistant](https://www.home-assistant.io/) integration for [DrivePro](https://www.drivepro.io/) vehicle trackers. It polls the DrivePro Fleet API and exposes each vehicle on your account as a device with sensors and a device tracker.

This is an official integration supported by DrivePro.io Ltd.

## Requirements

- A Home Assistant instance (2024.6.0 or newer).
- A DrivePro account with one or more vehicle trackers already registered.
- API credentials (Client ID / Client Secret) for the DrivePro Fleet API — see [Getting API credentials](#getting-api-credentials) below.

If you don't yet own any DrivePro tracking hardware, compatible trackers and dash cams can be purchased directly from the DrivePro website: [https://www.drivepro.io/](https://www.drivepro.io/).

## Getting API credentials

This integration authenticates with the DrivePro Fleet API using an OAuth2 `client_credentials` grant. You will need a **Client ID** and **Client Secret** for your account:

1. Sign in to your account at [https://www.drivepro.io/](https://www.drivepro.io/).
2. Visit [https://www.drivepro.io/FleetApi/Clients](https://www.drivepro.io/FleetApi/Clients).
3. Add a new API client. The system will display a **Client ID** and **Client Secret**.
4. Keep these safe — you'll enter them as the "Username" and "Password" fields when setting up the integration in Home Assistant.

If you can't find API access on your account, contact DrivePro support to have it enabled.

## Installation

### Option 1: HACS (recommended)

1. In Home Assistant, open **HACS**.
2. Click the three-dot menu in the top right and choose **Custom repositories**.
3. Add this repository URL, select **Integration** as the category, and click **Add**.
4. Find "DrivePro Integration" in HACS and click **Download**.
5. Restart Home Assistant.

### Option 2: Manual install

1. Download or clone this repository.
2. Copy the `custom_components/drivepro_integration` folder into the `custom_components` directory of your Home Assistant configuration (create the folder if it doesn't exist).
3. Restart Home Assistant.

## Setup

1. In Home Assistant, go to **Settings → Devices & Services → Add Integration**.
2. Search for **DrivePro Integration**.
3. Enter your DrivePro Fleet API **Client ID** (as "Username") and **Client Secret** (as "Password").
4. Submit the form. Home Assistant will verify the credentials and create a device for each vehicle on your account.

## Entities

For each vehicle, the integration creates:

- **Device tracker** — current GPS location, with heading, speed, location name and driver name as attributes.
- **Sensors** — odometer, trip odometer, speed, heading, ignition-on time, fault count, CO2 emissions, model year, arm state, mode, registration number, VIN, driver, last known location, group, and more.
- **Binary sensor** — "Armed" state of the vehicle.

Data is refreshed from the DrivePro API every 30 seconds.

## Troubleshooting

- Enable debug logging to help diagnose issues by adding the following to your `configuration.yaml`:

  ```yaml
  logger:
    default: info
    logs:
      custom_components.drivepro_integration: debug
  ```

- If setup fails with an authentication error, double-check your Client ID/Secret and that Fleet API access is enabled on your DrivePro account.
- Please report bugs or feature requests via the [issue tracker](https://github.com/viamatt/hacs_drivepro/issues).

## Disclaimer

This official integration is supported by DrivePro.io Ltd and is provided as-is. Never share your DrivePro API credentials or Home Assistant configuration containing them publicly.
