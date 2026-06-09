"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import confetti from "canvas-confetti";

export interface Message {
  id: string;
  sender: "user" | "ai";
  text: string;
  timestamp: string;
}

export interface ProjectSuggestion {
  name: string;
  idea: string;
  features: string[];
  tech_stack: string;
}

export interface ChatSession {
  id: string;
  title: string;
  category: string;
  messages: Message[];
  created: string;
  selected_project: ProjectSuggestion | null;
  is_confirmed: boolean;
  project_id: string | null;
}

export interface CodeFile {
  name: string;
  path: string;
  content: string;
  language: string;
}

export interface Project {
  id: string;
  name: string;
  category: string;
  status: "idle" | "generating" | "completed" | "failed" | "documents_ready";
  progress: number;
  step: string;
  summary: string;
  codebase: CodeFile[];
  created: string;
  chat_id: string;
  requirements?: any;
  planning?: any;
  db_architecture?: any;
  backend_architecture?: any;
  api_architecture?: any;
  frontend_architecture?: any;
  theme_styling?: any;
  auth_architecture?: any;
  realtime_architecture?: any;
  state_management?: any;
  devops_architecture?: any;
  security_architecture?: any;
  testing_architecture?: any;
  validation_architecture?: any;
  optimization_architecture?: any;
  code_generation_plan?: any;
  database_model_generation?: any;
  backend_code_generation?: any;
  api_implementation?: any;
  frontend_code_generation?: any;
  ui_component_generation?: any;
  state_implementation?: any;
  integration_generation?: any;
  build_compilation?: any;
  error_correction?: any;
  project_export?: any;
  agent_context?: any;
  hackathon_metadata?: any;
  mcp_evidence?: any;
  prd?: string;
  mrd?: string;
  trd?: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

interface WorkspaceContextType {
  user: { id: string; name: string; email: string } | null;
  login: (email: string, password: string) => Promise<void>;
  signup: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  
  chats: ChatSession[];
  activeChatId: string | null;
  setActiveChatId: (id: string | null) => void;
  createNewChat: (category: string, title: string, selectedProject?: ProjectSuggestion) => Promise<string>;
  addMessageToChat: (chatId: string, sender: "user" | "ai", text: string) => Promise<void>;
  editMessageText: (chatId: string, messageId: string, newText: string) => Promise<void>;
  deleteChat: (chatId: string) => Promise<void>;
  renameChat: (chatId: string, newTitle: string) => Promise<void>;
  updateChatSelectedProject: (chatId: string, selectedProject: ProjectSuggestion) => Promise<void>;

  projects: Project[];
  activeProjectId: string | null;
  setActiveProjectId: (id: string | null) => void;
  generateProject: (
    chatId: string,
    projectName: string,
    category: string,
    theme?: string,
    blueprint?: any,
    themePalette?: any
  ) => Promise<void>;
  compileProjectCodebase: (projectId: string, chatId: string) => Promise<void>;
  generateDocuments: (projectName: string, prompt: string) => Promise<void>;
  deleteProject: (projectId: string) => Promise<void>;
  renameProject: (projectId: string, newTitle: string) => Promise<void>;
  updateProject: (projectId: string, updates: Partial<Project>) => void;

  currentCategory: string;
  setCurrentCategory: (category: string) => void;
  currentInput: string;
  setCurrentInput: (input: string) => void;

  showAuthModal: boolean;
  setShowAuthModal: (show: boolean) => void;
  authMode: "login" | "signup";
  setAuthMode: (mode: "login" | "signup") => void;

  showAbout: boolean;
  setShowAbout: (show: boolean) => void;
  showContact: boolean;
  setShowContact: (show: boolean) => void;
  
  isGeneratingProject: boolean;

  showRightPane: boolean;
  setShowRightPane: (show: boolean) => void;

  showLeftPane: boolean;
  setShowLeftPane: (show: boolean) => void;

