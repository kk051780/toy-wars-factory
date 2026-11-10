# TRAP RAIDERS D17 — metrics reference only

`engagement_metrics.py` is a pure Python, read-only local KPI aggregator. It performs no Roblox network calls, no live collection, no SDK instrumentation, no payments and no personal data collection. All user-origin events MUST be authenticated by a real server adapter in a future project. Input event IDs and ephemeral session IDs are only for toy modelling.

Run: `python -m unittest discover -s tests -p 'test_*.py' -v`.

No claims of real retention, conversion, purchases, revenue, Studio or physical phone testing.
