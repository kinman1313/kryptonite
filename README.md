# Kryptonite - Crypto Wallet Verification API & Web UI

Kryptonite is a FastAPI-based application designed to check cryptocurrency wallet addresses against local and external blacklists, and fetch address tags from a GraphSense-compatible API to assess risk. It now includes a simple web interface for ease of use.

## Features

*   Web UI for easy address verification.
*   Verifies crypto addresses against a user-maintained local `blacklist.txt`.
*   Integrates with Polkadot.js phishing lists (`address.json` for scam addresses, `all.json` for scam domains) to identify known malicious entities, primarily within the Polkadot/Substrate ecosystem.
*   Integrates with a GraphSense API (if configured) to retrieve address tags (e.g., identifying tags like "exchange", "miner", "scam").
*   Provides a risk level and score based on local blacklist status, Polkadot.js scam lists, and GraphSense tags.
*   Containerized with Docker and managed via `docker-compose`.

## Project Structure

*   `main.py`: The main FastAPI application code (serves API and frontend).
*   `static/`: Directory containing frontend files (`index.html`, `style.css`, `script.js`).
*   `Dockerfile`: Used to build the Docker image for the Kryptonite application.
*   `docker-compose.yml`: Defines and manages the application services.
*   `requirements.txt`: Python dependencies.
*   `blacklist.txt`: A list of cryptocurrency addresses manually added by the user for blacklisting.
*   `graphsense-REST/`: Intended location for a GraphSense API implementation (currently appears to be missing from this repository).
*   `scripts/update_blacklists.sh`: A script presumably for updating blacklist files (its functionality is not fully integrated or documented within the core app).

## Installation and Usage

Follow these steps to get the Kryptonite Wallet Verifier web application running on your local machine.

### Prerequisites

*   **Docker:** Ensure Docker is installed and running. ([Get Docker](https://docs.docker.com/get-docker/))
*   **Docker Compose:** Ensure Docker Compose is installed. (It's often included with Docker Desktop).

### Steps

1.  **Clone the Repository:**
    Open your terminal and clone the project from GitHub:
    ```bash
    git clone https://github.com/your-username/kryptonite.git 
    # Replace with the actual repository URL if you are forking or have a specific source
    ```
    Navigate into the cloned directory:
    ```bash
    cd kryptonite 
    # Or your chosen directory name if different
    ```

2.  **Customize Local Blacklist (Optional):**
    You can add cryptocurrency addresses you want to personally blacklist to the `blacklist.txt` file located in the root of the project. Add one address per line. These addresses will be flagged as "critical" risk by the application.

3.  **Advanced Configuration (Optional):**
    The application uses default URLs for fetching external data (Polkadot.js lists) and allows for an optional GraphSense API integration. If you need to use a custom GraphSense instance or different Polkadot.js phishing list URLs, you can configure them by editing the `environment` section of the `kryptonite-app` service in the `docker-compose.yml` file:
    ```yaml
    services:
      kryptonite-app:
        # ... other configurations ...
        environment:
          - GRAPHSENSE_API_BASE_URL=http://your-graphsense-api-url:9000 # Example for GraphSense
          - POLKADOT_ADDRESS_JSON_URL=https://your-custom-address-list.json # Example for Polkadot addresses
          - POLKADOT_ALL_JSON_URL=https://your-custom-domain-list.json # Example for Polkadot domains
    ```
    If `GRAPHSENSE_API_BASE_URL` is not set or the API is unavailable, GraphSense checks will be skipped, and this will be noted in the results.

4.  **Build and Run the Application:**
    In your terminal, from the project's root directory (e.g., `kryptonite/`), run:
    ```bash
    docker-compose up --build
    ```
    This command will:
    *   Build the Docker image for the application (this might take a few minutes the first time).
    *   Start the Kryptonite web application.
    You should see log output in your terminal from the application services.

5.  **Access the Web Application:**
    Once the application is running (you'll typically see messages like `Uvicorn running on http://0.0.0.0:8000` in the logs from the `kryptonite-app` service), open your web browser and navigate to:
    [http://localhost:8080](http://localhost:8080) 
    (Port 8080 on your host machine is mapped to port 8000 in the container as per `docker-compose.yml`).

6.  **Using the Web App:**
    *   On the main page, you'll see an input field. Enter the cryptocurrency wallet address you want to check.
    *   Click the "Verify Wallet" button.
    *   The verification results will be displayed below the input field. This includes:
        *   Whether the address is on your local `blacklist.txt`.
        *   Whether the address is on the Polkadot.js scam address list.
        *   Tags from the GraphSense API (if configured and the address is found).
        *   An overall risk level and a numerical risk score.

## Direct API Usage (Advanced)

For developers or automated systems, the Kryptonite API can be accessed directly.

### API Status

*   **GET /api_status**
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
    *   Example Response (address not on any blacklists, GraphSense configured):
        ```json
        {
          "address": "1SomeBitcoinAddressXYZ",
          "sanctioned_by_local_blacklist": false,
          "on_polkadot_scam_list": false,
          "graphsense_tags": [
            {
              "label": "Exchange",
              "source": "SomeGraphSenseSource",
              "category": "organization",
              "abuse": null,
              "tagpack_uri": "http://example.com/tagpack",
              "lastmod": 1678886400000,
              "active": true,
              "currency": "btc"
            }
          ],
          "risk_level": "low", 
          "risk_score": 10     
        }
        ```
    *   Example Response (address on Polkadot.js scam list):
        ```json
        {
          "address": "1PolkadotScammerAddressABC",
          "sanctioned_by_local_blacklist": false,
          "on_polkadot_scam_list": true,
          "graphsense_tags": ["GraphSense API not configured"], 
          "risk_level": "high", 
          "risk_score": 90
        }
        ```

## Development Notes

*   The `kryptonite-app` service in `docker-compose.yml` mounts the current directory into `/app` in the container. This allows for live reloading of code changes in `main.py` if `uvicorn` is run with the `--reload` flag (Note: the current `Dockerfile` CMD does not include `--reload`. For development, you might want to adjust the CMD in the `Dockerfile` or override the command in `docker-compose.yml`).

## Important Considerations & Missing Components

*   **GraphSense API Implementation:** The GraphSense API is an optional external dependency. If you wish to use it, you need to set up your own instance and configure its URL via `GRAPHSENSE_API_BASE_URL`. The repository does not provide a GraphSense API.
*   **Scope of Polkadot.js Lists:** The scam lists from Polkadot.js primarily focus on the Polkadot/Substrate ecosystem. While they provide valuable data, they may not cover scams on all other blockchains.
*   **Sanction Screening:** This application, with its current data sources, does **not** perform comprehensive global sanction screening (e.g., OFAC lists). For such requirements, dedicated commercial data providers or official government sources should be consulted.
*   **`scripts/update_blacklists.sh`:** The functionality and integration of this script are not fully clear from the existing codebase and may require separate attention if its use is desired.
```