  suggestions: ProjectSuggestion[];
  isFetchingSuggestions: boolean;
  fetchSuggestions: (category: string) => Promise<void>;
  clearSuggestions: () => void;
}

const WorkspaceContext = createContext<WorkspaceContextType | undefined>(undefined);

// Initial Mock Chats
const INITIAL_CHATS: ChatSession[] = [
  {
    id: "chat-1",
    title: "CalmPath Breathing App",
    category: "health",
    created: "May 22, 2026",
    selected_project: {
      name: "CalmPath Breathing Guide",
      idea: "Interactive breathing timer with stress logging sheets",
      features: ["Paced pacing ring", "Weekly mood trends", "Audio cues"],
      tech_stack: "React, Framer Motion, Tailwind, LocalStorage"
    },
    is_confirmed: true,
    project_id: "proj-1",
    messages: [
      {
        id: "m-1",
        sender: "user",
        text: "I want an app that tracks daily stress levels and suggests breathing exercises.",
        timestamp: "5:30 PM",
      },
      {
        id: "m-2",
        sender: "ai",
        text: "That's a wonderful idea! I've designed a structure for 'CalmPath'. It uses a simple visual mood logger, tracks heart rate variability (mocked), and opens an interactive breathing ring. I will compile a complete project structure for you. Click 'Generate Project' on the top right when you are ready!",
        timestamp: "5:31 PM",
      },
    ],
  },
  {
    id: "chat-2",
    title: "EcoFootprint Carbon Tracker",
    category: "sustainability",
    created: "May 22, 2026",
    selected_project: null,
    is_confirmed: false,
    project_id: null,
    messages: [
      {
        id: "m-3",
        sender: "user",
        text: "Can you design a dashboard that helps me calculate my daily carbon footprint?",
        timestamp: "4:15 PM",
      },
      {
        id: "m-4",
        sender: "ai",
        text: "Sure! Let's build EcoFootprint. It will contain inputs for commute distances, energy consumption, and food habits. Then it computes offset recommendations and shows a visual bar graph. I can compile this React dashboard for you.",
        timestamp: "4:16 PM",
      },
    ],
  },
];

// Mock Projects Codebases
const HEALTH_PROJECT_CODE: CodeFile[] = [
  {
    name: "README.md",
    path: "README.md",
    language: "markdown",
    content: `# CalmPath Wellness Workspace\n\nAn interactive web application designed to track wellness levels, log daily moods, and provide guide-focused paced breathing exercises to lower stress.\n\n## Core Features\n- Interactive Breathing Ring (Framer Motion)\n- Mood Logger and Tracker Dashboard\n- Stress Score Calculator\n\n## Tech Stack\n- React\n- Tailwind CSS\n- Framer Motion`,
  },
  {
    name: "App.tsx",
    path: "src/App.tsx",
    language: "typescript",
    content: `import React, { useState } from 'react';
import BreathingRing from './components/BreathingRing';
import MoodLogger from './components/MoodLogger';

export default function App() {
  const [stressScore, setStressScore] = useState(45);
  
  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 p-8">
      <header className="max-w-4xl mx-auto mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">CalmPath</h1>
          <p className="text-slate-500">Your breathing and mood companion</p>
        </div>
        <div className="bg-emerald-50 text-emerald-700 px-4 py-2 rounded-full font-medium text-sm">
          Stress Level: {stressScore}% (Moderate)
        </div>
      </header>
      
      <main className="max-w-4xl mx-auto grid md:grid-cols-2 gap-8">
        <section className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex flex-col items-center">
          <h2 className="text-xl font-semibold mb-6">Paced Breathing Guide</h2>
          <BreathingRing />
        </section>
        
        <section className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
          <h2 className="text-xl font-semibold mb-6">Mood Logger</h2>
          <MoodLogger onStressChange={setStressScore} />
        </section>
      </main>
    </div>
  );
}`,
  },
  {
    name: "BreathingRing.tsx",
    path: "src/components/BreathingRing.tsx",
    language: "typescript",
    content: `import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

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
      <div className="relative w-64 h-64 flex items-center justify-center">
        {/* Animated breathing circle */}
        <motion.div
          animate={{
            scale: phase === 'Inhale' ? 1.4 : phase === 'Hold' ? 1.4 : 0.9,
            backgroundColor: phase === 'Inhale' ? '#d1fae5' : phase === 'Hold' ? '#a7f3d0' : '#e0f2fe'
          }}
          transition={{ duration: phase === 'Hold' ? 0 : 4, ease: "easeInOut" }}
          className="absolute w-44 h-44 rounded-full flex items-center justify-center shadow-lg"
        />
        <div className="z-10 text-center">
          <h3 className="text-2xl font-bold text-slate-800 transition-all">{phase}</h3>
          <p className="text-slate-500 font-mono text-lg">{seconds}s</p>
        </div>
      </div>
      <p className="text-sm text-slate-400 mt-4 text-center">
        Breathe in as the circle expands, hold, and breathe out as it contracts.
      </p>
    </div>
  );
}`,
  },
];

const INITIAL_PROJECTS: Project[] = [
  {
    id: "proj-1",
    name: "CalmPath Breathing Space",
    category: "health",
    status: "completed",
    progress: 100,
    step: "Completed",
    created: "May 22, 2026",
    summary: "A wellness application featuring a real-time breathing visualizer (Inhale/Hold/Exhale phases) and custom stress tracking dashboard logic.",
    codebase: HEALTH_PROJECT_CODE,
    chat_id: "chat-1",
    requirements: {
      "status": "success",
      "project_overview": {
        "name": "CalmPath Breathing Space",
        "type": "Health & Wellness App",
        "description": "A wellness application featuring a real-time breathing visualizer (Inhale/Hold/Exhale phases) and custom stress tracking dashboard logic.",
        "complexity": "Low"
      },
      "tech_stack": {
        "frontend": ["React", "Tailwind CSS", "Framer Motion"],
        "backend": [],
        "database": [],
        "ai_tools": [],
        "deployment": ["Vercel"]
      },
      "theme": {
        "design_style": "Minimal Slate / Emerald Wellness",
        "ui_type": "Paced Breathing Visualizer",
        "special_effects": ["Calm pulse scaling transitions", "Dynamic color fades"]
      },
      "features": ["paced_breathing_timer", "stress_logger_dashboard", "mood_history_charts"],
      "core_modules": ["BreathingEngine", "WellnessDashboard"],
      "authentication": {
        "required": false,
        "type": ""
      },
      "database_requirements": {
        "required": false,
        "entities": [],
        "storage_type": ""
      },
      "api_integrations": [],
      "scalability": {
        "realtime_features": false,
        "high_scalability_needed": false,
        "microservices_ready": false
      },
      "project_workflow_summary": [
        "User opens the app and sees the current stress level.",
        "User completes paced breathing cycles inside the expanding/contracting breathing ring.",
        "User logs their daily stress score inside the mood logger component."
      ],
      "recommendations": [
        "Ensure smooth Framer Motion scaling transitions to keep user interface feel soothing.",
        "Persist local stress log history inside LocalStorage for offline-first support."
      ]
    },
    planning: {
      "status": "success",
      "execution_strategy": {
        "project_type": "Health & Wellness App",
        "architecture_style": "Client-Side Single Page Application",
        "development_strategy": "Establish reactive UI components followed by integration of state management hooks for session tracking.",
        "scalability_strategy": "Serve static assets via CDN (Vercel) and cache user state inside browser LocalStorage."
      },
      "project_phases": [
        {
          "phase": 1,
          "title": "Onboarding & Layout Setup",
          "description": "Construct UI skeletons, color styling configuration, and configure client routers.",
          "tasks": [
            "Implement basic layout with responsive navigation bars.",
            "Install and import Lucide React and Framer Motion packages."
          ],
          "expected_output": [
            "Styling and navigation shells ready"
          ]
        },
        {
          "phase": 2,
          "title": "Interactive Breathing & Logger Widgets",
          "description": "Build functional timers, breathing rings, and mood logs.",
          "tasks": [
            "Code the breathing ring component using requestAnimationFrame/setInterval loops.",
            "Code the state-bound stress score selectors."
          ],
          "expected_output": [
            "Breathing Ring and Mood Logger fully interactive"
          ]
        }
      ],
      "module_execution_order": ["BreathingEngine", "WellnessDashboard"],
      "parallel_execution_groups": [
        ["BreathingEngine", "WellnessDashboard"]
      ],
      "module_dependencies": [],
      "agent_execution_plan": [
        {
          "agent": "UIUXStylistAgent",
          "responsibility": "Design static page layout and emerald wellness theme colors.",
          "execution_stage": "Stage 3: Frontend Compilation"
        },
        {
          "agent": "FrontendGeneratorAgent",
          "responsibility": "Generate state hooks and timers for the breathing ring.",
          "execution_stage": "Stage 4: Interactive Assembly"
        }
      ],
      "compilation_pipeline": [
        {
          "stage": "Requirements Extraction",
          "purpose": "Construct technical details from blueprint."
        },
        {
          "stage": "Orchestration Planning",
          "purpose": "Define tasks and downstream agent sequencing."
        }
      ],
      "system_workflow": {
        "initialization": [
          "State management loads cached stress logs from LocalStorage."
        ],
        "backend_flow": [],
        "frontend_flow": [
          "Client runs breathing loop showing Inhale/Hold/Exhale instructions."
        ],
        "integration_flow": []
      },
      "risk_analysis": {
        "complex_modules": ["BreathingEngine"],
        "potential_bottlenecks": [
          "Timer drift or frame drops during heavy tab switching in browsers."
        ],
        "optimization_suggestions": [
          "Use requestAnimationFrame or web workers to execute precise interval pulses."
        ]
      },
      "recommended_next_agents": [
        "FrontendGeneratorAgent"
      ]
    },
    db_architecture: {
      "status": "success",
      "database_strategy": {
        "primary_database": "IndexedDB / LocalStorage",
        "secondary_databases": [],
        "cache_layer": "None",
        "vector_database": "None",
        "database_reasoning": [
          "IndexedDB provides local, non-blocking storage inside user browser.",
          "LocalStorage stores small settings preferences like user visual theme selection."
        ]
      },
      "entities": [
        {
          "entity_name": "StressLog",
          "entity_type": "Store / Table",
          "description": "User logged stress records",
          "fields": [
            {
              "name": "id",
              "type": "String",
              "required": true,
              "unique": true,
              "indexed": true,
              "default": "AutoIncrement"
            },
            {
              "name": "stress_score",
              "type": "Integer",
              "required": true,
              "unique": false,
              "indexed": false,
              "default": null
            },
            {
              "name": "timestamp",
              "type": "DateTime",
              "required": true,
              "unique": false,
              "indexed": true,
              "default": "CurrentDate"
            }
          ]
        }
      ],
      "relationships": [],
      "authentication_storage": {
        "required": false,
        "auth_entities": [],
        "security_requirements": [],
        "token_storage_strategy": ""
      },
      "indexing_strategy": {
        "indexes": ["idx_log_timestamp"],
        "search_optimization": [],
        "vector_indexes": []
      },
      "realtime_architecture": {
        "required": false,
        "sync_strategy": [],
        "event_driven_entities": []
      },
      "scalability_strategy": {
        "horizontal_scaling": false,
        "sharding_required": false,
        "high_write_load_entities": [],
        "caching_targets": []
      },
      "backend_integration_context": {
        "important_models": [],
        "service_dependencies": [],
        "repository_patterns": []
      },
      "api_integration_context": {
        "crud_entities": [],
        "protected_entities": [],
        "high_frequency_routes": []
      },
      "frontend_data_contracts": {
        "stateful_entities": ["StressLog"],
        "realtime_entities": [],
        "dashboard_entities": ["StressLog"]
      },
      "workflow_mappings": [
        {
          "workflow": "Mood log submission",
          "database_interactions": ["Insert into StressLog database store."]
        }
      ],
      "future_agent_context": {
        "important_notes_for_backend_agents": [],
        "important_notes_for_api_agents": [],
        "important_notes_for_frontend_agents": [
          "Dashboard should read local IndexedDB state on startup and render wellness charts."
        ]
      }
    },
    backend_architecture: {
      "status": "success",
      "backend_strategy": {
        "architecture_style": "Client-Only Architecture / Serverless Static",
        "backend_framework": "React (Next.js Static Export)",
        "execution_model": "Client-side async scheduling loops",
        "scalability_model": "Stateless frontend distributed via CDN Edge networks"
      },
      "backend_structure": {
        "root_modules": ["src", "public"],
        "feature_modules": ["components", "context"],
        "shared_modules": ["hooks"],
        "core_directories": ["src/components", "src/context"]
      },
      "service_architecture": [],
      "repository_patterns": {
        "pattern_type": "None",
        "repositories": []
      },
      "middleware_architecture": [],
      "authentication_backend_flow": {
        "auth_strategy": "None",
        "protected_modules": [],
        "token_flow": [],
        "session_management": []
      },
      "api_groupings": [],
      "websocket_architecture": {
        "required": false,
        "channels": [],
        "realtime_modules": []
      },
      "async_task_architecture": {
        "required": false,
        "background_jobs": [],
        "queue_strategy": ""
      },
      "dependency_injection_strategy": {
        "required": false,
        "shared_dependencies": [],
        "service_bindings": []
      },
      "backend_workflows": [],
      "scalability_architecture": {
        "microservice_ready": false,
        "horizontal_scaling": false,
        "high_load_modules": [],
        "optimization_targets": []
      },
      "future_agent_context": {
        "important_notes_for_api_agents": [],
        "important_notes_for_frontend_agents": [
          "Establish clean React context providers to manage app-wide state variables."
        ],
        "important_notes_for_devops_agents": []
      }
    },
    api_architecture: {
      "status": "success",
      "api_strategy": {
        "protocol": "HTTP/REST",
        "base_path": "/api/v1",
        "versioning": "URL Path prefixing",
        "default_response_format": "application/json"
      },
      "endpoints": [
        {
          "group_name": "Authentication API",
          "path": "/api/v1/auth/signup",
          "method": "POST",
          "description": "Registers a new user account profile.",
          "request_body": {
            "name": { "type": "string", "required": true },
            "email": { "type": "string", "format": "email", "required": true },
            "password": { "type": "string", "required": true }
          },
          "query_parameters": [],
          "response_payload": {
            "status": "success",
            "message": "User registered successfully.",
            "user_id": "string"
          },
          "requires_auth": false,
          "roles_allowed": []
        },
        {
          "group_name": "Authentication API",
          "path": "/api/v1/auth/login",
          "method": "POST",
          "description": "Verifies password and issues JWT token credentials.",
          "request_body": {
            "email": { "type": "string", "format": "email", "required": true },
            "password": { "type": "string", "required": true }
          },
          "query_parameters": [],
          "response_payload": {
            "status": "success",
            "access_token": "string",
            "refresh_token": "string",
            "user": { "id": "string", "name": "string", "email": "string" }
          },
          "requires_auth": false,
          "roles_allowed": []
        },
        {
          "group_name": "StressLog API",
          "path": "/api/v1/stresslogs",
          "method": "GET",
          "description": "Retrieves user's historical stress logs.",
          "request_body": {},
          "query_parameters": [
            { "name": "limit", "type": "integer", "required": false, "default": 20 }
          ],
          "response_payload": {
            "status": "success",
            "stresslogs": "array"
          },
          "requires_auth": true,
          "roles_allowed": []
        },
        {
          "group_name": "StressLog API",
          "path": "/api/v1/stresslogs",
          "method": "POST",
          "description": "Submits a new stress log entry.",
          "request_body": {
            "stress_score": { "type": "integer", "required": true }
          },
          "query_parameters": [],
          "response_payload": {
            "status": "success",
            "id": "string",
            "message": "Stress log entry created successfully."
          },
          "requires_auth": true,
          "roles_allowed": []
        }
      ],
      "global_configurations": {
        "cors_policy": {
          "allowed_origins": ["http://localhost:3000"],
          "allowed_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
          "allowed_headers": ["Content-Type", "Authorization"]
        },
        "rate_limiting": {
          "rate_limit_enabled": true,
          "max_requests_per_minute": 60,
          "block_duration_seconds": 600
        }
      },
      "security_schemes": {
        "bearer_auth": {
          "type": "http",
          "scheme": "bearer",
          "bearer_format": "JWT",
          "header_name": "Authorization"
        }
      },
      "error_architecture": {
        "error_response_format": {
          "error": {
            "code": "string",
            "message": "string",
            "details": "array"
          }
        },
        "error_codes": [
          { "code": "UNAUTHORIZED", "http_status": 401, "message": "Access credentials are invalid or expired." },
          { "code": "VALIDATION_FAILED", "http_status": 422, "message": "Parameters failed validation check rules." }
        ]
      },
      "future_agent_context": {
        "important_notes_for_frontend_agents": [
          "Include Authorization: Bearer token header on all GET/POST requests targeting /stresslogs endpoints."
        ],
        "important_notes_for_backend_agents": [
          "Validate stress_score falls between the range 0 to 100 before database insertion."
        ],
        "important_notes_for_devops_agents": []
      }
    },
    frontend_architecture: {
      status: "success",
      frontend_strategy: {
        architecture_style: "SPA (Single Page Application)",
        frontend_framework: "React (Vite)",
        rendering_strategy: "Client-side rendering (CSR)",
        state_management_strategy: "React Context Hooks & LocalState"
      },
      frontend_structure: {
        root_modules: ["src/App.tsx", "src/index.css", "src/main.tsx"],
        feature_modules: ["breathing", "mood-logger"],
        shared_components: ["Button", "CardPanel", "ModalWrapper", "FormInput"],
        core_directories: ["src/components", "src/context", "src/hooks"]
      },
      pages: [
        {
          "page_name": "AppDashboard",
          "purpose": "Renders breathing ring visualizer and mood history charts in a unified workspace.",
          "protected": false,
          "related_modules": ["breathing", "mood-logger"]
        }
      ],
      layouts: [
        {
          "layout_name": "MainAppLayout",
          "used_for": ["/"],
          "components": ["AppHeaderBar", "LayoutGrid"]
        }
      ],
      component_hierarchy: [
        {
          "component_name": "App",
          "type": "Root Container",
          "children": ["BreathingRing", "MoodLogger"],
          "reusable": false
        },
        {
          "component_name": "BreathingRing",
          "type": "Interactive Paced Timer Widget",
          "children": [],
          "reusable": true
        },
        {
          "component_name": "MoodLogger",
          "type": "Data Form Input Panel",
          "children": ["StressScoreInput"],
          "reusable": true
        }
      ],
      routing_structure: {
        "routing_style": "Single page tab toggles",
        "route_groups": ["dashboard"],
        "protected_routes": []
      },
      state_management_architecture: {
        "global_states": ["active_stress_score_history", "theme_preference"],
        "local_states": ["breathing_timer_phase", "breathing_phase_seconds", "mood_form_submitting"],
        "realtime_states": []
      },
      api_integrations: {
        "connected_api_groups": ["StressLog API"],
        "high_frequency_routes": ["GET /api/v1/stresslogs"],
        "realtime_integrations": []
      },
      authentication_ui_flow: {
        "auth_pages": [],
        "protected_ui_modules": [],
        "session_handling": ["Read stored stresslogs cache from LocalStorage on mount"]
      },
      dashboard_architecture: {
        "required": true,
        "dashboard_modules": ["BreathingRingContainer", "MoodLoggerPanel"],
        "analytics_components": ["MoodTrendsLineChart"]
      },
      responsive_strategy: {
        "mobile_support": true,
        "tablet_support": true,
        "desktop_support": true,
        "responsive_modules": ["TwoColumnAppGrid", "MobileBottomNavigationBar"]
      },
      frontend_workflows: [
        {
          "workflow_name": "Submit daily mood score",
          "execution_flow": [
            "User selects a stress score from 0-100.",
            "Form state validates score range.",
            "Updates stressScore state in parent App.tsx.",
            "Persists new score history to LocalStorage."
          ]
        }
      ],
      frontend_data_flow: {
        "state_updates": [
          "Updating stressScore triggers re-render of stress level badge."
        ],
        "api_to_ui_flows": [
          "LocalStorage stress history loads into state variables for rendering charts."
        ],
        "realtime_data_flows": []
      },
      future_generation_context: {
        "important_notes_for_ui_generation": [
          "Ensure emerald primary coloring is consistently applied to visual breathing rings."
        ],
        "important_notes_for_frontend_code_generation": [
          "Use Framer Motion's AnimatePresence for smooth transitions on phase changes."
        ],
        "important_notes_for_testing_agents": [
          "Test breathing timer logic handles tab focus/blur events gracefully."
        ]
      }
    },
    theme_styling: {
      status: "success",
      design_system: {
        design_style: "Minimal Emerald / Slate Soft Glow",
        ui_philosophy: "Calming wellness-focused UI with spacious typography and smooth state fades.",
        theme_strategy: "TailwindCSS custom palette config mapping semantic color names.",
        component_styling_approach: "shadcn/ui primitive configuration with custom micro-shadow utilities."
      },
      color_palette: {
        primary_colors: ["#10b981", "#059669", "#047857"],
        secondary_colors: ["#f0fdf4", "#d1fae5", "#a7f3d0"],
        accent_colors: ["#3b82f6", "#60a5fa"],
        background_colors: ["#fafafa", "#ffffff"],
        text_colors: ["#0f172a", "#334155", "#64748b"],
        status_colors: {
          success: "#10b981",
          warning: "#f59e0b",
          error: "#ef4444",
          info: "#3b82f6"
        }
      },
      typography_system: {
        font_families: ["Outfit", "Inter", "ui-sans-serif"],
        heading_styles: ["font-display text-slate-900 tracking-tight font-bold"],
        body_styles: ["font-sans text-slate-600 antialiased"],
        responsive_typography: true
      },
      spacing_layout_system: {
        spacing_scale: ["0.25rem", "0.5rem", "1rem", "1.5rem", "2rem", "3rem"],
        container_rules: ["max-w-4xl mx-auto px-4 sm:px-6 lg:px-8"],
        grid_strategy: "12-column responsive flexbox layouts with gap-6 spacing",
        layout_consistency_rules: ["Align headers to central viewport grids", "Inject uniform cards border-radius tokens"]
      },
      component_styling_system: [
        {
          component_type: "Button",
          styling_rules: ["px-4 py-2 rounded-xl transition-all select-none hover:scale-[1.01]"],
          interactive_states: ["hover:shadow-sm", "focus:ring-2 focus:ring-emerald-500", "active:scale-[0.99]"]
        }
      ],
      responsive_design_system: {
        mobile_strategy: "Fluid single column container grids with bottom bar navigations.",
        tablet_strategy: "Flexible dual sidebar triggers.",
        desktop_strategy: "Side-by-side dashboard viewports.",
        breakpoints: ["sm: 640px", "md: 768px", "lg: 1024px"]
      },
      animation_motion_system: {
        animation_style: "Framer Motion spring animations",
        transition_rules: ["duration: 0.3s, ease: easeInOut"],
        interactive_animations: ["breathing_pulse_expand", "stress_log_slide_up"],
        motion_principles: ["Avoid sudden layout shifts", "Align scaling limits to a maximum of 5% increment"]
      },
      theme_modes: {
        dark_mode_supported: false,
        light_mode_supported: true,
        theme_switching_strategy: ["Read media settings preference on mount"]
      },
      dashboard_styling: {
        dashboard_theme: "Emerald Soft Dashboard",
        widget_styles: ["border border-slate-100 shadow-sm p-6 rounded-2xl bg-white"],
        analytics_ui_patterns: ["SummaryStatCardsGrid", "TrendChartTimelineWrapper"]
      },
      accessibility_system: {
        contrast_rules: ["Failsafe fallback borders for colorblind accessibility options", "Contrast ratio target minimum 4.5:1"],
        keyboard_navigation_support: true,
        accessibility_features: ["Aria attributes for breathing ring countdown controls", "Screen-reader text logs"]
      },
      tailwind_shadcn_architecture: {
        tailwind_strategy: ["Extend themes inside tailwind.config.js"],
        shadcn_components: ["Button", "Dialog", "Card", "Progress"],
        utility_patterns: ["glassmorphic_card_bg", "soothing_green_gradient"]
      },
      visual_workflows: [
        {
          workflow_name: "Log stress and update stats",
          visual_flow: [
            "Open Form Dialog with slight spring slide-up transition.",
            "Highlight target stress rating dials on hover.",
            "Fade out form and pop green checklist checkmark on successful save."
          ]
        }
      ],
      future_generation_context: {
        important_notes_for_ui_generation: ["Use rounded-2xl for all central cards widgets."],
        important_notes_for_component_generation: ["Utilize CSS variables for background colors to prepare for future dark mode updates."],
        important_notes_for_frontend_code_generation: ["Avoid absolute positioning layouts for analytics dashboard modules."]
      }
    },
    auth_architecture: {
      status: "success",
      authentication_strategy: {
        auth_type: "JWT-based stateless bearer tokens",
        session_strategy: "Token-based browser memory storage",
        token_strategy: "Access token + Refresh token rotation",
        authorization_model: "RBAC (Role-Based Access Control)"
      },
      authentication_entities: [
        {
          entity_name: "User",
          purpose: "Stores core profile credentials and authorization roles.",
          related_permissions: ["read:profile", "write:profile"]
        }
      ],
      role_based_access_control: {
        enabled: true,
        roles: ["User", "Admin"],
        permission_groups: ["profile_management", "stress_logs_management"],
        role_hierarchy: ["Admin > User"]
      },
      protected_route_architecture: {
        backend_protected_routes: ["GET /api/v1/stresslogs", "POST /api/v1/stresslogs"],
        frontend_protected_routes: ["/dashboard", "/history"],
        permission_based_routes: []
      },
      authentication_workflows: [
        {
          workflow_name: "Email & Password login",
          execution_flow: [
            "User submits email and password credentials.",
            "Validate inputs on client.",
            "POST request is verified on backend using bcrypt hashing comparison.",
            "Generate access and refresh tokens.",
            "Save access token in React state context."
          ]
        }
      ],
      session_management_architecture: {
        multi_device_support: true,
        session_persistence: ["Refresh token saved inside HttpOnly cookies"],
        logout_strategy: ["Blacklist active access token key inside Redis cache", "Clear cookie values on response header"]
      },
      oauth_architecture: {
        enabled: false,
        providers: [],
        social_login_flows: []
      },
      realtime_authentication: {
        required: false,
        websocket_auth_strategy: ["Token validation during query upgrade handshake"],
        realtime_permission_checks: []
      },
      authentication_middleware_architecture: {
        middlewares: ["FastAPI JWTBearer dependencies handler"],
        security_layers: ["CORS policy origin checker", "XSS cookie protection flags"],
        request_validation_layers: ["Pydantic payload constraint checkers"]
      },
      frontend_authentication_flow: {
        auth_pages: ["/login", "/signup"],
        auth_states: ["isAuthenticated", "userProfile", "jwtAccessToken"],
        protected_ui_flows: ["Redirect to /login on fetch returning HTTP 401 status"]
      },
      security_considerations: {
        password_security_rules: ["Minimum length 8 characters", "Must contain special symbols"],
        token_security_rules: ["Access token expiry set to 15 minutes", "Refresh token expiry set to 7 days"],
        authentication_risks: ["Token hijacking via client localstorage if cookies fail", "Replay attacks if TLS is not enforced"]
      },
      future_generation_context: {
        important_notes_for_backend_generation: ["Use passlib with bcrypt context for password hashing."],
        important_notes_for_frontend_generation: ["Protect workspace pages using React Router DOM Navigate guards."],
        important_notes_for_security_agents: ["Perform input validation to prevent SQL/NoSQL Injection vulnerabilities."]
      }
    },
    realtime_architecture: {
      status: "success",
      realtime_strategy: {
        communication_model: "WebSockets for bi-directional streaming, Pub/Sub events for async distribution",
        event_architecture: "Event-driven broadcasting via Redis broker and FastAPI WebSockets",
        scalability_strategy: "Horizontal scaling using Redis pub/sub adapter with multi-instance socket servers",
        synchronization_strategy: "Optimistic UI state updates with back-end database synchronization confirmations"
      },
      websocket_architecture: {
        enabled: true,
        websocket_channels: ["/ws/v1/breathing", "/ws/v1/dashboard", "/ws/v1/notifications"],
        channel_groups: ["paced_breathing", "user_dashboard", "global_alerts"],
        connection_strategy: ["Auto-reconnect with exponential backoff on client", "Query-param auth token upgrade on server"]
      },
      event_driven_architecture: {
        event_types: ["breathing_phase_changed", "stress_logged", "system_alert"],
        event_sources: ["BreathingEngine", "MoodLogger", "SystemWorker"],
        event_consumers: ["React Dashboard UI", "NotificationLogger", "AnalyticsService"],
        event_flow_patterns: ["Source -> Publish to topic -> Redis pub/sub broadcast -> Client websocket sockets"]
      },
      notification_architecture: {
        notification_types: ["Breathing Cycle Milestone", "Stress Score High Warning", "General System Update"],
        delivery_channels: ["In-app toast notifications", "Local browser notifications"],
        priority_rules: ["Breathing milestones = Low priority", "Stress warning = High priority with color-coded prompts", "System update = Info priority"],
        notification_workflows: ["User finishes 3 cycles -> Emit milestone -> Push websocket toast -> Re-render milestone counter badge"]
      },
      frontend_realtime_sync: {
        live_components: ["BreathingRingContainer", "MoodTrendsLineChart", "AlertsDropdownPanel"],
        sync_states: ["active_breathing_timer_seconds", "stress_score_history_list", "unread_alerts_count"],
        realtime_ui_flows: ["Synchronize breathing ring phases in sync with system timer server upgrades"]
      },
      backend_realtime_systems: {
        event_processors: ["FastAPI Websocket router connections manager", "Redis background task subscribers listener"],
        async_services: ["Celery worker background data logger", "Aiohttp websocket handlers"],
        background_event_handlers: ["Database transaction event triggers updates propagation"]
      },
      pubsub_architecture: {
        enabled: true,
        message_brokers: ["Redis"],
        topic_groups: ["breathing_cycles", "user_mood_updates"],
        subscription_patterns: ["Broadcast pattern for breathing ring pacing", "Point-to-point websocket connection for user notifications"]
      },
      websocket_authentication: {
        authentication_required: true,
        auth_flow: ["Retrieve query param token from websocket connection URL path", "Verify signature on server using JWT HS256", "Reject handshake upgrading if signature is invalid"],
        connection_security_rules: ["Enforce TLS (wss://) connections in production", "Rate limit websocket handshakes per IP client"]
      },
      distributed_scalability: {
        horizontal_scaling: true,
        load_distribution_strategy: ["Sticky session load balancer mapping users to same nodes", "Redis adapter broadcasting events across multiple instances"],
        high_frequency_event_groups: ["Paced breathing ring countdown intervals (1Hz updates)"]
      },
      realtime_workflows: [
        {
          "workflow_name": "Broadcast breathing timer sync",
          "event_flow": [
            "Server breathing timer tick runs on 1-second interval loop.",
            "Server publishes phase change (Inhale/Hold/Exhale) to Redis.",
            "Redis broadcasts event to all active websocket connections.",
            "Client UI receives state update and triggers Framer Motion spring expands."
          ]
        }
      ],
      future_generation_context: {
        "important_notes_for_websocket_generation": ["Use fastapi.WebSocket class routers to manage active connections client mappings."],
        "important_notes_for_frontend_generation": ["Protect websocket reconnect loop with exponential backoff backoffs to avoid server overloading."],
        "important_notes_for_backend_generation": ["Utilize aioredis or redis-py asyncio pub/sub client for non-blocking sub listening loops."]
      }
    },
    state_management: {
      status: "success",
      state_management_strategy: {
        global_state_strategy: "Zustand stores isolating user auth sessions and consolidated dashboard metrics lists.",
        local_state_strategy: "React useState hook handles isolated dialog toggles and input fields payloads.",
        cache_strategy: "SWR data fetching hooks cache GET queries with automatic validation on window focus.",
        realtime_sync_strategy: "WebSocket subscriptions push live updates directly into Zustand store layers."
      },
      global_state_architecture: {
        global_states: [
          {
            store_name: "useAuthStore",
            state_variables: ["user", "token", "isAuthenticated", "isVerifying"],
            actions: ["login", "logout", "setToken", "fetchCurrentUser"]
          },
          {
            store_name: "useWellnessStore",
            state_variables: ["active_session_seconds", "breathing_cycles_completed", "active_timer_phase"],
            actions: ["incrementCycles", "setTimerPhase", "resetTimerCycle"]
          }
        ],
        shared_state_groups: ["auth_state", "dashboard_metrics"],
        cross_module_dependencies: ["Dashboard components check useAuthStore.isAuthenticated before mounting views."]
      },
      local_state_architecture: {
        component_states: [
          {
            component_name: "Dashboard",
            state_variables: ["is_modal_open", "form_errors_payload", "search_query"]
          }
        ],
        isolated_states: ["form_fields_buffer", "active_modal_id"],
        ui_interaction_states: ["is_sidebar_collapsed", "current_menu_active_tab"]
      },
      api_cache_architecture: {
        cache_layers: ["SWR cache map providers"],
        cache_targets: [
          {
            endpoint: "/api/v1/users/me",
            cache_key: "swr_user_me",
            ttl_seconds: 300
          }
        ],
        cache_invalidation_rules: [
          "Mutations (POST/PUT/DELETE) on endpoints automatically trigger SWR mutate() calls for corresponding GET keys."
        ]
      },
      realtime_state_synchronization: {
        realtime_states: ["unread_alerts_count", "live_data_heartbeat"],
        websocket_state_flows: [
          "Receive packet on WebSocket connection -> Decode JSON event -> Update global Zustand dashboard store -> Reactive component re-render triggers."
        ],
        live_update_groups: ["global_system_alerts"]
      },
      authentication_state_management: {
        auth_states: ["currentUserProfile", "jwtTokenString", "isAuthenticatedFlag"],
        session_persistence: ["LocalStorage token caching", "Refresh Token secured cookie validation"],
        protected_state_flows: [
          "App mount -> read token from local storage -> verification fetch -> update isAuthenticated store state."
        ]
      },
      frontend_data_synchronization: {
        api_sync_flows: [
          "Dashboard lists trigger cache reload on user pull-to-refresh actions."
        ],
        async_state_updates: ["asyncThunkFetchOverviewStats"],
        data_refresh_patterns: ["Focus refetch validations", "Slow polling intervals for stats widgets"]
      },
      optimistic_ui_architecture: {
        enabled: true,
        optimistic_update_flows: [
          "Pre-insert client entries before network callbacks resolve."
        ],
        rollback_strategies: [
          "Restore state stores from pre-transaction copy maps if API triggers invalid returns."
        ]
      },
      dashboard_state_architecture: {
        dashboard_states: ["selected_time_range_filter", "graph_metric_active_axes"],
        analytics_sync_patterns: ["Time range change triggers reload of cached charts data structures."],
        widget_update_flows: ["Widgets query shared Zustand store selectors to prevent child renders overhead."]
      },
      performance_optimization: {
        memoization_targets: ["useMemoizedAnalyticsGraphsData", "useCallbackTimerCallbacks"],
        lazy_loading_targets: ["SettingsConfigurationPanel", "DetailedAnalyticsChartsTab"],
        high_frequency_update_optimizations: [
          "Throttle ranges and slider updates to reduce state dispatch actions.",
          "Isolate high-frequency websocket counter states into small, memoized react sub-nodes."
        ]
      },
      state_workflows: [
        {
          workflow_name: "Optimistic Stress Score Log",
          state_flow: [
            "User clicks score rating dial.",
            "Add score to local list immediately with temp ID.",
            "Dispatch POST request to backend API.",
            "On success: replace temp ID with database ID.",
            "On failure: restore previous list state and trigger toast."
          ]
        }
      ],
      future_generation_context: {
        important_notes_for_frontend_generation: [
          "Always define strictly typed TypeScript interfaces for Zustand store variables and actions."
        ],
        important_notes_for_realtime_generation: [
          "Isolate WebSocket event listening hooks inside single global context listeners to avoid duplicate socket connections."
        ],
        important_notes_for_testing_agents: [
          "Mock SWR providers and use wrapper hooks to assert store rollback outcomes."
        ]
      }
    },
    devops_architecture: {
      status: "success",
      infrastructure_strategy: {
        deployment_model: "Containerized multi-tier architecture using microservices distribution.",
        containerization_strategy: "Multi-stage production Dockerfiles isolating build assets from lightweight runtimes.",
        cloud_strategy: "Managed serverless container service (AWS ECS Fargate or Google Cloud Run) backed by managed SQL/NoSQL resources.",
        scalability_strategy: "Horizontal application autoscaling with Redis container backend session replication."
      },
      containerization_architecture: {
        docker_required: true,
        container_groups: ["frontend", "backend", "db", "cache"],
        service_containers: [
          {
            name: "frontend",
            image: "node:20-alpine",
            ports: ["5173:5173"],
            env_vars: ["VITE_API_URL", "NODE_ENV"]
          },
          {
            name: "backend",
            image: "python:3.11-slim",
            ports: ["8000:8000"],
            env_vars: ["MONGODB_URI", "REDIS_HOST", "JWT_SECRET", "NODE_ENV"]
          }
        ],
        orchestration_strategy: [
          "Docker Compose orchestration handles local frontend, backend, caching, and database replication.",
          "Production Kubernetes (K8s) Deployment definitions with horizontal pod autoscaler targets."
        ]
      },
      deployment_pipeline_architecture: {
        deployment_stages: ["lint", "test", "build_image", "push_registry", "deploy_stage", "deploy_prod"],
        environment_flow: [
          "Developer Branch -> Merge to Main -> Deploy to Staging (validation) -> Promote to Production (blue/green)."
        ],
        rollback_strategy: [
          "Automatic image-version rollback to previous Docker repository SHA target on health check ping failures."
        ]
      },
      cicd_architecture: {
        pipeline_stages: ["CI Validation", "CD Artifact Generation", "CD Deployment Orchestration"],
        automation_targets: [
          "Trigger automated tests and Docker image compilation on PR merges.",
          "Sync infrastructure declarations with GitOps controllers (e.g. ArgoCD)."
        ],
        testing_gates: [
          "Unit test suites coverage threshold must exceed 80%.",
          "Static application security testing (SAST) scanning with zero high vulnerabilities allowed."
        ]
      },
      cloud_infrastructure: {
        providers: ["AWS (Amazon Web Services)", "GCP (Google Cloud Platform)"],
        service_groups: [
          "AWS ECS (Elastic Container Service) or GCP Cloud Run for application containers.",
          "Amazon RDS or GCP Cloud SQL for database backend layers.",
          "Amazon ElastiCache or GCP Cloud Memorystore for fast Redis caching."
        ],
        deployment_targets: [
          "Secure VPC subnet container endpoints behind Application Load Balancer layers."
        ]
      },
      reverse_proxy_architecture: {
        gateway_strategy: "Nginx edge ingress controller handling SSL termination and payload routing.",
        load_balancing_rules: [
          "Round-robin distribution of API requests across active healthy backend pod replicas.",
          "WebSocket clients sticky sessions routing based on client IP hash rules."
        ],
        routing_rules: [
          "Route '/' and static files directly to frontend container.",
          "Route '/api/v1/*' requests to backend REST API service on port 8000."
        ]
      },
      monitoring_observability: {
        monitoring_targets: [
          "Backend CPU/Memory utilization logs.",
          "API request response times (Latency metrics).",
          "Database active network connections and active operations pool."
        ],
        logging_strategy: [
          "Consolidate container stdout/stderr records into Central Logging service (AWS CloudWatch / ELK Stack)."
        ],
        alerting_systems: [
          "Pushes critical server errors notifications directly to Slack alerts / PagerDuty integration."
        ]
      },
      environment_management: {
        environment_groups: ["development", "staging", "production"],
        secret_management_rules: [
          "Inject database credentials, JWT secrets, and third-party APIs from cloud-native vaults (AWS Secrets Manager / GCP Secret Manager).",
          "Prevent storing secrets, keys, or configurations in git codebase repositories."
        ],
        configuration_layers: [
          "Manage non-sensitive env variables inside environment files (.env) or K8s ConfigMaps."
        ]
      },
      distributed_scalability: {
        horizontal_scaling: true,
        autoscaling_targets: ["backend", "frontend"],
        high_load_services: ["backend"]
      },
      production_optimization: {
        performance_targets: [
          "Ensure response latency remains under 200ms for REST requests.",
          "Optimize Docker image bundle sizing to remain under 150MB."
        ],
        caching_layers: ["Redis API route cache", "CDN static assets cache"],
        optimization_rules: [
          "Enable Gzip/Brotli compression at the Nginx edge layer.",
          "Configure client-side browser caching headers for static frontend assets."
        ]
      },
      deployment_workflows: [
        {
          workflow_name: "Staging Deployment Action",
          deployment_flow: [
            "Lint and execute unit tests on backend/frontend code.",
            "Build docker container images for all updated components.",
            "Push compiled images to Docker Registry tag 'staging'.",
            "Restart staging cluster containers and verify health endpoints status."
          ]
        }
      ],
      future_generation_context: {
        important_notes_for_deployment_generation: [
          "Ensure Nginx configs support WebSocket upgrade request headers.",
          "Confirm database host variables resolve to docker network namespaces locally."
        ],
        important_notes_for_backend_generation: [
          "Do not bundle secrets inside the build. Inject them via runtime environment maps.",
          "Configure database connection pools to handle dynamically scale backend pod counts."
        ],
        important_notes_for_monitoring_agents: [
          "Export metrics on '/metrics' endpoint using Prometheus format.",
          "Provide logs containing trace-ids mapping REST endpoints to background workers."
        ]
      }
    },
    security_architecture: {
      status: "success",
      security_strategy: {
        application_security_model: "Defense-in-depth layout isolating service credentials and enforcing authorization tokens.",
        authentication_security_model: "JWT stateless token pair configuration with sliding rotation rules.",
        infrastructure_security_model: "VPC container networking, Nginx ingress proxying, and managed secrets manager injections.",
        validation_strategy: "Double-barrier input sanitization verifying payloads at controller layers and database schemas validation."
      },
      api_security_architecture: {
        protected_api_groups: ["users", "portfolios", "assets"],
        rate_limiting_rules: [
          "Limit general REST API endpoints to 100 requests per minute per IP address.",
          "Limit authentication routes (login/signup) to 5 requests per minute per IP address to block brute force attempts."
        ],
        request_validation_rules: [
          "Validate incoming payloads against Pydantic model validations inside controllers.",
          "Verify Content-Type header matches application/json and drop malformed REST structures."
        ],
        api_abuse_prevention: [
          "Reject API calls exceeding limit thresholds with HTTP 429 Too Many Requests status code.",
          "Configure SQL injection safeguards by executing operations through backend ORM builders."
        ]
      },
      authentication_security: {
        token_security_rules: [
          "Sign access tokens with HS256 algorithm.",
          "Limit access token expiration durations to 15 minutes."
        ],
        session_security_rules: [
          "Manage refresh tokens within HttpOnly, Secure, SameSite=Strict cookies."
        ],
        password_security_rules: [
          "Hash passwords using bcrypt before committing to databases.",
          "Enforce minimum password length rules of 8 characters containing letters and numbers."
        ],
        refresh_token_policies: [
          "Enforce single-use refresh token rotation (RTR) to block reuse."
        ]
      },
      authorization_security: {
        rbac_validation_rules: [
          "Verify user role maps against endpoint authorization annotations inside router filters."
        ],
        permission_enforcement_layers: [
          "Gateway path filters verify valid headers.",
          "Application controller filters verify role privileges scopes."
        ],
        protected_resource_groups: [
          "Data access layers (verify ownership IDs before deleting/modifying entities)."
        ]
      },
      websocket_security: {
        connection_validation_rules: [
          "Perform initial handshake authentication checking query string token parameters."
        ],
        realtime_permission_checks: [
          "Perform subscription validations whenever a client requests to join a channel."
        ],
        event_authorization_rules: [
          "Verify user token permissions scopes before broadcast relays trigger."
        ]
      },
      frontend_security: {
        protected_frontend_routes: [
          "Block access to dashboards routes when client side isAuthenticated flag is false."
        ],
        frontend_validation_rules: [
          "Sanitize form data entries to prevent basic script injections."
        ],
        secure_storage_rules: [
          "Store transient access tokens in memory variables inside frontend stores."
        ]
      },
      cors_csp_architecture: {
        cors_rules: [
          "Allow CORS headers only from trusted domains listed in configuration files."
        ],
        csp_rules: [
          "Enforce CSP rules: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self' wss:;"
        ],
        trusted_origin_groups: ["localhost:3000", "localhost:5173"]
      },
      input_validation_security: {
        sanitization_rules: [
          "Sanitize strings using libraries to strip script tags and escape HTML chars."
        ],
        payload_validation_rules: [
          "Reject payloads containing elements exceeding size boundaries."
        ],
        file_upload_security_rules: [
          "Scan uploaded file packages using antivirus engines if upload modules exist."
        ]
      },
      environment_security: {
        secret_management_rules: [
          "Load secrets from environment variables injected by secure vault containers."
        ],
        environment_isolation_rules: [
          "Maintain distinct isolation boundaries between staging and production database endpoints."
        ],
        credential_protection_rules: [
          "Rotate API keys on scheduled intervals to limit vulnerability windows."
        ]
      },
      infrastructure_security: {
        container_security_rules: [
          "Run application containers as non-root users inside Docker settings."
        ],
        deployment_security_rules: [
          "Enable automated dependencies security scanning inside CI pipelines."
        ],
        network_security_rules: [
          "Isolate databases containers inside private subnets unreachable from external internet addresses."
        ]
      },
      security_workflows: [
        {
          "workflow_name": "API Handshake Token Rotation Flow",
          "security_flow": [
            "Client submits refresh token stored in secure cookie.",
            "Verify refresh token validity and expiration status.",
            "Generate new access token and new rotated refresh token.",
            "Set new refresh token cookie and return new access token."
          ]
        }
      ],
      future_generation_context: {
        "important_notes_for_backend_generation": [
          "Confirm Pydantic validation handles extreme input sizes to prevent DoS attacks."
        ],
        "important_notes_for_api_generation": [
          "Confirm FastAPI Dependency Injectors enforce oauth2 scheme requirements."
        ],
        "important_notes_for_deployment_generation": [
          "Verify container configurations drop all permissions privileges after setup."
        ]
      }
    },
    testing_architecture: {
      status: "success",
      testing_strategy: {
        testing_model: "Pyramid testing model: comprehensive unit tests, target API integration tests, and critical path end-to-end tests.",
        automation_strategy: "Automated testing pipeline triggered on git push and pull request activities.",
        validation_strategy: "Strict assertions on REST schemas structure and state cache consistency checks.",
        quality_gate_strategy: "Block merge approvals on failing test coverage gates or syntax validation failures."
      },
      unit_testing_architecture: {
        backend_unit_targets: ["app/core/security.py", "app/api/auth.py", "app/api/projects.py"],
        frontend_unit_targets: ["src/hooks/useAuth.ts", "src/store/useDashboardStore.ts"],
        shared_module_targets: ["app/core/config.py", "src/utils/helpers.ts"]
      },
      integration_testing_architecture: {
        integration_flows: [
          "User auth flow verifying database insertions and token cookie returns.",
          "Project creation flows storing blueprint details and triggering background compile runners."
        ],
        cross_module_validation: [
          "Database ORM entity saves verify against controller serialization outputs.",
          "WebSocket event triggers update local Zustand store metrics objects."
        ],
        service_interaction_tests: [
          "Validate backend services connect cleanly to MongoDB and Redis cache clients."
        ]
      },
      api_testing_architecture: {
        api_validation_targets: ["/api/v1/auth/login", "/api/v1/projects"],
        request_response_validation: [
          "Assert API returns HTTP 200 OK with correct schema mapping on valid parameters.",
          "Assert API returns HTTP 422 Unprocessable Entity on schema validation mismatches."
        ],
        rate_limit_testing_rules: [
          "Simulate high request frequencies using Locust to verify HTTP 429 rate limit triggers."
        ]
      },
      frontend_testing_architecture: {
        component_testing_targets: ["ProjectViewer", "SidebarNavigation", "CategorySelectorPanel"],
        ui_interaction_flows: [
          "User clicks categories -> assert project suggestion sliders render suggestions.",
          "User selects suggestions -> verify selection discussion thread loads."
        ],
        frontend_state_validation: [
          "Assert Zustand stores mutate values correctly on action dispatches.",
          "Assert SWR local caches reload query lists automatically on focus events."
        ]
      },
      authentication_testing: {
        auth_validation_flows: [
          "Login API submits passwords -> verify Bcrypt hash matches.",
          "Assert JWT token headers match HS256 encryption keys."
        ],
        permission_testing_rules: [
          "Request user details as unauthenticated guest -> assert API returns HTTP 401 Unauthorized.",
          "Request admin utilities using standard role permissions -> assert API returns HTTP 403 Forbidden."
        ],
        session_validation_rules: [
          "Simulate expired token usage -> assert token rotation refresh loop triggers correctly."
        ]
      },
      realtime_testing_architecture: {
        websocket_test_flows: [
          "Connect test client to WebSocket gateway `/ws/v1/updates`.",
          "Send mock subscription payload and verify immediate confirmation packet.",
          "Assert broadcast events are received by multiple connected test socket instances."
        ],
        event_validation_rules: [
          "Assert broadcasts drop client connection on malformed packet uploads."
        ],
        realtime_sync_validation: [
          "Verify clients receive updates state packet matches current server database values."
        ]
      },
      e2e_testing_architecture: {
        critical_user_flows: [
          "User visits LandingPage -> logs in via LoginPage -> redirects to UserDashboard view.",
          "Session expiry redirects unauthorized user instantly back to LoginPage."
        ],
        workflow_validation_targets: [
          "Verify generated virtual file viewer pane renders codebase JSON configs after compilation completes."
        ],
        cross_platform_validation: [
          "Verify responsive UI layouts adapt cleanly on mobile and desktop layout frame boundaries."
        ]
      },
      load_testing_architecture: {
        high_load_targets: ["backend REST API gateway", "WebSocket connections broker engine"],
        stress_testing_flows: [
          "Increase virtual users count up to 1000 requests/sec and monitor database connection pooling states."
        ],
        performance_validation_rules: [
          "Average API response times must remain under 300ms under load conditions."
        ]
      },
      mocking_fixture_architecture: {
        mock_services: ["Nvidia NIM completions endpoint", "OAuth login providers callbacks"],
        fixture_groups: ["Mock User profiles datasets", "Mock Project blueprints JSON files"],
        test_environment_rules: [
          "Use separate test databases (e.g. sarthi_test MongoDB) and drop db after unit test suite runs."
        ]
      },
      cicd_testing_gates: {
        pipeline_validation_stages: ["PR lint check", "Unit testing suite execution", "Build validations gate"],
        blocking_conditions: [
          "Block branch merging on test suites failures or coverage drops under 80%."
        ],
        quality_thresholds: [
          "Lint rules must pass with zero critical code quality errors."
        ]
      },
      future_generation_context: {
        important_notes_for_test_generation: [
          "Ensure tests use mock databases to prevent local workspace data corruption.",
          "Confirm all test runs cleanly close databases sessions pools to avoid network hangs."
        ],
        important_notes_for_backend_generation: [
          "Provide explicit API endpoint routers configurations to enable automated integration test scans."
        ],
        important_notes_for_frontend_generation: [
          "Include data-testid properties inside key UI components to support automated Playwright test targets."
        ]
      }
    },
    validation_architecture: {
      status: "success",
      validation_strategy: {
        validation_model: "Cross-tier consistency checking executing identity, contract, and deployment alignment verification checks.",
        consistency_strategy: "Direct property mapping asserting DB entity fields correctly match API response serializers and frontend Zustand stores.",
        dependency_validation_strategy: "Acyclic topological sorting verifying frontend page dependencies and backend service components initialize cleanly.",
        compilation_readiness_strategy: "Multi-point check blocking downstream codebase compilation generators on interface mismatches."
      },
      entity_validation: {
        validated_entities: ["User", "Portfolio", "Asset", "Transaction"],
        missing_entities: [],
        conflicting_entities: []
      },
      api_validation: {
        validated_routes: ["/api/v1/auth/signup", "/api/v1/auth/login", "/api/v1/projects"],
        missing_routes: [],
        frontend_backend_contract_conflicts: []
      },
      database_validation: {
        validated_relationships: [
          "User (1) has many Portfolios (N)",
          "Portfolio (1) contains many Assets (N)",
          "User (1) records many Transactions (N)"
        ],
        missing_relations: [],
        schema_conflicts: []
      },
      authentication_validation: {
        validated_auth_flows: ["JWT login token validation loop", "Stateless bearer header validations"],
        permission_conflicts: [],
        protected_route_conflicts: []
      },
      realtime_validation: {
        validated_websocket_flows: ["Active connection subscription handshake authentication verification"],
        event_conflicts: [],
        sync_conflicts: []
      },
      frontend_validation: {
        validated_components: ["ProjectViewer", "SidebarNavigation", "CategorySelectorPanel"],
        missing_ui_dependencies: [],
        state_conflicts: []
      },
      infrastructure_validation: {
        deployment_conflicts: [],
        service_dependency_conflicts: [],
        environment_validation_rules: [
          "Database port variables must match container bindings parameters."
        ]
      },
      cross_module_validation: {
        dependency_graph_issues: [],
        module_alignment_checks: [
          "Verify frontend API fetches correctly call endpoints defined in router lists.",
          "Verify state store actions map directly to backend mutations interfaces."
        ],
        pipeline_integrity_checks: [
          "Check previous 13 stages generated output JSON objects are present and parse correctly."
        ]
      },
      compilation_readiness: {
        ready_for_generation: true,
        blocking_issues: [],
        recommended_corrections: []
      },
      future_generation_context: {
        important_notes_for_generation_agents: [
          "Code generators should strictly use the field names defined in Database Architecture entities."
        ],
        important_notes_for_integration_agents: [
          "Confirm API serializers map exactly to frontend fetch response parameters mappings."
        ],
        important_notes_for_compilation_agents: [
          "Generate fully functional Dockerfiles matching DevOps container groups."
        ]
      }
    },
    database_model_generation: {
      status: "success",
      persistence_generation_strategy: {
        orm_strategy: "SQLAlchemy declarative base class mapping utilizing async PG engines.",
        migration_strategy: "Alembic autogenerated revisions with sequential constraint mapping checks.",
        validation_strategy: "Pydantic v2 schemas validating request and response payloads matching DB data classes.",
        repository_mapping_strategy: "Generic repositories wrapping db sessions with type-safe operations."
      },
      generated_models: [
        {
          model_name: "User",
          table_name: "users",
          fields: [
            { "name": "id", "type": "UUID", "primary_key": true, "nullable": false, "default": "uuid.uuid4" },
            { "name": "email", "type": "String(255)", "primary_key": false, "nullable": false },
            { "name": "hashed_password", "type": "String(255)", "primary_key": false, "nullable": false }
          ],
          relationships: [
            { "target_model": "Portfolio", "relationship_type": "one-to-many", "backref": "user", "cascade": "all, delete-orphan" }
          ],
          indexes: [
            { "index_name": "idx_users_email", "fields": ["email"], "unique": true }
          ]
        }
      ],
      relationship_generation: {
        foreign_keys: [],
        many_to_many_mappings: [],
        cascade_rules: [
          "User cascades delete-orphan to Portfolio."
        ]
      },
      migration_generation: {
        migration_groups: ["users_migration"],
        dependency_order: ["users_migration"],
        rollback_rules: [
          "Drop tables users."
        ]
      },
      validation_schema_generation: {
        request_validation_models: [],
        response_validation_models: [],
        shared_validation_contracts: []
      },
      repository_generation: {
        repository_targets: ["UserRepository"],
        shared_persistence_layers: ["DatabaseSessionManager"],
        async_repository_targets: ["AsyncUserRepository"]
      },
      authentication_persistence: {
        auth_models: ["UserAuth"],
        session_models: ["UserSession"],
        token_persistence_rules: []
      },
      optimization_generation: {
        index_generation_targets: [],
        cache_compatible_models: [],
        high_frequency_models: []
      },
      generation_dependencies: {
        blocking_models: [],
        shared_dependencies: [],
        cross_module_dependencies: []
      },
      future_generation_context: {
        important_notes_for_backend_generation: [],
        important_notes_for_api_generation: [],
        important_notes_for_compilation_agents: []
      }
    },
    backend_code_generation: {
      status: "success",
      backend_generation_strategy: {
        architecture_style: "FastAPI Clean service-repository layout separating controllers from persistence operations.",
        service_pattern: "Stateless service modules wrapping generic repositories and injecting database sessions.",
        dependency_injection_strategy: "Hierarchical FastAPI dependencies for database connection retrieval and JWT validations.",
        async_execution_strategy: "Async-first service routines using SQLAlchemy async database drivers."
      },
      generated_backend_structure: {
        root_modules: ["app/main.py", "app/core/config.py", "app/db/session.py"],
        service_modules: ["app/services/stresslog_service.py"],
        repository_modules: ["app/repositories/stresslog_repository.py"],
        middleware_modules: ["app/middlewares/auth_middleware.py", "app/middlewares/logging_middleware.py"],
        utility_modules: ["app/utils/security.py", "app/utils/datetime_utils.py"]
      },
      service_generation: {
        generated_services: [
          {
            service_name: "StressLogService",
            methods: ["create_stresslog", "get_stresslog_by_id", "update_stresslog", "delete_stresslog"],
            injected_repositories: ["StressLogRepository"]
          }
        ],
        transactional_workflows: [
          "User signup workflow executing password hashing, unique check, database write, and JWT response generation."
        ],
        cross_service_dependencies: []
      },
      repository_generation: {
        generated_repositories: [
          {
            repository_name: "StressLogRepository",
            mapped_model: "StressLog",
            custom_queries: ["find_stresslog_by_id"]
          }
        ],
        orm_bindings: [
          "StressLogRepository connects to StressLog database model."
        ],
        persistence_dependencies: []
      },
      middleware_generation: {
        generated_middlewares: [
          {
            name: "CORSMiddleware",
            configuration: "Configure trusted origins list with allowed headers and request methods."
          }
        ],
        auth_middlewares: [
          "JWTMiddleware validating Authorization Bearer headers and storing payload in request state."
        ],
        request_validation_middlewares: []
      },
      dependency_injection_generation: {
        generated_dependencies: ["get_db", "get_current_user_from_token"],
        shared_bindings: ["db -> get_db session dependency mapper"],
        service_container_rules: [
          "All repositories must receive the active db session dependency.",
          "All services receive their respective repository containers."
        ]
      },
      background_worker_generation: {
        async_workers: ["Celery app utilizing Redis brokers"],
        scheduled_tasks: ["Daily cache cleanup", "Weekly transaction reports generation"],
        event_processing_flows: []
      },
      exception_handling_generation: {
        global_exception_handlers: ["HTTPException handler", "ValidationError handler", "SQLAlchemyError handler"],
        custom_error_groups: ["EntityNotFound", "DuplicateKeyError", "InsufficientPermissions"],
        validation_error_handlers: []
      },
      configuration_generation: {
        environment_configs: ["DATABASE_URL", "JWT_SECRET", "REDIS_URL"],
        runtime_configs: ["PORT", "WORKERS_COUNT"],
        secret_dependencies: ["Access Token Secret key", "Refresh Token Secret key"]
      },
      websocket_backend_generation: {
        websocket_integrations: ["WebSocketConnectionManager routing live socket connections"],
        event_handlers: ["broadcast_update", "handle_disconnect"],
        realtime_dependencies: ["Redis channels pub/sub connector"]
      },
      generation_dependencies: {
        blocking_modules: ["app/core/config.py", "app/db/session.py"],
        shared_dependencies: ["app/models/project.py"],
        cross_module_generation_rules: [
          "Core configurations must compile first.",
          "Database model schemas compile before service classes."
        ]
      },
      future_generation_context: {
        important_notes_for_frontend_generation: [
          "Frontend API actions must match controller endpoint path structures."
        ],
        important_notes_for_auth_generation: [
          "Authorize decorators must matches authentication claims models."
        ],
        important_notes_for_compilation_agents: [
          "Verify requirements.txt installs asyncpg and PyJWT correctly."
        ]
      }
    },
    api_implementation: {
      status: "success",
      api_generation_strategy: {
        routing_architecture: "Modular FastAPI APIRouter structures grouped by sub-domain modules, registered inside app/main.py",
        validation_strategy: "Pydantic v2 schemas executing strict types checking with clean validation mappings.",
        async_execution_strategy: "Async-first controller routes executing non-blocking service tasks.",
        response_strategy: "Standardized envelopes containing user payloads, metadata timestamps, and success descriptors."
      },
      generated_routes: [
        {
          route_name: "auth_signup",
          route_path: "/api/v1/auth/signup",
          http_method: "POST",
          service_binding: "UserService.signup",
          dependencies: ["get_db"]
        },
        {
          route_name: "auth_login",
          route_path: "/api/v1/auth/login",
          http_method: "POST",
          service_binding: "UserService.login",
          dependencies: ["get_db"]
        },
        {
          route_name: "create_stresslog",
          route_path: "/api/v1/stresslogs",
          http_method: "POST",
          service_binding: "StressLogService.create_stresslog",
          dependencies: ["get_db", "get_current_user"]
        },
        {
          route_name: "get_stresslogs",
          route_path: "/api/v1/stresslogs",
          http_method: "GET",
          service_binding: "StressLogService.get_stresslogs",
          dependencies: ["get_db", "get_current_user"]
        }
      ],
      router_generation: {
        router_modules: ["app/api/v1/auth.py", "app/api/v1/stresslogs.py"],
        route_groupings: ["auth", "stresslogs"],
        shared_router_dependencies: ["get_db", "get_current_user"]
      },
      request_response_generation: {
        request_models: ["UserSignupSchema", "UserLoginSchema", "StressLogCreateSchema"],
        response_models: ["UserResponseSchema", "TokenResponseSchema", "StressLogResponseSchema"],
        shared_validation_contracts: ["UUIDValidationRule", "PaginationLimitsValidationRule"]
      },
      crud_generation: {
        crud_groups: ["StressLog CRUD"],
        entity_route_mappings: ["StressLog -> /api/v1/stresslogs"],
        repository_bindings: ["StressLogRepository -> db"]
      },
      protected_route_generation: {
        protected_routes: ["/api/v1/stresslogs"],
        permission_bindings: ["/api/v1/stresslogs -> user"],
        auth_dependencies: ["get_current_user"]
      },
      async_api_generation: {
        async_routes: ["POST /api/v1/stresslogs"],
        background_execution_routes: ["POST /api/v1/projects -> compile_project_background"],
        event_trigger_routes: []
      },
      websocket_route_generation: {
        websocket_routes: ["/ws/v1/updates"],
        event_bindings: ["milestone_reached -> broadcast_update"],
        realtime_dependencies: ["RedisPubSubClient"]
      },
      pagination_filter_generation: {
        pagination_routes: ["GET /api/v1/stresslogs"],
        filtering_contracts: ["limit", "offset"],
        sorting_rules: ["created_at -> DESC"]
      },
      exception_handling_generation: {
        generated_error_handlers: ["HTTPExceptionHandler", "RequestValidationError", "ServiceException"],
        validation_error_groups: ["PydanticValidationError"],
        custom_exception_mappings: ["EntityNotFound -> 404", "AuthenticationFailed -> 401", "DatabaseOperationFailed -> 500"]
      },
      generation_dependencies: {
        blocking_routes: ["/api/v1/auth/login", "/api/v1/auth/signup"],
        shared_dependencies: ["app/api/deps.py", "app/core/security.py"],
        cross_module_generation_rules: [
          "Sub-routers must import the global dependency bindings from app/api/deps.py."
        ]
      },
      future_generation_context: {
        important_notes_for_frontend_generation: [
          "Frontend request interceptors must append bearer tokens to routes requiring authentication."
        ],
        important_notes_for_integration_agents: [
          "Websockets routing must resolve connection upgrades securely."
        ],
        important_notes_for_compilation_agents: [
          "Ensure main.py imports and aggregates all routes to the main app instance."
        ]
      }
    },
    frontend_code_generation: {
      status: "success",
      frontend_generation_strategy: {
        frontend_architecture: "Next.js 14 App Router layout separating presentation components from client-side state managers.",
        routing_strategy: "Static and dynamic folder routing mappings backed by AuthSessionGuard layouts.",
        state_integration_strategy: "Consolidated Zustand client stores synced with SWR background query caches.",
        ui_rendering_strategy: "React Server Components (RSC) for metadata, client-side dynamic widgets (CSR) for charts."
      },
      generated_frontend_structure: {
        app_routes: ["app/page.tsx", "app/layout.tsx", "app/globals.css", "app/login/page.tsx", "app/signup/page.tsx", "app/dashboard/page.tsx"],
        layout_modules: ["app/layout.tsx", "app/dashboard/layout.tsx"],
        shared_components: ["components/Button.tsx", "components/Input.tsx", "components/Card.tsx", "components/Navbar.tsx"],
        frontend_utilities: ["utils/api_client.ts", "utils/date_helpers.ts"]
      },
      page_generation: {
        generated_pages: ["LandingPage", "LoginPage", "SignupPage", "DashboardOverviewPage"],
        dashboard_views: ["OverviewTab", "AnalyticsTab"],
        protected_pages: ["/dashboard"]
      },
      api_integration_generation: {
        api_hooks: ["useAuth", "useUpdatesWebSocket", "useStressLogsList"],
        request_handlers: ["GET /api/v1/stresslogs -> fetchStressLogsList"],
        response_state_bindings: ["stresslogsListData -> useWellnessStore"]
      },
      authentication_frontend_generation: {
        auth_flows: ["Email Credentials Signin", "Register account verification form"],
        protected_route_bindings: ["/dashboard -> AuthSessionGuard"],
        session_state_integrations: ["userProfileInfo -> useAuthStore", "jwtCredentials -> localStorageSession"]
      },
      realtime_frontend_generation: {
        websocket_integrations: ["useWebSocketUpdatesStreamListener"],
        realtime_ui_bindings: ["alerts_event -> dispatchToastAlertNotification"],
        live_state_dependencies: ["webSocketConnectedStateVariable"]
      },
      form_generation: {
        generated_forms: ["LoginForm", "SignupForm", "CreateStressLogForm"],
        validation_integrations: ["Zod Schema Validation bindings inside React Hook Form controllers"],
        submission_workflows: ["submitFormAction -> apiRequestPayloadSerializer"]
      },
      error_boundary_generation: {
        error_boundaries: ["AppLevelGlobalErrorBoundary", "ComponentLevelFallbackWrapper"],
        fallback_ui_flows: ["displayErrorStateToastMessageUI"],
        frontend_exception_rules: ["status401Error -> clearSessionAndRedirectToLoginScreen"]
      },
      responsive_generation: {
        responsive_layouts: ["GridTwoColumnSidebarDesktopView", "ResponsiveFlexColumnMobileView"],
        mobile_adaptations: ["CollapsibleSideDrawerNavTabs", "SwipeableDataCardActions"],
        accessibility_integrations: ["AriaTogglesForThemeMode", "AccessibleFormInputLabelsWithAriaDescriptors"]
      },
      generation_dependencies: {
        blocking_modules: ["app/layout.tsx", "utils/api_client.ts"],
        shared_dependencies: ["components/Button.tsx", "components/Input.tsx"],
        cross_module_generation_rules: [
            "Next.js Global Root Layout compiles first.",
            "Common component elements compile before pages routes modules are initialized."
        ]
      },
      future_generation_context: {
        important_notes_for_ui_generation: [
            "Ensure Tailwind config supports HSL values to match active palette parameters."
        ],
        important_notes_for_theme_generation: [
            "Typography font config inherits configurations from Tailwind tailwind.config.js."
        ],
        important_notes_for_integration_agents: [
            "All SWR fetch requests must check valid JWT signatures in state stores."
        ]
      }
    },
    ui_component_generation: {
      status: "success",
      ui_generation_strategy: {
        component_architecture: "Atomic Component Architecture organizing UI elements into visual primitives.",
        design_system_strategy: "TailwindCSS config token injection matching custom HSL palette mapping.",
        responsive_strategy: "Fluid mobile-first responsive grids resizing into bottom navigation wrappers.",
        ui_rendering_strategy: "Hybrid React Server Components (RSC) layout containing client-side interactive widgets."
      },
      generated_components: {
        shared_components: ["Button", "Input", "Card", "Badge", "Separator"],
        dashboard_components: ["SidebarNavigation", "DashboardHeader", "SummaryMetricCard", "StressLogCardRowWidget"],
        form_components: ["LoginFormFields", "SignupFormFields", "CreateStressLogFormFields", "UpdateStressLogFormFields"],
        navigation_components: ["TabsMenuSelector", "SidebarNavGroup"],
        modal_components: ["ConfirmActionDialog", "CreateStressLogModalDialog"]
      },
      dashboard_generation: {
        analytics_widgets: ["StressLogSummaryOverviewWidget", "StressLogDistributionChart"],
        chart_components: ["ResponsiveBarChart", "TrendLineWidget"],
        realtime_dashboard_bindings: ["webSocketConnectionStream -> updateDashboardViewports"]
      },
      form_generation: {
        generated_forms: ["LoginForm", "SignupForm", "CreateStressLogForm", "UpdateStressLogForm"],
        validation_integrations: ["Zod validations for credentials matches", "Zod validations for StressLog payload fields"],
        submission_ui_flows: ["onSubmit -> setSpinnerLoadingState", "submitStressLogAction -> dispatchPOSTRequest"]
      },
      protected_ui_generation: {
        protected_components: ["ProtectedDashboardLayout", "ManageStressLogAccessControl"],
        role_based_ui_rules: ["userPrivilegeRoleUser -> blockSettingsControlsEdit", "adminRolePrivilege -> allowCreateStressLogButton"],
        session_visibility_bindings: ["isAuthenticated -> renderSidebarNavigation", "userProfileInfo -> renderStressLogRowsData"]
      },
      responsive_generation: {
        responsive_components: ["MobileNavbar", "ResponsiveGridWrapper", "StressLogGridMobileLayout"],
        mobile_adaptations: ["BottomBarMobileNavigation", "SwipeableStressLogActionMenu"],
        adaptive_layout_rules: ["smBreakpoint -> toggleCollapsedSidebar", "lgBreakpoint -> renderDetailedStressLogColumns"]
      },
      loading_error_generation: {
        loading_components: ["CircularLoadingSpinner"],
        skeleton_components: ["MetricCardSkeleton", "DashboardGridSkeleton", "StressLogListSkeletonLoader"],
        error_state_components: ["LoadFailedBannerAlert", "GlobalErrorBoundaryBoundary", "StressLogNotFoundFallbackView"]
      },
      accessibility_generation: {
        accessibility_rules: ["ariaLabelOnBreathingPacedRing", "colorContrastMinRatioRequirement4.5"],
        keyboard_navigation_rules: ["escapeKeyToDismissModals", "tabIndexSequenceFocusControls"],
        screen_reader_integrations: ["announceActiveMilestoneAlertMessage"]
      },
      shared_ui_utilities: {
        shared_hooks: ["useThemeState", "useWebSocketUpdates", "useStressLogMutations"],
        ui_helpers: ["cnMerger", "formatDatetimeString", "formatStressLogMetadataPayload"],
        component_abstractions: ["BaseModalShell", "StressLogPrimitiveRowAbstract"]
      },
      generation_dependencies: {
        blocking_components: ["app/layout.tsx", "components/Button.tsx"],
        shared_dependencies: ["lucide-react", "framer-motion", "clsx"],
        cross_component_generation_rules: [
          "Design tokens are compiled first so that primitives resolve theme styles variables correctly."
        ]
      },
      future_generation_context: {
        important_notes_for_theme_generation: [
          "Tailwind config must support standard HSL variables to match theme specifications."
        ],
        important_notes_for_state_generation: [
          "Always define type interfaces for components properties when binding stores values."
        ],
        important_notes_for_integration_agents: [
          "Ensure form handlers correctly toggle submission buttons loading indicators."
        ]
      }
    },
    state_implementation: {
      status: "success",
      state_generation_strategy: {
        state_architecture: "Zustand global stores managing user authentication and wellness states paired with SWR cache.",
        cache_strategy: "Focus-revalidated SWR data fetches with automatic invalidation query hooks.",
        realtime_strategy: "FastAPI WebSocket event listeners updating Zustand store states dynamically.",
        session_strategy: "JWT accessToken verification with silent sliding cookies refresh validations."
      },
      zustand_generation: {
        generated_stores: ["useAuthStore", "useWellnessStore"],
        shared_state_groups: ["authSessionGroup", "wellnessMetricsGroup"],
        cross_store_dependencies: ["useWellnessStore reads useAuthStore.isAuthenticated before submitting stress logs."]
      },
      cache_generation: {
        swr_query_hooks: ["useCurrentUserProfile", "useStressLogsList"],
        cache_invalidation_rules: ["mutate('/api/v1/stresslogs') on log creation or removal"],
        async_refetch_flows: ["fetchStressLogsList -> updateWellnessStoreCache"]
      },
      optimistic_ui_generation: {
        optimistic_update_flows: ["addStressLogOptimistically -> prependTempLogIntoStoreList"],
        rollback_rules: ["logSubmissionPOSTFailure -> revertWellnessStoreToPreTransactionSnapshot"],
        sync_recovery_rules: ["onNetworkReconnect -> triggerStressLogsSWRRevalidate"]
      },
      realtime_state_generation: {
        websocket_state_bindings: ["wsBreathingUpdatesChannel -> updatePacedSecondsState"],
        event_sync_flows: ["onMilestoneEvent -> triggerMilestoneToastNotificationAlert"],
        live_dashboard_states: ["activeBreathingSecondsCompletedCount"]
      },
      session_state_generation: {
        auth_state_flows: ["onSubmitLoginForm -> setAuthenticatedCredentialsState"],
        protected_session_bindings: ["useAuthStore.token -> appendBearerHeaderToSWRFetchRequests"],
        token_refresh_sync_rules: ["tokenExpiryCountdown -> triggerTokenRotationRefreshQuery"]
      },
      shared_hook_generation: {
        custom_hooks: ["useActiveThemeState", "useSessionStoreData"],
        shared_ui_bindings: ["useThemeState -> applyStylingClasses"],
        frontend_state_utilities: ["mergerStatePayload", "formatDatetimeTimestamp"]
      },
      loading_error_state_generation: {
        loading_state_flows: ["setStressLogSubmitActionLoadingStateSpinner"],
        error_recovery_flows: ["fetchAPIFailure -> triggerFallbackBannerAlertView"],
        fallback_state_rules: ["apiUnauthError401 -> clearAuthSessionAndRedirect"]
      },
      state_persistence_generation: {
        persisted_states: ["themeModeSelectionSetting", "lastVisitedDashboardRoute"],
        local_storage_rules: ["persistToLocalStorageWithSessionExpiryCheck"],
        hydration_flows: ["onAppMountHydrateThemeStateFromLocalStorage"]
      },
      generation_dependencies: {
        blocking_state_dependencies: ["useAuthStore.ts", "utils/api_client.ts"],
        shared_dependencies: ["zustand/middleware", "swr"],
        cross_module_generation_rules: [
          "useAuthStore compiles first to configure session token tokens headers for SWR."
        ]
      },
      future_generation_context: {
        important_notes_for_integration_agents: [
          "All REST calls require valid JWT signatures in authorization header mappings."
        ],
        important_notes_for_validation_agents: [
          "Zustand selectors should isolate components states updates to prevent extra render cycles."
        ],
        important_notes_for_compilation_agents: [
          "Ensure requirements.txt builds asyncpg and PyJWT correctly."
        ]
      }
    },
    integration_generation: {
      status: "success",
      integration_generation_strategy: {
        runtime_architecture: "React dynamic layouts binding FastAPI REST and WebSockets controllers.",
        integration_strategy: "Zustand selector states mapping SWR caches to render lists.",
        realtime_strategy: "FastAPI WebSocket connections relaying broadcast messages to dashboard states.",
        session_sync_strategy: " Bearer tokens headers attached dynamically to API client instances."
      },
      frontend_backend_integration: {
        api_bindings: ["useCurrentUserProfile -> GET /api/v1/auth/me", "useStressLogsList -> GET /api/v1/stresslogs"],
        service_integrations: ["FastAPI routing stress logs submissions to local stores"],
        cross_module_runtime_flows: ["Auth token verify checks upgrading HTTP handshakes to WSS"]
      },
      authentication_integration: {
        protected_route_integrations: ["/dashboard -> ProtectedLayout", "/api/v1/stresslogs -> JWTBearer"],
        session_sync_flows: ["tokenExpiration -> triggerTokenRotationQuery"],
        rbac_runtime_bindings: ["User.role == 'user' -> enableStressLogsCRUD"]
      },
      realtime_integration: {
        websocket_runtime_bindings: ["wsBreathingChannel -> updateWellnessStorePacedSeconds"],
        event_sync_flows: ["milestone_event -> triggerMilestoneAlertToast"],
        live_state_integrations: ["activeBreathingSecondsCompletedCount -> dashboardProgressCircle"]
      },
      state_integration: {
        store_api_bindings: ["useAuthStore.token -> APIClientInstance"],
        cache_runtime_integrations: ["mutate('/api/v1/stresslogs') on stress score submissions"],
        optimistic_ui_runtime_flows: ["addStressLogOptimistically -> preInsertTempLogIntoLocalList"]
      },
      shared_dependency_integration: {
        shared_runtime_dependencies: ["zustand", "swr", "framer-motion", "clsx"],
        cross_module_bindings: ["APIClient -> useAuthStore"],
        global_runtime_utilities: ["cnClassNamesMerger"]
      },
      environment_integration: {
        environment_bindings: ["VITE_API_URL -> http://localhost:8000"],
        runtime_configuration_flows: ["loadEnvironmentVariables -> configureAPIClientUrl"],
        secret_dependency_integrations: ["JWT_SECRET -> authMiddlewareSignatureVerifier"]
      },
      error_runtime_integration: {
        error_propagation_flows: ["apiFailure -> displayToastAlert"],
        fallback_runtime_rules: ["status401Error -> clearSessionAndRedirect"],
        runtime_recovery_systems: ["onNetworkReconnect -> triggerSWRCacheRefetch"]
      },
      workflow_integrations: {
        end_to_end_workflows: ["UserLogin -> RedirectDashboard -> FetchWellnessMetrics"],
        async_runtime_flows: ["submitStressLog -> triggerBackgroundCompilation"],
        distributed_execution_flows: ["WebSocketEvent -> BroadcastAllConnectedUsers"]
      },
      generation_dependencies: {
        blocking_integrations: ["utils/api_client.ts", "context/WorkspaceContext.tsx"],
        shared_dependencies: ["react", "react-dom"],
        cross_module_generation_rules: ["APIClient loads before SWR queries mount."]
      },
      future_generation_context: {
        important_notes_for_build_compilation: ["Verify uvicorn port variables map cleanly inside environment configuration files."],
        important_notes_for_validation_agents: ["Ensure token verify checks do not block static client asset compilation routes."],
        important_notes_for_export_agents: ["Compile and bundle all environment configurations into final production build images."]
      }
    },
    build_compilation: {
      status: "success",
      build_compilation_strategy: {
        project_architecture: "React SPA coupled with FastAPI microservice.",
        runtime_strategy: "Uvicorn asynchronous worker processes orchestrating Next.js frontend builds.",
        dependency_strategy: "Consolidated npm packages paired with virtualenv Python modules.",
        build_assembly_strategy: "Multi-stage production build building client static assets and package servers."
      },
      project_structure_generation: {
        root_structure: ["backend", "frontend", "docker-compose.yml", "README.md"],
        backend_structure: ["app/main.py", "app/core/config.py", "app/api/v1/auth.py", "app/api/v1/stresslogs.py"],
        frontend_structure: ["app/page.tsx", "app/layout.tsx", "app/globals.css", "app/dashboard/page.tsx"],
        shared_runtime_modules: ["shared/types", "shared/validators"]
      },
      dependency_compilation: {
        resolved_dependencies: ["fastapi>=0.100.0", "uvicorn>=0.22.0", "react>=18.2.0", "zustand>=4.3.8", "swr>=2.2.0"],
        shared_package_integrations: ["shared/types -> backend & frontend definitions"],
        runtime_dependency_graph: ["app/main.py -> app/api/v1 -> app/services"]
      },
      runtime_assembly: {
        startup_workflows: ["runDatabaseMigrations -> launchFastAPIApp -> runFrontendBuild"],
        environment_runtime_bindings: ["VITE_API_URL -> http://localhost:8000"],
        cross_module_runtime_flows: ["Client UI calls REST API endpoints on Mount"]
      },
      frontend_backend_compilation: {
        api_runtime_integrations: ["HTTP REST integrations bridging CORS APIs"],
        auth_runtime_integrations: ["JWT bearer token validation middleware checking route actions"],
        realtime_runtime_integrations: ["Websocket subscriptions synching dashboard store models"]
      },
      configuration_assembly: {
        environment_configs: ["VITE_API_URL=http://localhost:8000", "MONGODB_URI=mongodb://localhost:27017"],
        runtime_configs: ["next.config.js", "tsconfig.json", "requirements.txt"],
        secret_runtime_dependencies: ["JWT_SECRET", "MONGODB_URI"]
      },
      realtime_compilation: {
        websocket_runtime_systems: ["Websocket router mapping channels"],
        event_runtime_flows: ["wsChannelUpdates -> updatePacedSecondsState"],
        distributed_sync_integrations: ["Redis adapter mapping websocket pub/sub events"]
      },
      build_validation: {
        validated_modules: ["backend/app", "frontend/src"],
        resolved_runtime_conflicts: ["Port collision resolved by mapping API to 8000 & frontend to 3000"],
        compilation_integrity_rules: ["All typescript packages compile with zero --noEmit warnings"]
      },
      production_assembly: {
        production_ready_modules: ["build/dist", "app/compiled"],
        deployment_safe_structures: ["Dockerfile.frontend", "Dockerfile.backend", "nginx.conf"],
        export_ready_packages: ["fullstack-app-v1.zip"]
      },
      generation_dependencies: {
        blocking_build_dependencies: ["npm install", "pip install -r requirements.txt"],
        shared_runtime_dependencies: ["react", "fastapi"],
        cross_module_compilation_rules: ["Backend ORM models compile before launching main server route."]
      },
      future_generation_context: {
        important_notes_for_export_agents: ["Ensure build folders contain clean README deployment logs."],
        important_notes_for_deployment_agents: ["Verify uvicorn target port variables are configured in Dockerfile runtime commands."],
        important_notes_for_validation_agents: ["Verify websocket connection handshakes run successfully on staging routes."]
      }
    }
  },
];

export const WorkspaceProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<{ id: string; name: string; email: string } | null>(null);
  
