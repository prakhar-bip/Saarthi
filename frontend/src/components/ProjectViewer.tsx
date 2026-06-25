"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence, useMotionValue, useTransform, animate } from "framer-motion";
import { useWorkspace, CodeFile, Project, API_BASE } from "@/context/WorkspaceContext";
import { CategoryIcon, SarthiLogo } from "./CustomSvgs";
import { Copy, Check, FileCode, CheckCircle2, AlertCircle, X, ArrowLeft, Sparkles, Download, GitBranch, ExternalLink, Loader2, Plus, Database, ClipboardCheck, PanelLeft, AlertTriangle, RefreshCw, Eye, EyeOff, BookOpen, FileEdit, Palette, Cpu, FolderGit2, Lock, FolderPlus, Pause, Play } from "lucide-react";
import { MarkdownRenderer } from "./MarkdownRenderer";
import { DivineCelebration } from "./DivineCelebration";

// 28-agent pipeline sequence for Sarthi
const agentPipeline = [
  "RequirementAnalyzerAgent",
  "PlannerAgent",
  "DatabaseArchitectureAgent",
  "BackendArchitectureAgent",
  "APIAgent",
  "FrontendArchitectureAgent",
  "UIUXArchitectAgent",
  "AuthArchitectureAgent",
  "RealtimeArchitectureAgent",
  "StateManagementAgent",
  "DevOpsArchitectureAgent",
  "SecurityArchitectureAgent",
  "TestingArchitectureAgent",
  "ValidationArchitectureAgent",
  "OptimizationArchitectureAgent",
  "CodeGenerationPlannerAgent",
  "DatabaseModelGenerationAgent",
  "BackendCodeGenerationAgent",
  "APIImplementationAgent",
  "FrontendCodeGenerationAgent",
  "UIComponentGenerationAgent",
  "StateImplementationAgent",
  "IntegrationGenerationAgent",
  "BuildCompilationAgent",
  "ErrorCorrectionAgent",
  "ProjectExportAgent"
];

const agentDescriptions: Record<string, string> = {
  "RequirementAnalyzerAgent": "Analyzing initial project idea and mapping core requirements...",
  "PlannerAgent": "Compiling module execution sequencing and dependency graph...",
  "DatabaseArchitectureAgent": "Architecting collection schemas and indexing strategies via MongoDB MCP...",
  "BackendArchitectureAgent": "Designing backend service modules, middleware, and routers...",
  "APIAgent": "Designing API payload contracts, endpoints, and status codes...",
  "FrontendArchitectureAgent": "Mapping frontend route views, layouts, and page structures...",
  "UIUXArchitectAgent": "Defining HSL color tokens, typography scale, and responsive grid layouts...",
  "AuthArchitectureAgent": "Establishing JWT session auth flows and route guard logic...",
  "RealtimeArchitectureAgent": "Configuring WebSocket pub/sub brokers and event routing...",
  "StateManagementAgent": "Designing Zustand store models, cache keys, and optimistic updates...",
  "DevOpsArchitectureAgent": "Generating Docker configurations and Cloud Run deployment scripts...",
  "SecurityArchitectureAgent": "Enforcing API rate limits, CORS policies, and security sanitization...",
  "TestingArchitectureAgent": "Compiling unit, integration, and E2E test suite specs...",
  "ValidationArchitectureAgent": "Running cross-contract structural validation checks...",
  "OptimizationArchitectureAgent": "Applying server-side caching and performance tuning parameters...",
  "CodeGenerationPlannerAgent": "Planning deterministic source code file writing batches...",
  "DatabaseModelGenerationAgent": "Generating concrete MongoDB database models and schemas...",
  "BackendCodeGenerationAgent": "Generating FastAPI service controllers, repositories, and dependencies...",
  "APIImplementationAgent": "Implementing FastAPI endpoints and request/response models...",
  "FrontendCodeGenerationAgent": "Generating Next.js client-side pages and API fetch wrappers...",
  "UIComponentGenerationAgent": "Generating reusable React components and responsive styling...",
  "StateImplementationAgent": "Implementing Zustand stores and WebSocket subscription hooks...",
  "IntegrationGenerationAgent": "Assembling frontend, backend, auth, and database modules...",
  "BuildCompilationAgent": "Running typescript compiler tests and build packaging checks...",
  "ErrorCorrectionAgent": "Checking imports and fixing compilation errors dynamically...",
  "ProjectExportAgent": "Compiling production monorepo packaging and export ZIP targets..."
};

const vyuhNodes = [
  {
    id: "orchestrator",
    name: "Sri Krishna (Orchestrator)",
    desc: "Gemini multi-agent core driving document compilation, database mapping, and code generation.",
    role: "Steers project generation plans and validates code syntax.",
    x: 250, y: 200, r: 35,
    color: "#eab308", // gold
    glow: "rgba(234, 179, 8, 0.4)",
    files: ["sarthi-internal/AI_Planner.json", "sarthi-internal/AI_AgentContext.json"]
  },
  {
    id: "backend",
    name: "FastAPI Backend Module",
    desc: "FastAPI endpoints controllers, routers, and CORS configurations.",
    role: "Provides API access endpoints to fetch and write data.",
    x: 390, y: 120, r: 28,
    color: "#06b6d4", // cyan
    glow: "rgba(6, 182, 212, 0.3)",
    files: ["sarthi-internal/AI_BackendCodeGeneration.json", "sarthi-internal/AI_APIImplementation.json"]
  },
  {
    id: "database",
    name: "MongoDB Models Layer",
    desc: "MongoDB collection models, schema designs, and indices configs.",
    role: "Manages data persistence and schema structures.",
    x: 390, y: 280, r: 28,
    color: "#8b5cf6", // purple
    glow: "rgba(139, 92, 246, 0.3)",
    files: ["sarthi-internal/AI_DatabaseModelGeneration.json", "sarthi-internal/AI_DatabaseArchitecture.json"]
  },
  {
    id: "frontend",
    name: "Next.js Frontend Client",
    desc: "React/Next.js page layouts, fetch modules, and server-side routes.",
    role: "Provides interactive client dashboard interfaces.",
    x: 110, y: 280, r: 28,
    color: "#ec4899", // pink
    glow: "rgba(236, 72, 153, 0.3)",
    files: ["sarthi-internal/AI_FrontendCodeGeneration.json"]
  },
  {
    id: "uiux",
    name: "Tailwind UI Components",
    desc: "Reusable styling tokens, buttons, and custom layout components.",
    role: "Renders modern styling and glassmorphic designs.",
    x: 110, y: 120, r: 28,
    color: "#f59e0b", // amber
    glow: "rgba(245, 158, 11, 0.3)",
    files: ["sarthi-internal/AI_UIComponentGeneration.json"]
  },
  {
    id: "devops",
    name: "System DevOps Layer",
    desc: "Docker container settings, scripts, and GCP Cloud Run manifests.",
    role: "Builds and deploys the compiled application.",
    x: 250, y: 340, r: 28,
    color: "#3b82f6", // blue
    glow: "rgba(59, 130, 246, 0.3)",
    files: ["sarthi-internal/AI_BuildCompilation.json", "sarthi-internal/AI_IntegrationGeneration.json"]
  }
];

const getProjectFiles = (proj: Project): CodeFile[] => {
  const files: CodeFile[] = [...(proj.codebase || [])];
  if (proj.mcp_evidence) {
    files.unshift({
      name: "MCP_EVIDENCE.json",
      path: "sarthi-internal/MCP_EVIDENCE.json",
      language: "json",
      content: JSON.stringify(proj.mcp_evidence, null, 2),
    });
  }
  if (proj.hackathon_metadata) {
    files.unshift({
      name: "HACKATHON_METADATA.json",
      path: "sarthi-internal/HACKATHON_METADATA.json",
      language: "json",
      content: JSON.stringify(proj.hackathon_metadata, null, 2),
    });
  }
  if (proj.prd) {
    files.unshift({
      name: "Product Requirement Document (PRD).md",
      path: "PRD.md",
      language: "markdown",
      content: proj.prd,
    });
  }
  if (proj.mrd) {
    files.unshift({
      name: "Market Requirement Document (MRD).md",
      path: "MRD.md",
      language: "markdown",
      content: proj.mrd,
    });
  }
  if (proj.trd) {
    files.unshift({
      name: "Technical Requirement Document (TRD).md",
      path: "TRD.md",
      language: "markdown",
      content: proj.trd,
    });
  }
  if (proj.build_compilation) {
    files.unshift({
      name: "AI_BuildCompilation.json",
      path: "sarthi-internal/AI_BuildCompilation.json",
      language: "json",
      content: JSON.stringify(proj.build_compilation, null, 2),
    });
  }
  if (proj.integration_generation) {
    files.unshift({
      name: "AI_IntegrationGeneration.json",
      path: "sarthi-internal/AI_IntegrationGeneration.json",
      language: "json",
      content: JSON.stringify(proj.integration_generation, null, 2),
    });
  }
  if (proj.state_implementation) {
    files.unshift({
      name: "AI_StateImplementation.json",
      path: "sarthi-internal/AI_StateImplementation.json",
      language: "json",
      content: JSON.stringify(proj.state_implementation, null, 2),
    });
  }
  if (proj.ui_component_generation) {
    files.unshift({
      name: "AI_UIComponentGeneration.json",
      path: "sarthi-internal/AI_UIComponentGeneration.json",
      language: "json",
      content: JSON.stringify(proj.ui_component_generation, null, 2),
    });
  }
  if (proj.frontend_code_generation) {
    files.unshift({
      name: "AI_FrontendCodeGeneration.json",
      path: "sarthi-internal/AI_FrontendCodeGeneration.json",
      language: "json",
      content: JSON.stringify(proj.frontend_code_generation, null, 2),
    });
  }
  if (proj.api_implementation) {
    files.unshift({
      name: "AI_APIImplementation.json",
      path: "sarthi-internal/AI_APIImplementation.json",
      language: "json",
      content: JSON.stringify(proj.api_implementation, null, 2),
    });
  }
  if (proj.backend_code_generation) {
    files.unshift({
      name: "AI_BackendCodeGeneration.json",
      path: "sarthi-internal/AI_BackendCodeGeneration.json",
      language: "json",
      content: JSON.stringify(proj.backend_code_generation, null, 2),
    });
  }
  if (proj.database_model_generation) {
    files.unshift({
      name: "AI_DatabaseModelGeneration.json",
      path: "sarthi-internal/AI_DatabaseModelGeneration.json",
      language: "json",
      content: JSON.stringify(proj.database_model_generation, null, 2),
    });
  }
  if (proj.agent_context) {
    files.unshift({
      name: "AI_AgentContext.json",
      path: "sarthi-internal/AI_AgentContext.json",
      language: "json",
      content: JSON.stringify(proj.agent_context, null, 2),
    });
  }
  if (proj.code_generation_plan) {
    files.unshift({
      name: "AI_CodeGenerationPlanner.json",
      path: "sarthi-internal/AI_CodeGenerationPlanner.json",
      language: "json",
      content: JSON.stringify(proj.code_generation_plan, null, 2),
    });
  }
  if (proj.optimization_architecture) {
    files.unshift({
      name: "AI_OptimizationArchitecture.json",
      path: "sarthi-internal/AI_OptimizationArchitecture.json",
      language: "json",
      content: JSON.stringify(proj.optimization_architecture, null, 2),
    });
  }
  if (proj.validation_architecture) {
    files.unshift({
      name: "AI_ValidationArchitecture.json",
      path: "sarthi-internal/AI_ValidationArchitecture.json",
      language: "json",
      content: JSON.stringify(proj.validation_architecture, null, 2),
    });
  }
  if (proj.error_correction) {
    files.unshift({
      name: "AI_ErrorCorrection.json",
      path: "sarthi-internal/AI_ErrorCorrection.json",
      language: "json",
      content: JSON.stringify(proj.error_correction, null, 2),
    });
  }
  if (proj.project_export) {
    files.unshift({
      name: "AI_ProjectExport.json",
      path: "sarthi-internal/AI_ProjectExport.json",
      language: "json",
      content: JSON.stringify(proj.project_export, null, 2),
    });
  }
  if (proj.db_architecture) {
    files.unshift({
      name: "AI Database Architecture.json",
      path: "sarthi-internal/AI_DatabaseArchitecture.json",
      language: "json",
      content: JSON.stringify(proj.db_architecture, null, 2),
    });
  }
  if (proj.planning) {
    files.unshift({
      name: "AI Planner.json",
      path: "sarthi-internal/AI_Planner.json",
      language: "json",
      content: JSON.stringify(proj.planning, null, 2),
    });
  }
  if (proj.requirements) {
    files.unshift({
      name: "AI Requirements.json",
      path: "sarthi-internal/AI_Requirements.json",
      language: "json",
      content: JSON.stringify(proj.requirements, null, 2),
    });
  }
  return files;
};

