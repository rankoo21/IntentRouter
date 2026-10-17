# IntentRouter

IntentRouter converts a natural-language request into a bounded service lane using a public catalog as evidence. The owner supplies an intent ID, request text, catalog URL, and an allowlist of lanes. Validators independently fetch the catalog, choose exactly one allowed lane, return a confidence score and explanation, and bind the catalog bytes to a SHA-256 digest.

Lifecycle: `DRAFT` -> `ROUTED` -> `CONFIRMED`. Duplicate IDs, invalid lane lists, malformed URLs, unavailable catalogs, forged routing receipts, and validator disagreement fail closed.

Run tests:

```text
python -m pytest test_intent_router.py -q
genvm-lint intent_router.py
```

Verified Studionet deployment (canonical V2): `0xD3b147EE46206a9a8055529eeAa74617A1093874`.
Deployment transaction: `0x377b74f81aedd61a62331b403b8503ced4fa9203f5d51731581a7aeac515c416`.
Live create transaction: `0x6b61314a23ca2cdb25210fc446b091c1ef21e55d37507fbc3d8ab0297c7dae2d`.
Live route transaction: `0x337000ae6b018d2dc5a5bc4d427d0fe1abbd34b6bfbb1a8f5ef165a109e083fc` (`MAJORITY_AGREE`, `SUCCESS`).
