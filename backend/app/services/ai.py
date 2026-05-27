import json
import logging
import time
from typing import List, Dict, Any
from app.core.config import settings
from app.agents.context import build_compilation_context
from app.services.llm_router import get_llm_completion

logger = logging.getLogger(__name__)

async def generate_chat_reply(category: str, messages: List[Dict[str, str]], selected_project: dict = None) -> str:
    """
    Generate a reply using the LLM Router.
    Converts list of messages into Chat Completions.
    """
    start_time = time.perf_counter()
    try:
        if selected_project:
            system_prompt = (
                f"You are Sarthi, an expert AI development partner for hackathons specializing in the '{category}' domain. "
                f"The user has selected the project blueprint: **{selected_project.get('name')}**.\n"
                f"Core Idea: {selected_project.get('idea')}\n"
                f"Key Features: {', '.join(selected_project.get('features', []))}\n"
                f"Suggested Tech Stack: {selected_project.get('tech_stack')}\n\n"
                "First, analyze the user's message to determine their specific intent (e.g. brainstorming, refining features, writing code, technical layout discussion).\n"
                "Maintain continuity with prior chat messages: restate relevant confirmed decisions, update assumptions when the user changes direction, and keep the blueprint internally consistent for the compiler agents.\n"
                "When the user proposes a change, translate it into concrete feature, data, API, UI, auth, realtime, or deployment implications.\n"
                "Decide the most suitable response format based on your analysis:\n"
                "- Use clean, conversational paragraphs for explanations and feedback.\n"
                "- Use bullet points / numbered lists for step-by-step guides, checklists, or pros/cons.\n"
                "- Use code blocks for code snippets, commands, or data formats.\n"
                "- CRITICAL: Do NOT use markdown tables to respond to general queries, questions, or refinements. Only use tables if the user explicitly requests structured tabular data.\n\n"
                "Keep your responses concise, friendly, and structured. End with a note suggesting to confirm and compile the codebase when ready."
            )
        else:
            system_prompt = (
                f"You are Sarthi, an expert AI development partner for hackathons specializing in the '{category}' domain. "
                "First, analyze the user's message to determine their intent.\n"
                "Use the conversation as live project memory: infer domain, target users, data needs, UI workflows, and likely integrations before answering.\n"
                "When discussing an idea, keep outputs aligned with what Sarthi's downstream requirement, planning, architecture, and compiler agents can use.\n"
                "Decide the most suitable response format based on your analysis:\n"
                "- ONLY if the user explicitly asks for new project suggestions, ideas, or recommendations, suggest exactly 5 projects formatted strictly as a markdown table with the columns: | # | Project Name | Core Idea | Key Features | Suggested Tech Stack |.\n"
                "- For all other discussions (brainstorming, answering tech questions, explaining layouts), use standard paragraphs, bulleted lists, or code blocks as appropriate. Do NOT use markdown tables.\n\n"
                "Keep your responses concise, friendly, and structured."
            )
        
        chat_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            role = "user" if msg["sender"] == "user" else "assistant"
            chat_messages.append({"role": role, "content": msg["text"]})

        reply = await get_llm_completion(
            agent_name="ChatReply",
            messages=chat_messages,
            temperature=0.7,
            max_tokens=1024
        )
        return reply
    except Exception as e:
        duration = time.perf_counter() - start_time
        logger.error(f"❌ [CHAT COMPLETION FAILED] Error: {e} | Duration: {duration:.2f}s")
        return get_fallback_chat_reply(category, messages[-1]["text"] if messages else "", selected_project)


async def generate_codebase(
    project_name: str, 
    category: str, 
    chat_history: List[Dict[str, str]], 
    theme: str = None,
    blueprint: dict = None,
    theme_palette: dict = None,
    architecture_context: dict = None
) -> Dict[str, Any]:
    """
    Generate files for a project using Nvidia NIM.
    Should return a dictionary containing 'summary' and 'codebase' (list of CodeFiles).
    """
    start_time = time.perf_counter()
    context = "\n".join([f"{m['sender'].upper()}: {m['text']}" for m in chat_history])
    
    if not settings.NVIDIA_API_KEY:
        logger.warning("NVIDIA_API_KEY not configured. Generating template codebase.")
        return get_fallback_codebase(project_name, category, theme, blueprint, theme_palette, architecture_context)

    blueprint_prompt = ""
    if blueprint:
        blueprint_prompt = f"\n\nConfirmed Project Blueprint (JSON):\n{json.dumps(blueprint, indent=2)}"

    theme_palette_prompt = ""
    if theme_palette:
        theme_palette_prompt = f"\n\nSelected Theme Palette (JSON):\n{json.dumps(theme_palette, indent=2)}"

    theme_prompt = f"\nThe user selected the design theme: '{theme}'. Please apply this theme's color palette, design styles, and dark/light configuration in the styling of the generated components using Tailwind CSS classes." if theme else ""

    architecture_context_prompt = ""
    if architecture_context:
        compiled_context = build_compilation_context(architecture_context)
        architecture_context_prompt = (
            "\n\nConnected Sarthi Agent Architecture Context (compact JSON):\n"
            f"{json.dumps(compiled_context, indent=2)}"
        )

    prompt = f"""
You are Sarthi AI compiler. You need to generate a high-fidelity prototype frontend codebase for a hackathon project.
Project Name: {project_name}
Category: {category}{theme_prompt}{blueprint_prompt}{theme_palette_prompt}{architecture_context_prompt}
Context/Chat History:
{context}

Generate a complete, fully functional, multi-file code structure. 
Honor the Connected Sarthi Agent Architecture Context as the source of truth:
- Use declared entities, endpoints, stores, pages, theme tokens, auth rules, realtime channels, and validation notes when present.
- Keep names consistent across README, components, hooks, mock APIs, and state.
- If backend/API/devops agents declared routes or containers, document them in README and mirror their shape in frontend service helpers or mock adapters.
- If validation reports blocking issues, resolve them in the generated prototype or call them out as fixed assumptions in README.
Return your output ONLY as a valid JSON object. Do not include markdown code block syntax (like ```json ... ```). Just return the raw JSON.
The JSON must follow this exact schema:
{{
  "summary": "A concise paragraph describing what the project does, key features, and instructions on how to use it.",
  "codebase": [
    {{
      "name": "README.md",
      "path": "README.md",
      "language": "markdown",
      "content": "# MarkDown content here..."
    }},
    {{
      "name": "App.tsx",
      "path": "src/App.tsx",
      "language": "typescript",
      "content": "Full React component content using clean styling..."
    }},
    {{
      "name": "Component1.tsx",
      "path": "src/components/Component1.tsx",
      "language": "typescript",
      "content": "React component content..."
    }}
  ]
}}

Generate at least 3 files (README.md, src/App.tsx, and at least one custom component). Make sure the content uses beautiful UI layouts.
"""
    try:
        content = await get_llm_completion(
            agent_name="CodebaseCompiler",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Sarthi's final compiler. Generate cohesive React/Tailwind prototype files "
                        "from the chat, blueprint, selected theme, and connected architecture-agent context. "
                        "Return only valid JSON."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=6000
        )
        raw_content = content.strip()
        # Strip code blocks if LLM included them despite instructions
        if raw_content.startswith("```"):
            lines = raw_content.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            raw_content = "\n".join(lines).strip()
            
        data = json.loads(raw_content)
        duration = time.perf_counter() - start_time
        
        # Structured terminal logging
        logger.info("==================================================")
        logger.info(f"🛠️ [CODEBASE GENERATION SUCCESS] Latency: {duration:.2f}s")
        logger.info(f"🔹 Project Name: {project_name}")
        logger.info(f"🔹 Category: {category}")
        logger.info(f"🔹 Summary: {data.get('summary', '')[:100]}...")
        logger.info(f"🔹 Code Files Generated ({len(data.get('codebase', []))}):")
        for f in data.get('codebase', []):
            logger.info(f"  - {f.get('path')} ({len(f.get('content', ''))} chars)")
        logger.info("==================================================")
        
        if "summary" in data and "codebase" in data:
            return data
        else:
            raise ValueError("Invalid JSON structure returned by NIM model")
    except Exception as e:
        duration = time.perf_counter() - start_time
        logger.error(f"❌ [CODEBASE GENERATION FAILED] Error: {e} | Duration: {duration:.2f}s")
        return get_fallback_codebase(project_name, category, theme, blueprint, theme_palette, architecture_context)


