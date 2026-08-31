# Fix Tasks — Generation Hang (2-hour loop)

- [x] Fix 1: Update .env — correct model names + DEV_PRIMARY_PROVIDER
- [x] Fix 2: Add ADK runner 60s timeout in llm_router.py
- [x] Fix 3: Add 5-min wall-clock timeout per agent in workflow.py
- [x] Fix 4: Reduce MAX_BACKTRACK_DEPTH to 1 in dev in backtrack.py
- [x] Fix 5: Reduce retry count to 2 in dev in workflow.py
- [x] Fix 6: Lower verifier thresholds (pages/features) in dev in verifier_agent.py
