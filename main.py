from fastapi import FastAPI, HTTPException
import httpx
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

blacklist_file = 'blacklist.txt'


def load_blacklist():
    return set(line.strip() for line in open(blacklist_file))


@app.get("/")
async def home():
    return {"message": "Crypto Wallet Verification API is running"}


@app.get("/verify/{address}")
async def verify_wallet(address: str):
    blacklist = load_blacklist()
    result = {
        "address": address,
        "sanctioned": address in blacklist,
        "tags": [],
        "risk_level": "unknown"
    }

    async with httpx.AsyncClient() as client:
        graphsense_url = f"http://graphsense-api:9000/btc/addresses/{address}/tags"
        try:
            response = await client.get(graphsense_url)
            if response.status_code == 200:
                tags = response.json()
                result["tags"] = tags
                result["risk_level"] = (
                    "high" if result["sanctioned"] or any('scam' in tag['label'].lower() for tag in tags)
                    else "low"
                )
            else:
                result["tags"] = ["No tags found"]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"GraphSense API error: {str(e)}")

    return result
