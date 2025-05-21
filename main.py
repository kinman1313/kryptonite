from fastapi import FastAPI, HTTPException
import httpx
from dotenv import load_dotenv
import os
import logging

load_dotenv()

app = FastAPI()

blacklist_file = 'blacklist.txt'
SANCTIONED_ADDRESSES = set()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def load_application_data():
    global SANCTIONED_ADDRESSES
    try:
        with open(blacklist_file) as f:
            SANCTIONED_ADDRESSES = set(line.strip() for line in f if line.strip()) # Ensure empty lines are not added
        logger.info(f"Successfully loaded {len(SANCTIONED_ADDRESSES)} addresses from {blacklist_file}")
    except FileNotFoundError:
        logger.warning(f"Blacklist file '{blacklist_file}' not found. No addresses will be considered sanctioned by local blacklist.")
        SANCTIONED_ADDRESSES = set()
    except Exception as e:
        logger.error(f"Error loading blacklist file '{blacklist_file}': {e}")
        SANCTIONED_ADDRESSES = set()

@app.get("/")
async def home():
    return {"message": "Crypto Wallet Verification API is running"}

@app.get("/verify/{address}")
async def verify_wallet(address: str):
    is_sanctioned_locally = address in SANCTIONED_ADDRESSES
    
    # Initialize response structure
    result = {
        "address": address,
        "sanctioned_by_local_blacklist": is_sanctioned_locally,
        "graphsense_tags": [],
        "risk_level": "unknown", # Potential values: low, medium, high, critical
        "risk_score": 0 # Numerical score 0-100
    }

    # Determine initial risk based on local blacklist
    if is_sanctioned_locally:
        result["risk_level"] = "critical"
        result["risk_score"] = 95 # High score for local blacklist match

    graphsense_base_url = os.getenv("GRAPHSENSE_API_BASE_URL")

    if not graphsense_base_url:
        result["graphsense_tags"] = ["GraphSense API not configured"]
        if not is_sanctioned_locally: # Not on local blacklist, and GraphSense not configured
            result["risk_level"] = "low" # Or "unknown" - let's assume low if no other info
            result["risk_score"] = 10
        # If sanctioned locally, risk is already critical, no change here
    else:
        full_graphsense_url = f"{graphsense_base_url.rstrip('/')}/addresses/{address}/tags"
        try:
            async with httpx.AsyncClient() as client:
                logger.info(f"Querying GraphSense API: {full_graphsense_url}")
                # Added timeout to prevent indefinite hanging
                response = await client.get(full_graphsense_url, timeout=10.0) 

            if response.status_code == 200:
                tags_data = response.json()
                # Ensure tags_data is a dictionary and 'tags' key exists, expecting a list of dicts
                current_tags = tags_data.get("tags", []) if isinstance(tags_data, dict) else []
                result["graphsense_tags"] = current_tags
                
                has_scam_tag = any('scam' in str(tag.get('label', '')).lower() for tag in current_tags if isinstance(tag, dict))
                
                if has_scam_tag:
                    result["risk_level"] = "high"
                    result["risk_score"] = max(result["risk_score"], 75) # Scam tag implies high risk
                elif is_sanctioned_locally: # Already critical
                    pass
                elif current_tags: # Tags found, no scam, not locally sanctioned
                    result["risk_level"] = "low"
                    result["risk_score"] = max(result["risk_score"], 20)
                else: # No tags, not locally sanctioned
                    result["risk_level"] = "low"
                    result["risk_score"] = max(result["risk_score"], 10)

            elif response.status_code == 404:
                result["graphsense_tags"] = ["Address not found in GraphSense"]
                if not is_sanctioned_locally:
                    result["risk_level"] = "low"
                    result["risk_score"] = max(result["risk_score"], 10)
            else:
                error_message = f"GraphSense API error: status code {response.status_code}"
                try:
                    error_detail = response.text
                    error_message += f" - {error_detail[:200]}" # Limit error detail length
                except Exception:
                    pass # Ignore if response.text is not available or causes error
                logger.warning(error_message) # Changed from error to warning for non-critical API issues
                result["graphsense_tags"] = [error_message]
                # If API fails, risk shouldn't be low unless already determined by local blacklist
                if not is_sanctioned_locally:
                    result["risk_level"] = "medium" # API error introduces uncertainty
                    result["risk_score"] = max(result["risk_score"], 40)


        except httpx.TimeoutException as e:
            logger.warning(f"GraphSense API request timed out: {str(e)}")
            result["graphsense_tags"] = [f"GraphSense API request timed out"]
            if not is_sanctioned_locally:
                result["risk_level"] = "medium" 
                result["risk_score"] = max(result["risk_score"], 45)
        except httpx.RequestError as e: # Covers connection errors, DNS issues etc.
            logger.warning(f"GraphSense API request error: {str(e)}")
            result["graphsense_tags"] = [f"GraphSense API connection error"]
            if not is_sanctioned_locally:
                result["risk_level"] = "medium" 
                result["risk_score"] = max(result["risk_score"], 50)
        except Exception as e: # Catch other potential errors (e.g., JSON decoding if response not valid JSON)
            logger.error(f"Unexpected error during GraphSense interaction: {str(e)}")
            result["graphsense_tags"] = [f"Unexpected error processing GraphSense data"]
            if not is_sanctioned_locally:
                result["risk_level"] = "medium" # Or "high" depending on policy for unexpected errors
                result["risk_score"] = max(result["risk_score"], 55)
    
    # Final check: if risk_level is still "unknown" and not locally sanctioned, default to "low".
    # This can happen if GraphSense is configured, returns no tags, and no errors.
    if result["risk_level"] == "unknown" and not is_sanctioned_locally:
        result["risk_level"] = "low"
        result["risk_score"] = 10

    # Ensure risk_score is within 0-100
    result["risk_score"] = max(0, min(100, result["risk_score"]))
    
    return result
