import { ChatSession, Project } from "../context/WorkspaceContext";

export const MOCK_USER = {
  id: "demo-user",
  name: "Arjuna Developer",
  email: "arjuna@sarthi.ai",
  bio: "Architecting software ecosystems via AI and MongoDB.",
  title: "Full Stack Engineer & Architect",
  skills: ["React", "Next.js", "Node.js", "MongoDB", "Tailwind CSS", "Framer Motion", "MCP"],
  github_url: "https://github.com/arjuna-dev",
  linkedin_url: "https://linkedin.com/in/arjuna-dev",
  portfolio_url: "https://arjuna.dev"
};

export const MOCK_CHATS: ChatSession[] = [
  {
    id: "chat-1",
    title: "CalmPath Breathing App",
    category: "health",
    created: "June 10, 2026",
    selected_project: {
      name: "CalmPath Breathing Guide",
      idea: "Interactive breathing spacer designed to reduce chronic stress using paced HRV cycles.",
      features: ["Paced Breathing Ring", "Weekly Mood Trends", "Audio Soundscapes"],
      tech_stack: "React, Tailwind CSS, Framer Motion, LocalStorage"
    },
    is_confirmed: false,
    project_id: null,
    messages: [
      {
        id: "c1-m1",
        sender: "user",
        text: "Hi, I want to create an app that guides users through paced breathing exercises and lets them log their stress levels.",
        timestamp: "10:30 AM"
      },
      {
        id: "c1-m2",
        sender: "ai",
        text: "Namaste! That sounds like a wonderful initiative. I can compile a complete design blueprint for your CalmPath Breathing Guide. What tech stack would you like to use?",
        timestamp: "10:31 AM"
      },
      {
        id: "c1-m3",
        sender: "user",
        text: "Let's use React, Tailwind CSS, and Framer Motion.",
        timestamp: "10:32 AM"
      },
      {
        id: "c1-m4",
        sender: "ai",
        text: "Perfect. I have drafted the project specifications and key feature lists. You can review and customize the blueprint in the right panel, and then proceed to choose a color theme.",
        timestamp: "10:32 AM"
      }
    ]
  },
  {
    id: "chat-2",
    title: "Vedic Yoga Planner",
    category: "fitness",
    created: "June 10, 2026",
    selected_project: {
      name: "Vedic Yoga Planner",
      idea: "Yoga scheduling and posture guides utilizing local calendar sync.",
      features: ["Daily Asana Routines", "Posture Timer", "Calendar Schedule Exporter"],
      tech_stack: "Next.js, Tailwind CSS, TypeScript"
    },
    is_confirmed: true,
    project_id: "proj-1",
    messages: [
      {
        id: "c2-m1",
        sender: "user",
        text: "I need an application to schedule my daily asanas and postures.",
        timestamp: "11:00 AM"
      },
      {
        id: "c2-m2",
        sender: "ai",
        text: "Greetings! I've created the specifications (PRD, MRD, TRD) for your Vedic Yoga Planner. You can review them in the right pane. Let me know if you would like me to begin codebase compilation.",
        timestamp: "11:01 AM"
      }
    ]
  },
  {
    id: "chat-3",
    title: "Divine Soundboard",
    category: "audio",
    created: "June 11, 2026",
    selected_project: {
      name: "Divine Soundboard",
      idea: "Ambient audio cue generation for concentration and deep work.",
      features: ["Binaural Beats Mixer", "Vedic Chants Player", "Focus Timer"],
      tech_stack: "React, Web Audio API, Tailwind CSS"
    },
    is_confirmed: true,
    project_id: "proj-2",
    messages: [
      {
        id: "c3-m1",
        sender: "user",
        text: "Build an ambient soundscape player for developers to focus.",
        timestamp: "02:00 PM"
      },
      {
        id: "c3-m2",
        sender: "ai",
        text: "Initializing multi-agent workspace compiler. Sarthi is architecting the collection schemas and API endpoints now.",
        timestamp: "02:02 PM"
      }
    ]
  },
  {
    id: "chat-4",
    title: "Ayurvedic Recipe Builder",
    category: "food",
    created: "June 11, 2026",
    selected_project: {
      name: "Ayurvedic Recipe Builder",
      idea: "Smart recipe builder with ingredient properties mappings.",
      features: ["Dosha Balancing Foods Finder", "Ingredient Catalog Database", "Meal Scheduler"],
      tech_stack: "React, Node.js, MongoDB"
    },
    is_confirmed: true,
    project_id: "proj-3",
    messages: [
      {
        id: "c4-m1",
        sender: "user",
        text: "Let's compile the Ayurvedic Recipe Builder codebase.",
        timestamp: "03:10 PM"
      },
      {
        id: "c4-m2",
        sender: "ai",
        text: "Beginning compilation of models and integration server. (Wait: Build encountered a missing dependency error).",
        timestamp: "03:12 PM"
      }
    ]
  },
  {
    id: "chat-5",
    title: "Stress Resilience Hub",
    category: "productivity",
    created: "June 12, 2026",
    selected_project: {
      name: "Stress Resilience Hub",
      idea: "Developers' stress manager dashboard integrated with Git commits analysis and soundscapes.",
      features: ["GitHub Commit Sync", "Visual Stress Level Indicator", "Break Alerts & Cues"],
      tech_stack: "Next.js, MongoDB, Tailwind CSS, Framer Motion"
    },
    is_confirmed: true,
    project_id: "proj-4",
    messages: [
      {
        id: "c5-m1",
        sender: "user",
        text: "Can you create a workspace that helps developers track their work fatigue using git metrics?",
        timestamp: "12:00 AM"
      },
      {
        id: "c5-m2",
        sender: "ai",
        text: "That is a brilliant productivity system. I'll architect a dashboard featuring Git hooks monitoring, stress visualizations, and integrated soundscapes. Let's begin compiling.",
        timestamp: "12:01 AM"
      },
      {
        id: "c5-m3",
        sender: "user",
        text: "Excellent! The build has completed. Confetti is everywhere!",
        timestamp: "12:05 AM"
      }
    ]
  }
];

