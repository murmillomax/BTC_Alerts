import os
import time
import json
import hmac
import hashlib
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

BYBIT_API_KEY = os.getenv("BYBIT_API_KEY", "")
BYBIT_API_SECRET = os.getenv("BYBIT_API_SECRET", "")
BYBIT_MERCHANT_ID = os.getenv("BYBIT_MERCHANT_ID", "")

BYBIT_BASE_URL = os.getenv(
    "BYBIT_BASE_URL",
    "https://api-testnet.bybit.com"
)

BYBIT_RECV_WINDOW = "5000"


def validate_config():
    missing = []

    if not BYBIT_API_KEY:
        missing.append("BYBIT_API_KEY")

    if not BYBIT_API_SECRET:
        missing.append("BYBIT_API_SECRET")

    if not BYBIT_MERCHANT_ID:
        missing.append("BYBIT_MERCHANT_ID")

    if missing:
        raise RuntimeError(
            "Faltan variables de Bybit: "
            + ", ".join(missing)
        )


def generate_signature(
    timestamp: str,
    recv_window: str,
    body: str
) -> str:

    payload = (
        timestamp
        + BYBIT_API_KEY
        + recv_window
        + body
    )

    return hmac.new(
        BYBIT_API_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


async def create_qr_payment(
    merchant_trade_no: str,
    amount: str,
    currency: str = "USDT",
    webhook_url: str | None = None,
    user_ip: str | None = None
) -> dict[str, Any]:

    validate_config()

    payload = {
        "merchantId": BYBIT_MERCHANT_ID,
        "clientId": "btcforecast",
        "paymentType": "E_COMMERCE",
        "merchantTradeNo": merchant_trade_no,
        "orderAmount": str(amount),
        "currency": currency,
        "expireTime": 1800
    }

    if webhook_url:
        payload["webhookUrl"] = webhook_url

    if user_ip:
        payload["env"] = {
            "ip": user_ip
        }

    body = json.dumps(
        payload,
        separators=(",", ":"),
        ensure_ascii=False
    )

    timestamp = str(
        int(time.time() * 1000)
    )

    signature = generate_signature(
        timestamp,
        BYBIT_RECV_WINDOW,
        body
    )

    headers = {
        "Content-Type": "application/json",
        "X-BAPI-API-KEY": BYBIT_API_KEY,
        "X-BAPI-TIMESTAMP": timestamp,
        "X-BAPI-SIGN": signature,
        "X-BAPI-RECV-WINDOW": BYBIT_RECV_WINDOW
    }

    url = (
        f"{BYBIT_BASE_URL}"
        "/v5/bybitpay/create_pay"
    )

    async with httpx.AsyncClient(
        timeout=30
    ) as client:

        response = await client.post(
            url,
            content=body,
            headers=headers
        )

    data = response.json()

    if response.status_code >= 400:
        raise RuntimeError(
            f"Bybit HTTP error: {data}"
        )

    if data.get("retCode") != 100000:
        raise RuntimeError(
            f"Bybit API error: "
            f"{data.get('retCode')} - "
            f"{data.get('retMsg')}"
        )

    return data