const getNodeFiles = (nodeId: string, proj: Project): CodeFile[] => {
  const allFiles = getProjectFiles(proj);
  const explicit = vyuhNodes.find(n => n.id === nodeId)?.files || [];
  
  return allFiles.filter(file => {
    if (explicit.includes(file.path)) return true;
    
    const pathLower = file.path.toLowerCase();
    
    if (nodeId === "orchestrator") {
      return pathLower.includes("prd") || pathLower.includes("planner") || pathLower.includes("requirements") || pathLower.includes("agentcontext");
    }
    if (nodeId === "backend") {
      return pathLower.includes("backend") || pathLower.includes("api_") || pathLower.includes("api/") || (pathLower.includes("server") && !pathLower.includes("frontend"));
    }
    if (nodeId === "database") {
      return pathLower.includes("database") || pathLower.includes("model") || pathLower.includes("schema") || pathLower.includes("mongo");
    }
    if (nodeId === "frontend") {
      return (pathLower.includes("frontend") || pathLower.includes("page.tsx") || pathLower.includes("layout.tsx")) && !pathLower.includes("components/");
    }
    if (nodeId === "uiux") {
      return pathLower.includes("component") || pathLower.includes("css") || pathLower.includes("tailwind") || pathLower.includes("theme");
    }
    if (nodeId === "devops") {
      return pathLower.includes("docker") || pathLower.includes("deploy") || pathLower.includes("export") || pathLower.includes("integration") || pathLower.includes("compilation");
    }
    return false;
  });
};

