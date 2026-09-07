from __future__ import annotations
import json, hmac, hashlib, secrets
from datetime import datetime, timezone
from urllib.request import Request, urlopen

def canonical_bytes(payload: dict) -> bytes:
    return json.dumps(payload, separators=(",",":"), sort_keys=True).encode()

def sign(secret: str, timestamp: str, nonce: str, body: bytes) -> str:
    msg=timestamp.encode()+b"."+nonce.encode()+b"."+body
    return hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()

def send_signed(gateway_url: str, source_id: str, secret: str, payload: dict, timeout=10):
    body=canonical_bytes(payload)
    timestamp=datetime.now(timezone.utc).isoformat()
    nonce=secrets.token_hex(16)
    signature=sign(secret,timestamp,nonce,body)
    req=Request(gateway_url,data=body,method="POST",headers={
        "Content-Type":"application/json",
        "X-Vortex-Source-Id":source_id,
        "X-Vortex-Timestamp":timestamp,
        "X-Vortex-Nonce":nonce,
        "X-Vortex-Signature":signature,
    })
    with urlopen(req,timeout=timeout) as r:
        return json.loads(r.read())