  const [chats, setChats] = useState<ChatSession[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);

  const [currentCategory, setCurrentCategory] = useState<string>("");
  const [currentInput, setCurrentInput] = useState<string>("");

  const [showAuthModal, setShowAuthModal] = useState<boolean>(false);
  const [authMode, setAuthMode] = useState<"login" | "signup">("login");

  const [showAbout, setShowAbout] = useState<boolean>(false);
  const [showContact, setShowContact] = useState<boolean>(false);
  
  const [isGeneratingProject, setIsGeneratingProject] = useState<boolean>(false);
  const [showRightPane, setShowRightPane] = useState<boolean>(true);
  const [showLeftPane, setShowLeftPane] = useState<boolean>(true);

  const [suggestions, setSuggestions] = useState<ProjectSuggestion[]>([]);
  const [isFetchingSuggestions, setIsFetchingSuggestions] = useState<boolean>(false);

  const fetchSuggestions = async (category: string) => {
    setIsFetchingSuggestions(true);
    setSuggestions([]);
    const token = localStorage.getItem("token");
    if (!token) {
      setIsFetchingSuggestions(false);
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/projects/suggestions?category=${category}`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setSuggestions(data);
      }
    } catch (e) {
      console.error("Fetch suggestions failed:", e);
    } finally {
      setIsFetchingSuggestions(false);
    }
  };

  const clearSuggestions = () => {
    setSuggestions([]);
  };

  // Fetch functions helper
  const fetchChats = async (token: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/chats`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setChats(data);
        if (data.length > 0 && !activeChatId) {
          setActiveChatId(data[0].id);
        }
      }
    } catch (e) {
      console.error("Fetch chats failed:", e);
    }
  };

  const fetchProjects = async (token: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/projects`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setProjects(data);
      }
    } catch (e) {
      console.error("Fetch projects failed:", e);
    }
  };

  // Check auth on mount
  useEffect(() => {
    const checkUser = async () => {
      const token = localStorage.getItem("token");
      if (token) {
        try {
          const res = await fetch(`${API_BASE}/api/auth/me`, {
            headers: { "Authorization": `Bearer ${token}` }
          });
          if (res.ok) {
            const data = await res.json();
            setUser(data);
            fetchChats(token);
            fetchProjects(token);
          } else {
            localStorage.removeItem("token");
          }
        } catch (e) {
          console.error("Auth verify failed:", e);
          localStorage.removeItem("token");
        }
      }
    };
    checkUser();
  }, []);

  const login = async (email: string, password: string) => {
    const res = await fetch(`${API_BASE}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });
    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(errorData.detail || "Invalid credentials");
    }
    const data = await res.json();
    localStorage.setItem("token", data.access_token);
    setUser(data.user);
    setShowAuthModal(false);
    fetchChats(data.access_token);
    fetchProjects(data.access_token);
  };

  const signup = async (name: string, email: string, password: string) => {
    const res = await fetch(`${API_BASE}/api/auth/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password })
    });
    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(errorData.detail || "Registration failed");
    }
    const data = await res.json();
    localStorage.setItem("token", data.access_token);
    setUser(data.user);
    setShowAuthModal(false);
    fetchChats(data.access_token);
    fetchProjects(data.access_token);
  };

  const logout = () => {
    localStorage.removeItem("token");
    setUser(null);
    setChats([]);
    setProjects([]);
    setActiveChatId(null);
    setActiveProjectId(null);
  };

  const updateChatSelectedProject = async (chatId: string, selectedProject: ProjectSuggestion) => {
    setChats((prev) =>
      prev.map((c) => (c.id === chatId ? { ...c, selected_project: selectedProject } : c))
    );
    const token = localStorage.getItem("token");
    if (!token) return;
    try {
      await fetch(`${API_BASE}/api/chats/${chatId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ selected_project: selectedProject })
      });
    } catch (e) {
      console.error("Update chat selected project failed:", e);
    }
  };

  const createNewChat = async (category: string, title: string, selectedProject?: ProjectSuggestion): Promise<string> => {
    const token = localStorage.getItem("token");
    if (!token) return "";
    try {
      const res = await fetch(`${API_BASE}/api/chats`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ 
          category, 
          title, 
          selected_project: selectedProject || null 
        })
      });
      if (res.ok) {
        const newChat = await res.json();
        setChats((prev) => [newChat, ...prev]);
        setActiveChatId(newChat.id);
        setActiveProjectId(null);
        setShowRightPane(true);
        return newChat.id;
      }
    } catch (e) {
      console.error("Create chat failed:", e);
    }
    return "";
  };

  const addMessageToChat = async (chatId: string, sender: "user" | "ai", text: string) => {
    if (sender !== "user") return;
    
    const tempUserMsgId = `m-temp-${Date.now()}`;
    const time = new Date().toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
    const userMsg: Message = { id: tempUserMsgId, sender: "user", text, timestamp: time };
    
    setChats((prev) =>
      prev.map((c) => {
        if (c.id === chatId) {
          return { ...c, messages: [...c.messages, userMsg] };
        }
        return c;
      })
    );
    
    const token = localStorage.getItem("token");
    if (!token) return;
    
    try {
      const res = await fetch(`${API_BASE}/api/chats/${chatId}/messages`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ text })
      });
      if (!res.ok) {
        if (res.status === 401) {
          console.error("Unauthorized: Token might be expired.");
          localStorage.removeItem("token");
          // Optionally trigger a reload or show auth modal to re-login
          window.location.reload();
          return;
        }
        throw new Error(`API returned status: ${res.status}`);
      }
      
      if (res.ok) {
        const data = await res.json();
        setChats((prev) =>
          prev.map((c) => {
            if (c.id === chatId) {
              const filtered = c.messages.filter(m => m.id !== tempUserMsgId);
              return {
                ...c,
                messages: [...filtered, data.user_message, data.ai_message]
              };
            }
            return c;
          })
        );

        // Auto-parse <blueprint> from AI response and update selected_project
        const aiText = data.ai_message?.text || "";
        const bpMatch = aiText.match(/<blueprint>([\s\S]*?)<\/blueprint>/);
        if (bpMatch && bpMatch[1]) {
          try {
            const parsed = JSON.parse(bpMatch[1].trim());
            if (parsed.name || parsed.idea || parsed.features) {
              const bp: ProjectSuggestion = {
                name: parsed.name || "",
                idea: parsed.idea || "",
                features: parsed.features || [],
                tech_stack: parsed.tech_stack || "Flask, HTML, CSS"
              };
              updateChatSelectedProject(chatId, bp);
            }
          } catch (_bpErr) {
            // Blueprint parse failed, ignore silently
          }
        }
      }
    } catch (e) {
      console.error("Send message failed:", e);
    }
  };

  const editMessageText = async (chatId: string, messageId: string, newText: string) => {
    // Update local state immediately
    setChats((prev) =>
      prev.map((c) => {
        if (c.id === chatId) {
          return {
            ...c,
            messages: c.messages.map((m) =>
              m.id === messageId ? { ...m, text: newText } : m
            )
          };
        }
        return c;
      })
    );

    const token = localStorage.getItem("token");
    if (!token) return;

    try {
      await fetch(`${API_BASE}/api/chats/${chatId}/messages/${messageId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ text: newText })
      });
    } catch (e) {
      console.error("Edit message failed:", e);
    }
  };

  const deleteChat = async (chatId: string) => {
    const token = localStorage.getItem("token");
    if (!token) return;
    
    // Optimistic UI Update for instant deletion
    setChats((prev) => prev.filter((c) => c.id !== chatId));
    if (activeChatId === chatId) {
      setActiveChatId(null);
    }
    
    try {
      await fetch(`${API_BASE}/api/chats/${chatId}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
      });
    } catch (e) {
      console.error("Delete chat failed:", e);
    }
  };

  const renameChat = async (chatId: string, newTitle: string) => {
    const token = localStorage.getItem("token");
    if (!token) return;
    
    setChats((prev) => prev.map((c) => c.id === chatId ? { ...c, title: newTitle } : c));
    try {
      await fetch(`${API_BASE}/api/chats/${chatId}`, {
        method: "PUT",
        headers: { 
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ title: newTitle })
      });
    } catch (e) {
      console.error("Rename chat failed:", e);
    }
  };

  const deleteProject = async (projectId: string) => {
    const token = localStorage.getItem("token");
    if (!token) return;
    
    // Optimistic UI Update
    setProjects((prev) => prev.filter((p) => p.id !== projectId));
    if (activeProjectId === projectId) {
      setActiveProjectId(null);
    }
    
    try {
      await fetch(`${API_BASE}/api/projects/${projectId}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
      });
    } catch (e) {
      console.error("Delete project failed:", e);
    }
  };

  const renameProject = async (projectId: string, newTitle: string) => {
    const token = localStorage.getItem("token");
    if (!token) return;
    
    setProjects((prev) => prev.map((p) => p.id === projectId ? { ...p, name: newTitle } : p));
    try {
      await fetch(`${API_BASE}/api/projects/${projectId}`, {
        method: "PUT",
        headers: { 
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ title: newTitle })
      });
    } catch (e) {
      console.error("Rename project failed:", e);
    }
  };

  const updateProject = (projectId: string, updates: Partial<Project>) => {
    setProjects((prev) =>
      prev.map((p) => (p.id === projectId ? { ...p, ...updates } : p))
    );
  };

  const pollProjectStatus = (projectId: string, chatId: string) => {
    const interval = setInterval(async () => {
      const token = localStorage.getItem("token");
      if (!token) {
        clearInterval(interval);
        setIsGeneratingProject(false);
        return;
      }
      try {
        const res = await fetch(`${API_BASE}/api/projects/${projectId}`, {
          headers: { "Authorization": `Bearer ${token}` }
        });
        if (res.ok) {
          const updatedProj = await res.json();
          setProjects((prev) =>
            prev.map((p) => (p.id === projectId ? updatedProj : p))
          );

          if (updatedProj.status === "completed") {
            clearInterval(interval);
            setIsGeneratingProject(false);
            fetchChats(token);
            confetti({
              particleCount: 120,
              spread: 80,
              origin: { y: 0.6 },
              colors: ["#6366f1", "#f43f5e", "#10b981", "#fbbf24"],
            });
          } else if (updatedProj.status === "failed") {
            clearInterval(interval);
            setIsGeneratingProject(false);
          }
        }
      } catch (e) {
        console.error("Polling project failed:", e);
        clearInterval(interval);
        setIsGeneratingProject(false);
      }
    }, 1500);
  };

  const generateProject = async (
    chatId: string,
    projectName: string,
    category: string,
    theme?: string,
    blueprint?: any,
    themePalette?: any
  ) => {
    if (isGeneratingProject) return;
    setIsGeneratingProject(true);
    setActiveProjectId(null);
    setShowRightPane(true);

    const token = localStorage.getItem("token");
    if (!token) {
      setIsGeneratingProject(false);
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/api/projects`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          chat_id: chatId,
          name: projectName,
          category,
          theme,
          blueprint,
          theme_palette: themePalette
        })
      });
      if (res.ok) {
        const newProj = await res.json();
        setProjects((prev) => [newProj, ...prev]);
        setActiveProjectId(newProj.id);
        if (newProj.status === "documents_ready") {
          setIsGeneratingProject(false);
        } else {
          pollProjectStatus(newProj.id, chatId);
        }
      }
    } catch (e) {
      console.error("Generate project failed:", e);
      setIsGeneratingProject(false);
    }
  };

  const compileProjectCodebase = async (projectId: string, chatId: string) => {
    if (isGeneratingProject) return;
    setIsGeneratingProject(true);

    const token = localStorage.getItem("token");
    if (!token) {
      setIsGeneratingProject(false);
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/api/projects/${projectId}/compile`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`
        }
      });
      if (res.ok) {
        const updatedProj = await res.json();
        setProjects((prev) =>
          prev.map((p) => (p.id === projectId ? updatedProj : p))
        );
        pollProjectStatus(projectId, chatId);
      } else {
        setIsGeneratingProject(false);
      }
    } catch (e) {
      console.error("Compile project codebase failed:", e);
      setIsGeneratingProject(false);
    }
  };

  const generateDocuments = async (projectName: string, prompt: string) => {
    if (isGeneratingProject) return;
    setIsGeneratingProject(true);
    setActiveProjectId(null);
    setShowRightPane(true);

    const token = localStorage.getItem("token");
    if (!token) {
      setIsGeneratingProject(false);
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/api/projects/generate-documents`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          name: projectName,
          prompt
        })
      });
      if (res.ok) {
        const newProj = await res.json();
        setProjects((prev) => [newProj, ...prev]);
        setActiveProjectId(newProj.id);
        confetti({
          particleCount: 150,
          spread: 80,
          origin: { y: 0.6 }
        });
      }
    } catch (e) {
      console.error("Generate documents failed:", e);
    } finally {
      setIsGeneratingProject(false);
    }
  };


  return (
    <WorkspaceContext.Provider
      value={{
        user,
        login,
        signup,
        logout,
        chats,
        activeChatId,
        setActiveChatId,
        createNewChat,
        addMessageToChat,
        editMessageText,
        deleteChat,
        renameChat,
        updateChatSelectedProject,
        projects,
        activeProjectId,
        setActiveProjectId,
        generateProject,
        compileProjectCodebase,
        generateDocuments,
        deleteProject,
        renameProject,
        updateProject,
        currentCategory,
        setCurrentCategory,
        currentInput,
        setCurrentInput,
        showAuthModal,
        setShowAuthModal,
        authMode,
        setAuthMode,
        showAbout,
        setShowAbout,
        showContact,
        setShowContact,
        isGeneratingProject,
        showRightPane,
        setShowRightPane,
        showLeftPane,
        setShowLeftPane,
        suggestions,
        isFetchingSuggestions,
        fetchSuggestions,
        clearSuggestions,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
};

export const useWorkspace = () => {
  const context = useContext(WorkspaceContext);
  if (context === undefined) {
    throw new Error("useWorkspace must be used within a WorkspaceProvider");
  }
  return context;
};

// Mock Code Generators based on Category
function generateMockCodeForCategory(name: string, category: string): CodeFile[] {
  const capitalName = name.charAt(0).toUpperCase() + name.slice(1);
  const normalizedCategory = category.toLowerCase();

  const readme = {
    name: "README.md",
    path: "README.md",
    language: "markdown",
    content: `# ${capitalName} (${category.toUpperCase()} category)\n\nWelcome to your customized Sarthi hackathon prototype!\n\n## Highlights\n- Custom dashboard elements with seamless state synchronization.\n- Built with high-fidelity React components using Tailwind CSS.\n- Modern modular code files, fully ready to build.\n\n## Getting Started\n1. Run \`npm install\`\n2. Run \`npm run dev\`\n3. Deploy immediately for your hackathon pitch!`,
  };

  if (normalizedCategory === "startup") {
    return [
      readme,
      {
        name: "SaaSMetrics.tsx",
        path: "src/SaaSMetrics.tsx",
        language: "typescript",
        content: `import React, { useState } from 'react';

export default function SaaSMetrics() {
  const [mrr, setMrr] = useState(12500);
  const [churn, setChurn] = useState(2.4);

  return (
    <div className="p-6 bg-white rounded-3xl border border-stone-200/60 max-w-md mx-auto shadow-sm">
      <h3 className="text-xl font-bold font-display text-indigo-900 mb-1">${capitalName} Launchpad</h3>
      <p className="text-xs text-stone-400 mb-6">Real-time SaaS product statistics simulation</p>
      
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="p-4 bg-indigo-50/50 rounded-2xl border border-indigo-100/30">
          <span className="text-[10px] text-indigo-600 font-bold uppercase tracking-wider block">Estimated MRR</span>
          <span className="text-xl font-extrabold text-indigo-900 mt-1 block">\${mrr.toLocaleString()}</span>
        </div>
        <div className="p-4 bg-rose-50/50 rounded-2xl border border-rose-100/30">
          <span className="text-[10px] text-rose-600 font-bold uppercase tracking-wider block">User Churn</span>
          <span className="text-xl font-extrabold text-rose-900 mt-1 block">{churn}%</span>
        </div>
      </div>
      
      <div className="mb-6">
        <label className="text-xs text-stone-500 font-semibold block mb-2">Simulate MRR Growth</label>
        <input 
          type="range" 
          min="5000" 
          max="50000" 
          step="1000"
          value={mrr}
          onChange={(e) => setMrr(parseInt(e.target.value))}
          className="w-full h-2 bg-stone-100 rounded-lg appearance-none cursor-pointer accent-indigo-600"
        />
        <div className="flex justify-between text-[10px] text-stone-400 mt-2">
          <span>\$5,000</span>
          <span>\$50,000</span>
        </div>
      </div>
      
      <div className="p-4 bg-emerald-50/50 rounded-2xl border border-emerald-100/30 text-center text-xs text-emerald-800">
        💡 High MRR & Low Churn indicates strong PMF. Generate the full codebase to deploy!
      </div>
    </div>
  );
}`,
      },
    ];
  } else if (normalizedCategory === "finance") {
    return [
      readme,
      {
        name: "Dashboard.tsx",
        path: "src/Dashboard.tsx",
        language: "typescript",
        content: `import React, { useState } from 'react';
import SavingsCalculator from './SavingsCalculator';

export default function Dashboard() {
  const [balance, setBalance] = useState(2450.75);
  
  return (
    <div className="p-6 bg-stone-50 rounded-3xl border border-stone-200/60 max-w-xl mx-auto shadow-sm">
      <h2 className="text-2xl font-bold font-display text-indigo-900 mb-2">${capitalName} Planner</h2>
      <p className="text-stone-500 mb-6">Financial tracking & budget optimization</p>
      
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="p-4 bg-white rounded-2xl border border-stone-100">
          <span className="text-xs text-stone-400 font-medium uppercase tracking-wide">Total Balance</span>
          <p className="text-xl font-bold text-stone-800 mt-1">\${balance.toFixed(2)}</p>
        </div>
        <div className="p-4 bg-indigo-50/50 rounded-2xl border border-indigo-100/50">
          <span className="text-xs text-indigo-500 font-medium uppercase tracking-wide">AI Health Score</span>
          <p className="text-xl font-bold text-indigo-700 mt-1">Excellent (94%)</p>
        </div>
      </div>
      
      <SavingsCalculator onSavings={(amount) => setBalance(prev => prev + amount)} />
    </div>
  );
}`,
      },
      {
        name: "SavingsCalculator.tsx",
        path: "src/SavingsCalculator.tsx",
        language: "typescript",
        content: `import React, { useState } from 'react';

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
}`,
      },
    ];
  } else if (normalizedCategory === "productivity") {
    return [
      readme,
      {
        name: "TaskList.tsx",
        path: "src/TaskList.tsx",
        language: "typescript",
        content: `import React, { useState } from 'react';

interface Task {
  id: number;
  text: string;
  done: boolean;
}

export default function TaskList() {
  const [tasks, setTasks] = useState<Task[]>([
    { id: 1, text: "Define product roadmap", done: true },
    { id: 2, text: "Draft slide-deck for hackathon", done: false },
    { id: 3, text: "Review user flow layouts", done: false },
  ]);
  const [input, setInput] = useState('');

  const addTask = () => {
    if (input.trim()) {
      setTasks([...tasks, { id: Date.now(), text: input, done: false }]);
      setInput('');
    }
  };

  return (
    <div className="p-6 bg-white rounded-3xl border border-stone-200/60 max-w-md mx-auto shadow-sm">
      <h3 className="text-xl font-bold font-display text-stone-800 mb-1">${capitalName} Tasks</h3>
      <p className="text-xs text-stone-400 mb-4">Focused execution & priority stack</p>
      
      <div className="space-y-2 mb-4">
        {tasks.map(t => (
          <div key={t.id} className="flex items-center gap-3 p-3 bg-stone-50 rounded-xl">
            <input 
              type="checkbox" 
              checked={t.done}
              onChange={() => setTasks(tasks.map(x => x.id === t.id ? {...x, done: !x.done} : x))}
              className="w-4 h-4 rounded accent-indigo-600"
            />
            <span className={t.done ? "line-through text-stone-400 text-sm" : "text-stone-700 text-sm"}>
              {t.text}
            </span>
          </div>
        ))}
      </div>
      
      <div className="flex gap-2">
        <input 
          type="text" 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="New milestone..."
          className="flex-1 bg-stone-50 border border-stone-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
        <button 
          onClick={addTask}
          className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-4 py-2 rounded-xl transition-colors"
        >
          Add Task
        </button>
      </div>
    </div>
  );
}`,
      },
    ];
  } else if (normalizedCategory === "education") {
    return [
      readme,
      {
        name: "Quiz.tsx",
        path: "src/Quiz.tsx",
        language: "typescript",
        content: `import React, { useState } from 'react';

export default function Quiz() {
  const [score, setScore] = useState(0);
  const [answered, setAnswered] = useState<number[]>([]);
  
  const questions = [
    { id: 1, q: "What is the primary benefit of spaced repetition?", options: ["Long-term retention", "Short-term cramming", "Better typing speed"], ans: 0 },
    { id: 2, q: "Which framework is optimized for React compilation in 2026?", options: ["NextJS with Turbopack", "Vanilla jQuery", "Svelte"], ans: 0 },
  ];

  const handleSelect = (qIndex: number, optionIndex: number) => {
    if (answered.includes(qIndex)) return;
    setAnswered([...answered, qIndex]);
    if (questions[qIndex].ans === optionIndex) {
      setScore(prev => prev + 1);
    }
  };

  return (
    <div className="p-6 bg-slate-50 rounded-3xl border border-stone-200/60 max-w-md mx-auto">
      <h3 className="text-xl font-bold font-display text-indigo-900 mb-1">${capitalName} Flashcards</h3>
      <p className="text-xs text-stone-400 mb-6">Test your retention levels dynamically</p>
      
      <div className="space-y-6">
        {questions.map((q, idx) => (
          <div key={q.id} className="bg-white p-4 rounded-2xl border border-stone-100">
            <p className="text-sm font-semibold text-stone-800 mb-3">{q.q}</p>
            <div className="space-y-2">
              {q.options.map((opt, oIdx) => (
                <button
                  key={oIdx}
                  onClick={() => handleSelect(idx, oIdx)}
                  disabled={answered.includes(idx)}
                  className="w-full text-left p-3 rounded-xl border border-stone-100 text-xs hover:bg-stone-50 transition-colors disabled:opacity-75 disabled:hover:bg-white"
                >
                  {opt}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
      
      {answered.length === questions.length && (
        <div className="mt-6 p-4 bg-emerald-50 text-emerald-800 rounded-2xl border border-emerald-100 text-center font-semibold">
          Quiz Completed! Score: {score}/{questions.length}
        </div>
      )}
    </div>
  );
}`,
      },
    ];
  } else if (normalizedCategory === "sustainability") {
    return [
      readme,
      {
        name: "CarbonCalculator.tsx",
        path: "src/CarbonCalculator.tsx",
        language: "typescript",
        content: `import React, { useState } from 'react';

export default function CarbonCalculator() {
  const [miles, setMiles] = useState(15);
  
  const CO2_PER_MILE = 0.404; // kg
  const carbonCommute = miles * CO2_PER_MILE;

  return (
    <div className="p-6 bg-white rounded-3xl border border-stone-200/60 max-w-sm mx-auto shadow-sm">
      <h3 className="text-xl font-bold font-display text-emerald-800 mb-1">${capitalName} Footprint</h3>
      <p className="text-xs text-stone-400 mb-6">Commute emission calculator</p>
      
      <div className="mb-6">
        <label className="text-xs text-stone-500 font-semibold block mb-2">Daily Commute Distance (miles)</label>
        <input 
          type="range" 
          min="0" 
          max="100" 
          value={miles}
          onChange={(e) => setMiles(parseInt(e.target.value))}
          className="w-full h-2 bg-stone-100 rounded-lg appearance-none cursor-pointer accent-emerald-600"
        />
        <div className="flex justify-between text-xs text-stone-400 mt-2">
          <span>0 miles</span>
          <span>{miles} miles</span>
          <span>100 miles</span>
        </div>
      </div>
      
      <div className="p-4 bg-emerald-50/50 rounded-2xl border border-emerald-100/30 text-center">
        <span className="text-xs text-emerald-600 font-bold uppercase tracking-wider block">Estimated Commute CO2</span>
        <span className="text-3xl font-extrabold text-emerald-800 mt-1 block">{carbonCommute.toFixed(1)} <span className="text-sm font-normal">kg</span></span>
        <span className="text-[10px] text-emerald-500 block mt-2">💡 Tip: Working from home today saves {carbonCommute.toFixed(1)}kg!</span>
      </div>
    </div>
  );
}`,
      },
    ];
  } else {
    // other/custom
    return [
      readme,
      {
        name: "InteractiveBox.tsx",
        path: "src/InteractiveBox.tsx",
        language: "typescript",
        content: `import React, { useState } from 'react';

export default function InteractiveBox() {
  const [clicks, setClicks] = useState(0);

  return (
    <div className="p-6 bg-white rounded-3xl border border-stone-200/60 max-w-xs mx-auto text-center">
      <h3 className="text-lg font-bold font-display text-indigo-900 mb-2">${capitalName} Hub</h3>
      <p className="text-xs text-stone-400 mb-6">Custom compiled hackathon module</p>
      
      <button 
        onClick={() => setClicks(c => c + 1)}
        className="w-full bg-indigo-600 hover:bg-indigo-700 text-white rounded-2xl py-3 text-sm font-semibold transition-all hover:shadow-lg active:scale-95 animate-pulse-ring"
      >
        Trigger Action ({clicks})
      </button>
      
      <div className="mt-4 text-[10px] text-stone-400 uppercase tracking-wide">
        Sarthi custom environment
      </div>
    </div>
  );
}`,
      },
    ];
  }
}
