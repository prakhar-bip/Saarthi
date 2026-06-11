"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence, useMotionValue, useTransform, animate } from "framer-motion";
import { useWorkspace, CodeFile, Project, API_BASE } from "@/context/WorkspaceContext";
import { CategoryIcon, CircuitDecor, SarthiLogo } from "./CustomSvgs";
import { Copy, Check, FileCode, CheckCircle2, Circle, AlertCircle, X, ArrowLeft, Sparkles, Download, GitBranch, ExternalLink, Loader2, Plus, Database, ClipboardCheck, PanelLeft } from "lucide-react";
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

export const ProjectViewer: React.FC = () => {
  const { 
    chats, 
    activeChatId, 
    projects, 
    activeProjectId, 
    generateProject, 
    compileProjectCodebase,
    isGeneratingProject, 
    setShowRightPane, 
    updateProject,
    updateChatSelectedProject,
    updateChatCategory,
    suggestions,
    isFetchingSuggestions,
    fetchSuggestions
  } = useWorkspace();
  const [selectedFile, setSelectedFile] = useState<CodeFile | null>(null);
  const [copied, setCopied] = useState(false);
  const [activeDocTab, setActiveDocTab] = useState<"prd" | "mrd" | "trd">("prd");

  // Theme selection states
  const [viewStage, setViewStage] = useState<"blueprint" | "theme">("blueprint");
  const [themes, setThemes] = useState<any[]>([]);
  const [loadingThemes, setLoadingThemes] = useState(false);
  const [selectedThemeIndex, setSelectedThemeIndex] = useState(0);
  const [activePreviewPage, setActivePreviewPage] = useState<"home" | "dashboard" | "analytics" | "settings" | "login">("home");
  const [customThemeInput, setCustomThemeInput] = useState("");

  // Custom project blueprint form and tab states
  const [sidebarTab] = useState<"custom">("custom");
  const [customName, setCustomName] = useState("");
  const [customIdea, setCustomIdea] = useState("");
  const [customFeatures, setCustomFeatures] = useState<string[]>(["", "", ""]);
  const [customTechStack, setCustomTechStack] = useState("React, Tailwind CSS, Node.js");

  // Export action states
  const [isDownloading, setIsDownloading] = useState(false);
  const [isPushingToGithub, setIsPushingToGithub] = useState(false);
  const [githubResult, setGithubResult] = useState<{ url: string; error?: string } | null>(null);
  const [showCelebration, setShowCelebration] = useState(false);
  const [showFilesPane, setShowFilesPane] = useState(true);
  const prevStatusRef = useRef<string | undefined>(undefined);
  const lastParsedMessageIdRef = useRef<string | null>(null);
  const terminalLogsRef = useRef<HTMLDivElement>(null);

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
        const newFeatures = [...parsed.features];
        while (newFeatures.length < 3) newFeatures.push("");
        setCustomFeatures(newFeatures);
      }
      if (parsed.tech_stack && parsed.tech_stack !== customTechStack) setCustomTechStack(parsed.tech_stack);
    }
  }, [activeChat?.selected_project]);

  // Animated counter for progress percentage
  const progressCount = useMotionValue(0);
  const progressRounded = useTransform(progressCount, Math.round);
  useEffect(() => {
    if (!activeProj) return;
    const controls = animate(progressCount, activeProj.progress, { duration: 0.8, ease: "easeOut" });
    return controls.stop;
  }, [activeProj?.progress]);

  // Reset viewStage on chat changes
  useEffect(() => {
    setViewStage("blueprint");
    setGithubResult(null);
  }, [activeChatId]);

  useEffect(() => {
    if (activeChat && !activeChat.selected_project && activeChat.category && suggestions.length === 0) {
      fetchSuggestions(activeChat.category);
    }
  }, [activeChat?.id, activeChat?.selected_project, activeChat?.category, suggestions.length]);


  // Fetch dynamic themes on stage change
  useEffect(() => {
    if (viewStage === "theme" && activeChatId) {
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
  }, [viewStage, activeChatId]);

  // Set the first file active by default when project changes or completes
  useEffect(() => {
    if (activeProj?.status === "completed" && prevStatusRef.current === "generating") {
      setShowCelebration(true);
    }
    prevStatusRef.current = activeProj?.status;

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
  }, [activeProjectId, activeProj?.status, activeProj?.prd]);

  // Auto scroll terminal to bottom on update
  useEffect(() => {
    if (terminalLogsRef.current) {
      terminalLogsRef.current.scrollTop = terminalLogsRef.current.scrollHeight;
    }
  }, [activeProj?.progress, activeProj?.step]);

  if (!activeProj) {
    if (isGeneratingProject) {
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

    if (activeChat && activeChat.selected_project && viewStage === "theme") {
      const blueprint = activeChat.selected_project;

      return (
        <div className="flex-1 flex flex-col h-full bg-transparent overflow-hidden transition-colors duration-300">
            {/* Header */}
            <div className="p-6 border-b border-stone-200/60 bg-white/20 backdrop-blur-md flex items-center justify-between shrink-0 transition-colors duration-300">
              <div className="flex items-center gap-3 overflow-hidden">
                <button
                  type="button"
                  onClick={() => setViewStage("blueprint")}
                  className="p-1.5 rounded-lg hover:bg-stone-100 text-stone-500 hover:text-stone-800 transition-colors cursor-pointer mr-1"
                  title="Back to Blueprint"
                >
                  <ArrowLeft className="w-4 h-4" />
                </button>
                <div className="overflow-hidden">
                  <h2 className="text-lg font-bold font-display text-stone-850 truncate leading-tight">
                    Theme & Wireframe
                  </h2>
                  <p className="text-[10px] text-stone-400 capitalize mt-0.5">
                    Customize styles for {blueprint.name}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => setShowRightPane(false)}
                  className="p-1 rounded-lg hover:bg-stone-100 text-stone-400 hover:text-stone-700 transition-colors cursor-pointer"
                  title="Collapse Panel"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Content Area */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {loadingThemes ? (
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
                  {/* Theme suggestions list */}
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <h3 className="text-xs font-bold uppercase tracking-wider text-stone-400">Select Project Theme</h3>
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
                    </div>
                    <div className="grid grid-cols-1 gap-3">
                      {themes.map((themeObj, index) => {
                        const isSelected = selectedThemeIndex === index;
                        const palette = themeObj.palette;
                        return (
                          <button
                            key={index}
                            type="button"
                            onClick={() => setSelectedThemeIndex(index)}
                            className={`w-full text-left p-4 rounded-2xl border transition-all cursor-pointer bg-stone-50 relative overflow-hidden group ${
                              isSelected
                                ? "border-amber-500 shadow-md shadow-indigo-50/50 scale-[1.01]"
                                : "border-stone-200/70 hover:border-stone-300 hover:bg-stone-50/20"
                            }`}
                          >
                            {isSelected && (
                              <div className="absolute top-0 bottom-0 left-0 w-1 bg-indigo-950" />
                            )}
                            <div className="flex justify-between items-start gap-4">
                              <div className="space-y-1">
                                <span className="text-xs font-bold text-stone-850 block group-hover:text-indigo-950 transition-colors">
                                  {themeObj.name}
                                </span>
                                <p className="text-[10px] text-stone-455 leading-relaxed font-medium">
                                  {themeObj.description}
                                </p>
                              </div>
                              
                              {/* Swatches */}
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

                  {/* Custom Theme Prompt builder */}
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

                  {/* Wireframe Skeletons Preview */}
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <h3 className="text-xs font-bold uppercase tracking-wider text-stone-400">Interactive Preview</h3>
                      <span className="text-[9px] uppercase tracking-wider font-semibold text-stone-400">Tweak style live</span>
                    </div>

                    {/* Page tabs */}
                    <div className="flex bg-stone-100 p-1 rounded-xl overflow-x-auto gap-0.5 scrollbar-none">
                      {(["home", "dashboard", "analytics", "settings", "login"] as const).map((page) => {
                        const isActive = activePreviewPage === page;
                        return (
                          <button
                            key={page}
                            type="button"
                            onClick={() => setActivePreviewPage(page)}
                            className={`flex-1 py-1.5 px-2 rounded-lg text-[9px] font-bold capitalize transition-all cursor-pointer whitespace-nowrap ${
                              isActive
                                ? "bg-stone-50 text-stone-850 shadow-sm"
                                : "text-stone-500 hover:text-stone-850"
                            }`}
                          >
                            {page}
                          </button>
                        );
                      })}
                    </div>

                    {/* Mockup Container */}
                    <div
                      className="border rounded-2xl overflow-hidden shadow-inner min-h-[220px] transition-all duration-300 relative flex flex-col"
                      style={{
                        backgroundColor: themes[selectedThemeIndex].palette.background,
                        color: themes[selectedThemeIndex].palette.text,
                        borderColor: themes[selectedThemeIndex].palette.border
                      }}
                    >
                      <AnimatePresence mode="wait">
                        <motion.div
                          key={activePreviewPage + "-" + selectedThemeIndex}
                          initial={{ opacity: 0, y: 4 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -4 }}
                          transition={{ duration: 0.2 }}
                          className="flex-1 flex flex-col text-[8px]"
                        >
                          {activePreviewPage === "home" && (
                            <div className="flex-1 flex flex-col p-3.5 space-y-3">
                              {/* Navigation bar */}
                              <div
                                className="flex justify-between items-center pb-2 border-b"
                                style={{ borderColor: themes[selectedThemeIndex].palette.border }}
                              >
                                <span className="font-extrabold tracking-tight uppercase" style={{ color: themes[selectedThemeIndex].palette.primary }}>
                                  {blueprint.name.slice(0, 10)}
                                </span>
                                <div className="flex gap-2 text-[6px] font-semibold opacity-70">
                                  <span>Product</span>
                                  <span>Solutions</span>
                                  <span>About</span>
                                </div>
                                <span
                                  className="px-2 py-0.5 rounded text-[6px] font-bold"
                                  style={{ backgroundColor: themes[selectedThemeIndex].palette.primary, color: '#ffffff' }}
                                >
                                  Start
                                </span>
                              </div>

                              {/* Hero section */}
                              <div className="text-center py-4 space-y-2">
                                <h4 className="text-[11px] font-extrabold tracking-tight leading-tight max-w-[200px] mx-auto">
                                  Experience the Future of {blueprint.name}
                                </h4>
                                <p className="text-[7px] opacity-70 max-w-[220px] mx-auto leading-normal">
                                  {blueprint.idea.slice(0, 75)}...
                                </p>
                                <div className="flex justify-center gap-2 pt-1">
                                  <span
                                    className="px-3 py-1 rounded-md font-bold shadow-sm"
                                    style={{ backgroundColor: themes[selectedThemeIndex].palette.primary, color: '#ffffff' }}
                                  >
                                    Get Started Free
                                  </span>
                                  <span
                                    className="px-3 py-1 rounded-md font-bold border"
                                    style={{
                                      backgroundColor: themes[selectedThemeIndex].palette.card_bg,
                                      borderColor: themes[selectedThemeIndex].palette.border
                                    }}
                                  >
                                    Learn More
                                  </span>
                                </div>
                              </div>

                              {/* Bottom Feature grid */}
                              <div className="grid grid-cols-2 gap-2 pt-1">
                                {blueprint.features.slice(0, 2).map((f, idx) => (
                                  <div
                                    key={idx}
                                    className="p-2 border rounded-xl"
                                    style={{
                                      backgroundColor: themes[selectedThemeIndex].palette.card_bg,
                                      borderColor: themes[selectedThemeIndex].palette.border
                                    }}
                                  >
                                    <span
                                      className="w-3.5 h-3.5 rounded-full flex items-center justify-center font-bold mb-1"
                                      style={{
                                        backgroundColor: themes[selectedThemeIndex].palette.secondary,
                                        color: themes[selectedThemeIndex].palette.primary
                                      }}
                                    >
                                      ✓
                                    </span>
                                    <span className="font-semibold block truncate">{f}</span>
                                    <span className="opacity-60 block mt-0.5 text-[6px]">Responsive layout module</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {activePreviewPage === "dashboard" && (
                            <div className="flex-1 flex overflow-hidden">
                              {/* Sidebar */}
                              <div
                                className="w-16 border-r p-2.5 flex flex-col gap-3 shrink-0"
                                style={{
                                  backgroundColor: themes[selectedThemeIndex].palette.card_bg,
                                  borderColor: themes[selectedThemeIndex].palette.border
                                }}
                              >
                                <span className="font-extrabold text-[7px]" style={{ color: themes[selectedThemeIndex].palette.primary }}>
                                  DB
                                </span>
                                <div className="flex flex-col gap-1.5 font-semibold opacity-70">
                                  <span className="font-bold" style={{ color: themes[selectedThemeIndex].palette.primary }}>Overview</span>
                                  <span>Activity</span>
                                  <span>Analytics</span>
                                  <span>Settings</span>
                                </div>
                              </div>

                              {/* Dashboard content */}
                              <div className="flex-1 flex flex-col p-2.5 space-y-3 overflow-hidden">
                                {/* Header */}
                                <div className="flex justify-between items-center">
                                  <span className="font-bold">Console Dashboard</span>
                                  <span
                                    className="w-3 h-3 rounded-full"
                                    style={{ backgroundColor: themes[selectedThemeIndex].palette.primary }}
                                  />
                                </div>

                                {/* Stats row */}
                                <div className="grid grid-cols-3 gap-1.5">
                                  {[
                                    { label: "Active", val: "1.2k" },
                                    { label: "Tasks", val: "86%" },
                                    { label: "Revenue", val: "$4.5k" }
                                  ].map((st, idx) => (
                                    <div
                                      key={idx}
                                      className="p-1.5 border rounded-lg"
                                      style={{
                                        backgroundColor: themes[selectedThemeIndex].palette.card_bg,
                                        borderColor: themes[selectedThemeIndex].palette.border
                                      }}
                                    >
                                      <span className="opacity-60 block text-[5px] uppercase font-bold tracking-wider">{st.label}</span>
                                      <span className="font-extrabold text-[9px] block mt-0.5">{st.val}</span>
                                    </div>
                                  ))}
                                </div>

                                {/* Graphic placeholder */}
                                <div
                                  className="flex-1 border rounded-lg p-2.5 flex flex-col justify-between"
                                  style={{
                                    backgroundColor: themes[selectedThemeIndex].palette.card_bg,
                                    borderColor: themes[selectedThemeIndex].palette.border
                                  }}
                                >
                                  <div className="flex justify-between items-center opacity-70 font-semibold text-[6px]">
                                    <span>Weekly Growth</span>
                                    <span>+14.2%</span>
                                  </div>
                                  <div className="flex items-end gap-1 h-8 pt-1">
                                    {[35, 60, 45, 80, 50, 70, 95].map((h, i) => (
                                      <div
                                        key={i}
                                        className="flex-1 rounded-sm"
                                        style={{
                                          height: `${h}%`,
                                          backgroundColor: i === 6 ? themes[selectedThemeIndex].palette.primary : themes[selectedThemeIndex].palette.secondary
                                        }}
                                      />
                                    ))}
                                  </div>
                                </div>
                              </div>
                            </div>
                          )}

                          {activePreviewPage === "analytics" && (
                            <div className="flex-1 flex flex-col p-3.5 space-y-3">
                              {/* Header */}
                              <div className="flex justify-between items-center pb-1 border-b" style={{ borderColor: themes[selectedThemeIndex].palette.border }}>
                                <span className="font-extrabold text-[8px]">Analytics & Reports</span>
                                <span className="text-[6px] opacity-70">Updated 1m ago</span>
                              </div>
                              
                              {/* Grid metrics */}
                              <div className="grid grid-cols-2 gap-2">
                                <div className="p-2 border rounded-xl" style={{ backgroundColor: themes[selectedThemeIndex].palette.card_bg, borderColor: themes[selectedThemeIndex].palette.border }}>
                                  <span className="opacity-60 block text-[5px] uppercase font-bold tracking-wider">Conversion Rate</span>
                                  <span className="font-extrabold text-[10px] block mt-0.5 text-amber-500">3.24%</span>
                                </div>
                                <div className="p-2 border rounded-xl" style={{ backgroundColor: themes[selectedThemeIndex].palette.card_bg, borderColor: themes[selectedThemeIndex].palette.border }}>
                                  <span className="opacity-60 block text-[5px] uppercase font-bold tracking-wider">Bounce Rate</span>
                                  <span className="font-extrabold text-[10px] block mt-0.5 text-rose-500">42.1%</span>
                                </div>
                              </div>

                              {/* Bar Chart / Table */}
                              <div className="border rounded-xl p-2 space-y-1.5" style={{ backgroundColor: themes[selectedThemeIndex].palette.card_bg, borderColor: themes[selectedThemeIndex].palette.border }}>
                                <span className="font-bold block text-[6px]">Top Traffic Sources</span>
                                <div className="space-y-1 text-[6px]">
                                  {[
                                    { name: "Direct Search", pct: "65%", val: "4,200" },
                                    { name: "Referral / Social", pct: "35%", val: "2,260" }
                                  ].map((source, idx) => (
                                    <div key={idx} className="flex justify-between items-center">
                                      <span className="opacity-85 font-medium">{source.name}</span>
                                      <div className="flex items-center gap-2">
                                        <span className="font-semibold">{source.val}</span>
                                        <span className="px-1 py-0.2 rounded text-[5px] font-bold" style={{ backgroundColor: themes[selectedThemeIndex].palette.secondary, color: themes[selectedThemeIndex].palette.primary }}>
                                          {source.pct}
                                        </span>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            </div>
                          )}

                          {activePreviewPage === "settings" && (
                            <div className="flex-1 flex overflow-hidden">
                              {/* Sidebar tabs */}
                              <div className="w-16 border-r p-2 flex flex-col gap-2 shrink-0" style={{ backgroundColor: themes[selectedThemeIndex].palette.card_bg, borderColor: themes[selectedThemeIndex].palette.border }}>
                                <span className="font-extrabold text-[7px]" style={{ color: themes[selectedThemeIndex].palette.primary }}>Settings</span>
                                <div className="flex flex-col gap-1 font-semibold opacity-70 text-[6px]">
                                  <span className="font-bold" style={{ color: themes[selectedThemeIndex].palette.primary }}>Account</span>
                                  <span>Security</span>
                                  <span>Billing</span>
                                </div>
                              </div>

                              {/* Config Fields */}
                              <div className="flex-1 flex flex-col p-2.5 space-y-2.5 overflow-hidden">
                                <span className="font-bold block">General Configuration</span>
                                
                                <div className="space-y-1.5">
                                  <div className="space-y-0.5">
                                    <span className="opacity-70 font-semibold block text-[5px]">Organization Name</span>
                                    <div className="h-5 rounded border px-1.5 flex items-center text-stone-400 text-[6px]" style={{ borderColor: themes[selectedThemeIndex].palette.border, backgroundColor: themes[selectedThemeIndex].palette.background }}>
                                      My Startup Workspace
                                    </div>
                                  </div>

                                  <div className="flex items-center justify-between py-1">
                                    <div className="space-y-0.2">
                                      <span className="font-semibold block text-[5px]">Developer Debug Mode</span>
                                      <span className="opacity-60 block text-[4px]">Log compiler traces</span>
                                    </div>
                                    <div className="w-6 h-3 rounded-full p-0.5 cursor-pointer flex items-center animate-pulse" style={{ backgroundColor: themes[selectedThemeIndex].palette.primary }}>
                                      <div className="w-2.5 h-2.5 rounded-full bg-stone-50 ml-auto" />
                                    </div>
                                  </div>
                                </div>

                                <div className="h-5 rounded font-bold flex items-center justify-center shadow-sm text-center cursor-pointer" style={{ backgroundColor: themes[selectedThemeIndex].palette.primary, color: '#ffffff' }}>
                                  Save Configuration
                                </div>
                              </div>
                            </div>
                          )}

                          {activePreviewPage === "login" && (
                            <div className="flex-1 flex items-center justify-center p-4">
                              <div
                                className="w-full max-w-[200px] p-3 border rounded-xl space-y-2.5 shadow-sm"
                                style={{
                                  backgroundColor: themes[selectedThemeIndex].palette.card_bg,
                                  borderColor: themes[selectedThemeIndex].palette.border
                                }}
                              >
                                <div className="text-center space-y-1">
                                  <h4 className="text-[9px] font-extrabold">Welcome back</h4>
                                  <p className="text-[6px] opacity-60">Log in to manage {blueprint.name}</p>
                                </div>

                                <div className="space-y-1.5">
                                  <div className="space-y-0.5">
                                    <span className="opacity-70 font-semibold block text-[5px]">Email Address</span>
                                    <div
                                      className="h-5 rounded border px-1.5 flex items-center text-stone-400 text-[6px]"
                                      style={{ borderColor: themes[selectedThemeIndex].palette.border, backgroundColor: themes[selectedThemeIndex].palette.background }}
                                    >
                                      username@email.com
                                    </div>
                                  </div>
                                  <div className="space-y-0.5">
                                    <span className="opacity-70 font-semibold block text-[5px]">Password</span>
                                    <div
                                      className="h-5 rounded border px-1.5 flex items-center text-stone-400 text-[6px]"
                                      style={{ borderColor: themes[selectedThemeIndex].palette.border, backgroundColor: themes[selectedThemeIndex].palette.background }}
                                    >
                                      ••••••••••••
                                    </div>
                                  </div>
                                </div>

                                <div
                                  className="h-5 rounded font-bold flex items-center justify-center shadow-sm"
                                  style={{ backgroundColor: themes[selectedThemeIndex].palette.primary, color: '#ffffff' }}
                                >
                                  Sign In
                                </div>

                                <p className="text-[5px] text-center opacity-60">
                                  Don't have an account? <span style={{ color: themes[selectedThemeIndex].palette.primary }} className="font-bold">Sign up</span>
                                </p>
                              </div>
                            </div>
                          )}
                        </motion.div>
                      </AnimatePresence>
                    </div>
                  </div>

                  {/* Confirm & Compile button */}
                  <div className="pt-4 pb-8">
                    <button
                      type="button"
                      onClick={() => generateProject(activeChat.id, blueprint.name, activeChat.category || "General", themes[selectedThemeIndex]?.name, blueprint, themes[selectedThemeIndex]?.palette)}
                      disabled={isGeneratingProject}
                      className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-indigo-950 via-indigo-900 to-amber-500 hover:from-indigo-900 hover:via-indigo-900 hover:to-amber-500 text-white font-bold py-3.5 rounded-2xl shadow-lg shadow-indigo-200 transition-all hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50 cursor-pointer text-xs"
                    >
                      🚀 Build Codebase with {themes[selectedThemeIndex]?.name || "Selected"} Theme
                    </button>
                    <p className="text-center text-[10px] text-stone-400 mt-2.5 leading-relaxed max-w-xs mx-auto">
                      Sarthi will generate React & Tailwind codebase pages styled with the {themes[selectedThemeIndex]?.name || "selected"} color scheme.
                    </p>
                  </div>
                </>
              )}
            </div>
          </div>
        );
    }

    if (activeChat) {
      return (
        <div className="flex-1 flex flex-col h-full bg-transparent overflow-hidden transition-colors duration-300 relative z-0">
          {/* Header */}
          <div className="p-6 border-b border-stone-200/60 bg-stone-50/50 backdrop-blur-md flex items-center justify-between shrink-0 transition-colors duration-300">
            <div className="flex items-center gap-3 overflow-hidden">
              <div className="p-2 rounded-xl bg-indigo-50 text-indigo-950 border border-indigo-100/50">
                <CategoryIcon category={activeChat.category} className="w-5 h-5" />
              </div>
              <div className="overflow-hidden">
                <h2 className="text-lg font-bold font-display text-stone-850 truncate leading-tight">
                  Design Blueprint
                </h2>
                <p className="text-[10px] text-stone-400 capitalize mt-0.5">
                  Category: {activeChat.category}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => setShowRightPane(false)}
                className="p-1 rounded-lg hover:bg-stone-100 text-stone-400 hover:text-stone-700 transition-colors cursor-pointer"
                title="Collapse Panel"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Contents */}
          <div className="flex-1 overflow-y-auto p-6">
            <form onSubmit={async (e) => {
                e.preventDefault();
                if (!customName.trim() || !customIdea.trim()) return;
                const newBlueprint = {
                  name: customName.trim(),
                  idea: customIdea.trim(),
                  features: customFeatures.map(f => f.trim()).filter(Boolean),
                  tech_stack: customTechStack.trim(),
                  category: activeChat.category
                };
                await updateChatSelectedProject(activeChat.id, newBlueprint);
                setViewStage("theme");
              }} className="space-y-4 bg-stone-50 p-5 rounded-2xl border border-stone-200/70 shadow-sm">
                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold uppercase tracking-wider text-stone-450">Project Name</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. 'Personal Finance Manager'"
                    value={customName}
                    onChange={(e) => setCustomName(e.target.value)}
                    className="w-full bg-stone-50 border border-stone-200 rounded-xl px-3 py-2 text-xs text-stone-800 focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-400 transition-all font-medium"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold uppercase tracking-wider text-stone-450">Core Idea / Description</label>
                  <textarea
                    required
                    rows={4}
                    placeholder="Describe the application's vision and value proposition..."
                    value={customIdea}
                    onChange={(e) => setCustomIdea(e.target.value)}
                    className="w-full bg-stone-50 border border-stone-200 rounded-xl px-3 py-2 text-xs text-stone-800 focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-400 transition-all resize-none font-medium leading-relaxed"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold uppercase tracking-wider text-stone-455">Key Features</label>
                  {customFeatures.map((feat, fidx) => (
                    <div key={fidx} className="flex gap-2">
                      <input
                        type="text"
                        placeholder={`Feature ${fidx + 1} (e.g. 'Stripe Payment Sync')`}
                        value={feat}
                        onChange={(e) => {
                          const updated = [...customFeatures];
                          updated[fidx] = e.target.value;
                          setCustomFeatures(updated);
                        }}
                        className="flex-1 bg-stone-50 border border-stone-200 rounded-xl px-3 py-2 text-xs text-stone-800 focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-400 transition-all font-medium"
                      />
                      {customFeatures.length > 1 && (
                        <button
                          type="button"
                          onClick={() => {
                            const updated = customFeatures.filter((_, i) => i !== fidx);
                            setCustomFeatures(updated);
                          }}
                          className="p-2 text-stone-400 hover:text-rose-500 hover:bg-rose-50 rounded-xl transition-colors cursor-pointer"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  ))}
                  <button
                    type="button"
                    onClick={() => setCustomFeatures([...customFeatures, ""])}
                    className="w-full mt-2 py-2 border border-dashed border-stone-300 text-stone-500 hover:text-indigo-950 hover:border-indigo-300 hover:bg-indigo-50 rounded-xl text-xs font-medium transition-all flex items-center justify-center gap-1 cursor-pointer"
                  >
                    <Plus className="w-3 h-3" /> Add Feature
                  </button>
                </div>

                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold uppercase tracking-wider text-stone-450">Tech Stack</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. 'React, Tailwind CSS, Node.js'"
                    value={customTechStack}
                    onChange={(e) => setCustomTechStack(e.target.value)}
                    className="w-full bg-stone-50 border border-stone-200 rounded-xl px-3 py-2 text-xs text-stone-800 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 transition-all font-mono font-semibold text-indigo-950"
                  />
                </div>

                <button
                  type="submit"
                  className="w-full mt-2 py-3 bg-indigo-950 hover:bg-indigo-900 text-amber-500 font-bold tracking-wide border border-indigo-900/50 shadow-inner text-xs font-bold rounded-xl shadow-md transition-all hover:scale-[1.01] active:scale-[0.99] cursor-pointer text-center"
                >
                  Save Blueprint & Choose Theme
                </button>
              </form>
          </div>
        </div>
      );
    }

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
    } catch (err) {
      console.error("Download failed:", err);
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

  const steps = [
    { label: "Ideation & UX Mapping", minProg: 15, color: "#6366f1" },
    { label: "Requirements Definition", minProg: 35, color: "#8b5cf6" },
    { label: "UI Component Generation", minProg: 60, color: "#f59e0b" },
    { label: "Software Architecture Assembly", minProg: 85, color: "#06b6d4" },
    { label: "Compiled Codebase Draft", minProg: 100, color: "#eab308" },
  ];

  // Animated counter for progress percentage is declared at the top of the component to follow the Rules of Hooks

  return (
    <div className="flex-1 flex flex-col h-full bg-transparent overflow-hidden transition-colors duration-300 relative">
      {showCelebration && <DivineCelebration onComplete={() => setShowCelebration(false)} />}
      {/* Header */}
      <div className="min-h-20 py-4 border-b border-stone-200/60 bg-white/30 backdrop-blur-md flex flex-wrap items-center justify-between gap-4 px-6 shrink-0 shadow-sm relative z-10">
        <div className="flex items-center gap-4 flex-1 min-w-[200px]">
          <div className="p-2 rounded-xl bg-indigo-50 text-indigo-950 border border-indigo-100/50">
            <CategoryIcon category={activeProj.category} className="w-5 h-5" />
          </div>
          <div className="overflow-hidden">
            <h2 className="text-lg font-bold font-display text-stone-800 truncate leading-tight">
              {activeProj.name}
            </h2>
            <p className="text-[10px] text-stone-400 capitalize mt-0.5">
              Category: {activeProj.category}
            </p>
            <div className="mt-1 flex flex-wrap items-center gap-1.5">
              <span className="inline-flex items-center gap-1 rounded-md border border-indigo-100 bg-indigo-50 px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider text-indigo-950">
                <Database className="w-3 h-3" />
                {partnerTrack} MCP
              </span>
              {subAgentCount > 0 && (
                <span className="inline-flex items-center gap-1 rounded-md border border-indigo-100 bg-indigo-50 px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider text-indigo-950">
                  <ClipboardCheck className="w-3 h-3" />
                  {subAgentCount} sub-agents
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 justify-end">
          {activeProj.status === "generating" ? (
            <motion.span
              animate={{ opacity: [1, 0.6, 1] }}
              transition={{ duration: 1.5, repeat: Infinity }}
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-50 border border-amber-100 text-amber-700"
            >
              Compiling ({activeProj.progress}%)
            </motion.span>
          ) : activeProj.status === "documents_ready" ? (
            <>
              <motion.span
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-50/50 border border-indigo-200/50 text-indigo-950"
              >
                ✓ Requirements Ready
              </motion.span>
              <motion.button
                onClick={handleDownloadZip}
                disabled={isDownloading}
                whileHover={{ scale: 1.04 }}
                whileTap={{ scale: 0.96 }}
                title="Download documents as ZIP"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-gradient-to-r from-indigo-950 via-indigo-900 to-amber-500 hover:from-indigo-900 hover:via-indigo-900 hover:to-amber-500 text-white shadow-sm transition-all disabled:opacity-60 cursor-pointer"
              >
                {isDownloading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
                <span>{isDownloading ? "Zipping…" : "Download Documents"}</span>
              </motion.button>
            </>
          ) : (
            <>
              <motion.span
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-50/50 border border-indigo-200/50 text-indigo-950"
              >
                ✓ Generated
              </motion.span>
              <motion.button
                onClick={handleDownloadZip}
                disabled={isDownloading}
                whileHover={{ scale: 1.04 }}
                whileTap={{ scale: 0.96 }}
                title="Download project as ZIP"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-gradient-to-r from-indigo-950 via-indigo-900 to-amber-500 hover:from-indigo-900 hover:via-indigo-900 hover:to-amber-500 text-white shadow-sm transition-all disabled:opacity-60 cursor-pointer"
              >
                {isDownloading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
                <span>{isDownloading ? "Zipping…" : "Download"}</span>
              </motion.button>
              <motion.button
                onClick={handleGithubPush}
                disabled={isPushingToGithub}
                whileHover={{ scale: 1.04 }}
                whileTap={{ scale: 0.96 }}
                title="Push project to a new GitHub repo"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-stone-800 hover:bg-indigo-900 text-white shadow-sm transition-all disabled:opacity-60 cursor-pointer"
              >
                {isPushingToGithub ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <GitBranch className="w-3.5 h-3.5" />}
                <span>{isPushingToGithub ? "Pushing…" : "GitHub"}</span>
              </motion.button>
            </>
          )}
        </div>
      </div>

      {/* Main Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* DOCUMENTS REVIEW PANEL (when documents are ready) */}
        {activeProj.status === "documents_ready" && (
          <div className="flex-1 flex overflow-hidden bg-transparent">
            {/* Left Content Area */}
            <div className="flex-1 flex flex-col overflow-hidden border-r border-stone-200/60">
              {/* Tab Navigation */}
              <div className="px-6 py-4 bg-white/20 backdrop-blur-md border-b border-stone-200/60 flex items-center justify-between">
                <div className="flex gap-2">
                  {(["prd", "mrd", "trd"] as const).map((tab) => (
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
                </div>
              </div>

              {/* Document Text View */}
              <div className="flex-1 overflow-y-auto p-8 bg-transparent">
                <div className="max-w-3xl mx-auto bg-stone-50 p-10 rounded-3xl border border-stone-200/60 shadow-sm">
                  {activeDocTab === "prd" && (
                    <MarkdownRenderer text={activeProj.prd || "# Product Requirements\nNo PRD generated."} />
                  )}
                  {activeDocTab === "mrd" && (
                    <MarkdownRenderer text={activeProj.mrd || "# Market Requirements\nNo MRD generated."} />
                  )}
                  {activeDocTab === "trd" && (
                    <MarkdownRenderer text={activeProj.trd || "# Technical Requirements\nNo TRD generated."} />
                  )}
                </div>
              </div>
            </div>

            {/* Right Action Sidebar */}
            <div className="w-85 bg-white/10 backdrop-blur-md p-6 pb-24 flex flex-col justify-between shrink-0 overflow-y-auto border-l border-stone-200/60">
              <div className="space-y-6">
                <div>
                  <h3 className="text-sm font-bold text-stone-850 uppercase tracking-wider">Specifications Review</h3>
                  <p className="text-xs text-stone-500 mt-1.5 leading-relaxed">
                    Sarthi has generated complete Product, Market, and Technical specifications. Please review them before proceeding to the code generation phase.
                  </p>
                </div>

                <div className="p-4 rounded-2xl bg-indigo-50/40 border border-indigo-100/50 space-y-3">
                  <span className="text-[10px] font-bold text-indigo-950 uppercase tracking-wider block">Prototype Tech Stack</span>
                  <div className="flex items-center gap-2 text-stone-750">
                    <FileCode className="w-4 h-4 text-amber-500 font-bold" />
                    <span className="text-xs font-semibold">HTML5 + CSS3 + Flask (Python)</span>
                  </div>
                  <p className="text-[10px] text-stone-500 leading-normal">
                    This prototype is configured to be compiled into a lightweight Python/Flask backend and a modern HTML/CSS frontend.
                  </p>
                </div>

                <div className="p-4 rounded-2xl bg-indigo-50/50 border border-indigo-100/70 space-y-3">
                  <span className="text-[10px] font-bold text-indigo-950 uppercase tracking-wider block">System Integration</span>
                  <div className="grid grid-cols-2 gap-2">
                    <div className="rounded-xl bg-stone-50/70 border border-indigo-100 p-3">
                      <span className="text-[9px] uppercase font-bold text-indigo-950 block">Partner</span>
                      <span className="text-xs font-semibold text-stone-800">{partnerTrack}</span>
                    </div>
                    <div className="rounded-xl bg-stone-50/70 border border-indigo-100 p-3 overflow-hidden">
                      <span className="text-[9px] uppercase font-bold text-indigo-950 block">MCP Mode</span>
                      <span className="text-xs font-semibold text-stone-800 break-all select-all block mt-0.5 leading-tight" title={mcpStatus.mode || "pending"}>
                        {mcpStatus.mode || "pending"}
                      </span>
                    </div>
                  </div>
                  <p className="text-[10px] text-stone-500 leading-normal">
                    The generated workspace contains a README.md, database configurations, and MCP client modules.
                  </p>
                </div>
              </div>

              {activeProj.category !== "documents" && (
                <div className="mt-8 border-t border-stone-200/60 pt-6 space-y-4">
                  <div className="text-[11px] text-stone-500 leading-normal">
                    Everything looks good? Proceed to generate the codebase and assemble the working application.
                  </div>
                  <motion.button
                    onClick={() => compileProjectCodebase(activeProj.id, activeProj.chat_id)}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="w-full flex items-center justify-center gap-2 py-3.5 rounded-2xl bg-gradient-to-r from-indigo-950 via-indigo-900 to-amber-500 hover:from-indigo-900 hover:via-indigo-900 hover:to-amber-500 text-white font-semibold text-sm shadow-md shadow-indigo-100 transition-all cursor-pointer"
                  >
                    <Sparkles className="w-4 h-4 animate-pulse" />
                    <span>Proceed to Build Codebase</span>
                  </motion.button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* PROGRESS TRACKER VIEW (when generating) */}
        {activeProj.status === "generating" && (
          <div className="flex-1 flex flex-col items-center justify-center p-8 overflow-y-auto bg-transparent">
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, ease: "easeOut" }}
              className="max-w-4xl w-full bg-white p-8 rounded-3xl border border-stone-200/60 shadow-lg relative overflow-hidden flex flex-col md:flex-row gap-8"
            >
              {/* Top gradient bar */}
              <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-amber-500 via-indigo-500 to-purple-600" />

              {/* Left Column: Progress Circle and Timeline Milestones */}
              <div className="flex-1 md:w-5/12 flex flex-col justify-between">
                <div>
                  {/* Circuit decor top-left/right in column */}
                  <div className="flex justify-between items-center mb-6">
                    <div>
                      <span className="text-[10px] uppercase font-bold tracking-wider text-amber-500">Sarthi Compiler</span>
                      <h3 className="text-lg font-bold font-display text-stone-800 mt-1">Generating Prototype</h3>
                      <div className="mt-1 flex items-center gap-1.5 text-[9px] font-bold uppercase tracking-wider text-indigo-950">
                        <Database className="w-3 h-3" />
                        <span>{partnerTrack} MCP + Gemini Agents</span>
                      </div>
                    </div>
                  </div>

                  {/* Progress Ring with outer pulsing ring + rotating dashes */}
                  <div className="relative w-32 h-32 mx-auto mb-6 flex items-center justify-center">
                    {/* Outer pulsing ring */}
                    <motion.div
                      className="absolute inset-0 rounded-full border-2 border-indigo-300/30"
                      animate={{ scale: [1, 1.06, 1], opacity: [0.5, 0.2, 0.5] }}
                      transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                    />

                    {/* Rotating dashed ring (outer) */}
                    <svg className="absolute inset-0 w-full h-full animate-spin-slow" viewBox="0 0 100 100">
                      <circle
                        cx="50" cy="50" r="47"
                        stroke="rgba(99,102,241,0.15)"
                        strokeWidth="1.5"
                        fill="none"
                        strokeDasharray="6 8"
                      />
                    </svg>

                    {/* Main progress ring */}
                    <svg className="absolute inset-0 w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                      <circle cx="50" cy="50" r="40" stroke="#f5f5f4" strokeWidth="5" fill="transparent" />
                      <motion.circle
                        cx="50" cy="50" r="40"
                        stroke="url(#progress-grad-v2)"
                        strokeWidth="5"
                        fill="transparent"
                        strokeLinecap="round"
                        strokeDasharray="251.2"
                        animate={{ strokeDashoffset: 251.2 - (251.2 * activeProj.progress) / 100 }}
                        transition={{ duration: 0.6, ease: "easeOut" }}
                      />
                      <defs>
                        <linearGradient id="progress-grad-v2" x1="0" y1="0" x2="1" y2="1">
                          <stop offset="0%" stopColor="#6366f1" />
                          <stop offset="50%" stopColor="#8b5cf6" />
                          <stop offset="100%" stopColor="#f43f5e" />
                        </linearGradient>
                      </defs>
                    </svg>

                    {/* Center text */}
                    <div className="absolute text-center">
                      <motion.span className="text-xl font-extrabold text-stone-800 font-display">
                        {progressRounded}
                      </motion.span>
                      <span className="text-[8px] text-stone-400 block font-semibold uppercase tracking-wider">%</span>
                    </div>
                  </div>

                  {/* Vertical connected timeline */}
                  <div className="relative mb-6">
                    {steps.map((st, idx) => {
                      const isDone = activeProj.progress >= st.minProg;
                      const isCurrent = activeProj.progress < st.minProg &&
                        (idx === 0 || activeProj.progress >= steps[idx - 1].minProg);
                      const isLast = idx === steps.length - 1;

                      return (
                        <div key={idx} className="relative flex items-start gap-3 mb-0">
                          {/* Vertical connector line */}
                          {!isLast && (
                            <div className="absolute left-[9px] top-5 w-[1.5px] h-[calc(100%+0px)] bottom-0">
                              <motion.div
                                className="w-full rounded-full"
                                style={{ backgroundColor: isDone ? st.color : "#e7e5e4" }}
                                initial={{ height: 0 }}
                                animate={{ height: isDone ? "100%" : "0%" }}
                                transition={{ duration: 0.5, delay: idx * 0.1, ease: "easeOut" }}
                              />
                              {!isDone && (
                                <div className="w-full h-full bg-stone-200" />
                              )}
                            </div>
                          )}

                          <div className="flex items-center gap-3 py-1.5 z-10">
                            {/* Step Node */}
                            <div className="shrink-0 w-5 h-5 flex items-center justify-center">
                              {isDone ? (
                                <motion.div
                                  initial={{ scale: 0, opacity: 0 }}
                                  animate={{ scale: 1, opacity: 1 }}
                                  transition={{ type: "spring", stiffness: 500, damping: 20 }}
                                  className="w-5 h-5 rounded-full flex items-center justify-center"
                                  style={{ backgroundColor: st.color }}
                                >
                                  <svg viewBox="0 0 12 12" className="w-3 h-3" fill="none">
                                    <motion.path
                                      d="M2 6 L5 9 L10 3"
                                      stroke="white"
                                      strokeWidth="1.8"
                                      strokeLinecap="round"
                                      strokeLinejoin="round"
                                      initial={{ pathLength: 0 }}
                                      animate={{ pathLength: 1 }}
                                      transition={{ duration: 0.4, ease: "easeOut" }}
                                    />
                                  </svg>
                                </motion.div>
                              ) : isCurrent ? (
                                <motion.div
                                  className="w-5 h-5 rounded-full border-2 flex items-center justify-center"
                                  style={{ borderColor: st.color }}
                                >
                                  <motion.div
                                    className="w-1.5 h-1.5 rounded-full"
                                    style={{ backgroundColor: st.color }}
                                    animate={{ scale: [1, 1.3, 1] }}
                                    transition={{ duration: 0.9, repeat: Infinity, ease: "easeInOut" }}
                                  />
                                </motion.div>
                              ) : (
                                <div className="w-5 h-5 rounded-full border-2 border-stone-200" />
                              )}
                            </div>

                            {/* Label */}
                            <motion.span
                              animate={{
                                color: isDone ? "#78716c" : isCurrent ? st.color : "#a8a29e",
                                fontWeight: isCurrent ? 700 : isDone ? 500 : 400,
                              }}
                              transition={{ duration: 0.3 }}
                              className={`text-[11px] transition-all ${
                                isDone ? "line-through decoration-stone-300 decoration-1" : ""
                              }`}
                            >
                              {st.label}
                            </motion.span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Bottom live progress bar strip */}
                <div className="pt-4 border-t border-stone-100">
                  <div className="flex justify-between items-center mb-1.5">
                    <span className="text-[10px] text-stone-400 font-semibold">Overall Progress</span>
                    <span className="text-[10px] font-bold text-indigo-950">{activeProj.progress}%</span>
                  </div>
                  <div className="h-1.5 bg-stone-100 rounded-full overflow-hidden">
                    <motion.div
                      className="h-full rounded-full bg-gradient-to-r from-amber-500 via-indigo-500 to-purple-600"
                      animate={{ width: `${activeProj.progress}%` }}
                      transition={{ duration: 0.6, ease: "easeOut" }}
                    />
                  </div>
                </div>
              </div>

              {/* Right Column: Live Agent Activity Monitor Console */}
              <div className="flex-1 md:w-7/12 flex flex-col">
                <div className="mb-2 flex justify-between items-center">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-stone-400">Agent Activity Monitor</span>
                  <span className="text-[9px] font-bold text-amber-500 animate-pulse uppercase tracking-wider">● Compiling Code</span>
                </div>
                
                {/* Terminal Console */}
                <div className="bg-stone-900 border border-stone-850 rounded-2xl p-4 font-mono text-[9px] h-[360px] flex flex-col shadow-inner relative overflow-hidden text-stone-300">
                  {/* Terminal Header */}
                  <div className="flex items-center justify-between pb-2 border-b border-stone-800/80 mb-3 shrink-0 select-none">
                    <div className="flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-rose-500/80" />
                      <span className="w-2 h-2 rounded-full bg-amber-500/80" />
                      <span className="w-2 h-2 rounded-full bg-emerald-500/80" />
                    </div>
                    <span className="text-[8px] uppercase tracking-wider text-stone-500 font-bold">sarthi-agent-monitor</span>
                    <span className="text-[7px] text-emerald-400 opacity-80 animate-pulse font-bold">● Active</span>
                  </div>

                  {/* Terminal Log Lines */}
                  <div 
                    ref={terminalLogsRef} 
                    className="flex-1 overflow-y-auto space-y-2 pr-1 scrollbar-thin scrollbar-thumb-stone-800"
                  >
                    <div className="text-stone-500">Initialized Sarthi Multi-Agent Compilation Engine [v1.0]</div>
                    <div className="text-stone-500">Connected to local MongoDB workspace broker...</div>
                    {agentPipeline.slice(0, currentAgentIdx + 1).map((agentName, idx) => {
                      const isLast = idx === currentAgentIdx;
                      const timeStr = new Date(Date.now() - (currentAgentIdx - idx) * 3500).toLocaleTimeString("en-US", { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" });
                      
                      return (
                        <motion.div 
                          key={agentName}
                          initial={{ opacity: 0, x: -4 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ duration: 0.3 }}
                          className={`flex items-start gap-2 leading-relaxed ${isLast ? "text-amber-400" : "text-emerald-400/90"}`}
                        >
                          <span className="text-stone-600 shrink-0">[{timeStr}]</span>
                          <span className="font-bold shrink-0">{agentName}:</span>
                          <span className="text-stone-200">
                            {isLast ? (
                              <span className="flex items-center gap-1.5">
                                <span className="w-1.5 h-1.5 bg-amber-400 rounded-full animate-ping" />
                                <span>{agentDescriptions[agentName] || "Orchestrating agent tasks..."}</span>
                              </span>
                            ) : (
                              <span>[COMPLETE] Task contract generated successfully.</span>
                            )}
                          </span>
                        </motion.div>
                      );
                    })}
                    
                    {/* Blinking Cursor */}
                    <div className="flex items-center gap-1 text-stone-500 pt-1">
                      <span>sarthi_compilation_broker:~ $</span>
                      <span className="w-1.5 h-3 bg-amber-400 animate-cursor-blink" />
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        )}

        {/* GitHub Result Toast */}
        <AnimatePresence>
          {githubResult && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              className={`absolute top-20 left-1/2 -translate-x-1/2 z-50 flex items-center gap-3 px-4 py-3 rounded-2xl shadow-xl text-xs font-semibold border ${
                githubResult.error
                  ? "bg-rose-50 border-rose-200 text-rose-700"
                  : "bg-indigo-50 border-indigo-200 text-indigo-950"
              }`}
            >
              {githubResult.error ? (
                <><AlertCircle className="w-4 h-4 shrink-0" /><span>{githubResult.error}</span></>
              ) : (
                <><CheckCircle2 className="w-4 h-4 shrink-0" /><span>Pushed to GitHub!</span>
                  <a href={githubResult.url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 underline underline-offset-2 hover:opacity-75">
                    View repo <ExternalLink className="w-3 h-3" />
                  </a>
                </>
              )}
              <button onClick={() => setGithubResult(null)} className="ml-2 p-0.5 rounded hover:bg-black/10 cursor-pointer">
                <X className="w-3.5 h-3.5" />
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* CODEBASE VIEW PANEL (when completed) */}
        {activeProj.status === "completed" && (
          <div className="flex-1 flex overflow-hidden">
            {/* Left File Tree Pane */}
            <AnimatePresence initial={false}>
              {showFilesPane && (
                <motion.div
                  initial={{ width: 0, opacity: 0 }}
                  animate={{ width: 256, opacity: 1 }}
                  exit={{ width: 0, opacity: 0 }}
                  transition={{ duration: 0.3, ease: "easeInOut" }}
                  className="border-r border-stone-200/60 bg-white/30 backdrop-blur-md flex flex-col shrink-0 transition-colors duration-300 overflow-hidden"
                >
                  <div className="p-4 border-b border-stone-200/60 shrink-0 w-64">
                    <span className="text-[10px] font-bold text-stone-400 uppercase tracking-wider block">Generated Files</span>
                  </div>
                  <div className="flex-1 overflow-y-auto p-3 space-y-1 select-none w-64">
                    {(() => {
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
                  if (activeProj.trd) {
                    filesToRender.unshift({
                      name: "Technical Requirement Document (TRD).md",
                      path: "TRD.md",
                      language: "markdown",
                      content: activeProj.trd,
                    });
                  }
                  if (activeProj.mrd) {
                    filesToRender.unshift({
                      name: "Market Requirement Document (MRD).md",
                      path: "MRD.md",
                      language: "markdown",
                      content: activeProj.mrd,
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
                  if (activeProj.agent_context) {
                    filesToRender.unshift({
                      name: "AI_AgentContext.json",
                      path: "sarthi-internal/AI_AgentContext.json",
                      language: "json",
                      content: JSON.stringify(activeProj.agent_context, null, 2),
                    });
                  }
                  if (activeProj.code_generation_plan) {
                    filesToRender.unshift({
                      name: "AI_CodeGenerationPlanner.json",
                      path: "sarthi-internal/AI_CodeGenerationPlanner.json",
                      language: "json",
                      content: JSON.stringify(activeProj.code_generation_plan, null, 2),
                    });
                  }
                  if (activeProj.optimization_architecture) {
                    filesToRender.unshift({
                      name: "AI_OptimizationArchitecture.json",
                      path: "sarthi-internal/AI_OptimizationArchitecture.json",
                      language: "json",
                      content: JSON.stringify(activeProj.optimization_architecture, null, 2),
                    });
                  }
                  if (activeProj.validation_architecture) {
                    filesToRender.unshift({
                      name: "AI_ValidationArchitecture.json",
                      path: "sarthi-internal/AI_ValidationArchitecture.json",
                      language: "json",
                      content: JSON.stringify(activeProj.validation_architecture, null, 2),
                    });
                  }
                  if (activeProj.testing_architecture) {
                    filesToRender.unshift({
                      name: "AI_TestingArchitecture.json",
                      path: "sarthi-internal/AI_TestingArchitecture.json",
                      language: "json",
                      content: JSON.stringify(activeProj.testing_architecture, null, 2),
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
                  if (activeProj.devops_architecture) {
                    filesToRender.unshift({
                      name: "AI_DevOpsArchitecture.json",
                      path: "sarthi-internal/AI_DevOpsArchitecture.json",
                      language: "json",
                      content: JSON.stringify(activeProj.devops_architecture, null, 2),
                    });
                  }
                  if (activeProj.state_management) {
                    filesToRender.unshift({
                      name: "AI_StateManagement.json",
                      path: "sarthi-internal/AI_StateManagement.json",
                      language: "json",
                      content: JSON.stringify(activeProj.state_management, null, 2),
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
                  if (activeProj.auth_architecture) {
                    filesToRender.unshift({
                      name: "AI_AuthenticationArchitecture.json",
                      path: "sarthi-internal/AI_AuthenticationArchitecture.json",
                      language: "json",
                      content: JSON.stringify(activeProj.auth_architecture, null, 2),
                    });
                  }
                  if (activeProj.theme_styling) {
                    filesToRender.unshift({
                      name: "AI_ThemeStyling.json",
                      path: "sarthi-internal/AI_ThemeStyling.json",
                      language: "json",
                      content: JSON.stringify(activeProj.theme_styling, null, 2),
                    });
                  }
                  if (activeProj.frontend_architecture) {
                    filesToRender.unshift({
                      name: "AI_FrontendStructure.json",
                      path: "sarthi-internal/AI_FrontendStructure.json",
                      language: "json",
                      content: JSON.stringify(activeProj.frontend_architecture, null, 2),
                    });
                  }
                  if (activeProj.api_architecture) {
                    filesToRender.unshift({
                      name: "AI_APIArchitecture.json",
                      path: "sarthi-internal/AI_APIArchitecture.json",
                      language: "json",
                      content: JSON.stringify(activeProj.api_architecture, null, 2),
                    });
                  }
                  if (activeProj.backend_architecture) {
                    filesToRender.unshift({
                      name: "AI_BackendArchitecture.json",
                      path: "sarthi-internal/AI_BackendArchitecture.json",
                      language: "json",
                      content: JSON.stringify(activeProj.backend_architecture, null, 2),
                    });
                  }
                  if (activeProj.db_architecture) {
                    filesToRender.unshift({
                      name: "AI_DatabaseArchitecture.json",
                      path: "sarthi-internal/AI_DatabaseArchitecture.json",
                      language: "json",
                      content: JSON.stringify(activeProj.db_architecture, null, 2),
                    });
                  }
                  if (activeProj.planning) {
                    filesToRender.unshift({
                      name: "AI Planner.json",
                      path: "sarthi-internal/AI_Planner.json",
                      language: "json",
                      content: JSON.stringify(activeProj.planning, null, 2),
                    });
                  }
                  if (activeProj.requirements) {
                    filesToRender.unshift({
                      name: "AI Requirements.json",
                      path: "sarthi-internal/AI_Requirements.json",
                      language: "json",
                      content: JSON.stringify(activeProj.requirements, null, 2),
                    });
                  }
                  return filesToRender.map((file, fIdx) => {
                    const isSel = selectedFile?.path === file.path;
                    return (
                      <motion.button
                        key={file.path}
                        initial={{ opacity: 0, x: -8 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: fIdx * 0.025, duration: 0.25, ease: "easeOut" }}
                        whileHover={{ x: 2 }}
                        onClick={() => setSelectedFile(file)}
                        className={`w-full flex items-center gap-2.5 p-2 rounded-xl text-left transition-all cursor-pointer ${isSel
                          ? "bg-indigo-50/50 text-indigo-950 border border-indigo-100/50"
                          : "hover:bg-stone-100/60 border border-transparent text-stone-600"
                          }`}
                      >
                        <motion.span whileHover={{ scale: 1.15, rotate: -5 }} transition={{ duration: 0.2 }}>
                          <FileCode className={`w-4 h-4 shrink-0 ${isSel ? "text-amber-500" : "text-stone-400"}`} />
                        </motion.span>
                        <div className="overflow-hidden">
                          <p className="text-xs font-semibold truncate">{file.name}</p>
                          <span className="text-[8px] font-mono text-stone-400 block truncate">{file.path}</span>
                        </div>
                      </motion.button>
                    );
                  });
                })()}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

            {/* Right Code Display Pane */}
            <div className="flex-1 flex flex-col overflow-hidden bg-transparent transition-colors duration-300">
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
                      className="inline-flex items-center gap-1 text-[10px] font-semibold text-stone-500 hover:text-stone-800 bg-stone-50 border border-stone-200 rounded-lg px-2.5 py-1.5 shadow-sm transition-all hover:bg-stone-50 cursor-pointer"
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
        )}
      </div>
    </div>
  );
};
