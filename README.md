# Kryptonite - Crypto Wallet Verification API

Kryptonite is a FastAPI-based application designed to check cryptocurrency wallet addresses against a local blacklist and fetch address tags from a GraphSense-compatible API to assess risk.

## Features

*   Verifies crypto addresses against a maintained `blacklist.txt`.
*   Integrates with a GraphSense API to retrieve address tags (e.g., identifying tags like "exchange", "miner", "scam").
*   Provides a risk level and score based on local blacklist status and GraphSense tags.
*   Containerized with Docker and managed via `docker-compose`.

## Project Structure

*   `main.py`: The main FastAPI application code.
*   `Dockerfile`: Used to build the Docker image for the Kryptonite application.
*   `docker-compose.yml`: Defines and manages the application services.
*   `requirements.txt`: Python dependencies.
*   `blacklist.txt`: A list of sanctioned cryptocurrency addresses (one address per line).
*   `graphsense-REST/`: Intended location for the GraphSense API implementation (currently appears to be missing).
*   `scripts/update_blacklists.sh`: A script presumably for updating the blacklist files (its functionality is not fully integrated or documented within the core app).

## Setup and Running the Application

### Prerequisites

*   Docker
*   Docker Compose

### Configuration

1.  **GraphSense API:**
    *   The Kryptonite application requires a running GraphSense API instance. The code for this API is expected to be in the `graphsense-REST` directory or available as a Docker image, but it appears to be missing from this repository.
    *   You need to configure the base URL of your GraphSense API by setting the `GRAPHSENSE_API_BASE_URL` environment variable for the `kryptonite-app` service in the `docker-compose.yml` file, or by setting it in your environment if running outside of docker-compose.
    *   Example: `GRAPHSENSE_API_BASE_URL=http://localhost:9000` (if your GraphSense API is running on `localhost:9000`).
    *   The `docker-compose.yml` includes a commented-out placeholder for a `graphsense-api` service. You will need to uncomment and configure this, or provide the GraphSense API via other means.

2.  **Blacklist:**
    *   The `blacklist.txt` file in the root directory is used to populate the list of locally sanctioned addresses. Add one address per line.

### Running with Docker Compose

1.  **Clone the repository (if you haven't already).**
2.  **Navigate to the project directory.**
3.  **Configure `GRAPHSENSE_API_BASE_URL`:**
    *   You can set this environment variable in your shell, or directly in the `docker-compose.yml` file for the `kryptonite-app` service.
    ```yaml
    services:
      kryptonite-app:
        # ... other configurations ...
        environment:
          - GRAPHSENSE_API_BASE_URL=http://your-graphsense-api-url:9000
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
    *   Description: Verifies a given cryptocurrency address.
    *   Path Parameter:
        *   `address` (string, required): The cryptocurrency address to verify.
    *   Response (Success - Example):
        ```json
        {
          "address": "some_crypto_address",
          "sanctioned_by_local_blacklist": false,
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
          "risk_level": "low", // Possible values: "low", "medium", "high", "critical"
          "risk_score": 10     // Numerical score: 0-100
        }
        ```
    *   Response (GraphSense API not configured):
        ```json
        {
          "address": "another_crypto_address",
          "sanctioned_by_local_blacklist": false,
          "graphsense_tags": ["GraphSense API not configured"],
          "risk_level": "low",
          "risk_score": 10
        }
        ```
    *   Response (Address on local blacklist):
        ```json
        {
          "address": "sanctioned_address",
          "sanctioned_by_local_blacklist": true,
          "graphsense_tags": ["GraphSense API not configured"], // Or actual tags if API is configured
          "risk_level": "critical",
          "risk_score": 95
        }
        ```

## Development

*   The `kryptonite-app` service in `docker-compose.yml` mounts the current directory into `/app` in the container. This allows for live reloading of code changes in `main.py` if `uvicorn` is run with the `--reload` flag (Note: the current `Dockerfile` CMD does not include `--reload`. For development, you might want to adjust the CMD in the `Dockerfile` or override the command in `docker-compose.yml`).

## Missing Components

*   **GraphSense API Implementation:** As mentioned, the actual GraphSense API that this application is designed to connect to (referred to as `graphsense-api` in `main.py` and `docker-compose.yml`) is not provided in this repository. You will need to set up and configure your own instance of a GraphSense-compatible API.
*   **`scripts/update_blacklists.sh`:** The functionality and integration of this script are not fully clear from the existing codebase.
