import json
import pytest
from test_harness import load


def test_route_and_confirm():
    contract, prompts, bodies, _ = load()
    lanes = '["SUPPORT","BILLING","SECURITY","OTHER"]'
    contract.create_intent("REQ-1", "I cannot access my account after changing my device", "https://catalog.example/services", lanes)
    body = "Public service catalog: SUPPORT handles access problems; BILLING handles invoices; SECURITY handles abuse."
    result = '{"lane":"SUPPORT","confidence":60,"summary":"unused"}'
    bodies.extend([body, body]); prompts.extend([result, result])
    contract.route_intent("req-1")
    record = json.loads(contract.get_intent("0xowner", "REQ-1"))
    assert record["state"] == "ROUTED" and record["lane"] == "SUPPORT" and len(record["digest"]) == 64
    contract.confirm_route("REQ-1")
    assert json.loads(contract.get_intent("0xowner", "REQ-1"))["state"] == "CONFIRMED"


def test_duplicate_and_lane_guards():
    contract, _, _, user_error = load()
    with pytest.raises(user_error):
        contract.create_intent("BAD", "short", "https://catalog.example/x", '["A"]')
    contract.create_intent("REQ-2", "A valid request that is long enough", "https://catalog.example/x", '["SUPPORT","OTHER"]')
    with pytest.raises(user_error):
        contract.create_intent(" req-2 ", "another valid request", "https://other.example/x", '["SUPPORT","OTHER"]')


def test_forged_validator_receipt_rejected():
    contract, prompts, bodies, user_error = load()
    contract.create_intent("REQ-3", "A valid request that needs routing", "https://catalog.example/x", '["SUPPORT","OTHER"]')
    body = "Public catalog describing support and other service lanes with enough content for the audit."
    bodies.extend([body, body + " tampered"]); prompts.extend(["unused", "unused"])
    with pytest.raises(user_error):
        contract.route_intent("REQ-3")
