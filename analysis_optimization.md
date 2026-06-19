# Sarthi Architecture Analysis & Optimization Report

## 1. Complete Analysis of Current Workflow

### Architecture Overview
The current Sarthi system operates via a decoupled LangGraph state machine orchestrating 28 unique specialized agents. The generation lifecycle breaks down roughly into:
- Requirement gathering and documentation creation (PRD, TRD, MRD).
- Human-in-the-loop (HITL) approval gate.
- Architecture blueprinting (Database, Backend, Frontend, DevOps).
- Pipeline validation.
- Massive downstream generation pipeline terminating in `CodeSynthesizerAgent`.

### Identified Weaknesses and Limitations
- **Generation Inconsistencies & Fragmentation**: Previous prompts failed to explicitly mandate full files. The system allowed generation of "placeholder" code using ellipsis (`...`) bypassing actual completion logic.
- **Scope Creep / Minimal "Toy" Scale**: Due to lack of hard scope constraints, typical generations hovered around 1-3 simple entities (e.g. `User`), ignoring broader, feature-rich context.
- **Broken Handoffs**: While the planning agents set up elaborate architecture diagrams, the actual synthesizer step would often hallucinate functionality or ignore the generated Project Documents completely. 
- **Model Routing Bottlenecks**: The Fallback sequence included Nvidia on the Dev environment which increased failure probabilities given incomplete configs.

## 2. Optimized Workflow Architecture

### Overhauled Code Synthesis Strategy
To cure fragmentation and disconnected features, the `CodeSynthesizerAgent` logic has been entirely refactored conceptually through its prompting instructions.
- **Single Source of Truth Enforced**: The Prompts now mandate that the generated frontend, backend, and infrastructure strictly adhere to the `PRD`, `TRD`, `MRD`, and `Implementation Plan` contents avoiding hallucination. 
- **Min SCOPE Enforcement**: Bounding logic added to generation requests—if fewer than 5 functional modules/pages/routes are produced, the engine overrides and infers missing functionality matching the requirements. 

## 3. Implementation Delivery

### Completed Improvements Across the System:
1. **Frontend Requirements**: Forced generation of a minimum of 5 interconnected pages/screens. Design token context propagation strictly applied.
2. **Backend & Database Requirements**: Instructed to generate exact matching schema models, services, Pydantic schemas, and endpoints for each entity bypassing toy-app limitations.  
3. **Infrastructure & DevOps Base**: Rewritten to force fully functional Docker-compose builds with correct proxies, `README` instructions, and strict schema mirroring to TypeScript via `shared/types`.
4. **Development vs. Production Model Routing**: Updated `/app/services/llm_router.py`. Production defaults to Vertex AI ("gemini") falling back safely to OpenRouter. Development environments constrain exclusively around OpenRouter as requested.
5. **No Placeholders Check**: Introduced `"ABSOLUTELY NO TODOs or PLACEHOLDERS"` clauses directly at the point of compilation, ensuring the generator natively solves the logic directly inside the AST context before committing.

With these changes integrated natively, the workflow translates your required user actions directly into a fully encapsulated codebase without omissions.