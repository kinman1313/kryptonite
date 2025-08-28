# Kryptonite - Crypto Wallet Verification API & Web UI

Kryptonite is a FastAPI-based application designed to check cryptocurrency wallet addresses against local and external blacklists, and fetch address tags from a GraphSense-compatible API to assess risk. It now includes a simple web interface for ease of use.

## Features

*   Web UI for easy address verification.
*   Verifies crypto addresses against a user-maintained local `blacklist.txt`.
*   Integrates with Polkadot.js phishing lists (`address.json` for scam addresses) and additional sources like the spmedia threat intel feed (for scam domains) to identify known malicious entities. The Polkadot.js address list is primarily focused on the Polkadot/Substrate ecosystem.
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
*   `scripts/update_blacklists.sh`: A script originally intended for updating blacklists. Currently, its primary crypto address source (CryptoScamDB) is unavailable, and its OFAC SDN list parsing is not reliable for direct address extraction. Manual review and updates to this script would be needed to make it a robust, automated blacklist generator.

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

3.  **Advanced Configuration - External Blacklist Feeds (Optional):**
    The application uses default URLs for fetching external data. The `KNOWN_SCAM_DOMAINS` set is populated by combining data from Polkadot.js `all.json` and the spmedia threat intel feed. If you need to use custom URLs, you can configure them by editing the `environment` section of the `kryptonite-app` service in the `docker-compose.yml` file:
    *   `GRAPHSENSE_API_BASE_URL`: For your GraphSense instance (if used).
    *   `POLKADOT_ADDRESS_JSON_URL`: URL for the Polkadot.js scam address list.
        *   Default: `https://polkadot.js.org/phishing/address.json`
    *   `POLKADOT_ALL_JSON_URL`: URL for the Polkadot.js scam domain list (contributes to `KNOWN_SCAM_DOMAINS`).
        *   Default: `https://polkadot.js.org/phishing/all.json`
    *   `SPMEDIA_SCAM_DOMAINS_URL`: URL for the spmedia scam domain list (contributes to `KNOWN_SCAM_DOMAINS`).
        *   Default: `https://raw.githubusercontent.com/spmedia/Crypto-Scam-and-Crypto-Phishing-Threat-Intel-Feed/main/detected_urls.txt`

    Example `docker-compose.yml` snippet:
    ```yaml
    services:
      kryptonite-app:
        # ... other configurations ...
        environment:
          - GRAPHSENSE_API_BASE_URL=http://your-graphsense-api-url:9000
          - POLKADOT_ADDRESS_JSON_URL=https://your-custom-polkadot-address-list.json
          - POLKADOT_ALL_JSON_URL=https://your-custom-polkadot-domain-list.json
          - SPMEDIA_SCAM_DOMAINS_URL=https://your-custom-spmedia-domain-list.txt
    ```
    If `GRAPHSENSE_API_BASE_URL` is not set or the API is unavailable, GraphSense checks will be skipped.

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
    *   The verification results will be displayed below the input field.

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
    *   Example Response:
        ```json
        {
          "address": "1SomeBitcoinAddressXYZ",
          "sanctioned_by_local_blacklist": false,
          "on_polkadot_scam_list": false,
          "graphsense_tags": [/* ... GraphSense data ... */],
          "risk_level": "low",
          "risk_score": 10
        }
        ```

## Development Notes

*   The `kryptonite-app` service in `docker-compose.yml` mounts the current directory into `/app` in the container. This allows for live reloading of code changes in `main.py` if `uvicorn` is run with the `--reload` flag.

## Important Considerations & Missing Components
