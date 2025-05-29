from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware # Import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import httpx
from dotenv import load_dotenv
import os
import logging
import json # Added for JSON parsing

load_dotenv()

app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for development
    allow_credentials=True, # Allow credentials (cookies, authorization headers, etc.)
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- Existing Global Variables ---
blacklist_file = 'blacklist.txt'
SANCTIONED_ADDRESSES = set()

# --- New Global Variables for Polkadot.js lists ---
POLKADOT_SCAM_ADDRESSES = set()
POLKADOT_SCAM_DOMAINS = set() # Loaded but not used in /verify endpoint for now

# --- Environment Variable Names for Polkadot.js list URLs ---
POLKADOT_ADDRESS_JSON_URL_ENV = "POLKADOT_ADDRESS_JSON_URL"
POLKADOT_ALL_JSON_URL_ENV = "POLKADOT_ALL_JSON_URL"

# Default URLs for Polkadot.js lists
DEFAULT_POLKADOT_ADDRESS_JSON_URL = "https://polkadot.js.org/phishing/address.json"
DEFAULT_POLKADOT_ALL_JSON_URL = "https://polkadot.js.org/phishing/all.json"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fetch_and_process_polkadot_lists():
    global POLKADOT_SCAM_ADDRESSES, POLKADOT_SCAM_DOMAINS

    address_json_url = os.getenv(POLKADOT_ADDRESS_JSON_URL_ENV, DEFAULT_POLKADOT_ADDRESS_JSON_URL)
    all_json_url = os.getenv(POLKADOT_ALL_JSON_URL_ENV, DEFAULT_POLKADOT_ALL_JSON_URL)

    async with httpx.AsyncClient(timeout=20.0) as client: # Increased timeout for external fetches
        # Fetch address.json
        try:
            logger.info(f"Fetching Polkadot.js scam addresses from: {address_json_url}")
            response_address = await client.get(address_json_url)
            response_address.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            data_address = response_address.json()
            
            count = 0
            # Iterates through entries like "0x...": ["address1", "address2"] or "someSite": ["address3"]
            for _site_key, addresses_list in data_address.items(): 
                if isinstance(addresses_list, list):
                    for addr in addresses_list:
                        if isinstance(addr, str) and addr.strip():
                            POLKADOT_SCAM_ADDRESSES.add(addr.strip())
                            count +=1
            logger.info(f"Successfully loaded {len(POLKADOT_SCAM_ADDRESSES)} unique addresses from Polkadot.js address.json (processed {count} entries).")

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching Polkadot.js address.json: {e}")
        except httpx.RequestError as e:
            logger.error(f"Request error fetching Polkadot.js address.json: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from Polkadot.js address.json: {e}")
        except Exception as e:
            logger.error(f"Unexpected error processing Polkadot.js address.json: {e}")

        # Fetch all.json
        try:
            logger.info(f"Fetching Polkadot.js scam domains from: {all_json_url}")
            response_all = await client.get(all_json_url)
            response_all.raise_for_status()
            data_all = response_all.json()

            # This is the parsing logic specified in the current prompt for all.json
            if isinstance(data_all, dict) and "deny" in data_all and isinstance(data_all["deny"], list):
                denied_domains = set(domain.strip() for domain in data_all["deny"] if isinstance(domain, str) and domain.strip())
                POLKADOT_SCAM_DOMAINS.update(denied_domains)
                logger.info(f"Successfully loaded {len(POLKADOT_SCAM_DOMAINS)} domains from Polkadot.js all.json deny list.")
            else:
                logger.warning("Polkadot.js all.json deny list is not in the expected format or is missing.")
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching Polkadot.js all.json: {e}")
        except httpx.RequestError as e:
            logger.error(f"Request error fetching Polkadot.js all.json: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from Polkadot.js all.json: {e}")
        except Exception as e:
            logger.error(f"Unexpected error processing Polkadot.js all.json: {e}")


@app.on_event("startup")
async def load_application_data():
    global SANCTIONED_ADDRESSES
    # Load local blacklist
    try:
        with open(blacklist_file) as f:
            SANCTIONED_ADDRESSES = set(line.strip() for line in f if line.strip())
        logger.info(f"Successfully loaded {len(SANCTIONED_ADDRESSES)} addresses from local {blacklist_file}")
    except FileNotFoundError:
        logger.warning(f"Local blacklist file '{blacklist_file}' not found. No addresses will be considered sanctioned by local blacklist.")
        SANCTIONED_ADDRESSES = set()
    except Exception as e:
        logger.error(f"Error loading local blacklist file '{blacklist_file}': {e}")
        SANCTIONED_ADDRESSES = set()
    
    # Fetch and process Polkadot.js lists
    await fetch_and_process_polkadot_lists()