export const ProjectViewer: React.FC = () => {
  const { 
    chats, 
    activeChatId, 
    projects, 
    activeProjectId, 
    generateProject, 
    compileProjectCodebase,
    pauseProjectCodebase,
    resumeProjectCodebase,
    isGeneratingProject, 
    setShowRightPane, 
    updateChatSelectedProject,
    suggestions,
    fetchSuggestions,
    approveProjectPlan,
    updateProjectHitl,
    compilationLogs,
    showSpecsDocs,
    setShowSpecsDocs,
    createNewChat,
    updateProject
  } = useWorkspace();
  const terminalEndRef = useRef<HTMLDivElement>(null);
  const [selectedFile, setSelectedFile] = useState<CodeFile | null>(null);
  const [copied, setCopied] = useState(false);
  const [activeDocTab, setActiveDocTab] = useState<"trd" | "plan">("trd");
  const [editedPlanMarkdown, setEditedPlanMarkdown] = useState<string>("");
  const [isEditingPlan, setIsEditingPlan] = useState<boolean>(false);

  const [completedTab, setCompletedTab] = useState<"files" | "vyuh">("files");
  const [hoveredVyuhNode, setHoveredVyuhNode] = useState<any | null>(null);
  const [selectedVyuhNode, setSelectedVyuhNode] = useState<any | null>(null);



  // Stepper & Workflow traveling states
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [themes, setThemes] = useState<any[]>([]);
  const [loadingThemes, setLoadingThemes] = useState(false);
  const [selectedThemeIndex, setSelectedThemeIndex] = useState(0);
  const [activePreviewPage, setActivePreviewPage] = useState<"home" | "dashboard" | "analytics" | "settings" | "login">("home");
  const [customThemeInput, setCustomThemeInput] = useState("");
  // Custom project blueprint form and tab states
  const [customName, setCustomName] = useState("");
  const [customIdea, setCustomIdea] = useState("");
  const [customFeatures, setCustomFeatures] = useState<string[]>([""]);
  const [customTechStack, setCustomTechStack] = useState("React, Tailwind CSS, Node.js");
  const [customGenType, setCustomGenType] = useState("full_stack");

  // Project Creator Landing states
  const [creatorPrompt, setCreatorPrompt] = useState("");
  const [creatorGenType, setCreatorGenType] = useState("full_stack");
  const [isSuggestingBlueprint, setIsSuggestingBlueprint] = useState(false);
  const [isGeneratingDocs, setIsGeneratingDocs] = useState(false);
  const [loadingIdeas, setLoadingIdeas] = useState(false);
  const [suggestedIdeas, setSuggestedIdeas] = useState<any[]>([]);

  // Export action states
  const [isDownloading, setIsDownloading] = useState(false);
  const [isPushingToGithub, setIsPushingToGithub] = useState(false);
  const [githubResult, setGithubResult] = useState<{ url: string; error?: string } | null>(null);
  const [showCelebration, setShowCelebration] = useState(false);
  const [showFilesPane, setShowFilesPane] = useState(true);
  const prevStatusRef = useRef<string | undefined>(undefined);


  const handleSuggestIdeas = async () => {
    setLoadingIdeas(true);
    setSuggestedIdeas([]);
    try {
      const token = localStorage.getItem("token");
      const category = activeChat?.category || "General";
      const res = await fetch(`${API_BASE}/api/projects/suggestions?category=${encodeURIComponent(category)}`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setSuggestedIdeas(data.slice(0, 3));
      }
    } catch (err) {
      console.error("Failed to suggest ideas", err);
    } finally {
      setLoadingIdeas(false);
    }
  };

  const handleSuggestMoreThemes = async () => {
    if (!activeChatId) return;
    setLoadingThemes(true);
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API_BASE}/api/chats/${activeChatId}/themes`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setThemes(data);
        setSelectedThemeIndex(0);
      }
    } catch (err) {
      console.error("Failed to fetch more themes", err);
    } finally {
      setLoadingThemes(false);
    }
  };

  const handleRequestCustomThemes = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customThemeInput.trim() || !activeChatId) return;
    setLoadingThemes(true);
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API_BASE}/api/chats/${activeChatId}/themes?prompt=${encodeURIComponent(customThemeInput.trim())}`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setThemes(data);
        setSelectedThemeIndex(0);
      }
    } catch (err) {
      console.error("Failed to fetch custom themes", err);
    } finally {
      setLoadingThemes(false);
    }
  };

  const activeChat = chats.find((c) => c.id === activeChatId);
  const activeProj = projects.find((p) => p.id === (activeProjectId || activeChat?.project_id)) ||
    (activeChatId ? projects.find((p) => p.chat_id === activeChatId) : undefined);
  const hackathonMetadata = activeProj?.hackathon_metadata || {};
  const mcpEvidence = activeProj?.mcp_evidence || {};
  const mcpStatus = mcpEvidence?.mcp_status || {};
  const subAgentCount = Array.isArray(hackathonMetadata?.sub_agent_pipeline)
    ? hackathonMetadata.sub_agent_pipeline.length
    : 0;
  const partnerTrack = hackathonMetadata?.partner_track || "MongoDB";

  const handleCopy = () => {
    if (!selectedFile) return;
    navigator.clipboard.writeText(selectedFile.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadZip = async () => {
    if (!activeProj || isDownloading) return;
    setIsDownloading(true);
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API_BASE}/api/projects/${activeProj.id}/download`, {
        headers: { "Authorization": `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(await res.text());
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${activeProj.name.toLowerCase().replace(/\s+/g, "-")}.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err: any) {
      console.error("Download failed:", err);
      let errorMsg = "An unknown error occurred.";
      try {
        if (err.message) {
          const parsed = JSON.parse(err.message);
          errorMsg = parsed.detail || err.message;
        }
      } catch {
        errorMsg = err.message || errorMsg;
      }
      alert(`Download Failed:\n${errorMsg}\n\nPlease verify that Sarthi has successfully compiled the project codebase, or try again.`);
    } finally {
      setIsDownloading(false);
    }
  };

  const handleGithubPush = async () => {
    if (!activeProj || isPushingToGithub) return;
    setIsPushingToGithub(true);
    setGithubResult(null);
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API_BASE}/api/projects/${activeProj.id}/github-push`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "GitHub push failed");
      setGithubResult({ url: data.repo_url });
    } catch (err: any) {
      setGithubResult({ url: "", error: err.message || "Unknown error" });
    } finally {
      setIsPushingToGithub(false);
    }
  };

  // Sync activeDocTab when status changes to waiting_approval
  useEffect(() => {
    if (activeProj?.status === "waiting_approval" && activeProj.hitl_enabled !== false) {
      setActiveDocTab("plan");
    } else {
      setActiveDocTab("trd");
    }
  }, [activeProjectId, activeProj?.status, activeProj?.hitl_enabled]);

  // Sync edited plan text from project
  useEffect(() => {
    if (activeProj?.implementation_plan?.plan_markdown) {
      setEditedPlanMarkdown(activeProj.implementation_plan.plan_markdown);
    } else {
      setEditedPlanMarkdown("");
    }
    setIsEditingPlan(false);
  }, [activeProjectId, activeProj?.implementation_plan]);

  const currentAgentIdx = (() => {
    if (!activeProj) return -1;
    const stepStr = activeProj.step || "";
    const idx = agentPipeline.findIndex(agent => stepStr.includes(agent));
    if (idx !== -1) return idx;
    return Math.min(agentPipeline.length - 1, Math.floor((activeProj.progress / 100) * agentPipeline.length));
  })();

  useEffect(() => {
    if (activeChat?.selected_project) {
      const parsed = activeChat.selected_project;
      if (parsed.name && parsed.name !== customName) setCustomName(parsed.name);
      if (parsed.idea && parsed.idea !== customIdea) setCustomIdea(parsed.idea);
      if (parsed.features && Array.isArray(parsed.features)) {
        setCustomFeatures([...parsed.features]);
      }
      if (parsed.tech_stack && parsed.tech_stack !== customTechStack) setCustomTechStack(parsed.tech_stack);
      if (parsed.generation_type && parsed.generation_type !== customGenType) setCustomGenType(parsed.generation_type);
    }
  }, [activeChat?.selected_project]);

  // Animated counter for progress percentage
  const progressCount = useMotionValue(0);
  const progressRounded = useTransform(progressCount, Math.round);
  const progressDecimal = useTransform(progressCount, (v) => v >= 100 ? "100" : v.toFixed(2));
  useEffect(() => {
    if (!activeProj) return;
    const controls = animate(progressCount, activeProj.progress, { duration: 0.8, ease: "easeOut" });
    return controls.stop;
  }, [activeProj?.progress]);

  // Reset Github Result on chat select
  useEffect(() => {
    setGithubResult(null);
  }, [activeChatId]);

  // Stepper unlocking & travelling computations (4 Steps workflow)
  const maxUnlockedStep = (() => {
    if (!activeChat) return 0;
    let step = 1;
    if (activeChat.selected_project?.name && activeChat.selected_project?.idea) {
      step = 2;
    }
    if (activeProj) {
      if (activeProj.status === "completed") {
        step = 4;
      } else {
        step = 3;
      }
    }
    return step;
  })();

  const defaultStep = (() => {
    if (activeProj) {
      if (activeProj.status === "completed") return 4;
      return 3;
    }
    return 1;
  })();

  // Removed automatic step advancement to let the user review the generated blueprint first
  // The user must explicitly click the stepper or confirm buttons to advance.
  // Auto-trigger codebase compilation as soon as documents are ready or plan is waiting approval
  // Sync currentStep automatically on project/chat loads and status updates
  useEffect(() => {
    if (activeProj) {
      if (activeProj.status === "completed") {
        setCurrentStep(4);
      } else {
        setCurrentStep(3);
      }
    } else if (activeChat?.selected_project?.name) {
      setCurrentStep(2);
    } else {
      setCurrentStep(1);
    }
  }, [activeProj?.id, activeProj?.status, activeChat?.id, activeChat?.selected_project?.name]);

  useEffect(() => {
    if (activeProj && !isGeneratingProject) {
      if (activeProj.status === "documents_ready") {
        compileProjectCodebase(activeProj.id, activeProj.chat_id);
      } else if (activeProj.status === "waiting_approval") {
        // Manual wait-gate enabled: Wait for user's explicit action inside the TRD/Plan viewer
      }
    }
  }, [activeProj?.id, activeProj?.status, isGeneratingProject, compileProjectCodebase, approveProjectPlan]);

  const projLogs = activeProj ? (compilationLogs[activeProj.id] || []) : [];
  useEffect(() => {
    if (terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [projLogs.length]);

  useEffect(() => {
    if (activeChat && !activeChat.selected_project && activeChat.category && suggestions.length === 0) {
      fetchSuggestions(activeChat.category);
    }
  }, [activeChat?.id, activeChat?.selected_project, activeChat?.category, suggestions.length]);

  // Reset themes when chat session changes
  useEffect(() => {
    setThemes([]);
    setSelectedThemeIndex(0);
  }, [activeChatId]);

  // Populate themes from existing project if it is already compiled or compiling
  useEffect(() => {
    if (activeProj && activeProj.theme) {
      setThemes([{ 
        name: activeProj.theme, 
        palette: activeProj.theme_palette || {
          primary: "#1e1b4b",
          secondary: "#312e81",
          accent: "#f59e0b",
          background: "#fafaf9",
          surface: "#ffffff",
          text: "#1c1917",
          border: "#e7e5e4"
        } 
      }]);
      setSelectedThemeIndex(0);
    }
  }, [activeProj?.id, activeProj?.theme, activeProj?.theme_palette]);

  // Fetch dynamic themes on stage change
  useEffect(() => {
    if (currentStep === 2 && activeChatId && themes.length === 0 && !activeProj) {
      const fetchThemes = async () => {
        setLoadingThemes(true);
        try {
          const token = localStorage.getItem("token");
          const res = await fetch(`${API_BASE}/api/chats/${activeChatId}/themes`, {
            headers: { "Authorization": `Bearer ${token}` }
          });
          if (res.ok) {
            const data = await res.json();
            setThemes(data);
            setSelectedThemeIndex(0);
          }
        } catch (err) {
          console.error("Failed to fetch themes", err);
        } finally {
          setLoadingThemes(false);
        }
      };
      fetchThemes();
    }
  }, [currentStep, activeChatId, themes.length, activeProj]);

  // Set the first file active by default when project changes or completes
  useEffect(() => {
    if (activeProj?.status === "completed" && prevStatusRef.current === "generating") {
      setShowCelebration(true);
    }
    prevStatusRef.current = activeProj?.status;

    if (activeProj && (activeProj.status === "documents_ready" || activeProj.status === "waiting_approval")) {
      setShowSpecsDocs(true);
    }

    if (activeProj && activeProj.status === "completed") {
      if (activeProj.category === "documents" || activeProj.prd) {
        setSelectedFile({
          name: "Product Requirement Document (PRD).md",
          path: "PRD.md",
          language: "markdown",
          content: activeProj.prd || "# Product Requirement Document (PRD)\n*No content generated.*",
        });
      } else if (activeProj.requirements) {
        setSelectedFile({
          name: "AI Requirements.json",
          path: "sarthi-internal/AI_Requirements.json",
          language: "json",
          content: JSON.stringify(activeProj.requirements, null, 2),
        });
      } else if (activeProj.codebase && activeProj.codebase.length > 0) {
        setSelectedFile(activeProj.codebase[0]);
      } else {
        setSelectedFile(null);
      }
    } else {
      setSelectedFile(null);
    }
  }, [activeProjectId, activeProj?.status, activeProj?.prd, setShowSpecsDocs]);

  useEffect(() => {
    const handleSelectFile = (e: Event) => {
      const customEvent = e as CustomEvent;
      if (customEvent.detail && customEvent.detail.file) {
        setSelectedFile(customEvent.detail.file);
        setCompletedTab("files");
      }
    };
    window.addEventListener("select-codebase-file", handleSelectFile);
    return () => window.removeEventListener("select-codebase-file", handleSelectFile);
  }, [activeProj?.codebase]);



  if (!activeChat) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 bg-transparent">
        <div className="text-center max-w-sm">
          <AlertCircle className="w-10 h-10 text-stone-300 mx-auto mb-3" />
          <h4 className="text-sm font-semibold text-stone-700">No project active</h4>
          <p className="text-xs text-stone-400 mt-1">
            Describe your project idea in the chatbox to start.
          </p>
        </div>
      </div>
    );
  }

  // --- STEP 1: BLUEPRINT STEP ---
  const renderBlueprintStep = () => {
    const blueprint = activeChat.selected_project;
    if (!blueprint) {
      if (isSuggestingBlueprint) {
        return (
          <div className="flex-1 flex flex-col items-center justify-center p-8 bg-transparent">
            <Loader2 className="w-8 h-8 animate-spin text-indigo-950 mb-3" />
            <p className="text-xs text-stone-500 font-semibold">Generating suggested blueprint...</p>
          </div>
        );
      }

      return (
        <div className="flex-1 overflow-y-auto p-6 flex justify-center items-center w-full">
          <form 
            onSubmit={async (e) => {
              e.preventDefault();
              if (!creatorPrompt.trim()) return;
              setIsSuggestingBlueprint(true);
              try {
                const token = localStorage.getItem("token");
                const res = await fetch(`${API_BASE}/api/projects/suggest-blueprint`, {
                  method: "POST",
                  headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                  },
                  body: JSON.stringify({
                    idea: creatorPrompt.trim(),
                    generation_type: creatorGenType
                  })
                });
                if (res.ok) {
                  const blueprintData = await res.json();
                  if (!blueprintData.features || !Array.isArray(blueprintData.features)) {
                    blueprintData.features = [""];
                  }
                  blueprintData.generation_type = creatorGenType;
                  await updateChatSelectedProject(activeChat.id, blueprintData);
                } else {
                  console.error("Failed to suggest project details");
                }
              } catch (err) {
                console.error("Error suggesting project:", err);
              } finally {
                setIsSuggestingBlueprint(false);
              }
            }} 
            className="w-full max-w-lg space-y-5 bg-white/60 backdrop-blur-md p-6 rounded-2xl border border-stone-200/70 shadow-lg"
          >
            <div className="text-center space-y-1">
              <div className="w-12 h-12 rounded-2xl bg-indigo-50/80 border border-indigo-100 flex items-center justify-center text-indigo-950 shadow-sm mx-auto">
                <FolderPlus className="w-6 h-6" />
              </div>
              <h3 className="text-sm font-bold text-stone-850">Create New Project</h3>
              <p className="text-[10px] text-stone-500 font-medium">Select a scope and describe your project idea to generate a blueprint.</p>
            </div>

            <div className="space-y-2">
              <label className="text-[9px] font-bold uppercase tracking-wider text-stone-450 flex items-center gap-1.5">
                1. Select Generation Scope
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                {[
                  { id: "full_stack", label: "Enterprise (Full Stack)", desc: "API + UI + Database" },
                  { id: "backend_only", label: "Microservice (Backend)", desc: "REST APIs & Schemas" },
                  { id: "frontend_only", label: "UI/UX (Frontend)", desc: "UI Pages & Styling" }
                ].map((item) => {
                  const isLocked = item.id !== "full_stack";
                  return (
                    <button
                      key={item.id}
                      type="button"
                      disabled={isLocked}
                      title={isLocked ? "Coming Soon" : ""}
                      onClick={() => {
                        if (isLocked) return;
                        setCreatorGenType(item.id);
                      }}
                      className={`flex flex-col items-center justify-center p-3 rounded-xl border text-center transition-all ${
                        isLocked
                          ? "border-stone-200 bg-stone-100/50 text-stone-400 opacity-60 cursor-not-allowed"
                          : creatorGenType === item.id
                          ? "border-indigo-950 bg-indigo-50/30 text-indigo-950 shadow-sm ring-1 ring-indigo-950/20 cursor-pointer"
                          : "border-stone-200 bg-stone-50 hover:bg-stone-100/80 text-stone-600 cursor-pointer"
                      }`}
                    >
                      <span className="text-[11px] font-bold flex items-center gap-1 justify-center w-full">
                        {item.label}
                        {isLocked && <Lock className="w-2.5 h-2.5 text-stone-450" />}
                      </span>
                      <span className="text-[8px] mt-0.5 opacity-80">{item.desc}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="border-t border-stone-100 my-2" />

            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <label className="text-[9px] font-bold uppercase tracking-wider text-stone-455 flex items-center gap-1.5 select-none">
                  <Sparkles className="w-3 h-3 text-indigo-650 animate-pulse" />
                  2. Describe Project Idea
                </label>
                <button
                  type="button"
                  disabled={loadingIdeas}
                  onClick={handleSuggestIdeas}
                  className="flex items-center gap-1 text-[9px] font-bold text-indigo-650 hover:text-indigo-800 disabled:opacity-50 transition-all cursor-pointer bg-transparent border-none p-0 select-none"
                >
                  {loadingIdeas ? (
                    <Loader2 className="w-3 h-3 animate-spin text-indigo-650" />
                  ) : (
                    <Sparkles className="w-3 h-3 text-indigo-650" />
                  )}
                  <span>{loadingIdeas ? "Fetching..." : "Suggest Ideas"}</span>
                </button>
              </div>
              <textarea
                required
                rows={4}
                placeholder="Describe your project idea in a sentence or two... (e.g. 'A payment validation microservice that consumes stripe webhook payloads, validates signature, and publishes to RabbitMQ')"
                value={creatorPrompt}
                onChange={(e) => setCreatorPrompt(e.target.value)}
                className="w-full bg-stone-50 border border-stone-200 rounded-xl px-3 py-2 text-xs text-stone-800 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 transition-all font-medium resize-none leading-relaxed"
              />

              {/* Suggested Ideas Pills */}
              {suggestedIdeas.length > 0 && (
                <div className="pt-1.5 space-y-2">
                  <span className="text-[9px] font-bold uppercase tracking-wider text-stone-400 select-none">Select a suggested idea:</span>
                  <div className="flex flex-col gap-2">
                    {suggestedIdeas.map((ideaObj, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => {
                          setCreatorPrompt(ideaObj.idea);
                          // Clear suggestions list once selected to keep UI clean
                          setSuggestedIdeas([]);
                        }}
                        className="w-full p-2.5 bg-white border border-stone-200 hover:border-indigo-400 hover:bg-indigo-50/20 rounded-xl text-left transition-all cursor-pointer flex flex-col gap-0.5 shadow-sm group"
                      >
                        <span className="text-[10px] font-bold text-stone-800 group-hover:text-indigo-950 flex items-center gap-1.5">
                          <Sparkles className="w-2.5 h-2.5 text-amber-500" />
                          {ideaObj.name}
                        </span>
                        <span className="text-[9px] text-stone-450 leading-relaxed font-medium line-clamp-2">{ideaObj.idea}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <button
              type="submit"
              disabled={!creatorPrompt.trim()}
              className="w-full mt-2 py-2.5 bg-indigo-950 hover:bg-indigo-900 text-amber-500 font-bold tracking-wide border border-indigo-900/50 shadow-inner text-xs font-bold rounded-xl shadow-md transition-all hover:scale-[1.01] active:scale-[0.99] cursor-pointer flex items-center justify-center gap-1.5 disabled:opacity-50"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Draft Project Blueprint</span>
            </button>
          </form>
        </div>
      );
    }

    const isBlueprintReadOnly = maxUnlockedStep >= 3;

    return (
      <div className="flex-1 overflow-y-auto p-4 flex justify-center items-start w-full">
        <form onSubmit={async (e) => {
            e.preventDefault();
            if (isBlueprintReadOnly) return;
            if (!customName.trim() || !customIdea.trim()) return;
            const newBlueprint = {
              name: customName.trim(),
              idea: customIdea.trim(),
              features: customFeatures.map(f => f.trim()).filter(Boolean),
              tech_stack: customTechStack.trim(),
              category: activeChat.category,
              generation_type: customGenType
            };
            await updateChatSelectedProject(activeChat.id, newBlueprint);
            setCurrentStep(2);
          }} className="w-full max-w-lg space-y-3 bg-stone-50 p-4 rounded-xl border border-stone-200/70 shadow-sm">
            <div className="space-y-1">
              <label className="text-[9px] font-bold uppercase tracking-wider text-stone-450">Project Name</label>
              <input
                type="text"
                required
                disabled={isBlueprintReadOnly}
                placeholder="e.g. 'Personal Finance Manager'"
                value={customName}
                onChange={(e) => setCustomName(e.target.value)}
                className="w-full bg-stone-50 border border-stone-200 rounded-xl px-2.5 py-1.5 text-xs text-stone-850 focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-400 transition-all font-medium disabled:opacity-75 disabled:cursor-not-allowed"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[9px] font-bold uppercase tracking-wider text-stone-450">Core Idea / Description</label>
              <textarea
                required
                disabled={isBlueprintReadOnly}
                rows={3}
                placeholder="Describe the application's vision and value proposition..."
                value={customIdea}
                onChange={(e) => setCustomIdea(e.target.value)}
                className="w-full bg-stone-50 border border-stone-200 rounded-xl px-2.5 py-1.5 text-xs text-stone-855 focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-400 transition-all resize-none font-medium leading-relaxed disabled:opacity-75 disabled:cursor-not-allowed"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[9px] font-bold uppercase tracking-wider text-stone-455">Key Features</label>
              <div className="space-y-1.5">
                {customFeatures.map((feat, fidx) => (
                  <div key={fidx} className="flex gap-2">
                    <input
                      type="text"
                      disabled={isBlueprintReadOnly}
                      placeholder={`Feature ${fidx + 1} (e.g. 'Stripe Payment Sync')`}
                      value={feat}
                      onChange={(e) => {
                        const updated = [...customFeatures];
                        updated[fidx] = e.target.value;
                        setCustomFeatures(updated);
                      }}
                      className="flex-1 bg-stone-50 border border-stone-200 rounded-xl px-2.5 py-1.5 text-xs text-stone-850 focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-400 transition-all font-medium disabled:opacity-75 disabled:cursor-not-allowed"
                    />
                    {customFeatures.length > 1 && !isBlueprintReadOnly && (
                      <button
                        type="button"
                        onClick={() => {
                          const updated = customFeatures.filter((_, i) => i !== fidx);
                          setCustomFeatures(updated);
                        }}
                        className="p-1.5 text-stone-400 hover:text-rose-500 hover:bg-rose-50 rounded-xl transition-colors cursor-pointer"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                ))}
              </div>
              {!isBlueprintReadOnly && (
                <button
                  type="button"
                  onClick={() => setCustomFeatures([...customFeatures, ""])}
                  className="w-full mt-1.5 py-1.5 border border-dashed border-stone-300 text-stone-500 hover:text-indigo-950 hover:border-indigo-300 hover:bg-indigo-50 rounded-xl text-xs font-medium transition-all flex items-center justify-center gap-1 cursor-pointer"
                >
                  <Plus className="w-3 h-3" /> Add Feature
                </button>
              )}
            </div>

            <div className="space-y-1">
              <label className="text-[9px] font-bold uppercase tracking-wider text-stone-450">Generation Scope</label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                {[
                  { id: "full_stack", label: "Enterprise (Full Stack)", desc: "API + UI + Database" },
                  { id: "backend_only", label: "Microservice (Backend)", desc: "REST APIs & Schemas" },
                  { id: "frontend_only", label: "UI/UX (Frontend)", desc: "UI Pages & Styling" }
                ].map((item) => {
                  const isLocked = item.id !== "full_stack";
                  return (
                    <button
                      key={item.id}
                      type="button"
                      disabled={isLocked || isBlueprintReadOnly}
                      title={isLocked ? "Coming Soon" : ""}
                      onClick={() => {
                        if (isLocked) return;
                        setCustomGenType(item.id);
                        if (item.id === "frontend_only") {
                          setCustomTechStack("Next.js, Tailwind CSS");
                        } else if (item.id === "backend_only") {
                          setCustomTechStack("FastAPI, MongoDB");
                        } else {
                          setCustomTechStack("React, Tailwind CSS, FastAPI, MongoDB");
                        }
                      }}
                      className={`flex flex-col items-center justify-center p-2 rounded-xl border text-center transition-all ${
                        isLocked
                          ? "border-stone-200 bg-stone-100/70 text-stone-400 opacity-60 cursor-not-allowed"
                          : customGenType === item.id
                          ? "border-indigo-950 bg-indigo-50/50 text-indigo-950 shadow-sm cursor-pointer"
                          : "border-stone-200 bg-stone-50 hover:bg-stone-100 text-stone-600 cursor-pointer"
                      } disabled:opacity-75 disabled:cursor-not-allowed`}
                    >
                      <span className="text-[11px] font-bold flex items-center gap-1 justify-center w-full">
                        {item.label}
                        {isLocked && <Lock className="w-2.5 h-2.5 text-stone-400" />}
                      </span>
                      <span className="text-[8px] mt-0.5 opacity-80">{item.desc}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-[9px] font-bold uppercase tracking-wider text-stone-450">Tech Stack</label>
              <input
                type="text"
                required
                disabled={isBlueprintReadOnly}
                placeholder="e.g. 'React, Tailwind CSS, Node.js'"
                value={customTechStack}
                onChange={(e) => setCustomTechStack(e.target.value)}
                className="w-full bg-stone-50 border border-stone-200 rounded-xl px-2.5 py-1.5 text-xs text-stone-850 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 transition-all font-mono font-semibold text-indigo-950 disabled:opacity-75 disabled:cursor-not-allowed"
              />
            </div>

            {!isBlueprintReadOnly ? (
              <button
                type="submit"
                className="w-full mt-1.5 py-2 bg-indigo-950 hover:bg-indigo-900 text-amber-500 font-bold tracking-wide border border-indigo-900/50 shadow-inner text-xs font-bold rounded-xl shadow-md transition-all hover:scale-[1.01] active:scale-[0.99] cursor-pointer text-center"
              >
                Confirm Blueprint & Proceed
              </button>
            ) : (
              <div className="w-full mt-2 py-2 bg-stone-100 border border-stone-200 text-stone-400 rounded-xl text-center text-xs font-bold">
                ✓ Blueprint Confirmed & Locked
              </div>
            )}
          </form>
      </div>
    );
  };

  // --- STEP 2: THEME STEP ---
  const renderThemeStep = () => {
    const blueprint = activeChat.selected_project;
    if (!blueprint) return null;

    const isThemeReadOnly = maxUnlockedStep >= 3;

    return (
      <div className="flex-1 flex flex-col h-full bg-transparent overflow-hidden">
        <div className="flex-1 overflow-y-auto p-4 flex justify-center items-start w-full">
          <div className="w-full max-w-2xl space-y-4 bg-transparent">
            {customGenType === "backend_only" ? (
              <>
                <div className="bg-indigo-50/50 p-6 rounded-2xl border border-indigo-100/40 shadow-sm space-y-3">
                  <h3 className="text-sm font-bold text-indigo-950">Backend-Only Project Scope</h3>
                  <p className="text-xs text-stone-650 leading-relaxed font-medium">
                    You have selected a **Backend Only** codebase generation. UI themes, stylesheets, and frontend pages are excluded. 
                    Sarthi will compile database models, auth middlewares, and REST API controllers based on your blueprint.
                  </p>
                </div>
                
                <div className="pt-2 pb-8">
                  {!isThemeReadOnly ? (
                    <button
                      type="button"
                      onClick={() => {
                        generateProject(
                          activeChat.id, 
                          blueprint.name, 
                          activeChat.category || "General", 
                          "BackendDefault", 
                          blueprint, 
                          undefined,
                          false,
                          "backend_only"
                        );
                        setCurrentStep(3);
                      }}
                      disabled={isGeneratingProject}
                      className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-indigo-950 via-indigo-900 to-amber-500 hover:from-indigo-900 hover:via-indigo-900 hover:to-amber-500 text-white font-bold py-3.5 rounded-2xl shadow-lg shadow-indigo-200 transition-all hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50 cursor-pointer text-xs"
                    >
                      🚀 Confirm Scope & Start Project Build
                    </button>
                  ) : (
                    <div className="w-full py-3.5 bg-stone-100 border border-stone-200 text-stone-400 rounded-2xl text-center text-xs font-bold">
                      ✓ Scope Confirmed & Built
                    </div>
                  )}
                  <p className="text-center text-[10px] text-stone-400 mt-2.5 leading-relaxed max-w-xs mx-auto">
                    Sarthi will design database models, API controllers, and compile the backend codebase.
                  </p>
                </div>
              </>
            ) : loadingThemes ? (
              <div className="flex flex-col items-center justify-center py-16 space-y-4">
                <div className="relative w-12 h-12">
                  <span className="absolute inset-0 rounded-full border-4 border-indigo-100 animate-pulse" />
                  <span className="absolute inset-0 rounded-full border-4 border-t-indigo-700 border-r-transparent border-b-transparent border-l-transparent animate-spin" />
                </div>
                <p className="text-xs text-stone-500 font-semibold animate-pulse">
                  Sarthi is drafting custom themes for {blueprint.name}...
                </p>
              </div>
            ) : themes.length === 0 ? (
              <div className="text-center p-8 bg-stone-50 rounded-3xl border border-stone-200/60 shadow-sm">
                <p className="text-xs text-stone-400 font-medium">Failed to load theme recommendations. Please check backend connection.</p>
              </div>
            ) : (
              <>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-stone-400">Select Project Theme</h3>
                    {!isThemeReadOnly && (
                      <button
                        type="button"
                        onClick={handleSuggestMoreThemes}
                        disabled={loadingThemes}
                        className="flex items-center gap-1 text-[10px] font-bold text-indigo-950 hover:text-indigo-900 disabled:opacity-50 transition-all cursor-pointer bg-transparent border-none p-0"
                        title="Generate more design themes"
                      >
                        <Sparkles className="w-3.5 h-3.5" />
                        <span>Suggest More</span>
                      </button>
                    )}
                  </div>
                  <div className="grid grid-cols-1 gap-3">
                    {themes.map((themeObj, index) => {
                      const isSelected = selectedThemeIndex === index;
                      const palette = themeObj.palette;
                      return (
                        <button
                          key={index}
                          type="button"
                          disabled={isThemeReadOnly}
                          onClick={() => setSelectedThemeIndex(index)}
                          className={`w-full text-left p-4 rounded-2xl border transition-all bg-stone-50 relative overflow-hidden group ${
                            isSelected
                              ? "border-amber-500 shadow-md scale-[1.01]"
                              : "border-stone-200/70"
                          } ${isThemeReadOnly ? "cursor-default opacity-85" : "cursor-pointer hover:border-stone-300 hover:bg-stone-50/20"}`}
                        >
                          {isSelected && (
                            <div className="absolute top-0 bottom-0 left-0 w-1 bg-indigo-950" />
                          )}
                          <div className="flex justify-between items-start gap-4">
                            <div className="space-y-1">
                              <span className="text-xs font-bold text-stone-850 block transition-colors">
                                {themeObj.name}
                              </span>
                              <p className="text-[10px] text-stone-455 leading-relaxed font-medium">
                                {themeObj.description}
                              </p>
                            </div>
                            <div className="flex -space-x-1.5 shrink-0 pt-0.5 select-none">
                              <span className="w-4 h-4 rounded-full border border-white/80 shadow-sm" style={{ backgroundColor: palette.primary }} title="Primary" />
                              <span className="w-4 h-4 rounded-full border border-white/80 shadow-sm" style={{ backgroundColor: palette.secondary }} title="Secondary" />
                              <span className="w-4 h-4 rounded-full border border-white/80 shadow-sm" style={{ backgroundColor: palette.background }} title="Background" />
                              <span className="w-4 h-4 rounded-full border border-white/80 shadow-sm" style={{ backgroundColor: palette.card_bg }} title="Card BG" />
                            </div>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>

                {!isThemeReadOnly && (
                  <div className="bg-stone-50 p-4 rounded-2xl border border-stone-200/60 shadow-sm space-y-3">
                    <h4 className="text-[10px] font-bold uppercase tracking-wider text-stone-400">Not satisfied? Ask Sarthi for another style:</h4>
                    <form onSubmit={handleRequestCustomThemes} className="flex gap-2">
                      <input
                        type="text"
                        placeholder="e.g. 'cyberpunk black & orange', 'soft pastel blue'"
                        value={customThemeInput}
                        onChange={(e) => setCustomThemeInput(e.target.value)}
                        className="flex-1 bg-stone-50 border border-stone-200 rounded-xl px-3 py-2 text-[10px] text-stone-850 placeholder:text-stone-400 focus:outline-none focus:ring-1 focus:ring-amber-500 focus:border-amber-500 transition-all"
                      />
                      <button
                        type="submit"
                        disabled={!customThemeInput.trim() || loadingThemes}
                        className="px-3 py-2 bg-gradient-to-r from-indigo-950 via-indigo-900 to-amber-500 hover:from-indigo-900 hover:via-indigo-900 hover:to-amber-500 disabled:opacity-50 text-white text-[10px] font-bold rounded-xl transition-all cursor-pointer whitespace-nowrap shadow-sm"
                      >
                        Draft Style
                      </button>
                    </form>
                  </div>
                )}

                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-stone-400">Interactive Preview</h3>
                  </div>

                  <div className="flex bg-stone-100 p-1 rounded-xl overflow-x-auto gap-0.5 scrollbar-none">
                    {(["home", "dashboard", "analytics", "settings", "login"] as const).map((page) => {
                      const isActive = activePreviewPage === page;
                      return (
                        <button
                          key={page}
                          type="button"
                          onClick={() => setActivePreviewPage(page)}
                          className={`flex-1 py-1.5 px-2 rounded-lg text-[9px] font-bold capitalize transition-all cursor-pointer whitespace-nowrap ${
                            isActive ? "bg-stone-50 text-stone-850 shadow-sm" : "text-stone-500 hover:text-stone-855"
                          }`}
                        >
                          {page}
                        </button>
                      );
                    })}
                  </div>

                  <div
                    className="border rounded-2xl overflow-hidden shadow-inner min-h-[220px] transition-all duration-300 relative flex flex-col"
                    style={{
                      backgroundColor: themes[selectedThemeIndex]?.palette.background || "#ffffff",
                      color: themes[selectedThemeIndex]?.palette.text || "#1c1917",
                      borderColor: themes[selectedThemeIndex]?.palette.border || "#e7e5e4"
                    }}
                  >
                    {activePreviewPage === "home" && (
                      <div className="p-4 flex-1 flex flex-col justify-between select-none">
                        <div className="flex justify-between items-center">
                          <span className="text-[8px] font-bold" style={{ color: themes[selectedThemeIndex]?.palette.primary }}>Logo</span>
                          <div className="flex gap-2">
                            <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: themes[selectedThemeIndex]?.palette.primary }} />
                            <span className="w-1.5 h-1.5 rounded-full bg-stone-300" />
                          </div>
                        </div>
                        <div className="my-auto py-2 text-center">
                          <h4 className="text-[11px] font-bold">Build Your Vision</h4>
                          <p className="text-[7px] opacity-70 mt-1 max-w-[160px] mx-auto">Create beautiful components with interactive custom UI wireframes.</p>
                          <button
                            type="button"
                            className="mt-2 text-[7px] font-bold px-3 py-1 rounded shadow-sm border border-transparent text-white"
                            style={{ backgroundColor: themes[selectedThemeIndex]?.palette.primary }}
                          >
                            Get Started
                          </button>
                        </div>
                      </div>
                    )}
                    {activePreviewPage === "dashboard" && (
                      <div className="p-4 flex-1 flex gap-3 select-none">
                        <div className="w-10 border-r pr-1.5 py-1 flex flex-col gap-1.5" style={{ borderColor: themes[selectedThemeIndex]?.palette.border || "#e7e5e4" }}>
                          <span className="w-full h-1 bg-stone-300 rounded" />
                          <span className="w-full h-1 bg-stone-200 rounded" />
                        </div>
                        <div className="flex-1 space-y-3">
                          <div className="flex justify-between items-center">
                            <span className="text-[9px] font-bold">Analytics Panel</span>
                          </div>
                          <div className="grid grid-cols-2 gap-2">
                            <div className="p-2 border rounded-lg" style={{ borderColor: themes[selectedThemeIndex]?.palette.border || "#e7e5e4" }}>
                              <span className="text-[7px] block opacity-60">Total Users</span>
                              <span className="text-[10px] font-bold" style={{ color: themes[selectedThemeIndex]?.palette.primary }}>12,840</span>
                            </div>
                            <div className="p-2 border rounded-lg" style={{ borderColor: themes[selectedThemeIndex]?.palette.border || "#e7e5e4" }}>
                              <span className="text-[7px] block opacity-60">Conversion</span>
                              <span className="text-[10px] font-bold" style={{ color: themes[selectedThemeIndex]?.palette.secondary }}>+4.82%</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                    {activePreviewPage === "analytics" && (
                      <div className="p-4 flex-1 flex flex-col justify-between select-none">
                        <span className="text-[9px] font-bold">Weekly Performance</span>
                        <div className="flex items-end justify-between gap-1.5 h-20 px-4 mt-2">
                          {[35, 60, 45, 80, 50, 95, 75].map((val, i) => (
                            <div key={i} className="flex-1 flex flex-col items-center gap-1">
                              <div
                                className="w-full rounded-t"
                                style={{
                                  height: `${val * 0.7}px`,
                                  backgroundColor: i === 5 ? themes[selectedThemeIndex]?.palette.primary : themes[selectedThemeIndex]?.palette.secondary
                                }}
                              />
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    {activePreviewPage === "settings" && (
                      <div className="p-4 flex-1 space-y-2.5 select-none">
                        <span className="text-[9px] font-bold">System Preferences</span>
                        <div className="space-y-1.5">
                          <div className="flex items-center justify-between p-1.5 border rounded-lg" style={{ borderColor: themes[selectedThemeIndex]?.palette.border || "#e7e5e4" }}>
                            <span className="text-[8px] font-semibold">Enable Notifications</span>
                            <span className="w-5 h-2.5 rounded-full bg-stone-300 relative"><span className="absolute top-0.5 left-0.5 w-1.5 h-1.5 rounded-full bg-white" /></span>
                          </div>
                          <div className="flex items-center justify-between p-1.5 border rounded-lg" style={{ borderColor: themes[selectedThemeIndex]?.palette.border || "#e7e5e4" }}>
                            <span className="text-[8px] font-semibold">Dark Mode Layout</span>
                            <span className="w-5 h-2.5 rounded-full relative" style={{ backgroundColor: themes[selectedThemeIndex]?.palette.primary }}><span className="absolute top-0.5 right-0.5 w-1.5 h-1.5 rounded-full bg-white" /></span>
                          </div>
                        </div>
                      </div>
                    )}
                    {activePreviewPage === "login" && (
                      <div className="p-4 flex-1 flex flex-col justify-center max-w-[150px] mx-auto space-y-2 select-none">
                        <h4 className="text-[9px] font-bold text-center">Welcome Back</h4>
                        <div className="space-y-1">
                          <div className="h-4 border rounded px-1.5 flex items-center text-[6px] text-stone-300" style={{ borderColor: themes[selectedThemeIndex]?.palette.border || "#e7e5e4" }}>Email address</div>
                          <div className="h-4 border rounded px-1.5 flex items-center text-[6px] text-stone-300" style={{ borderColor: themes[selectedThemeIndex]?.palette.border || "#e7e5e4" }}>Password</div>
                        </div>
                        <div
                          className="h-5 rounded font-bold flex items-center justify-center shadow-sm text-[8px]"
                          style={{ backgroundColor: themes[selectedThemeIndex]?.palette.primary, color: '#ffffff' }}
                        >
                          Sign In
                        </div>
                      </div>
                    )}
                  </div>
                </div>


                <div className="pt-2 pb-8">
                  {!isThemeReadOnly ? (
                    <button
                      type="button"
                      onClick={() => {
                        generateProject(
                          activeChat.id, 
                          blueprint.name, 
                          activeChat.category || "General", 
                          themes[selectedThemeIndex]?.name || "default", 
                          blueprint, 
                          themes[selectedThemeIndex]?.palette || {},
                          false,
                          activeChat.selected_project?.generation_type || "full_stack"
                        );
                        setCurrentStep(3);
                      }}
                      disabled={isGeneratingProject}
                      className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-indigo-950 via-indigo-900 to-amber-500 hover:from-indigo-900 hover:via-indigo-900 hover:to-amber-500 text-white font-bold py-3.5 rounded-2xl shadow-lg shadow-indigo-200 transition-all hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50 cursor-pointer text-xs"
                    >
                      🚀 Confirm Theme & Start Project Build
                    </button>
                  ) : (
                    <div className="w-full py-3.5 bg-stone-100 border border-stone-200 text-stone-400 rounded-2xl text-center text-xs font-bold">
                      ✓ Theme Configured & Built
                    </div>
                  )}
                  <p className="text-center text-[10px] text-stone-400 mt-2.5 leading-relaxed max-w-xs mx-auto">
                    Sarthi will compile the monorepo codebase styled with the {themes[selectedThemeIndex]?.name || "selected"} theme.
                  </p>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    );
  };

  // --- STEP 3: SPECIFICATIONS STEP ---
  const renderSpecificationsStep = () => {
    if (isGeneratingProject && !activeProj) {
      return (
        <div className="flex-1 flex flex-col items-center justify-center p-8 bg-transparent overflow-y-auto">
          <motion.div
            animate={{
              y: [0, -10, 0]
            }}
            transition={{
              duration: 2.5,
              repeat: Infinity,
              ease: "easeInOut"
            }}
            className="mb-8 flex items-center justify-center drop-shadow-2xl"
          >
            <SarthiLogo className="text-6xl" />
          </motion.div>
          <h3 className="text-xs font-bold text-stone-800 uppercase tracking-wider text-center">Generating Specifications...</h3>
          <p className="text-center text-[10px] text-stone-500 mt-2.5 max-w-xs leading-relaxed">
            Sarthi is analyzing your requirements to compile the Product, Market, and Technical Requirements Documents.
          </p>
        </div>
      );
    }

    if (!activeProj) return null;

    return (
      <div className="flex-1 flex overflow-hidden bg-transparent">
        {/* Left Content Area (Specs & Plan Docs) */}
        <AnimatePresence initial={false}>
          {showSpecsDocs && (
            <motion.div
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: "calc(100% - 340px)", opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ duration: 0.3, ease: "easeInOut" }}
              className="flex-1 flex flex-col overflow-hidden border-r border-stone-200/60"
            >
              {/* Tab Navigation */}
              <div className="px-6 py-4 bg-white/20 backdrop-blur-md border-b border-stone-200/60 flex items-center justify-between">
                <div className="flex gap-2">
                  {(["trd"] as const).map((tab) => (
                    <button
                      key={tab}
                      onClick={() => setActiveDocTab(tab)}
                      className={`px-4 py-2 rounded-xl text-xs font-semibold tracking-wide uppercase transition-all cursor-pointer ${
                        activeDocTab === tab
                          ? "bg-indigo-950 text-white shadow-sm"
                          : "bg-stone-100 hover:bg-stone-200 text-stone-600"
                      }`}
                    >
                      {tab.toUpperCase()} Spec
                    </button>
                  ))}
                  {activeProj.hitl_enabled !== false && (
                    <button
                      onClick={() => setActiveDocTab("plan")}
                      className={`px-4 py-2 rounded-xl text-xs font-semibold tracking-wide uppercase transition-all cursor-pointer ${
                        activeDocTab === "plan"
                          ? "bg-indigo-950 text-white shadow-sm"
                          : "bg-stone-100 hover:bg-stone-200 text-stone-600"
                      }`}
                    >
                      Implementation Plan
                    </button>
                  )}
                </div>
                
                {/* Hide Button in the tab bar */}
                <button
                  onClick={() => setShowSpecsDocs(false)}
                  className="p-1.5 rounded-lg hover:bg-stone-200/50 text-stone-500 transition-colors cursor-pointer"
                  title="Hide Documents"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Document Text View */}
              <div className="flex-1 overflow-y-auto p-8 bg-transparent">
                <div className="w-full max-w-3xl mx-auto bg-stone-50 p-10 rounded-3xl border border-stone-200/60 shadow-sm text-left">
                  {activeDocTab === "trd" && (
                    <MarkdownRenderer text={activeProj.trd || "# Technical Requirements\nNo TRD generated."} />
                  )}
                  {activeDocTab === "plan" && (
                    <div className="space-y-4 text-left">
                      <div className="flex justify-between items-center border-b border-stone-200 pb-3 mb-3">
                        <h4 className="text-xs font-bold text-indigo-950 uppercase tracking-wider">File Modification Blueprint</h4>
                        {activeProj.status === "waiting_approval" && (
                          <button
                            onClick={() => setIsEditingPlan(!isEditingPlan)}
                            className="px-3 py-1 rounded-lg text-[10px] font-semibold bg-stone-200 hover:bg-stone-300 text-stone-700 transition-all cursor-pointer"
                          >
                            {isEditingPlan ? "Preview Mode" : "Edit Plan"}
                          </button>
                        )}
                      </div>
                      {activeProj.status === "documents_ready" && !activeProj.implementation_plan?.plan_markdown ? (
                        <div className="py-6 space-y-4">
                          <h3 className="text-sm font-bold text-indigo-950">⏩ Direct Compilation Enabled</h3>
                          <p className="text-xs text-stone-500 leading-relaxed">
                            Planning review is disabled. Sarthi will compile the production codebase directly when you click Proceed to Build.
                          </p>
                        </div>
                      ) : isEditingPlan ? (
                        <textarea
                          value={editedPlanMarkdown}
                          onChange={(e) => setEditedPlanMarkdown(e.target.value)}
                          className="w-full h-[500px] p-4 font-mono text-xs text-stone-855 bg-white border border-stone-300 rounded-2xl focus:outline-none focus:ring-1 focus:ring-indigo-950 resize-y"
                        />
                      ) : (
                        <MarkdownRenderer text={editedPlanMarkdown || activeProj.implementation_plan?.plan_markdown || "# Implementation Plan\n*No plan details available.*"} />
                      )}
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Right Action Sidebar */}
        <div className="w-85 bg-white/10 backdrop-blur-md p-6 pb-24 flex flex-col justify-between shrink-0 overflow-y-auto border-l border-stone-200/60">
          <div className="space-y-6">
            <div>
              <h3 className="text-xs font-bold text-stone-855 uppercase tracking-wider">
                {activeProj.status === "waiting_approval" ? "Review & Approve Plan" : "Specifications Review"}
              </h3>
              <p className="text-[11px] text-stone-500 mt-1.5 leading-relaxed font-medium">
                {activeProj.status === "waiting_approval" 
                  ? "Review the proposed files alterations on the left. You can modify the plan details, then approve it to compile the codebase."
                  : "Sarthi has generated complete Product, Market, and Technical specifications. Please review them before proceeding to the code generation phase."
                }
              </p>
            </div>

            <div className="p-4 rounded-2xl bg-indigo-50/40 border border-indigo-100/50 space-y-3">
              <span className="text-[10px] font-bold text-indigo-950 uppercase tracking-wider block">Prototype Tech Stack</span>
              <div className="flex items-center gap-2 text-stone-750">
                <FileCode className="w-4 h-4 text-amber-500 font-bold" />
                <span className="text-xs font-semibold">{activeProj.blueprint?.tech_stack || "React + FastAPI + MongoDB"}</span>
              </div>
              <p className="text-[10px] text-stone-550 leading-normal font-medium">
                Monorepo structure with automated setup and configuration compiled cleanly by Sarthi's agent mesh.
              </p>
            </div>

            {activeProj.status === "waiting_approval" && (
              <div className="p-4 rounded-2xl bg-stone-50 border border-stone-200 space-y-3 text-left">
                <div className="flex justify-between items-center">
                  <span className="text-[10px] font-bold text-stone-500 uppercase tracking-wider">Planning Constraints</span>
                  <span className="text-[8px] bg-amber-500/10 text-amber-700 px-1.5 py-0.5 rounded font-bold uppercase">HITL Guard</span>
                </div>
                <div className="flex items-start gap-2">
                  <input
                    type="checkbox"
                    id="hitl-toggle-inner"
                    checked={activeProj.hitl_enabled !== false}
                    onChange={(e) => updateProjectHitl(activeProj.id, e.target.checked)}
                    className="mt-0.5 rounded border-stone-300 text-indigo-950 focus:ring-indigo-950 w-3.5 h-3.5 cursor-pointer"
                  />
                  <label htmlFor="hitl-toggle-inner" className="text-[10px] text-stone-500 leading-tight font-medium cursor-pointer">
                    Enable Human-in-the-Loop review guards for codebase generation steps
                  </label>
                </div>
              </div>
            )}
          </div>

          <div className="pt-4 border-t border-stone-150">
            {activeProj.status === "waiting_approval" ? (
              <button
                type="button"
                onClick={() => approveProjectPlan(activeProj.id, activeProj.chat_id, editedPlanMarkdown)}
                disabled={isGeneratingProject}
                className="w-full flex items-center justify-center gap-1.5 py-3 rounded-2xl bg-indigo-950 hover:bg-indigo-900 text-amber-500 font-bold text-xs shadow-md transition-all disabled:opacity-50 cursor-pointer"
              >
                🚀 Approve Plan & Compile Codebase
              </button>
            ) : (
              <button
                type="button"
                onClick={() => compileProjectCodebase(activeProj.id, activeProj.chat_id)}
                disabled={isGeneratingProject}
                className="w-full flex items-center justify-center gap-1.5 py-3 rounded-2xl bg-indigo-950 hover:bg-indigo-900 text-amber-500 font-bold text-xs shadow-md transition-all disabled:opacity-50 cursor-pointer"
              >
                🚀 Proceed to Compile Codebase
              </button>
            )}
          </div>
        </div>
      </div>
    );
  };

  // --- STEP 4: COMPILATION STEP ---
  const renderCompilationStep = () => {
    if (!activeProj) return null;

    if (activeProj.status === "failed") {
      return (
        <div className="flex-1 flex flex-col items-center justify-center p-8 bg-transparent">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="max-w-md w-full bg-slate-950/45 backdrop-blur-2xl p-8 rounded-3xl border border-rose-500/30 shadow-2xl relative overflow-hidden text-center space-y-6 shadow-rose-950/25"
          >
            <div className="absolute top-0 inset-x-0 h-1 bg-rose-500" />
            <div className="w-16 h-16 bg-rose-950/30 border border-rose-500/30 rounded-full flex items-center justify-center mx-auto text-rose-550">
              <AlertTriangle className="w-8 h-8 text-rose-500" />
            </div>
            <div className="space-y-2">
              <h3 className="text-base font-bold text-slate-100">Compilation Failed</h3>
              <p className="text-xs text-slate-400 leading-relaxed font-medium">
                An error occurred during codebase generation. Retrying the compile process might resolve intermittent network issues.
              </p>
            </div>
            
            <motion.button
              onClick={() => compileProjectCodebase(activeProj.id, activeProj.chat_id)}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="w-full flex items-center justify-center gap-2 py-3.5 rounded-2xl bg-indigo-950 hover:bg-indigo-900 border border-indigo-500/20 text-white font-semibold text-xs transition-colors cursor-pointer"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Retry Build Codebase</span>
            </motion.button>
          </motion.div>
        </div>
      );
    }

    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 overflow-y-auto bg-transparent">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          className="max-w-xl w-full bg-white/70 backdrop-blur-2xl p-8 rounded-3xl border border-indigo-100 shadow-xl shadow-indigo-950/5 relative overflow-hidden flex flex-col items-center"
        >
          <div className="absolute top-0 inset-x-0 h-1.5 bg-gradient-to-r from-indigo-500 via-amber-400 to-indigo-600" />

          {/* Header */}
          <div className="mb-6 flex flex-col items-center select-none">
            <div className="w-10 h-10 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center mb-3 text-indigo-600">
              <Cpu className="w-5 h-5 animate-pulse" />
            </div>
            <span className="text-[10px] uppercase font-bold tracking-widest text-amber-500">Sarthi Engine</span>
            <h3 className="text-base font-bold font-display text-indigo-950 mt-1 select-text">Synthesizing Codebase</h3>
            <div className="mt-1 flex items-center gap-1.5 text-[9px] font-bold uppercase tracking-wider text-stone-500">
              <Database className="w-3 h-3 text-indigo-400" />
              <span>{partnerTrack} MCP + Gemini Agents</span>
            </div>
          </div>

          {/* Clean Linear Progress bar */}
          <div className="w-full space-y-3 mb-6 bg-white p-5 rounded-2xl border border-stone-200/60 shadow-sm">
            <div className="flex justify-between items-end mb-1 select-none">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-stone-400 block mb-0.5">Pipeline Status</span>
                <span className="font-black text-indigo-950 text-sm select-text">{activeProj.progress >= 100 ? "Zipping Assets" : activeProj.step}</span>
              </div>
              <div className="flex items-baseline">
                <motion.span className="text-xl font-black font-display tracking-tight text-amber-500">
                  {progressRounded}
                </motion.span>
                <span className="text-xl font-black font-display tracking-tight text-amber-500">%</span>
              </div>
            </div>
            
            <div className="h-3 w-full bg-stone-100/80 rounded-full overflow-hidden border border-stone-200/50 shadow-inner">
              <motion.div
                className="h-full rounded-full bg-gradient-to-r from-indigo-900 to-amber-500 relative"
                style={{ width: `${Math.min(100, activeProj.progress)}%` }}
                transition={{ duration: 0.5, ease: "easeOut" }}
              >
                {/* Subtle shimmer effect inside the bar */}
                <div className="absolute inset-0 w-full h-full bg-gradient-to-r from-transparent via-white/20 to-transparent animate-pulse" />
              </motion.div>
            </div>
          </div>

          {/* Active Agent Status Badge */}
          <div className="w-full bg-indigo-50/50 border border-indigo-100 rounded-2xl p-4 text-left mb-6 select-none">
            <div className="flex items-center gap-2 text-indigo-600 mb-1.5">
              {activeProj.status === "paused" ? (
                <Pause className="w-3.5 h-3.5 text-amber-550" />
              ) : (
                <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-550" />
              )}
              <span className="text-[9px] uppercase font-bold tracking-wider">
                {activeProj.status === "paused" ? "Vyuh Process Paused" : "Active Vyuh Process"}
              </span>
            </div>
            <div className="text-[10px] text-stone-600 leading-normal font-semibold select-text">
              {activeProj.status === "paused" 
                ? "Generation paused by user. Click Resume to continue the synthesis pipeline."
                : (agentDescriptions[agentPipeline[currentAgentIdx]] || "Orchestrating codebase components...")}
            </div>
          </div>

          {/* Controls Panel */}
          <div className="w-full flex items-center justify-center gap-3 mb-6">
            {activeProj.status === "paused" ? (
              <motion.button
                onClick={() => resumeProjectCodebase(activeProj.id)}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="flex-1 flex items-center justify-center gap-2 py-3 rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-700 hover:to-teal-600 text-white font-bold text-xs shadow-md shadow-emerald-500/10 cursor-pointer transition-all border border-emerald-500/20"
              >
                <Play className="w-3.5 h-3.5" />
                <span>Resume Generation</span>
              </motion.button>
            ) : (
              <motion.button
                onClick={() => pauseProjectCodebase(activeProj.id)}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="flex-1 flex items-center justify-center gap-2 py-3 rounded-2xl bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white font-bold text-xs shadow-md shadow-orange-500/10 cursor-pointer transition-all border border-orange-500/20"
              >
                <Pause className="w-3.5 h-3.5" />
                <span>Pause Generation</span>
              </motion.button>
            )}
          </div>

          {/* Timeline Milestones */}
          <div className="w-full border-t border-stone-100 pt-5 text-left select-none">
            <h4 className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-4 px-1">Pipeline Milestones</h4>
            <div className="space-y-4">
              {[
                {
                  id: 1,
                  title: "Architecture & DB Design",
                  desc: "TRD, collection schemas & indexing mapping",
                  isActive: activeProj.progress < 25,
                  isCompleted: activeProj.progress >= 25,
                  icon: Database
                },
                {
                  id: 2,
                  title: "Codebase Synthesis",
                  desc: "FastAPI controllers, Next.js page views & Zustand stores",
                  isActive: activeProj.progress >= 25 && activeProj.progress < 70,
                  isCompleted: activeProj.progress >= 70,
                  icon: Cpu
                },
                {
                  id: 3,
                  title: "Integration & Testing",
                  desc: "System API links, Auth hooks & compiler check runs",
                  isActive: activeProj.progress >= 70 && activeProj.progress < 90,
                  isCompleted: activeProj.progress >= 90,
                  icon: RefreshCw
                },
                {
                  id: 4,
                  title: "Monorepo Packaging",
                  desc: "Production build compression & assets zip export",
                  isActive: activeProj.progress >= 90,
                  isCompleted: activeProj.status === "completed" || activeProj.progress >= 100,
                  icon: FolderGit2
                }
              ].map((stage) => {
                const StageIcon = stage.icon;
                let statusColor = "text-stone-400 border-stone-200 bg-stone-50";
                let textColor = "text-stone-500";
                let descColor = "text-stone-400";
                let indicator = <Lock className="w-3.5 h-3.5" />;

                if (stage.isCompleted) {
                  statusColor = "text-emerald-600 border-emerald-200 bg-emerald-50 shadow-sm";
                  textColor = "text-stone-800 font-bold";
                  descColor = "text-stone-500";
                  indicator = <CheckCircle2 className="w-3.5 h-3.5" />;
                } else if (stage.isActive) {
                  statusColor = "text-indigo-600 border-indigo-200 bg-indigo-50 shadow-md";
                  textColor = "text-indigo-950 font-bold";
                  descColor = "text-stone-600";
                  indicator = <Loader2 className="w-3.5 h-3.5 animate-spin" />;
                }

                return (
                  <div key={stage.id} className="flex items-start gap-4">
                    <div className={`w-8 h-8 rounded-lg border flex items-center justify-center shrink-0 transition-all ${statusColor}`}>
                      <StageIcon className="w-4 h-4" />
                    </div>
                    <div className="flex-1 min-w-0 select-text">
                      <h5 className={`text-xs ${textColor} leading-none flex items-center gap-1.5`}>
                        <span>{stage.title}</span>
                        <span className="shrink-0">{indicator}</span>
                      </h5>
                      <p className={`text-[10px] ${descColor} mt-1 leading-normal`}>{stage.desc}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Sarthi Live Compilation Log Console */}
          <div className="w-full bg-stone-950 text-stone-200 font-mono text-[10px] rounded-2xl border border-stone-850 shadow-2xl p-4 mt-6 h-60 flex flex-col relative overflow-hidden text-left">
            {/* Terminal Header */}
            <div className="flex items-center justify-between border-b border-stone-800/80 pb-2 mb-2 shrink-0 select-none">
              <div className="flex items-center gap-2">
                <div className="flex gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-rose-500/80" />
                  <span className="w-2 h-2 rounded-full bg-amber-500/80" />
                  <span className="w-2 h-2 rounded-full bg-emerald-500/80" />
                </div>
                <span className="text-[9px] uppercase font-bold tracking-wider text-stone-500 ml-1.5">Sarthi Live Compiler</span>
              </div>
              <div className="text-[8.5px] text-stone-600 font-bold uppercase tracking-wider">
                WebSocket Stream
              </div>
            </div>

            {/* Terminal Body */}
            <div className="flex-1 overflow-y-auto space-y-2 pr-1 custom-scrollbar scroll-smooth">
              {projLogs.map((log, i) => {
                const level = (log.level || "INFO").toUpperCase();
                let badgeBg = "bg-stone-850 text-stone-400 border border-stone-850";
                let messageColor = "text-stone-300";

                if (level === "SUCCESS") {
                  badgeBg = "bg-emerald-950/40 text-emerald-400 border border-emerald-900/30";
                  messageColor = "text-emerald-100/90 font-medium";
                } else if (level === "WARNING") {
                  badgeBg = "bg-amber-950/40 text-amber-400 border border-amber-900/30";
                  messageColor = "text-amber-100/90 font-medium";
                } else if (level === "HEAL") {
                  badgeBg = "bg-cyan-950/40 text-cyan-400 border border-cyan-900/30";
                  messageColor = "text-cyan-100/95 font-semibold";
                } else if (level === "ERROR") {
                  badgeBg = "bg-rose-950/40 text-rose-400 border border-rose-900/30";
                  messageColor = "text-rose-100/95 font-semibold";
                } else if (level === "INFO") {
                  badgeBg = "bg-indigo-950/40 text-indigo-400 border border-indigo-900/30";
                }

                return (
                  <div key={i} className="flex items-start gap-2 leading-normal">
                    <span className="text-stone-600 shrink-0 select-none font-bold">{log.timestamp || "00:00:00"}</span>
                    <span className={`px-1.5 py-0.5 rounded-[4px] text-[8px] font-black tracking-wide uppercase shrink-0 ${badgeBg}`}>
                      {level}
                    </span>
                    <span className="text-stone-500 shrink-0 font-semibold select-none">
                      [{log.sender ? log.sender.split(".").pop() : "System"}]
                    </span>
                    <span className={`flex-1 select-text whitespace-pre-wrap break-all ${messageColor}`}>
                      {log.message}
                    </span>
                  </div>
                );
              })}

              {projLogs.length === 0 && (
                <div className="flex-1 h-36 flex flex-col items-center justify-center text-stone-600 select-none animate-pulse space-y-1.5">
                  <span className="text-[9px] uppercase font-bold tracking-widest text-stone-500">Awaiting stream...</span>
                </div>
              )}
              <div ref={terminalEndRef} />
            </div>
          </div>
        </motion.div>
      </div>
    );
  };

  // --- STEP 5: CODEBASE STEP ---
  const renderCodebaseStep = () => {
    if (!activeProj || activeProj.status !== "completed") return null;

    return (
      <div className="flex-1 flex overflow-hidden">
        {/* Left File Tree Pane */}
        <AnimatePresence initial={false}>
          {showFilesPane && (
            <motion.div
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 256, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ duration: 0.3, ease: "easeInOut" }}
              className="border-r border-stone-200/60 bg-white/30 backdrop-blur-md flex flex-col shrink-0 overflow-hidden"
            >
              <div className="p-3.5 border-b border-stone-200/60 shrink-0 w-64 bg-stone-50/40">
                <div className="flex bg-stone-100 p-0.5 rounded-lg">
                  <button
                    onClick={() => setCompletedTab("files")}
                    className={`flex-1 py-1 rounded-md text-[9px] font-bold uppercase tracking-wider transition-all cursor-pointer ${
                      completedTab === "files" ? "bg-indigo-950 text-white shadow-sm" : "text-stone-400 hover:text-stone-700"
                    }`}
                  >
                    Files
                  </button>
                  <button
                    onClick={() => setCompletedTab("vyuh")}
                    className={`flex-1 py-1 rounded-md text-[9px] font-bold uppercase tracking-wider transition-all cursor-pointer ${
                      completedTab === "vyuh" ? "bg-indigo-950 text-white shadow-sm" : "text-stone-400 hover:text-stone-700"
                    }`}
                  >
                    Vyuh Map
                  </button>
                </div>
              </div>
              <div className="flex-1 overflow-y-auto p-3 space-y-1 select-none w-64">
                {completedTab === "files" ? (
                  (() => {
                    const filesToRender = [...(activeProj.codebase || [])];
                    if (activeProj.mcp_evidence && !filesToRender.some((file) => file.path === "sarthi-internal/MCP_EVIDENCE.json")) {
                      filesToRender.unshift({
                        name: "MCP_EVIDENCE.json",
                        path: "sarthi-internal/MCP_EVIDENCE.json",
                        language: "json",
                        content: JSON.stringify(activeProj.mcp_evidence, null, 2),
                      });
                    }
                    if (activeProj.hackathon_metadata && !filesToRender.some((file) => file.path === "sarthi-internal/HACKATHON_METADATA.json")) {
                      filesToRender.unshift({
                        name: "HACKATHON_METADATA.json",
                        path: "sarthi-internal/HACKATHON_METADATA.json",
                        language: "json",
                        content: JSON.stringify(activeProj.hackathon_metadata, null, 2),
                      });
                    }
                    if (activeProj.prd) {
                      filesToRender.unshift({
                        name: "Product Requirement Document (PRD).md",
                        path: "PRD.md",
                        language: "markdown",
                        content: activeProj.prd,
                      });
                    }
                    if (activeProj.build_compilation) {
                      filesToRender.unshift({
                        name: "AI_BuildCompilation.json",
                        path: "sarthi-internal/AI_BuildCompilation.json",
                        language: "json",
                        content: JSON.stringify(activeProj.build_compilation, null, 2),
                      });
                    }
                    if (activeProj.integration_generation) {
                      filesToRender.unshift({
                        name: "AI_IntegrationGeneration.json",
                        path: "sarthi-internal/AI_IntegrationGeneration.json",
                        language: "json",
                        content: JSON.stringify(activeProj.integration_generation, null, 2),
                      });
                    }
                    if (activeProj.state_implementation) {
                      filesToRender.unshift({
                        name: "AI_StateImplementation.json",
                        path: "sarthi-internal/AI_StateImplementation.json",
                        language: "json",
                        content: JSON.stringify(activeProj.state_implementation, null, 2),
                      });
                    }
                    if (activeProj.ui_component_generation) {
                      filesToRender.unshift({
                        name: "AI_UIComponentGeneration.json",
                        path: "sarthi-internal/AI_UIComponentGeneration.json",
                        language: "json",
                        content: JSON.stringify(activeProj.ui_component_generation, null, 2),
                      });
                    }
                    if (activeProj.frontend_code_generation) {
                      filesToRender.unshift({
                        name: "AI_FrontendCodeGeneration.json",
                        path: "sarthi-internal/AI_FrontendCodeGeneration.json",
                        language: "json",
                        content: JSON.stringify(activeProj.frontend_code_generation, null, 2),
                      });
                    }
                    if (activeProj.api_implementation) {
                      filesToRender.unshift({
                        name: "AI_APIImplementation.json",
                        path: "sarthi-internal/AI_APIImplementation.json",
                        language: "json",
                        content: JSON.stringify(activeProj.api_implementation, null, 2),
                      });
                    }
                    if (activeProj.backend_code_generation) {
                      filesToRender.unshift({
                        name: "AI_BackendCodeGeneration.json",
                        path: "sarthi-internal/AI_BackendCodeGeneration.json",
                        language: "json",
                        content: JSON.stringify(activeProj.backend_code_generation, null, 2),
                      });
                    }
                    if (activeProj.database_model_generation) {
                      filesToRender.unshift({
                        name: "AI_DatabaseModelGeneration.json",
                        path: "sarthi-internal/AI_DatabaseModelGeneration.json",
                        language: "json",
                        content: JSON.stringify(activeProj.database_model_generation, null, 2),
                      });
                    }
                    if (activeProj.code_generation_plan) {
                      filesToRender.unshift({
                        name: "AI_CodeGenerationPlanning.json",
                        path: "sarthi-internal/AI_CodeGenerationPlanning.json",
                        language: "json",
                        content: JSON.stringify(activeProj.code_generation_plan, null, 2),
                      });
                    }
                    if (activeProj.devops_architecture) {
                      filesToRender.unshift({
                        name: "AI_DevOpsArchitecture.json",
                        path: "sarthi-internal/AI_DevOpsArchitecture.json",
                        language: "json",
                        content: JSON.stringify(activeProj.devops_architecture, null, 2),
                      });
                    }
                    if (activeProj.realtime_architecture) {
                      filesToRender.unshift({
                        name: "AI_RealtimeArchitecture.json",
                        path: "sarthi-internal/AI_RealtimeArchitecture.json",
                        language: "json",
                        content: JSON.stringify(activeProj.realtime_architecture, null, 2),
                      });
                    }
                    if (activeProj.security_architecture) {
                      filesToRender.unshift({
                        name: "AI_SecurityArchitecture.json",
                        path: "sarthi-internal/AI_SecurityArchitecture.json",
                        language: "json",
                        content: JSON.stringify(activeProj.security_architecture, null, 2),
                      });
                    }
                    if (activeProj.auth_architecture) {
                      filesToRender.unshift({
                        name: "AI_AuthArchitecture.json",
                        path: "sarthi-internal/AI_AuthArchitecture.json",
                        language: "json",
                        content: JSON.stringify(activeProj.auth_architecture, null, 2),
                      });
                    }
                    if (activeProj.api_contract_design) {
                      filesToRender.unshift({
                        name: "AI_APIContractDesign.json",
                        path: "sarthi-internal/AI_APIContractDesign.json",
                        language: "json",
                        content: JSON.stringify(activeProj.api_contract_design, null, 2),
                      });
                    }
                    if (activeProj.database_architecture) {
                      filesToRender.unshift({
                        name: "AI_DatabaseArchitecture.json",
                        path: "sarthi-internal/AI_DatabaseArchitecture.json",
                        language: "json",
                        content: JSON.stringify(activeProj.database_architecture, null, 2),
                      });
                    }
                    if (activeProj.blueprint_planner) {
                      filesToRender.unshift({
                        name: "AI_BlueprintPlanner.json",
                        path: "sarthi-internal/AI_BlueprintPlanner.json",
                        language: "json",
                        content: JSON.stringify(activeProj.blueprint_planner, null, 2),
                      });
                    }
                    if (activeProj.requirement_analyzer) {
                      filesToRender.unshift({
                        name: "AI_RequirementAnalyzer.json",
                        path: "sarthi-internal/AI_RequirementAnalyzer.json",
                        language: "json",
                        content: JSON.stringify(activeProj.requirement_analyzer, null, 2),
                      });
                    }

                    // Helper to group by folder
                    const renderFileTree = (files: typeof filesToRender) => {
                      const tree: any = {};
                      files.forEach((file) => {
                        const parts = file.path.split("/");
                        let current = tree;
                        parts.forEach((part, index) => {
                          if (index === parts.length - 1) {
                            current[part] = file;
                          } else {
                            if (!current[part]) current[part] = {};
                            current = current[part];
                          }
                        });
                      });

                      const renderNode = (node: any, depth = 0, pathPrefix = "") => {
                        return Object.keys(node).sort().map((key) => {
                          const val = node[key];
                          const isFile = val && val.content !== undefined;
                          const currentPath = pathPrefix ? `${pathPrefix}/${key}` : key;
                          
                          if (isFile) {
                            const isSel = selectedFile?.path === val.path;
                            return (
                              <button
                                key={val.path}
                                onClick={() => setSelectedFile(val)}
                                className={`w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-[10px] font-mono transition-all text-left truncate cursor-pointer ${
                                  isSel ? "bg-indigo-950 text-white font-bold" : "text-stone-600 hover:bg-stone-150"
                                }`}
                                style={{ paddingLeft: `${depth * 10 + 10}px` }}
                              >
                                <FileCode className={`w-3.5 h-3.5 shrink-0 ${isSel ? "text-amber-500" : "text-stone-400"}`} />
                                <span className="truncate">{val.name}</span>
                              </button>
                            );
                          } else {
                            return (
                              <div key={currentPath} className="space-y-0.5">
                                <div
                                  className="flex items-center gap-2 px-2.5 py-1 text-[9px] uppercase tracking-wider font-extrabold text-stone-400 select-none"
                                  style={{ paddingLeft: `${depth * 10 + 10}px` }}
                                >
                                  <span className="truncate">{key}</span>
                                </div>
                                {renderNode(val, depth + 1, currentPath)}
                              </div>
                            );
                          }
                        });
                      };

                      return renderNode(tree);
                    };

                    return renderFileTree(filesToRender);
                  })()
                ) : (
                  <div className="space-y-4">
                    <div className="flex justify-between items-center px-1">
                      <span className="text-[10px] uppercase font-black tracking-wider text-indigo-950">Architecture Vyuh Map</span>
                      <span className="text-[8px] bg-emerald-500/10 text-emerald-700 px-1.5 py-0.5 rounded font-bold uppercase font-mono">compiled</span>
                    </div>
                    <div className="p-3 bg-stone-50 rounded-2xl border border-stone-200/50 space-y-4 min-h-[400px]">
                      <div className="flex flex-col gap-2.5">
                        {(hackathonMetadata.sub_agent_pipeline || []).map((agent: any, idx: number) => {
                          const isHovered = hoveredVyuhNode === agent.agent_name;
                          const isSelected = selectedVyuhNode?.agent_name === agent.agent_name;
                          
                          return (
                            <button
                              key={idx}
                              onClick={() => setSelectedVyuhNode(isSelected ? null : agent)}
                              onMouseEnter={() => setHoveredVyuhNode(agent.agent_name)}
                              onMouseLeave={() => setHoveredVyuhNode(null)}
                              className={`w-full text-left p-2.5 rounded-xl border transition-all cursor-pointer relative overflow-hidden ${
                                isSelected
                                  ? "border-amber-500 bg-white shadow"
                                  : isHovered
                                  ? "border-stone-300 bg-stone-50/50"
                                  : "border-stone-150 bg-stone-50/20"
                              }`}
                            >
                              <div className="flex justify-between items-center">
                                <span className="text-[9px] font-bold text-stone-850 font-mono">{agent.agent_name}</span>
                                <span
                                  className="w-1.5 h-1.5 rounded-full"
                                  style={{ backgroundColor: themes[selectedThemeIndex]?.palette.primary || "#6366f1" }}
                                />
                              </div>
                              <p className="text-[7.5px] text-stone-450 mt-1 leading-normal font-semibold">{agent.status}</p>
                              
                              {isSelected && (
                                <motion.div
                                  initial={{ opacity: 0, height: 0 }}
                                  animate={{ opacity: 1, height: "auto" }}
                                  className="mt-2.5 pt-2 border-t border-stone-100 text-[8px] text-stone-500 space-y-1.5 leading-normal"
                                >
                                  <div>
                                    <span className="font-bold text-stone-700">Modified Files:</span>
                                    <div className="flex flex-wrap gap-1 mt-1">
                                      {(agent.files_touched || []).map((file: string, fidx: number) => (
                                        <span key={fidx} className="px-1.5 py-0.5 bg-stone-100 border border-stone-200 rounded font-mono text-[7px] text-stone-600">
                                          {file}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                </motion.div>
                              )}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Right Code Display Area */}
        <div className="flex-1 flex flex-col bg-stone-50 overflow-hidden relative">
          {githubResult && (
            <div className={`absolute top-4 left-1/2 -translate-x-1/2 z-50 flex items-center gap-3 px-4 py-3 rounded-2xl shadow-xl text-xs font-semibold border bg-indigo-50 border-indigo-200 text-indigo-950`}>
              <CheckCircle2 className="w-4 h-4 shrink-0 text-indigo-700" />
              <span>Pushed to GitHub!</span>
              <a href={githubResult.url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 underline underline-offset-2 hover:opacity-75">
                View repo <ExternalLink className="w-3 h-3" />
              </a>
              <button onClick={() => setGithubResult(null)} className="ml-2 p-0.5 rounded hover:bg-black/10 cursor-pointer">
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

          {selectedFile ? (
            <div className="flex-1 flex flex-col overflow-hidden">
              {/* File title & Actions */}
              <div className="px-6 py-3 border-b border-stone-200/60 flex justify-between items-center bg-white/20 backdrop-blur-md shrink-0 select-none">
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setShowFilesPane(!showFilesPane)}
                    className="p-1.5 rounded-md hover:bg-stone-200/50 text-stone-500 transition-colors"
                    title="Toggle Files Pane"
                  >
                    <PanelLeft className="w-4 h-4" />
                  </button>
                  <span className="text-xs font-mono font-bold text-stone-500">
                    {selectedFile.path}
                  </span>
                </div>
                <button
                  onClick={handleCopy}
                  className="inline-flex items-center gap-1 text-[10px] font-semibold text-stone-500 hover:text-stone-850 bg-stone-50 border border-stone-200 rounded-lg px-2.5 py-1.5 shadow-sm transition-all hover:bg-stone-50 cursor-pointer"
                >
                  {copied ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-amber-500" />
                      <span>Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span>Copy code</span>
                    </>
                  )}
                </button>
              </div>
              {/* Code Block Container or Markdown Viewer */}
              {selectedFile.language === "markdown" ? (
                <div className="flex-1 overflow-y-auto p-8 bg-transparent text-stone-800 select-text leading-relaxed border-b border-transparent transition-colors duration-300">
                  <div className="max-w-3xl mx-auto bg-white border border-stone-200/80 rounded-2xl p-8 md:p-10 shadow-xl drop-shadow-sm">
                    <MarkdownRenderer text={selectedFile.content} />
                  </div>
                </div>
              ) : (
                <div className="flex-1 overflow-auto p-6 font-mono text-xs text-stone-800 leading-relaxed bg-white/50 backdrop-blur-sm select-text select-all border-b border-transparent">
                  <pre className="overflow-x-auto whitespace-pre-wrap md:whitespace-pre">
                    {selectedFile.content.split("\n").map((line, i) => (
                      <div key={i} className="table-row">
                        <span className="table-cell text-right pr-4 text-stone-300 select-none text-[10px] w-6">
                          {i + 1}
                        </span>
                        <span className="table-cell text-stone-850">{line}</span>
                      </div>
                    ))}
                  </pre>
                </div>
              )}
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center p-8">
              <div className="text-center text-stone-400">
                <FileCode className="w-8 h-8 mx-auto mb-2 text-stone-300" />
                <p className="text-xs">Select a file from the file explorer on the left.</p>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  const stepperSteps = [
    { id: 1, label: "Blueprint", icon: FileEdit },
    { id: 2, label: "Theme", icon: Palette },
    { id: 3, label: "Compilation", icon: Cpu },
    { id: 4, label: "Codebase", icon: FolderGit2 }
  ];

  return (
    <div className="flex-1 flex flex-col h-full bg-transparent overflow-hidden transition-colors duration-300 relative">
      {showCelebration && <DivineCelebration onComplete={() => setShowCelebration(false)} />}

      {/* Merged Compact Header & Stepper Bar */}
      <div className="h-14 border-b border-stone-200 bg-white/40 backdrop-blur-md flex items-center justify-between gap-4 px-6 shrink-0 shadow-sm relative z-20 select-none">
        {/* Left: Project Info */}
        <div className="flex items-center gap-3 min-w-0 max-w-[200px] sm:max-w-[250px] md:max-w-[300px]">
          <div className="p-1.5 rounded-lg bg-indigo-50 text-indigo-950 border border-indigo-100/50 shrink-0">
            <CategoryIcon category={activeProj?.category || activeChat?.category || "General"} className="w-4 h-4" />
          </div>
          <div className="overflow-hidden leading-tight">
            <h2 className="text-xs font-bold font-display text-stone-850 truncate">
              {activeProj?.name || activeChat.selected_project?.name || "Design Blueprint"}
            </h2>
            <p className="text-[9px] text-stone-400 capitalize mt-0.5 truncate">
              {activeProj?.category || activeChat?.category || "General"}
            </p>
          </div>
        </div>

        {/* Center: Stepper */}
        <div className="flex-1 max-w-sm mx-auto hidden sm:flex items-center justify-center">
          <div className="flex items-center justify-between w-full relative">
            <div className="absolute top-[12px] left-[5%] right-[5%] h-[1px] bg-stone-200 -z-10" />
            <div 
              className="absolute top-[12px] left-[5%] h-[1px] bg-indigo-950 transition-all duration-500 -z-10"
              style={{ width: `${((maxUnlockedStep - 1) / 3) * 90}%` }}
            />

            {stepperSteps.map((step) => {
              const isCurrent = currentStep === step.id;
              const isUnlocked = step.id <= maxUnlockedStep;
              const Icon = step.icon;

              return (
                <button
                  key={step.id}
                  type="button"
                  disabled={!isUnlocked}
                  onClick={() => isUnlocked && setCurrentStep(step.id)}
                  className={`flex flex-col items-center group relative focus:outline-none ${isUnlocked ? "cursor-pointer" : "cursor-not-allowed opacity-50"}`}
                >
                  <div 
                    className={`w-6 h-6 rounded-full flex items-center justify-center border transition-all duration-300 ${
                      isCurrent 
                        ? "bg-indigo-950 border-indigo-950 text-white shadow-sm shadow-indigo-950/20 scale-105" 
                        : isUnlocked 
                        ? "bg-white border-indigo-950 text-indigo-950 hover:bg-indigo-50" 
                        : "bg-stone-50 border-stone-200 text-stone-400"
                    }`}
                  >
                    <Icon className="w-3 h-3" />
                  </div>
                  <span 
                    className={`text-[8px] font-bold mt-1 transition-colors duration-300 ${
                      isCurrent ? "text-indigo-950 font-black" : isUnlocked ? "text-stone-650 hover:text-stone-900" : "text-stone-400"
                    }`}
                  >
                    {step.label}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-1.5 shrink-0">
          {currentStep === 4 && activeProj && activeProj.status === "completed" && (
            <>
              {!activeProj.prd && (
                <motion.button
                  onClick={async () => {
                    if (isGeneratingDocs) return;
                    setIsGeneratingDocs(true);
                    try {
                      const token = localStorage.getItem("token");
                      const res = await fetch(`${API_BASE}/api/projects/${activeProj.id}/generate-prd-mrd`, {
                        method: "POST",
                        headers: { "Authorization": `Bearer ${token}` }
                      });
                      if (res.ok) {
                        const updatedProj = await res.json();
                        updateProject(activeProj.id, updatedProj);
                        setSelectedFile({
                          name: "Product Requirement Document (PRD).md",
                          path: "PRD.md",
                          language: "markdown",
                          content: updatedProj.prd || "",
                        });
                      } else {
                        alert("Failed to generate PRD & MRD documents.");
                      }
                    } catch (err) {
                      console.error("Error generating docs:", err);
                      alert("Error generating PRD & MRD.");
                    } finally {
                      setIsGeneratingDocs(false);
                    }
                  }}
                  disabled={isGeneratingDocs}
                  whileHover={{ scale: 1.04 }}
                  whileTap={{ scale: 0.96 }}
                  className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-[10px] font-bold bg-amber-500 hover:bg-amber-600 text-indigo-950 shadow-sm transition-all disabled:opacity-60 cursor-pointer shrink-0"
                >
                  {isGeneratingDocs ? <Loader2 className="w-3 h-3 animate-spin" /> : <Sparkles className="w-3 h-3" />}
                  <span>Generate PRD</span>
                </motion.button>
              )}
              <motion.button
                onClick={handleDownloadZip}
                disabled={isDownloading}
                whileHover={{ scale: 1.04 }}
                whileTap={{ scale: 0.96 }}
                className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-[10px] font-bold bg-indigo-950 hover:bg-indigo-900 text-amber-500 shadow-sm transition-all disabled:opacity-60 cursor-pointer shrink-0"
              >
                {isDownloading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Download className="w-3 h-3" />}
                <span>Download</span>
              </motion.button>
              <motion.button
                onClick={handleGithubPush}
                disabled={isPushingToGithub}
                whileHover={{ scale: 1.04 }}
                whileTap={{ scale: 0.96 }}
                className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-[10px] font-bold bg-stone-800 hover:bg-stone-900 text-white shadow-sm transition-all disabled:opacity-60 cursor-pointer shrink-0"
              >
                {isPushingToGithub ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <GitBranch className="w-3.5 h-3.5" />}
                <span>GitHub</span>
              </motion.button>
            </>
          )}
        </div>
      </div>

      {/* Main Content Area based on currentStep */}
      <div className="flex-1 overflow-hidden flex flex-col relative bg-transparent">
        {currentStep === 1 && renderBlueprintStep()}
        {currentStep === 2 && renderThemeStep()}
        {currentStep === 3 && renderCompilationStep()}
        {currentStep === 4 && renderCodebaseStep()}
      </div>
    </div>
  );
};
