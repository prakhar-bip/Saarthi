# Sarthi Premium Logging & Self-Healing Synthesis Task Checklist

- [ ] Implement `_store_intermediate` inside `backend/app/agents/code_synthesizer.py`
- [ ] Implement self-healing feedback retry loops (up to 3 attempts) inside `_run_phase` in `backend/app/agents/code_synthesizer.py`
- [ ] Implement `generation_type` folder isolation/filtering in `_merge_codebases` inside `backend/app/services/project_assembler.py`
- [ ] Modify `backend/app/core/logger.py` to overhaul stdout format & ws_log_sink, and implement `SarthiConsoleLogger`
- [ ] Modify `backend/app/services/llm_router.py` to inject agent retry feedback before both ADK Runner and direct API calls
- [ ] Update frontend `ProjectViewer.tsx` to render beautiful colored log badges/capsules for [INFO], [SUCCESS], [WARNING], [HEAL], and [ERROR]
- [ ] Compile and verify entire backend & frontend application