FALLBACK_PROJECTS = {
    "startup": [
        {
            "name": "SaaS Growth CRM & Lead Engager",
            "idea": "A comprehensive B2B lead management and pipeline engagement platform tailored for early-stage startups. It centralizes customer communications, optimizes sales pipelines with real-time status reporting, handles dynamic contact action queues, and automates email sequence workflows to maximize user acquisition efficiency.",
            "features": [
                "Interactive Kanban Sales Pipeline: Drag-and-drop opportunity cards with instant value aggregates.",
                "Automated Outreach Sequence Builder: Configure multi-step email cadences triggered by client sign-up states.",
                "Realtime Notification Center: Pushes browser alerts whenever high-value leads perform target page events.",
                "Customer Activity Timeline: Chronological audit log tracking touchpoints, meetings, and support tickets.",
                "Growth Metrics Graph Dashboard: Analytics widget summarizing MRR, Churn Rate, LTV, and CAC inputs."
            ],
            "tech_stack": "React (Vite SPA), Tailwind CSS, Zustand Stores, FastAPI Backend, MongoDB Database, Redis Caching"
        },
        {
            "name": "AI-Powered Slide Deck Architect",
            "idea": "An interactive slide deck planner and narrative builder that leverages generative intelligence to structure business proposals. It parses raw product descriptions, configures responsive visual templates, maps slide-by-slide hierarchies, and provides AI content assistant widgets to bootstrap startup investor pitches.",
            "features": [
                "Markdown-to-Slide Compiler: Automatically transform bulleted outlines into structured slide layout blocks.",
                "Drag-and-Drop Narrative Sequencer: Rearrange pitch modules with auto-saving state validation.",
                "Nvidia NIM AI Copilot Sidebar: Real-time contextual content suggestions and copy improvements.",
                "Responsive Layout Previewer: Inspect presentation slides in mobile, tablet, and desktop aspect ratios.",
                "Universal JSON Export: Download clean schema metadata for custom player integrations."
            ],
            "tech_stack": "Next.js Framework, Tailwind CSS, Framer Motion, FastAPI Backend, SQLite relational storage, Nvidia NIM API"
        },
        {
            "name": "SaaS Billing & Metrics Aggregator",
            "idea": "A high-fidelity metrics dashboard built to track MRR growth and calculate transaction metrics. It offers mock Stripe integration, aggregates revenue numbers, provides scenario-modeling sandboxes, and logs churn rates to guide funding rounds and financial presentations.",
            "features": [
                "Simulated Stripe Sync Pipeline: Webhook listeners logging mock payment status upgrades.",
                "Scenarios Forecasting Sandbox: Interactive range sliders to simulate price adjustments impact on MRR.",
                "Financial PDF Report Exporter: Automated document generation detailing cash flow balances.",
                "Custom Alert Thresholds: Send webhook notifications when MRR milestones or churn rates cross set limits.",
                "Unified Cohort Retention Chart: Matrix representation of active subscribers over time."
            ],
            "tech_stack": "TypeScript, Tailwind CSS, Recharts Graphics, FastAPI, PostgreSQL Relational Database, Redis Broker"
        }
    ],
    "finance": [
        {
            "name": "Micro-Savings Companion",
            "idea": "An automated micro-deposit and financial goal ledger that securely saves transaction round-ups. It connects to mock banking data stream models, calculates residual change, and allocates fractional savings to specific long-term target goals via custom user rules.",
            "features": [
                "Automated Round-Up Engine: Multi-account ledger computing transaction margins for savings.",
                "Tiered Goal Allocation Framework: Split saved fractions across custom investment buckets dynamically.",
                "Interactive Savings Milestones: Visual progress ring with milestone badges and notification alerts.",
                "Smart Recurrence Scheduler: Form controllers defining daily, weekly, or monthly transfer rules.",
                "Projected Compound Calculator: Analytics forecasting growth trends over selectable year periods."
            ],
            "tech_stack": "React (Vite SPA), Tailwind CSS, Zustand Stores, Node.js Express, MongoDB, localForage storage"
        },
        {
            "name": "Crypto Asset Tracker & Modeler",
            "idea": "A real-time cryptocurrency portfolio tracker and scenario planning simulator. It maps active token holdings, fetches mock coin rates, logs transaction entries, and visualizes profits, losses, and historical values using interactive analytics widgets.",
            "features": [
                "Mock Pricing Live Simulator: Simulates fluctuations in coin valuations with connection heartbeat controls.",
                "Transaction Entry Ledger: Multi-currency records supporting buy, sell, transfer, and swap entries.",
                "Portfolio Allocation Charts: Interactive pie and radar graphs detailing asset distribution percentages.",
                "Price Threshold Webhook Alerts: Configure automatic notifications on sudden valuation shifts.",
                "Profit/Loss Projection Timeline: Historical performance curve chart tracking balance changes."
            ],
            "tech_stack": "TypeScript, Tailwind CSS, Recharts Library, Node.js Express, Redis cache stores, SQLite relational db"
        },
        {
            "name": "Split-Bill Ledger & Settlements",
            "idea": "A shared expense ledger utility built for group expense tracking and bill splitting. It logs shared payments, runs balance reconciliation math to minimize transfer loops, and manages transaction histories and reminder logs.",
            "features": [
                "Dynamic Split Ratio Calculator: Split bills by percentages, shares, or unequal item amounts.",
                "Optimized Balance Reconciler: Minimize transactions needed to settle debts across group members.",
                "Mock Settlement Payment Gate: Simulates immediate paybacks with instant state confirmation.",
                "Recurring Expense Scheduler: Creates recurring items for utility bills and shared subscriptions.",
                "Group Activity Ledger: Auditable chronology detailing added expenses and settlements."
            ],
            "tech_stack": "React (Vite SPA), Tailwind CSS, FastAPI Backend, PostgreSQL Relational Database, JWT middleware guards"
        }
    ],
    "health": [
        {
            "name": "CalmPath Breathing Guide",
            "idea": "An interactive wellness application featuring a real-time paced breathing visualizer. It provides Inhale/Hold/Exhale guidance, tracks breathing sessions, logs stress indicators, and displays wellness trends on a modern dashboard to help users maintain mindfulness.",
            "features": [
                "Paced Breathing Ring: Expanding and contracting Framer Motion visualizer with customizable tempos.",
                "Stress Score Mood Logger: Form-based logger to record daily anxiety levels and write notes.",
                "Audio Guidance Synthesis: Dynamic sound tones playing in sync with breathing phase transitions.",
                "Weekly Wellness Analytics: Recharts line visualization charting logged stress scores over time.",
                "Local Session Cache: LocalStorage persistence allowing complete offline-first breathing guides."
            ],
            "tech_stack": "React (Vite SPA), Tailwind CSS, Framer Motion, Zustand Stores, LocalStorage APIs"
        },
        {
            "name": "Hydration Tracker & Fluid Log",
            "idea": "A high-fidelity water intake tracker designed to optimize daily hydration goals. It sets custom targets based on body metrics, handles fluid logs, reminds users using in-app banners, and displays intake grids to visualize milestones.",
            "features": [
                "Fluid Logging Widget: Log water, tea, or coffee inputs with instant hydration multiplier calculations.",
                "Custom Intake Goal Configurator: Form computing recommended intake using user weight and activity logs.",
                "Hourly Reminder Notification Engine: Websocket-backed prompts driving in-app notifications.",
                "Intake History Calendar Grid: Grid visualization charting hydration performance over weeks.",
                "Interactive Water Milestone Badges: Gamified goals rewarding consistent compliance."
            ],
            "tech_stack": "Next.js SPA Mode, Tailwind CSS, localForage, Service Workers, FastAPI, PostgreSQL"
        },
        {
            "name": "Workout Routine Builder & Timer",
            "idea": "A modern workout customizer and interval countdown timer designed for training sessions. It allows users to build routine sets, customize rest buffers, manage timed countdown triggers, and review history logs on a unified user panel.",
            "features": [
                "Workout Plan Creator: Form builder supporting custom names, sets, reps, and time caps.",
                "Responsive Interval Timer: Clean visual countdown with audio alerts for workout and rest states.",
                "Exercise Library Manager: Customizable database of default card movements and guidelines.",
                "Performance History Analytics: Graph dashboards displaying active training duration averages.",
                "Active Share Sheet: Export workout routines as structured JSON configurations."
            ],
            "tech_stack": "TypeScript, Tailwind CSS, React Context, Node.js Express, MongoDB database"
        }
    ],
    "education": [
        {
            "name": "Spaced Repetition Flashcards",
            "idea": "An interactive flashcard study assistant powered by spaced repetition learning models. It manages user-created study decks, logs retention scores, and schedules cards for review based on difficulty ratings to accelerate knowledge retention.",
            "features": [
                "Deck Builder & Card Editor: Rich-text card creator supporting markdown prompts and code blocks.",
                "Spaced Repetition Scheduler: Algorithm-driven scheduling queue displaying weaker cards more frequently.",
                "Interactive Quiz Workspace: Double-sided card flip animations with self-grading controls.",
                "Study Session Analytics: Progress bar charts logging daily card review counts and accuracy scores.",
                "Shared Study Pool: Search and import community-shared card decks from global repository structures."
            ],
            "tech_stack": "React (Vite SPA), Tailwind CSS, Framer Motion, FastAPI Backend, MongoDB Database, Redis Cache"
        },
        {
            "name": "Pomodoro Focus Study Log",
            "idea": "A productivity dashboard combining Pomodoro work-break timers with task list tracking. It helps students partition study intervals, block distractions, log completed tasks, and view focus time metrics.",
            "features": [
                "Pomodoro Cycle Timer: Adjustable focus/short break/long break intervals with audio alarms.",
                "Focus Task Board: List management widget linking active tasks directly to the running timer.",
                "Daily Focus Log Chart: Recharts bar timeline tracking total daily focus minutes.",
                "In-App Distraction Shield: Configurable browser notifications block toggle during active sessions.",
                "Streak Milestone Tracker: Tracks consecutive study days with motivation prompts."
            ],
            "tech_stack": "TypeScript, Tailwind CSS, React Context, Zustand Stores, LocalStorage persistence"
        },
        {
            "name": "Skill Tree Learner & Roadmap",
            "idea": "A visual mapping application that structures educational subjects into interactive learning trees. It organizes complex topics into step-by-step nodes, tracks progress checkbox milestones, and suggests resources for each item.",
            "features": [
                "Interactive Skill Tree Graph: Visual Node Graph rendering dependent learning paths.",
                "Resources Database: Link resource tutorials, videos, and exercises to skill nodes.",
                "Concept Checkpoint Quizzes: In-app mini quizzes validating knowledge before unlocking nodes.",
                "Progress Milestone Tracker: Real-time progress bar computing overall subject completion.",
                "Custom Pathway Builder: Drag-and-drop node tool enabling teachers to design roadmaps."
            ],
            "tech_stack": "React Flow Library, Tailwind CSS, Framer Motion, FastAPI, SQLite Relational Database"
        }
    ],
    "productivity": [
        {
            "name": "Milestone Board & Sprint Tracker",
            "idea": "A drag-and-drop project management board tailored for sprint tracking. It coordinates tasks across pipeline columns (To Do, In Progress, Review, Done), calculates progress bars, and filters tasks by priority and assignment metrics.",
            "features": [
                "Drag-and-Drop Task Columns: Interactive board mapping tasks to workflow columns.",
                "Sprint Milestone Calculator: Progress bar tracking completed story points vs target values.",
                "Resource Allocation Manager: Assign tasks to team members with workload balance checks.",
                "Project Activity Feed: Chronological stream logging drag updates and task completions.",
                "Task Priority Matrix: Color-coded tags filtering tasks by urgency and impact criteria."
            ],
            "tech_stack": "React (Vite SPA), Tailwind CSS, Zustand client stores, Node.js Express, MongoDB"
        },
        {
            "name": "Eisenhower Priority Matrix",
            "idea": "A task prioritizer utilizing the Eisenhower Matrix model. It organizes todos into four quadrants (Do First, Schedule, Delegate, Eliminate), supports drag re-ordering, and structures task checklists to maximize daily efficiency.",
            "features": [
                "Quadrant Visual Grid: Clean 2x2 grid representing urgent/important prioritization splits.",
                "Quick-Add Task Bar: Inline text field enabling immediate task addition to active quadrants.",
                "Task Archive Vault: Toggle panels displaying historical completed tasks by date.",
                "Daily Planning Prompts: Short morning alerts prompting users to clear Quadrant 4 tasks.",
                "State Recovery Engine: Auto-saving data layers preventing data loss on window closes."
            ],
            "tech_stack": "TypeScript, Tailwind CSS, Framer Motion, LocalStorage APIs, React Context"
        },
        {
            "name": "Standup Notes & Hook Builder",
            "idea": "A team coordination portal that captures daily standup notes and triggers notification hooks. It logs yesterday's accomplishments, today's goals, and active blockers, and supports exporting logs to team channels.",
            "features": [
                "Standup Template Form: Text areas structured for completed tasks, goals, and blockers.",
                "Mock Slack Webhook Trigger: Simulate publishing formatted logs to team channels.",
                "Historical Standup Ledger: Database tracking past standup submissions by team members.",
                "Active Blockers Dashboard: Banner panel highlighting critical issues blocking progress.",
                "Clipboard Copy Formatter: Format updates as clean markdown bullet points for quick copies."
            ],
            "tech_stack": "Next.js SPA, Tailwind CSS, FastAPI Backend, SQLite relational storage, Redis pub/sub"
        }
    ],
    "sustainability": [
        {
            "name": "Carbon Calculator & Offset Log",
            "idea": "A sustainability calculator that computes commuting carbon footprints and logs offset activities. It guides users through daily transport inputs, performs carbon math, and lists eco-friendly actions to balance emissions.",
            "features": [
                "Commuting Footprint Slider: Interactive commuter forms computing CO2 emissions instantly.",
                "Carbon Offset Catalog: Directory detailing offset actions like planting trees or recycling.",
                "Monthly Carbon Breakdown Chart: Recharts pie representation displaying emissions by source.",
                "Community Green Leaderboard: Gamified standings page tracking offset scores.",
                "Eco-Tips Recommendation Engine: Tailored notification cards prompting custom energy saving guides."
            ],
            "tech_stack": "React (Vite SPA), Tailwind CSS, Recharts, FastAPI Backend, MongoDB Database, JWT auth"
        },
        {
            "name": "Waste Sorting & Recycling Guide",
            "idea": "An educational guide identifying recyclable, compostable, and trash items. It features a fast fuzzy-matching catalog search, displays detailed item sheets with disposal rules, and lists nearby center drop-offs.",
            "features": [
                "Fuzzy Material Search Bar: Real-time filter sorting items by material composition.",
                "Item Classification Details: Visual detail cards detailing local sorting regulations.",
                "Mock Recycling Centers Map: Mapbox dashboard displaying nearby collection points.",
                "Custom Disposal Checklist: In-app organizer helping users log waste sorting events.",
                "Sorting Milestone Badges: Digital rewards for logging correct sorting practices."
            ],
            "tech_stack": "Next.js SPA, Tailwind CSS, Mapbox GL UI, SQLite Database, FastAPI Backend"
        },
        {
            "name": "Energy Saver Utility Hub",
            "idea": "A smart home utility logger that monitors appliance power consumption and computes energy scores. It tracks appliance ratings, charts daily usage history, and suggests optimization steps to lower carbon outputs.",
            "features": [
                "Appliance Power Registry: Form tracker logging appliances and standard wattage rates.",
                "Usage Duration Log: Time input controllers recording hourly appliance activation stats.",
                "Daily Energy Score: Algorithm computing household efficiency ratings out of 100.",
                "Consumptions Column Chart: Recharts columns charting power usage patterns by hour.",
                "Smart Saving Workflows: Push notifications prompting users to turn off heavy appliances."
            ],
            "tech_stack": "TypeScript, Tailwind CSS, ChartJS, Node.js Express, MongoDB, Redis cache"
        }
    ],
    "other": [
        {
            "name": "API Sandbox & JSON Console",
            "idea": "An interactive API tester and JSON syntax formatter. It allows developers to configure mock requests, test status outputs, format payloads, and inspect authorization headers in a unified web console.",
            "features": [
                "Request Builder Console: Input URL, select HTTP verbs, and write JSON payloads.",
                "Status Code Mock Selector: Test response renderings for success, validation, and auth error states.",
                "Monaco JSON Code Editor: Code console with syntax checks and formatting tools.",
                "Headers Inspection Panel: Check authorization tokens and response metadata in tab views.",
                "Mock API Endpoints Pool: Simulated responses dashboard for testing client fetch functions."
            ],
            "tech_stack": "React (Vite SPA), Tailwind CSS, Monaco Editor, Express, LocalStorage APIs"
        },
        {
            "name": "WebSocket Mock Loopback Chat",
            "idea": "A local chat client simulating server loopbacks using client-side WebSockets. It enables testing group channel joins, chat history rendering, message dispatching, and connection status alerts.",
            "features": [
                "Active Channel Sidebar: Switch workspaces and group chat channels dynamically.",
                "Message Box Scroll View: Automatic auto-scroll messaging interface with sender tags.",
                "Status Connection Banner: Displays connection state changes (connecting, active, closed).",
                "Loopback Message Simulator: Automatically responds with simulated AI answers."
            ],
            "tech_stack": "React (Vite SPA), Tailwind CSS, WebSockets, Node.js, Redis cached logs"
        }
    ]
}