@app.get("/", response_class=FileResponse)
async def serve_index():
    return FileResponse('static/index.html')

@app.get("/api_status")
async def api_status():
    return {"message": "Crypto Wallet Verification API is running"}

@app.get("/verify/{address}")
async def verify_wallet(address: str):
    is_sanctioned_locally = address in SANCTIONED_ADDRESSES
    # --- New: Check against Polkadot.js scam address list ---
    on_polkadot_scam_list = address in POLKADOT_SCAM_ADDRESSES
    
    result = {
        "address": address,
        "sanctioned_by_local_blacklist": is_sanctioned_locally,
        "on_polkadot_scam_list": on_polkadot_scam_list, # --- New field ---
        "graphsense_tags": [],
        "risk_level": "unknown",
        "risk_score": 0 
    }

    # Determine initial risk based on local blacklist and Polkadot.js scam list
    if is_sanctioned_locally:
        result["risk_level"] = "critical"
        result["risk_score"] = 95 
    elif on_polkadot_scam_list: # Not on local, but on Polkadot scam list
        result["risk_level"] = "high" # Or critical, depending on policy
        result["risk_score"] = 90 # High score for Polkadot scam list match

    graphsense_base_url = os.getenv("GRAPHSENSE_API_BASE_URL")

    if not graphsense_base_url:
        result["graphsense_tags"] = ["GraphSense API not configured"]
        if result["risk_level"] == "unknown": # Not on any blacklist
            result["risk_level"] = "low"
            result["risk_score"] = 10
    else:
        full_graphsense_url = f"{graphsense_base_url.rstrip('/')}/addresses/{address}/tags"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client: # Timeout for GraphSense
                logger.info(f"Querying GraphSense API: {full_graphsense_url}")
                response = await client.get(full_graphsense_url)

            if response.status_code == 200:
                tags_data = response.json()
                current_tags = tags_data.get("tags", []) if isinstance(tags_data, dict) else []
                result["graphsense_tags"] = current_tags
                
                has_scam_tag = any('scam' in str(tag.get('label', '')).lower() for tag in current_tags if isinstance(tag, dict))
                
                if has_scam_tag:
                    result["risk_level"] = "high" # Could be critical if combined with other factors
                    result["risk_score"] = max(result["risk_score"], 75) 
                elif result["risk_level"] == "unknown": # No local/Polkadot blacklist hit, and no scam tag from GraphSense
                    if current_tags: # Tags found, no scam
                        result["risk_level"] = "low"
                        result["risk_score"] = max(result["risk_score"], 20)
                    else: # No tags
                        result["risk_level"] = "low"
                        result["risk_score"] = max(result["risk_score"], 10)

            elif response.status_code == 404:
                result["graphsense_tags"] = ["Address not found in GraphSense"]
                if result["risk_level"] == "unknown":
                    result["risk_level"] = "low"
                    result["risk_score"] = max(result["risk_score"], 10)
            else:
                error_message = f"GraphSense API error: status code {response.status_code}"
                try:
                    error_detail = response.text
                    error_message += f" - {error_detail[:200]}"
                except Exception:
                    pass
                logger.warning(error_message)
                result["graphsense_tags"] = [error_message]
                if result["risk_level"] == "unknown": # If no prior blacklist hit, API error means medium risk
                    result["risk_level"] = "medium" 
                    result["risk_score"] = max(result["risk_score"], 40)

        except httpx.TimeoutException as e:
            logger.warning(f"GraphSense API request timed out: {str(e)}")
            result["graphsense_tags"] = [f"GraphSense API request timed out"]
            if result["risk_level"] == "unknown":
                result["risk_level"] = "medium" 
                result["risk_score"] = max(result["risk_score"], 45)
        except httpx.RequestError as e:
            logger.warning(f"GraphSense API request error: {str(e)}")
            result["graphsense_tags"] = [f"GraphSense API connection error"]
            if result["risk_level"] == "unknown":
                result["risk_level"] = "medium" 
                result["risk_score"] = max(result["risk_score"], 50)
        except Exception as e:
            logger.error(f"Unexpected error during GraphSense interaction: {str(e)}")
            result["graphsense_tags"] = [f"Unexpected error processing GraphSense data"]
            if result["risk_level"] == "unknown":
                result["risk_level"] = "medium" 
                result["risk_score"] = max(result["risk_score"], 55)
    
    # Final risk assessment if still unknown
    if result["risk_level"] == "unknown": # This implies not on local, not on Polkadot, and GraphSense either not configured or returned no adverse info
        result["risk_level"] = "low"
        result["risk_score"] = 10

    result["risk_score"] = max(0, min(100, result["risk_score"]))
    
    return result
