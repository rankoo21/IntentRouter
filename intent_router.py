# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""Consensus routing of a natural-language request against a public service catalog."""
from genlayer import *
from urllib.parse import urlparse
import hashlib
import json


def enc(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def ident(value):
    value = value.strip().upper()
    if not 3 <= len(value) <= 48 or not all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in value):
        raise gl.vm.UserError("invalid intent id")
    return value


def https(value):
    parsed = urlparse(value.strip())
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
        raise gl.vm.UserError("clean HTTPS URL required")
    return value.strip()


def lanes(value):
    try:
        items = json.loads(value)
    except Exception:
        raise gl.vm.UserError("invalid lane list")
    if type(items) is not list or not 2 <= len(items) <= 8:
        raise gl.vm.UserError("lane list must contain 2 to 8 entries")
    cleaned = [str(item).strip().upper() for item in items]
    if len(set(cleaned)) != len(cleaned) or any(not 2 <= len(item) <= 32 for item in cleaned):
        raise gl.vm.UserError("invalid lane values")
    return cleaned


def canonical_route(request, catalog, allowed):
    """Use a deterministic allowlist match so every validator returns identical bytes."""
    text = (request + " " + catalog).lower()
    scored = [(text.count(lane.lower()), index, lane) for index, lane in enumerate(allowed)]
    score, _, lane = max(scored, key=lambda item: (item[0], -item[1]))
    if score == 0:
        lane = allowed[-1]
    confidence = min(99, 50 + (score * 10)) if score else 40
    return {"lane": lane, "confidence": confidence, "summary": "Canonical allowlist match against the request and fetched catalog."}


class IntentRouter(gl.Contract):
    intents: TreeMap[str, str]

    def __init__(self):
        pass

    def key(self, owner, intent_id):
        return str(owner).lower() + ":" + ident(intent_id)

    @gl.public.write
    def create_intent(self, intent_id: str, request_text: str, catalog_url: str, allowed_lanes_json: str) -> None:
        owner = str(gl.message.sender_address).lower()
        key = self.key(owner, intent_id)
        if self.intents.get(key, ""):
            raise gl.vm.UserError("intent id already exists")
        if not 12 <= len(request_text.strip()) <= 800:
            raise gl.vm.UserError("request text must be 12-800 characters")
        allowed = lanes(allowed_lanes_json)
        self.intents[key] = enc({
            "id": ident(intent_id), "owner": owner, "request": request_text.strip(),
            "catalog_url": https(catalog_url), "allowed_lanes": allowed,
            "state": "DRAFT", "lane": "", "confidence": 0, "summary": "", "digest": ""
        })

    @gl.public.write
    def route_intent(self, intent_id: str) -> None:
        key = self.key(str(gl.message.sender_address), intent_id)
        record = json.loads(self.intents.get(key, "{}"))
        if not record or record["state"] != "DRAFT":
            raise gl.vm.UserError("intent is not routable")

        def run():
            body = gl.nondet.web.get(record["catalog_url"]).body.decode("utf-8")
            if not 40 <= len(body) <= 120000:
                raise gl.vm.UserError("catalog unavailable")
            result = canonical_route(record["request"], body, record["allowed_lanes"])
            return enc({**result, "digest": hashlib.sha256(body.encode()).hexdigest()})

        def valid(receipt):
            if not isinstance(receipt, gl.vm.Return):
                return False
            try:
                body = gl.nondet.web.get(record["catalog_url"]).body.decode("utf-8")
                result = canonical_route(record["request"], body, record["allowed_lanes"])
                expected = {**result, "digest": hashlib.sha256(body.encode()).hexdigest()}
                return json.loads(receipt.calldata) == expected
            except Exception:
                return False

        record.update(json.loads(gl.vm.run_nondet_unsafe(run, valid)))
        record["state"] = "ROUTED"
        self.intents[key] = enc(record)

    @gl.public.write
    def confirm_route(self, intent_id: str) -> None:
        key = self.key(str(gl.message.sender_address), intent_id)
        record = json.loads(self.intents.get(key, "{}"))
        if not record or record["state"] != "ROUTED":
            raise gl.vm.UserError("intent is not routed")
        record["state"] = "CONFIRMED"
        self.intents[key] = enc(record)

    @gl.public.view
    def get_intent(self, owner: str, intent_id: str) -> str:
        return self.intents.get(self.key(owner, intent_id), "{}")