async def generate_project_suggestions(category: str) -> List[Dict[str, Any]]:
    """
    Generate exactly 2 project suggestions in JSON format using Nvidia NIM,
    or fall back to the structured fallback lists.
    """
    category_lower = category.lower()
    if not settings.NVIDIA_API_KEY:
        logger.warning("NVIDIA_API_KEY not configured. Falling back to local structured suggestions.")
        return FALLBACK_PROJECTS.get(category_lower, FALLBACK_PROJECTS["other"])
    
    prompt = f"""
You are Sarthi, an expert AI partner. Generate exactly 2 project suggestions for a hackathon under the category '{category}'.
Each suggestion must represent a detailed blueprint that can flow cleanly through Sarthi's connected agent pipeline.
For each suggestion, provide:
1. name (Project Name)
2. idea (A concise description of the application's vision - between 40 to 60 words)
3. features (List of exactly 3 descriptive system features/modules, e.g., 'Real-time WebSocket dashboard with interactive SVG charts' - under 15 words each)
4. tech_stack (Suggested Tech Stack, e.g. "React, Tailwind CSS, FastAPI, MongoDB")

Return your output ONLY as a valid JSON array of objects. Do not include markdown code block syntax. Just return the raw JSON.
The JSON must match this structure:
[
  {{
    "name": "Project Name",
    "idea": "Concise core idea description...",
    "features": [
      "Feature 1 description...",
      "Feature 2 description...",
      "Feature 3 description..."
    ],
    "tech_stack": "React, FastAPI, MongoDB"
  }}
]
"""
    try:
        content = await get_llm_completion(
            agent_name="ProjectSuggestions",
            messages=[
                {
                    "role": "system",
                    "content": "You are Sarthi's blueprint ideation agent. Produce detailed suggestions."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2048
        )
        raw_content = content.strip()
        if raw_content.startswith("```"):
            lines = raw_content.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            raw_content = "\n".join(lines).strip()
        
        data = json.loads(raw_content)
        if isinstance(data, list) and len(data) > 0:
            return data
        else:
            raise ValueError("Invalid suggestions format returned by NIM model")
    except Exception as e:
        logger.error(f"Error generating suggestions from NIM: {e}. Falling back.")
        return FALLBACK_PROJECTS.get(category_lower, FALLBACK_PROJECTS["other"])

def get_fallback_chat_reply(category: str, user_text: str, selected_project: dict = None) -> str:
    category_lower = category.lower()
    text_lower = user_text.lower()
    
    if selected_project:
        return (
            f"Understood. Let's discuss refinement of the blueprint for **{selected_project.get('name')}**. "
            f"Regarding your query '{user_text}', we can structure this component dynamically. What specific database fields or page animations do you want to add?"
        )

    responses: Dict[str, str] = {
        "startup": f"I can help construct a startup pitch draft and MVP architecture for '{user_text}'. I suggest creating a modular dashboard file containing SaaS growth metrics.",
        "finance": f"I can help construct a financial companion framework for '{user_text}'. I suggest creating a modular dashboard file containing calculation states and transactional lists.",
        "health": f"That sounds like a helpful health project. I have structured React widgets for mood tracking and deep breathing cycles. Let's build a codebase prototype for '{user_text}'.",
        "education": f"For this learning system, I recommend generating an interactive Flashcard quiz layout using standard React hooks. It will help test user retention rates.",
        "productivity": f"I will build a virtual Chief of Staff workspace template. We can compile check-lists and priority tags to help developers coordinate milestones.",
        "sustainability": f"An essential idea. I'll design a Carbon calculator layout with commuting values, carbon conversion weights, and simple suggestions.",
        "other": f"Understood. I will prepare custom interactive modules to bootstrap your hackathon pitch. Let's configure the structure."
    }
    reply = responses.get(category_lower, "I'll compile the custom modules for your workspace based on your specifications.")
    return f"{reply}\n\nType a name for your compiled codebase project below and click 'Generate' to initialize the software development pipeline!"

def get_fallback_codebase(
    name: str,
    category: str,
    theme: str = None,
    blueprint: dict = None,
    theme_palette: dict = None,
    architecture_context: dict = None
) -> Dict[str, Any]:
    capital_name = name.capitalize()
    normalized_category = category.lower()
    
    theme_lower = (theme or "").lower()
    
    # Default is Minimal Slate
    bg_class = "bg-slate-50 text-slate-800"
    header_class = "text-slate-900"
    subtext_class = "text-slate-500"
    card_class = "bg-white border-slate-100"
    primary_btn = "bg-indigo-600 hover:bg-indigo-700 text-white"
    badge_class = "bg-indigo-50 text-indigo-700 border-indigo-100"
    mrr_card_class = "bg-indigo-50 border-indigo-100 text-indigo-900"
    churn_card_class = "bg-rose-50 border-rose-100 text-rose-900"
    
    if "emerald" in theme_lower or "sage" in theme_lower or "green" in theme_lower:
        bg_class = "bg-emerald-50 text-emerald-900"
        header_class = "text-emerald-950"
        subtext_class = "text-emerald-700"
        card_class = "bg-white border-emerald-100"
        primary_btn = "bg-emerald-600 hover:bg-emerald-700 text-white"
        badge_class = "bg-emerald-100 text-emerald-800 border-emerald-200"
        mrr_card_class = "bg-emerald-50 border-emerald-100 text-emerald-900"
        churn_card_class = "bg-amber-50 border-amber-100 text-amber-900"
    elif "synthwave" in theme_lower or "dark" in theme_lower or "cyber" in theme_lower or "neon" in theme_lower:
        bg_class = "bg-slate-950 text-slate-100"
        header_class = "text-pink-500"
        subtext_class = "text-indigo-430"
        card_class = "bg-slate-900 border-slate-800"
        primary_btn = "bg-pink-600 hover:bg-pink-700 text-white"
        badge_class = "bg-indigo-950 text-indigo-300 border-indigo-900"
        mrr_card_class = "bg-slate-900 border-pink-500/30 text-pink-400"
        churn_card_class = "bg-slate-900 border-cyan-500/30 text-cyan-400"
    elif "warm" in theme_lower or "sunrise" in theme_lower or "orange" in theme_lower:
        bg_class = "bg-stone-50 text-stone-900"
        header_class = "text-orange-950"
        subtext_class = "text-stone-600"
        card_class = "bg-white border-stone-150"
        primary_btn = "bg-orange-600 hover:bg-orange-700 text-white"
        badge_class = "bg-orange-50 text-orange-850 border-orange-200"
        mrr_card_class = "bg-orange-50 border-orange-100 text-orange-900"
        churn_card_class = "bg-amber-50 border-amber-150 text-amber-900"

    blueprint_json_str = json.dumps(blueprint, indent=2) if blueprint else "None"
    theme_palette_json_str = json.dumps(theme_palette, indent=2) if theme_palette else "None"
    compiled_architecture_context = build_compilation_context(architecture_context or {}) if architecture_context else {}
    architecture_context_json_str = json.dumps(compiled_architecture_context, indent=2) if compiled_architecture_context else "None"

    readme = {
        "name": "README.md",
        "path": "README.md",
        "language": "markdown",
        "content": f"""# {capital_name} ({category.upper()} category)

Welcome to your customized Sarthi hackathon prototype!

## Confirmed Project Configuration

### Selected Design Theme
* Theme Name: **{theme or 'Slate Minimal'}**

### Theme Palette (JSON)
```json
{theme_palette_json_str}
```

### Confirmed Blueprint (JSON)
```json
{blueprint_json_str}
```

### Connected Agent Context (JSON)
```json
{architecture_context_json_str}
```

## Highlights
- Custom dashboard elements with seamless state synchronization.
- Built with high-fidelity React components.
- Uses Sarthi architecture memory, optimization guidance, and code-generation planning context when available.
- Modern modular code files, fully ready to build.

## Getting Started
1. Run `npm install`
2. Run `npm run dev`
3. Deploy immediately for your hackathon pitch!"""
    }
    
    if normalized_category == "startup":
        codebase = [
            readme,
            {
                "name": "App.tsx",
                "path": "src/App.tsx",
                "language": "typescript",
                "content": f"""import React, {{ useState }} from 'react';
import SaaSMetrics from './components/SaaSMetrics';

export default function App() {{
  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 p-8">
      <header className="max-w-4xl mx-auto mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">{capital_name}</h1>
          <p className="text-slate-500">Startup Launch Platform</p>
        </div>
      </header>
      
      <main className="max-w-4xl mx-auto">
        <section className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex flex-col items-center">
          <h2 className="text-xl font-semibold mb-6">SaaS Metric Dashboard</h2>
          <SaaSMetrics />
        </section>
      </main>
    </div>
  );
}}"""
            },
            {
                "name": "SaaSMetrics.tsx",
                "path": "src/components/SaaSMetrics.tsx",
                "language": "typescript",
                "content": """import React, { useState } from 'react';

export default function SaaSMetrics() {
  const [mrr, setMrr] = useState(12500);
  const [churn, setChurn] = useState(2.4);

  return (
    <div className="w-full max-w-lg">
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="p-4 bg-indigo-50 rounded-xl border border-indigo-100">
          <p className="text-xs text-indigo-600 font-semibold uppercase">Monthly Recurring Revenue</p>
          <h3 className="text-2xl font-extrabold text-indigo-900 mt-1">${mrr.toLocaleString()}</h3>
        </div>
        <div className="p-4 bg-rose-50 rounded-xl border border-rose-100">
          <p className="text-xs text-rose-600 font-semibold uppercase">Customer Churn Rate</p>
          <h3 className="text-2xl font-extrabold text-rose-900 mt-1">{churn}%</h3>
        </div>
      </div>
      
      <div className="bg-stone-50 p-4 rounded-xl border border-stone-200">
        <label className="text-xs font-semibold text-stone-500 block mb-2">Simulate MRR Growth</label>
        <input 
          type="range" 
          min="5000" 
          max="50000" 
          step="1000" 
          value={mrr} 
          onChange={(e) => setMrr(parseInt(e.target.value))}
          className="w-full h-2 bg-stone-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
        />
        <div className="flex justify-between text-[10px] text-stone-400 mt-1">
          <span>$5k</span>
          <span>$50k</span>
        </div>
      </div>
    </div>
  );
}"""
            }
        ]
    elif normalized_category == "finance":
        codebase = [
            readme,
            {
                "name": "Dashboard.tsx",
                "path": "src/Dashboard.tsx",
                "language": "typescript",
                "content": f"""import React, {{ useState }} from 'react';
import SavingsCalculator from './SavingsCalculator';

export default function Dashboard() {{
  const [balance, setBalance] = useState(2450.75);
  
  return (
    <div className="p-6 bg-stone-50 rounded-3xl border border-stone-200/60 max-w-xl mx-auto shadow-sm">
      <h2 className="text-2xl font-bold font-display text-indigo-900 mb-2">{capital_name} Planner</h2>
      <p className="text-stone-500 mb-6">Financial tracking & budget optimization</p>
      
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="p-4 bg-white rounded-2xl border border-stone-100">
          <span className="text-xs text-stone-400 font-medium uppercase tracking-wide">Total Balance</span>
          <p className="text-xl font-bold text-stone-800 mt-1">${{balance.toFixed(2)}}</p>
        </div>
        <div className="p-4 bg-indigo-50/50 rounded-2xl border border-indigo-100/50">
          <span className="text-xs text-indigo-500 font-medium uppercase tracking-wide">AI Health Score</span>
          <p className="text-xl font-bold text-indigo-700 mt-1">Excellent (94%)</p>
        </div>
      </div>
      
      <SavingsCalculator onSavings={{(amount) => setBalance(prev => prev + amount)}} />
    </div>
  );
}}"""
            },
            {
                "name": "SavingsCalculator.tsx",
                "path": "src/components/SavingsCalculator.tsx",
                "language": "typescript",
                "content": """import React, { useState } from 'react';

interface Props {
  onSavings: (amount: number) => void;
}

export default function SavingsCalculator({ onSavings }: Props) {
  const [deposit, setDeposit] = useState('');
  
  const handleSave = () => {
    const val = parseFloat(deposit);
    if (!isNaN(val) && val > 0) {
      onSavings(val);
      setDeposit('');
    }
  };

  return (
    <div className="bg-white p-4 rounded-2xl border border-stone-100">
      <h3 className="text-sm font-semibold text-stone-700 mb-3">Add to Micro-Savings</h3>
      <div className="flex gap-2">
        <input 
          type="number" 
          value={deposit}
          onChange={(e) => setDeposit(e.target.value)}
          placeholder="Amount (e.g. 50)"
          className="flex-1 bg-stone-50 border border-stone-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
        <button 
          onClick={handleSave}
          className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-4 py-2 rounded-xl transition-colors"
        >
          Save Now
        </button>
      </div>
    </div>
  );
}"""
            }
        ]
    elif normalized_category == "health":
        codebase = [
            readme,
            {
                "name": "App.tsx",
                "path": "src/App.tsx",
                "language": "typescript",
                "content": f"""import React, {{ useState }} from 'react';
import BreathingRing from './components/BreathingRing';

export default function App() {{
  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 p-8">
      <header className="max-w-4xl mx-auto mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">{capital_name}</h1>
          <p className="text-slate-500">Your health companion</p>
        </div>
      </header>
      
      <main className="max-w-4xl mx-auto">
        <section className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex flex-col items-center">
          <h2 className="text-xl font-semibold mb-6">Paced Breathing Ring</h2>
          <BreathingRing />
        </section>
      </main>
    </div>
  );
}}"""
            },
            {
                "name": "BreathingRing.tsx",
                "path": "src/components/BreathingRing.tsx",
                "language": "typescript",
                "content": """import React, { useState, useEffect } from 'react';

export default function BreathingRing() {
  const [phase, setPhase] = useState<'Inhale' | 'Hold' | 'Exhale'>('Inhale');
  const [seconds, setSeconds] = useState(4);

  useEffect(() => {
    const timer = setInterval(() => {
      setSeconds((prev) => {
        if (prev <= 1) {
          if (phase === 'Inhale') { setPhase('Hold'); return 4; }
          if (phase === 'Hold') { setPhase('Exhale'); return 4; }
          if (phase === 'Exhale') { setPhase('Inhale'); return 4; }
        }
        return prev - 1; 
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [phase]);

  return (
    <div className="flex flex-col items-center justify-center p-4">
      <div className="w-44 h-44 rounded-full flex items-center justify-center bg-emerald-50 border-4 border-emerald-250 shadow-md">
        <div className="text-center">
          <h3 className="text-2xl font-bold text-slate-800">{phase}</h3>
          <p className="text-slate-500 font-mono text-lg">{seconds}s</p>
        </div>
      </div>
    </div>
  );
}"""
            }
        ]
    else:
        codebase = [
            readme,
            {
                "name": "InteractiveBox.tsx",
                "path": "src/InteractiveBox.tsx",
                "language": "typescript",
                "content": f"""import React, {{ useState }} from 'react';

export default function InteractiveBox() {{
  const [clicks, setClicks] = useState(0);
  return (
    <div className="p-6 bg-white rounded-3xl border border-stone-200/60 max-w-xs mx-auto text-center">
      <h3 className="text-lg font-bold font-display text-indigo-900 mb-2">{capital_name} Hub</h3>
      <p className="text-xs text-stone-400 mb-6">Custom compiled hackathon module</p>
      <button 
        onClick={{() => setClicks(c => c + 1)}}
        className="w-full bg-indigo-600 hover:bg-indigo-700 text-white rounded-2xl py-3 text-sm font-semibold transition-all hover:shadow-lg active:scale-95"
      >
        Trigger Action ({{clicks}})
      </button>
    </div>
  );
}}"""
            }
        ]
        
    return {
        "summary": f"This is a prototype workspace for {capital_name} generated dynamically based on design requirements.",
        "codebase": codebase
    }

async def generate_theme_suggestions(blueprint: dict, custom_prompt: str = None) -> List[Dict[str, Any]]:
    """
    Generate exactly 3 custom color/style themes for the selected project blueprint using Nvidia NIM,
    or fall back to the structured category-specific lists.
    """
    if not settings.NVIDIA_API_KEY:
        logger.warning("NVIDIA_API_KEY not configured. Falling back to local dynamic themes.")
        return get_fallback_theme_suggestions(blueprint, custom_prompt)

    custom_guideline = f"\nCRITICAL: The user has requested custom themes matching this preference: '{custom_prompt}'. Please generate themes that specifically match this style/preference (e.g. naming, descriptions, and color choices matching '{custom_prompt}')." if custom_prompt else ""

    prompt = f"""
    You are Sarthi, an expert AI partner. Suggest exactly 3 custom design themes matching the styling requirements of this project blueprint:
    Blueprint Name: {blueprint.get('name')}
    Core Idea: {blueprint.get('idea')}
    Key Features: {', '.join(blueprint.get('features', []))}
    Suggested Tech Stack: {blueprint.get('tech_stack')}{custom_guideline}
    
    For each design theme, provide:
    1. name (Theme Name)
    2. description (Brief explanation of design choices, mood, typography, spacing, and styling aesthetic - keeping it strictly under 15 words to prevent response truncation)
    3. palette (ThemePalette object matching this JSON structure:
       {{
         "primary": "Hex color code",
         "secondary": "Hex color code",
         "background": "Hex color code",
         "card_bg": "Hex color code",
         "text": "Hex color code",
         "border": "Hex color code",
         "is_dark": true/false
       }}
    )
    
    Return your output ONLY as a valid JSON array of objects. Do not include markdown code block syntax (like ```json ... ```). Just return the raw JSON.
    The JSON must match this structure:
    [
      {{
        "name": "Theme Name",
        "description": "Theme Description",
        "palette": {{
          "primary": "#...",
          "secondary": "#...",
          "background": "#...",
          "card_bg": "#...",
          "text": "#...",
          "border": "#...",
          "is_dark": false
        }}
      }}
    ]
    """
    try:
        from app.services.llm_router import get_provider_client
        client = get_provider_client("nvidia")
        if not client:
            raise ValueError("NVIDIA API client could not be initialized (missing key)")
        completion = client.chat.completions.create(
            model=settings.NVIDIA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2048
        )
        content = completion.choices[0].message.content
        if not content:
            raise ValueError("NIM returned an empty or null theme suggestions response")
        raw_content = content.strip()
        if raw_content.startswith("```"):
            lines = raw_content.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            raw_content = "\n".join(lines).strip()

        data = json.loads(raw_content)
        if isinstance(data, list) and len(data) == 3:
            return data
        else:
            raise ValueError("Invalid themes suggestions format returned by NIM model")
    except Exception as e:
        logger.error(f"Error generating theme suggestions from NIM: {e}. Falling back.")
        return get_fallback_theme_suggestions(blueprint, custom_prompt)


def get_fallback_theme_suggestions(blueprint: dict, custom_prompt: str = None) -> List[Dict[str, Any]]:
    name = blueprint.get("name", "Workspace Project")
    category = blueprint.get("category", "other").lower()

    if custom_prompt:
        cp_lower = custom_prompt.lower()
        if "dark" in cp_lower or "black" in cp_lower or "night" in cp_lower:
            return [
                {
                    "name": f"Custom Dark Mode",
                    "description": f"A dark theme generated matching '{custom_prompt}' for {name}.",
                    "palette": {
                        "primary": "#3b82f6",
                        "secondary": "#1d4ed8",
                        "background": "#090d16",
                        "card_bg": "#111827",
                        "text": "#f3f4f6",
                        "border": "#1f2937",
                        "is_dark": True
                    }
                },
                {
                    "name": f"Midnight Neon",
                    "description": f"Vibrant custom tones matching '{custom_prompt}'.",
                    "palette": {
                        "primary": "#f43f5e",
                        "secondary": "#a855f7",
                        "background": "#030712",
                        "card_bg": "#0f172a",
                        "text": "#f9fafb",
                        "border": "#1e293b",
                        "is_dark": True
                    }
                },
                {
                    "name": f"Obsidian Theme",
                    "description": f"Sleek obsidian monochrome tones matching '{custom_prompt}'.",
                    "palette": {
                        "primary": "#10b981",
                        "secondary": "#047857",
                        "background": "#0b0f19",
                        "card_bg": "#161b22",
                        "text": "#e6edf3",
                        "border": "#30363d",
                        "is_dark": True
                    }
                }
            ]
        elif "light" in cp_lower or "white" in cp_lower or "clean" in cp_lower:
            return [
                {
                    "name": f"Clean Light Workspace",
                    "description": f"Ultra-clean light theme matching '{custom_prompt}' for {name}.",
                    "palette": {
                        "primary": "#4f46e5",
                        "secondary": "#c7d2fe",
                        "background": "#fafaf9",
                        "card_bg": "#ffffff",
                        "text": "#1c1917",
                        "border": "#e7e5e4",
                        "is_dark": False
                    }
                },
                {
                    "name": f"Soft Ivory",
                    "description": f"Warm ivory white background matching '{custom_prompt}'.",
                    "palette": {
                        "primary": "#d97706",
                        "secondary": "#fef3c7",
                        "background": "#fdfbf7",
                        "card_bg": "#ffffff",
                        "text": "#451a03",
                        "border": "#f5eebc",
                        "is_dark": False
                    }
                },
                {
                    "name": f"Minimalist White",
                    "description": f"Sleek monochrome light theme matching '{custom_prompt}'.",
                    "palette": {
                        "primary": "#000000",
                        "secondary": "#e5e5e5",
                        "background": "#ffffff",
                        "card_bg": "#f9f9f9",
                        "text": "#111111",
                        "border": "#e5e5e5",
                        "is_dark": False
                    }
                }
            ]
        else:
            return [
                {
                    "name": f"Dynamic {custom_prompt.title()}",
                    "description": f"A dynamic theme generated matching style preference '{custom_prompt}' for {name}.",
                    "palette": {
                        "primary": "#6366f1",
                        "secondary": "#e0e7ff",
                        "background": "#f8fafc",
                        "card_bg": "#ffffff",
                        "text": "#0f172a",
                        "border": "#e2e8f0",
                        "is_dark": False
                    }
                },
                {
                    "name": f"Accent {custom_prompt.title()}",
                    "description": f"Alternate accents generated matching '{custom_prompt}'.",
                    "palette": {
                        "primary": "#db2777",
                        "secondary": "#fce7f3",
                        "background": "#fff1f2",
                        "card_bg": "#ffffff",
                        "text": "#4c0519",
                        "border": "#ffe4e6",
                        "is_dark": False
                    }
                },
                {
                    "name": f"Dark {custom_prompt.title()}",
                    "description": f"A dark variation matching '{custom_prompt}'.",
                    "palette": {
                        "primary": "#f59e0b",
                        "secondary": "#78350f",
                        "background": "#111827",
                        "card_bg": "#1f2937",
                        "text": "#f9fafb",
                        "border": "#374151",
                        "is_dark": True
                    }
                }
            ]

    if category == "health" or "wellness" in name.lower() or "breathe" in name.lower():
        return [
            {
                "name": "Tranquil Sage",
                "description": f"A soft, nature-inspired palette designed to keep users of {name} focused and calm during breathing cycles.",
                "palette": {
                    "primary": "#059669",
                    "secondary": "#a7f3d0",
                    "background": "#f0fdf4",
                    "card_bg": "#ffffff",
                    "text": "#064e3b",
                    "border": "#d1fae5",
                    "is_dark": False
                }
            },
            {
                "name": "Ocean Serenity",
                "description": f"Cool blue gradients to evoke relaxation and trust, perfect for logging wellness habits.",
                "palette": {
                    "primary": "#0284c7",
                    "secondary": "#bae6fd",
                    "background": "#f0f9ff",
                    "card_bg": "#ffffff",
                    "text": "#0369a1",
                    "border": "#e0f2fe",
                    "is_dark": False
                }
            },
            {
                "name": "Midnight Breathe",
                "description": f"A soothing dark mode option with indigo accents, designed to reduce eye strain during nighttime sleep tracking.",
                "palette": {
                    "primary": "#6366f1",
                    "secondary": "#c7d2fe",
                    "background": "#0f172a",
                    "card_bg": "#1e293b",
                    "text": "#f1f5f9",
                    "border": "#334155",
                    "is_dark": True
                }
            }
        ]
    elif category == "finance" or "save" in name.lower() or "budget" in name.lower() or "invest" in name.lower() or "crypto" in name.lower():
        return [
            {
                "name": "Vibrant Mint",
                "description": f"Fresh green accent tones and a clean white background representing cash flow and financial growth for {name}.",
                "palette": {
                    "primary": "#10b981",
                    "secondary": "#d1fae5",
                    "background": "#f8fafc",
                    "card_bg": "#ffffff",
                    "text": "#0f172a",
                    "border": "#e2e8f0",
                    "is_dark": False
                }
            },
            {
                "name": "Slate Corporate",
                "description": f"Trustworthy steel blue accents and structured layouts for institutional accuracy.",
                "palette": {
                    "primary": "#1e3a8a",
                    "secondary": "#93c5fd",
                    "background": "#f8fafc",
                    "card_bg": "#ffffff",
                    "text": "#0f172a",
                    "border": "#e2e8f0",
                    "is_dark": False
                }
            },
            {
                "name": "Dark Gold Ledger",
                "description": f"A rich graphite dark mode theme with warm gold highlights for high-end investor vibes.",
                "palette": {
                    "primary": "#d97706",
                    "secondary": "#fde68a",
                    "background": "#121212",
                    "card_bg": "#1e1e1e",
                    "text": "#f5f5f5",
                    "border": "#2c2c2c",
                    "is_dark": True
                }
            }
        ]
    else:
        return [
            {
                "name": "Cyber Synthwave",
                "description": f"A retro neon dark mode built for developer tools and high-fidelity prototype dashboard layouts.",
                "palette": {
                    "primary": "#ec4899",
                    "secondary": "#a855f7",
                    "background": "#0f172a",
                    "card_bg": "#1e293b",
                    "text": "#f8fafc",
                    "border": "#334155",
                    "is_dark": True
                }
            },
            {
                "name": "Minimalist Clean",
                "description": f"Ultra-clean typography with cool grey accents and slate borders to emphasize content layout.",
                "palette": {
                    "primary": "#4f46e5",
                    "secondary": "#c7d2fe",
                    "background": "#f8fafc",
                    "card_bg": "#ffffff",
                    "text": "#1e293b",
                    "border": "#e2e8f0",
                    "is_dark": False
                }
            },
            {
                "name": "Sunrise Warmth",
                "description": f"Energizing orange-red primary accents on cream and beige, ideal for creative work.",
                "palette": {
                    "primary": "#f97316",
                    "secondary": "#ffedd5",
                    "background": "#fafaf9",
                    "card_bg": "#ffffff",
                    "text": "#292524",
                    "border": "#e7e5e4",
                    "is_dark": False
                }
            }
        ]
