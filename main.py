from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import httpx
from dotenv import load_dotenv
import os
import logging
import json

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

# --- Global Variables ---
blacklist_file = 'blacklist.txt'
SANCTIONED_ADDRESSES = set()

POLKADOT_SCAM_ADDRESSES = set()
KNOWN_SCAM_DOMAINS = set() # Renamed from POLKADOT_SCAM_DOMAINS

POLKADOT_ADDRESS_JSON_URL_ENV = "POLKADOT_ADDRESS_JSON_URL"
POLKADOT_ALL_JSON_URL_ENV = "POLKADOT_ALL_JSON_URL" # For Polkadot domains
DEFAULT_POLKADOT_ADDRESS_JSON_URL = "https://polkadot.js.org/phishing/address.json"
DEFAULT_POLKADOT_ALL_JSON_URL = "https://polkadot.js.org/phishing/all.json" # For Polkadot domains

# --- New: spmedia scam domains list config ---
SPMEDIA_SCAM_DOMAINS_URL_ENV = "SPMEDIA_SCAM_DOMAINS_URL"
DEFAULT_SPMEDIA_SCAM_DOMAINS_URL = "https://raw.githubusercontent.com/spmedia/Crypto-Scam-and-Crypto-Phishing-Threat-Intel-Feed/main/detected_urls.txt"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Function to fetch external blacklists (Polkadot and spmedia) ---
# Renamed from fetch_and_process_polkadot_lists
async def fetch_and_process_external_lists():
    global POLKADOT_SCAM_ADDRESSES, KNOWN_SCAM_DOMAINS # Updated to KNOWN_SCAM_DOMAINS

    polkadot_address_json_url = os.getenv(POLKADOT_ADDRESS_JSON_URL_ENV, DEFAULT_POLKADOT_ADDRESS_JSON_URL)
    polkadot_all_json_url = os.getenv(POLKADOT_ALL_JSON_URL_ENV, DEFAULT_POLKADOT_ALL_JSON_URL)
    spmedia_domains_url = os.getenv(SPMEDIA_SCAM_DOMAINS_URL_ENV, DEFAULT_SPMEDIA_SCAM_DOMAINS_URL)

    async with httpx.AsyncClient(timeout=20.0) as client:
        # Fetch Polkadot.js address.json
        try:
            logger.info(f"Fetching Polkadot.js scam addresses from: {polkadot_address_json_url}")
            response_address = await client.get(polkadot_address_json_url)
            response_address.raise_for_status()
            data_address = response_address.json()
            count = 0
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

        # Fetch Polkadot.js all.json for domains
        try:
            logger.info(f"Fetching Polkadot.js scam domains from: {polkadot_all_json_url}")
            response_all_polkadot = await client.get(polkadot_all_json_url)
            response_all_polkadot.raise_for_status()
            data_all_polkadot = response_all_polkadot.json()
            if isinstance(data_all_polkadot, dict) and "deny" in data_all_polkadot and isinstance(data_all_polkadot["deny"], list):
                denied_domains_polkadot = set(domain.strip() for domain in data_all_polkadot["deny"] if isinstance(domain, str) and domain.strip())
                KNOWN_SCAM_DOMAINS.update(denied_domains_polkadot) # Use KNOWN_SCAM_DOMAINS
                logger.info(f"Successfully loaded {len(denied_domains_polkadot)} domains from Polkadot.js all.json deny list into KNOWN_SCAM_DOMAINS.")
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

        # --- New: Fetch spmedia detected_urls.txt for domains ---
        try:
            logger.info(f"Fetching spmedia scam domains from: {spmedia_domains_url}")
            response_spmedia = await client.get(spmedia_domains_url)
            response_spmedia.raise_for_status()
            domains_text = response_spmedia.text
            count_spmedia = 0
            for line in domains_text.splitlines():
                domain = line.strip()
                if domain and not domain.startswith("#"): # Ignore empty lines and comments
                    KNOWN_SCAM_DOMAINS.add(domain)
                    count_spmedia += 1
            logger.info(f"Successfully loaded {count_spmedia} domains from spmedia list into KNOWN_SCAM_DOMAINS. Total unique scam domains in KNOWN_SCAM_DOMAINS: {len(KNOWN_SCAM_DOMAINS)}.")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching spmedia scam domains: {e}")
        except httpx.RequestError as e:
            logger.error(f"Request error fetching spmedia scam domains: {e}")
        except Exception as e:
            logger.error(f"Unexpected error processing spmedia scam domains: {e}")


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

    # Fetch and process external lists (Polkadot and spmedia)
    await fetch_and_process_external_lists() # Updated call to renamed function

# --- Routes ---
@app.get("/", response_class=FileResponse)
async def serve_index():
    return FileResponse('static/index.html')

@app.get("/api_status")
async def api_status():
    return {"message": "Crypto Wallet Verification API is running"}

@app.get("/verify/{address}")
async def verify_wallet(address: str):
    is_sanctioned_locally = address in SANCTIONED_ADDRESSES
    on_polkadot_scam_list = address in POLKADOT_SCAM_ADDRESSES
    # Note: KNOWN_SCAM_DOMAINS is loaded but not directly used in this address verification endpoint by default.
    # This endpoint primarily focuses on address-based checks.

    result = {
        "address": address,
        "sanctioned_by_local_blacklist": is_sanctioned_locally,
        "on_polkadot_scam_list": on_polkadot_scam_list,
        "graphsense_tags": [],
        "risk_level": "unknown",
        "risk_score": 0
    }

    # Determine initial risk based on blacklist hits
    if is_sanctioned_locally:
        result["risk_level"] = "critical"
        result["risk_score"] = 95
    elif on_polkadot_scam_list: # Not on local, but on Polkadot scam list
        result["risk_level"] = "high"
        result["risk_score"] = 90

    graphsense_base_url = os.getenv("GRAPHSENSE_API_BASE_URL")

    if not graphsense_base_url:
        result["graphsense_tags"] = ["GraphSense API not configured"]
        if result["risk_level"] == "unknown": # Not on any blacklist
            result["risk_level"] = "low"
            result["risk_score"] = 10
    else:
        full_graphsense_url = f"{graphsense_base_url.rstrip('/')}/addresses/{address}/tags"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                logger.info(f"Querying GraphSense API: {full_graphsense_url}")
                response = await client.get(full_graphsense_url)

            if response.status_code == 200:
                tags_data = response.json()
                current_tags = tags_data.get("tags", []) if isinstance(tags_data, dict) else []
                result["graphsense_tags"] = current_tags

                has_scam_tag = any('scam' in str(tag.get('label', '')).lower() for tag in current_tags if isinstance(tag, dict))

                if has_scam_tag:
                    result["risk_level"] = "high"
                    result["risk_score"] = max(result["risk_score"], 75)
                elif result["risk_level"] == "unknown":
                    if current_tags:
                        result["risk_level"] = "low"
                        result["risk_score"] = max(result["risk_score"], 20)
                    else:
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
                if result["risk_level"] == "unknown":
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

    if result["risk_level"] == "unknown":
        result["risk_level"] = "low"
        result["risk_score"] = 10

    result["risk_score"] = max(0, min(100, result["risk_score"]))

    return result