export const MOCK_PROJECTS: Project[] = [
  {
    id: "proj-1",
    name: "Vedic Yoga Planner",
    category: "fitness",
    status: "documents_ready",
    progress: 100,
    step: "Documents Compiled Successfully",
    summary: "Yoga scheduling and posture guides utilizing local calendar sync.",
    chat_id: "chat-2",
    created: "June 10, 2026",
    codebase: [],
    prd: `# Product Requirement Document (PRD) - Vedic Yoga Planner

## 1. Overview
The Vedic Yoga Planner helps users integrate yoga practice into their busy schedules by mapping customized asanas and logging workout durations.

## 2. Scope & Core Requirements
- **Daily Postures**: A catalog of 20+ basic and intermediate yoga postures with duration timers.
- **Calendar Integration**: Export session events directly to local calendars using ICS format.
- **Progress Badges**: Unlock milestones based on total yoga minutes logged.

## 3. User Flows
1. **Explore postures**: Tap on a posture tile to see benefits, guidelines, and animations.
2. **Schedule sessions**: Set time triggers to launch timers automatically.`,
    mrd: `# Market Requirement Document (MRD) - Vedic Yoga Planner

## 1. Market Opportunity
With increasing remote work fatigue, millions are turning to home workouts. Yoga is highly requested, but users suffer from lack of structured timers.

## 2. Competitive Edge
- **No Ads / Subscription**: Free and local-first data storage.
- **Holistic Vedic Focus**: Combines physical posture timers with breathing pacing alerts.`,
    trd: `# Technical Requirement Document (TRD) - Vedic Yoga Planner

## 1. Architecture
- **Framework**: Next.js App Router.
- **Database**: MongoDB server collection for storing user achievements and customized routine settings.
- **Components**: Framer Motion SVG timers.`
  },
  {
    id: "proj-2",
    name: "Divine Soundboard",
    category: "audio",
    status: "generating",
    progress: 45,
    step: "DatabaseModelGenerationAgent",
    summary: "Ambient audio cue generation for concentration and deep work.",
    chat_id: "chat-3",
    created: "June 11, 2026",
    codebase: [],
    prd: `# PRD - Divine Soundboard
Ambient sound mixer for focus.`,
    mrd: `# MRD - Divine Soundboard
Targeting developers who listen to music while coding.`,
    trd: `# TRD - Divine Soundboard
Web Audio API synthesis.`
  },
  {
    id: "proj-3",
    name: "Ayurvedic Recipe Builder",
    category: "food",
    status: "failed",
    progress: 75,
    step: "BuildCompilationAgent",
    summary: "Smart recipe builder with ingredient properties mappings.",
    chat_id: "chat-4",
    created: "June 11, 2026",
    codebase: [],
    prd: `# PRD - Ayurvedic Recipe Builder`,
    mrd: `# MRD - Ayurvedic Recipe Builder`,
    trd: `# TRD - Ayurvedic Recipe Builder`
  },
  {
    id: "proj-4",
    name: "Stress Resilience Hub",
    category: "productivity",
    status: "completed",
    progress: 100,
    step: "Project Compiled and Packaged",
    summary: "Developers' stress manager dashboard integrated with Git commits analysis and soundscapes.",
    chat_id: "chat-5",
    created: "June 12, 2026",
    prd: `# Product Requirement Document (PRD) - Stress Resilience Hub

## 1. Goals
Create a comprehensive cockpit for developers to self-regulate fatigue.

## 2. Core Features
- Git logs analyzer to count commits and alert users if they code for 3+ hours straight.
- Audio playbox with binaural waves.
- Interactive mood tracker logs.`,
    mrd: `# Market Requirement Document (MRD) - Stress Resilience Hub
Solving developer burnout using scientific metrics and proactive intervention.`,
    trd: `# Technical Requirement Document (TRD) - Stress Resilience Hub

## 1. Stack
- Next.js Client
- MongoDB Atlas (Capped logs collection for git events)
- Web Audio API`,
    hackathon_metadata: {
      partner_track: "MongoDB",
      sub_agent_pipeline: [
        "RequirementAnalyzerAgent",
        "DatabaseArchitectureAgent",
        "DatabaseModelGenerationAgent",
        "APIImplementationAgent",
        "IntegrationGenerationAgent",
        "BuildCompilationAgent",
        "ProjectExportAgent"
      ],
      submission_time: "June 12, 2026 12:05 AM",
      team_name: "Team Arjuna"
    },
    mcp_evidence: {
      mcp_status: "connected",
      mcp_server_queries: 24,
      schema_validation: "passed"
    },
    codebase: [
      {
        name: "README.md",
        path: "README.md",
        language: "markdown",
        content: `# Stress Resilience Hub 🕉️

Welcome to the **Stress Resilience Hub** — an automated productivity cockpit designed specifically for developers to log daily stress levels, sync with local Git repositories, and trigger ambient breathing exercises.

## Features
- **Git Commit Fatigue Analyzer**: Connect local workspaces to monitor commit frequency and prevent burnout.
- **HRV Audio Cue Player**: Procedure-based binaural waveforms using the Web Audio API.
- **MongoDB Atlas Integration**: Capped collections storing daily stress history.

## Development Setup
\`\`\`bash
# Install dependencies
npm install

# Start local server
npm run dev
\`\`\`
`
      },
      {
        name: "package.json",
        path: "package.json",
        language: "json",
        content: `{
  "name": "stress-resilience-hub",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "next": "^14.2.3",
    "framer-motion": "^11.2.10",
    "lucide-react": "^0.381.0"
  }
}`
      },
      {
        name: "App.tsx",
        path: "src/App.tsx",
        language: "typescript",
        content: `import React, { useState } from "react";
import { Heart, Activity, ShieldAlert, Disc } from "lucide-react";
import { StressTracker } from "./components/StressTracker";
import { SoundscapePlayer } from "./components/SoundscapePlayer";

export default function App() {
  const [activeTab, setActiveTab] = useState<"tracker" | "sound">("tracker");

  return (
    <div className="min-h-screen bg-stone-950 text-stone-100 flex flex-col font-sans">
      <header className="p-6 border-b border-stone-850 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Heart className="w-5 h-5 text-amber-500 fill-amber-500 animate-pulse" />
          <h1 className="text-md font-bold tracking-tight">Stress Resilience Hub</h1>
        </div>
        <div className="flex bg-stone-900 rounded-lg p-1 text-xs">
          <button 
            onClick={() => setActiveTab("tracker")}
            className={\`px-3 py-1.5 rounded \${activeTab === "tracker" ? "bg-amber-500 text-stone-950 font-bold" : "text-stone-400"}\`}
          >
            Fatigue Dashboard
          </button>
          <button 
            onClick={() => setActiveTab("sound")}
            className={\`px-3 py-1.5 rounded \${activeTab === "sound" ? "bg-amber-500 text-stone-950 font-bold" : "text-stone-400"}\`}
          >
            Soundscapes
          </button>
        </div>
      </header>
      
      <main className="flex-1 p-6 md:p-10 max-w-5xl mx-auto w-full">
        {activeTab === "tracker" ? <StressTracker /> : <SoundscapePlayer />}
      </main>
    </div>
  );
}`
      },
      {
        name: "StressTracker.tsx",
        path: "src/components/StressTracker.tsx",
        language: "typescript",
        content: `import React, { useState } from "react";
import { Activity, ShieldAlert, Sparkles } from "lucide-react";

export function StressTracker() {
  const [stressLevel, setStressLevel] = useState(45);

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div className="md:col-span-2 bg-stone-900 border border-stone-850 p-6 rounded-2xl space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="text-sm font-bold text-stone-200">Fatigue & Workload Analytics</h2>
          <span className="text-[10px] text-emerald-400 px-2 py-0.5 rounded bg-emerald-500/10 font-bold">Safe State</span>
        </div>
        
        <div className="h-44 flex items-end justify-between gap-2 border-b border-stone-800 pb-2">
          {[20, 35, 65, 80, 40, 50, 45].map((val, idx) => (
            <div key={idx} className="flex-1 flex flex-col items-center gap-2">
              <div 
                className="w-full rounded-t-lg transition-all duration-500" 
                style={{ 
                  height: \`\${val * 1.5}px\`,
                  backgroundColor: val > 60 ? "#ef4444" : "#eab308"
                }}
              />
              <span className="text-[8px] text-stone-500">Day \${idx + 1}</span>
            </div>
          ))}
        </div>
      </div>
      
      <div className="bg-stone-900 border border-stone-850 p-6 rounded-2xl flex flex-col justify-between">
        <div className="space-y-3">
          <h3 className="text-xs font-bold text-stone-400 uppercase tracking-wider">Active Alert</h3>
          <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 flex gap-3 text-amber-500">
            <ShieldAlert className="w-5 h-5 shrink-0" />
            <div className="text-[10px] leading-relaxed">
              <span className="font-bold block text-stone-200">Take a 5-minute break</span>
              You have been writing code continuously for 178 minutes.
            </div>
          </div>
        </div>
        
        <button 
          onClick={() => setStressLevel(20)}
          className="w-full py-2.5 bg-amber-500 hover:bg-amber-450 text-stone-950 font-bold rounded-xl text-xs transition-colors flex items-center justify-center gap-1"
        >
          <Sparkles className="w-4 h-4" /> Start Paced Breathing
        </button>
      </div>
    </div>
  );
}`
      },
      {
        name: "SoundscapePlayer.tsx",
        path: "src/components/SoundscapePlayer.tsx",
        language: "typescript",
        content: `import React, { useState } from "react";
import { Play, Pause, Volume2 } from "lucide-react";

export function SoundscapePlayer() {
  const [isPlaying, setIsPlaying] = useState(false);

  return (
    <div className="bg-stone-900 border border-stone-850 p-6 rounded-2xl max-w-md mx-auto space-y-6">
      <div className="text-center space-y-1">
        <h2 className="text-sm font-bold">Vedic Resonance Box</h2>
        <p className="text-[10px] text-stone-500">Procedural sine-wave binaural generator</p>
      </div>

      <div className="flex items-center justify-center py-6">
        <button 
          onClick={() => setIsPlaying(!isPlaying)}
          className="w-16 h-16 rounded-full bg-amber-500 hover:bg-amber-450 flex items-center justify-center text-stone-950 transition-transform active:scale-95"
        >
          {isPlaying ? <Pause className="w-6 h-6 fill-stone-950" /> : <Play className="w-6 h-6 fill-stone-950 ml-1" />}
        </button>
      </div>

      <div className="flex items-center justify-between text-xs text-stone-400 px-2">
        <div className="flex items-center gap-1.5">
          <Volume2 className="w-4 h-4 text-stone-500" />
          <span>Volume</span>
        </div>
        <span className="font-bold text-amber-500">75%</span>
      </div>
    </div>
  );
}`
      },
      {
        name: "connection.ts",
        path: "src/db/connection.ts",
        language: "typescript",
        content: `import { MongoClient } from "mongodb";

const uri = process.env.MONGODB_URI || "mongodb://127.0.0.1:27017/stress_resilience";
let client: MongoClient;
let clientPromise: Promise<MongoClient>;

if (!process.env.MONGODB_URI) {
  throw new Error("Please add your Mongo URI to .env.local");
}

client = new MongoClient(uri);
clientPromise = client.connect();

export default clientPromise;`
      }
    ]
  }
];
