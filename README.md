# Kryptonite - Crypto Wallet Verification API

Kryptonite is a FastAPI-based application designed to check cryptocurrency wallet addresses against local and external blacklists, and fetch address tags from a GraphSense-compatible API to assess risk.

## Features

*   Verifies crypto addresses against a user-maintained local `blacklist.txt`.
*   Integrates with Polkadot.js phishing lists (`address.json` for scam addresses, `all.json` for scam domains) to identify known malicious entities, primarily within the Polkadot/Substrate ecosystem.
*   Integrates with a GraphSense API (if configured) to retrieve address tags (e.g., identifying tags like "exchange", "miner", "scam").
*   Provides a risk level and score based on local blacklist status, Polkadot.js scam lists, and GraphSense tags.
*   Containerized with Docker and managed via `docker-compose`.

## Project Structure

*   `main.py`: The main FastAPI application code.
*   `Dockerfile`: Used to build the Docker image for the Kryptonite application.
*   `docker-compose.yml`: Defines and manages the application services.
*   `requirements.txt`: Python dependencies.
*   `blacklist.txt`: A list of cryptocurrency addresses manually added by the user for blacklisting.
*   `graphsense-REST/`: Intended location for a GraphSense API implementation (currently appears to be missing from this repository).
*   `scripts/update_blacklists.sh`: A script presumably for updating blacklist files (its functionality is not fully integrated or documented within the core app).

## Setup and Running the Application

### Prerequisites

*   Docker
*   Docker Compose

### Configuration

The application uses environment variables for configuration. These can be set in your shell or directly in the `docker-compose.yml` file for the `kryptonite-app` service.

1.  **GraphSense API (Optional):**
    *   The Kryptonite application can connect to a GraphSense API instance for enhanced address analysis.
    *   Configure the base URL of your GraphSense API using the `GRAPHSENSE_API_BASE_URL` environment variable.
    *   Example: `GRAPHSENSE_API_BASE_URL=http://localhost:9000`
    *   If not set, GraphSense checks will be skipped.
    *   The `docker-compose.yml` includes a commented-out placeholder for a `graphsense-api` service if you wish to run one locally.

2.  **Polkadot.js Phishing Lists (Enabled by Default):**
    *   The application fetches known scam addresses and domains from lists maintained by the Polkadot.js project. This is primarily focused on entities within the Polkadot/Substrate ecosystem.
    *   The URLs for these lists can be customized via environment variables:
        *   `POLKADOT_ADDRESS_JSON_URL`: URL for the scam address list.
            *   Default: `https://polkadot.js.org/phishing/address.json`
        *   `POLKADOT_ALL_JSON_URL`: URL for the scam domain list. (Note: The domain list is loaded but not currently used by the `/verify/{address}` endpoint).
            *   Default: `https://polkadot.js.org/phishing/all.json`

3.  **Local Blacklist:**
    *   The `blacklist.txt` file in the root directory can be used to populate a local list of sanctioned/blocked addresses. Add one address per line. This list is checked in addition to the Polkadot.js scam address list.

### Running with Docker Compose

1.  **Clone the repository (if you haven't already).**
2.  **Navigate to the project directory.**
3.  **Configure Environment Variables (Optional):**
    *   If you need to change the default URLs for GraphSense or Polkadot.js lists, modify the `environment` section in `docker-compose.yml` for the `kryptonite-app` service:
    ```yaml
    services:
      kryptonite-app:
        # ... other configurations ...
        environment:
          - GRAPHSENSE_API_URL=http://your-graphsense-api-url:9000 # Example
          - POLKADOT_ADDRESS_JSON_URL=https://your-custom-address-list.json # Example
          - POLKADOT_ALL_JSON_URL=https://your-custom-domain-list.json # Example
    ```
4.  **Build and start the services:**
    ```bash
    docker-compose up --build
    ```
    The Kryptonite application will be accessible at `http://localhost:8080` by default (as configured in `docker-compose.yml`).

## API Endpoints

### Home

*   **GET /**
    *   Description: Returns a welcome message indicating the API is running.
    *   Response:
        ```json
        {
          "message": "Crypto Wallet Verification API is running"
        }
        ```

### Verify Wallet Address

*   **GET /verify/{address}**
    *   Description: Verifies a given cryptocurrency address against configured blacklists and (optionally) GraphSense.
    *   Path Parameter:
        *   `address` (string, required): The cryptocurrency address to verify.
    *   Response (Success - Example, no blacklist hits):
        ```json
        {
          "address": "some_crypto_address",
          "sanctioned_by_local_blacklist": false,
          "on_polkadot_scam_list": false,
          "graphsense_tags": [
            {
              "label": "Exchange",
              "source": "SomeGraphSenseSource",
              // ... other tag details
            }
          ],
          "risk_level": "low", // Possible values: "low", "medium", "high", "critical"
          "risk_score": 10     // Numerical score: 0-100
        }
        ```
    *   Response (Address on Polkadot.js scam list):
        ```json
        {
          "address": "polkadot_scam_address",
          "sanctioned_by_local_blacklist": false,
          "on_polkadot_scam_list": true,
          "graphsense_tags": ["GraphSense API not configured"], // Or actual tags if API is configured
          "risk_level": "high", 
          "risk_score": 90
        }
        ```
    *   Response (Address on local blacklist):
        ```json
        {
          "address": "sanctioned_address",
          "sanctioned_by_local_blacklist": true,
          "on_polkadot_scam_list": false, // Could also be true if on both
          "graphsense_tags": ["GraphSense API not configured"], // Or actual tags
          "risk_level": "critical",
          "risk_score": 95
        }
        ```

## Development

*   The `kryptonite-app` service in `docker-compose.yml` mounts the current directory into `/app` in the container. This allows for live reloading of code changes in `main.py` if `uvicorn` is run with the `--reload` flag (Note: the current `Dockerfile` CMD does not include `--reload`. For development, you might want to adjust the CMD in the `Dockerfile` or override the command in `docker-compose.yml`).

## Important Notes & Missing Components

*   **GraphSense API Implementation:** The GraphSense API is an optional external dependency. If you wish to use it, you need to set up your own instance and configure its URL via `GRAPHSENSE_API_BASE_URL`.
*   **Scope of Polkadot.js Lists:** The scam lists from Polkadot.js primarily focus on the Polkadot/Substrate ecosystem. While they provide valuable data, they may not cover scams on all other blockchains.
*   **Sanction Screening:** This application, with its current data sources, does **not** perform comprehensive global sanction screening (e.g., OFAC lists). For such requirements, dedicated commercial data providers or official government sources should be consulted.
*   **`scripts/update_blacklists.sh`:** The functionality and integration of this script are not fully clear from the existing codebase and may require separate attention if its use is desired.

```
