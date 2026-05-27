"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence, useMotionValue, useTransform, animate } from "framer-motion";
import { useWorkspace, CodeFile, Project } from "@/context/WorkspaceContext";
import { CategoryIcon, CircuitDecor } from "./CustomSvgs";
import { Copy, Check, FileCode, CheckCircle2, Circle, AlertCircle, X, ArrowLeft, Sparkles, Download, GitBranch, ExternalLink, Loader2 } from "lucide-react";

export const ProjectViewer: React.FC = () => {
  const { chats, activeChatId, projects, activeProjectId, generateProject, isGeneratingProject, setShowRightPane, updateProject } = useWorkspace();
  const [selectedFile, setSelectedFile] = useState<CodeFile | null>(null);
  const [copied, setCopied] = useState(false);

  // Theme selection states
  const [viewStage, setViewStage] = useState<"blueprint" | "theme">("blueprint");
  const [themes, setThemes] = useState<any[]>([]);
  const [loadingThemes, setLoadingThemes] = useState(false);
  const [selectedThemeIndex, setSelectedThemeIndex] = useState(0);
  const [activePreviewPage, setActivePreviewPage] = useState<"home" | "dashboard" | "analytics" | "settings" | "login">("home");
  const [customThemeInput, setCustomThemeInput] = useState("");

  // Export action states
  const [isDownloading, setIsDownloading] = useState(false);
  const [isPushingToGithub, setIsPushingToGithub] = useState(false);
  const [githubResult, setGithubResult] = useState<{ url: string; error?: string } | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const handleSuggestMoreThemes = async () => {
    if (!activeChatId) return;
    setLoadingThemes(true);
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`http://127.0.0.1:8000/api/chats/${activeChatId}/themes`, {
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
      const res = await fetch(`http://127.0.0.1:8000/api/chats/${activeChatId}/themes?prompt=${encodeURIComponent(customThemeInput.trim())}`, {
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

  // WebSocket: connect when a project is generating, disconnect when done
  useEffect(() => {
    if (!activeProj) return;
    if (activeProj.status !== "generating") {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      return;
    }

    // Avoid double-connecting
    if (wsRef.current) return;

    const token = localStorage.getItem("token");
    const wsUrl = `ws://127.0.0.1:8000/ws/projects/${activeProj.id}${token ? `?token=${token}` : ""}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "progress" && msg.project_id === activeProj.id) {
          // Delegate update to workspace context if updateProject is available
          if (typeof updateProject === "function") {
            updateProject(activeProj.id, {
              progress: msg.progress ?? activeProj.progress,
              step: msg.step ?? activeProj.step,
              status: msg.status ?? activeProj.status,
            });
          }
        }
      } catch (_) {}
    };

    ws.onerror = () => {};
    ws.onclose = () => { wsRef.current = null; };

    return () => {
      ws.close();
      wsRef.current = null;
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeProj?.id, activeProj?.status]);

  // Fetch dynamic themes on stage change
  useEffect(() => {
    if (viewStage === "theme" && activeChatId) {
      const fetchThemes = async () => {
        setLoadingThemes(true);
        try {
          const token = localStorage.getItem("token");
          const res = await fetch(`http://127.0.0.1:8000/api/chats/${activeChatId}/themes`, {
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
    if (activeProj && activeProj.status === "completed") {
      if (activeProj.requirements) {
        setSelectedFile({
          name: "AI Requirements.json",
          path: "sarthi-internal/AI_Requirements.json",
          language: "json",
          content: JSON.stringify(activeProj.requirements, null, 2),
        });
      } else if (activeProj.codebase.length > 0) {
        setSelectedFile(activeProj.codebase[0]);
      } else {
        setSelectedFile(null);
      }
    } else {
      setSelectedFile(null);
    }
  }, [activeProjectId, activeProj?.status]);

  if (!activeProj) {
    if (activeChat && activeChat.selected_project) {
      const blueprint = activeChat.selected_project;

      if (viewStage === "theme") {
        return (
          <div className="flex-1 flex flex-col h-full bg-stone-50/30 overflow-hidden transition-colors duration-300">
            {/* Header */}
            <div className="p-6 border-b border-stone-200/60 bg-white/50 backdrop-blur-md flex items-center justify-between shrink-0 transition-colors duration-300">
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
                    <span className="absolute inset-0 rounded-full border-4 border-t-indigo-600 border-r-transparent border-b-transparent border-l-transparent animate-spin" />
                  </div>
                  <p className="text-xs text-stone-500 font-semibold animate-pulse">
                    Sarthi is drafting custom themes for {blueprint.name}...
                  </p>
                </div>
              ) : themes.length === 0 ? (
                <div className="text-center p-8 bg-white rounded-3xl border border-stone-200/60 shadow-sm">
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
                        className="flex items-center gap-1 text-[10px] font-bold text-indigo-600 hover:text-indigo-800 disabled:opacity-50 transition-all cursor-pointer bg-transparent border-none p-0"
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
                            className={`w-full text-left p-4 rounded-2xl border transition-all cursor-pointer bg-white relative overflow-hidden group ${
                              isSelected
                                ? "border-indigo-500 shadow-md shadow-indigo-50/50 scale-[1.01]"
                                : "border-stone-200/70 hover:border-stone-300 hover:bg-stone-50/20"
                            }`}
                          >
                            {isSelected && (
                              <div className="absolute top-0 bottom-0 left-0 w-1 bg-indigo-600" />
                            )}
                            <div className="flex justify-between items-start gap-4">
                              <div className="space-y-1">
                                <span className="text-xs font-bold text-stone-850 block group-hover:text-indigo-600 transition-colors">
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
                  <div className="bg-white p-4 rounded-2xl border border-stone-200/60 shadow-sm space-y-3">
                    <h4 className="text-[10px] font-bold uppercase tracking-wider text-stone-400">Not satisfied? Ask Sarthi for another style:</h4>
                    <form onSubmit={handleRequestCustomThemes} className="flex gap-2">
                      <input
                        type="text"
                        placeholder="e.g. 'cyberpunk black & orange', 'soft pastel blue'"
                        value={customThemeInput}
                        onChange={(e) => setCustomThemeInput(e.target.value)}
                        className="flex-1 bg-stone-50 border border-stone-200 rounded-xl px-3 py-2 text-[10px] text-stone-850 placeholder:text-stone-400 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
                      />
                      <button
                        type="submit"
                        disabled={!customThemeInput.trim() || loadingThemes}
                        className="px-3 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-[10px] font-bold rounded-xl transition-all cursor-pointer whitespace-nowrap shadow-sm"
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
                                ? "bg-white text-stone-850 shadow-sm"
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
                                  <span className="font-extrabold text-[10px] block mt-0.5 text-emerald-500">3.24%</span>
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
                                      <div className="w-2.5 h-2.5 rounded-full bg-white ml-auto" />
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
                      onClick={() => generateProject(activeChat.id, blueprint.name, activeChat.category, themes[selectedThemeIndex]?.name, blueprint, themes[selectedThemeIndex]?.palette)}
                      disabled={isGeneratingProject}
                      className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3.5 rounded-2xl shadow-lg shadow-indigo-200 transition-all hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50 cursor-pointer text-xs"
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

      return (
        <div className="flex-1 flex flex-col h-full bg-stone-50/30 overflow-hidden transition-colors duration-300">
          {/* Header */}
          <div className="p-6 border-b border-stone-200/60 bg-white/50 backdrop-blur-md flex items-center justify-between shrink-0 transition-colors duration-300">
            <div className="flex items-center gap-3 overflow-hidden">
              <div className="p-2 rounded-xl bg-indigo-50 text-indigo-600 border border-indigo-100/50">
                <CategoryIcon category={activeChat.category} className="w-5 h-5" />
              </div>
              <div className="overflow-hidden">
                <h2 className="text-lg font-bold font-display text-stone-850 truncate leading-tight">
                  {blueprint.name}
                </h2>
                <p className="text-[10px] text-stone-400 capitalize mt-0.5">
                  Category: {activeChat.category}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-50 border border-indigo-100 text-indigo-700">
                Draft Blueprint
              </span>
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

          {/* Blueprint Details Content */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            <div className="bg-white p-6 rounded-3xl border border-stone-200/60 shadow-sm space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-stone-400">Core Idea</h3>
              <p className="text-sm text-stone-750 leading-relaxed font-medium">
                {blueprint.idea}
              </p>
            </div>

            <div className="bg-white p-6 rounded-3xl border border-stone-200/60 shadow-sm space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-stone-400">Proposed Features Roadmap</h3>
              <div className="space-y-3">
                {blueprint.features.map((feat, idx) => (
                  <div key={idx} className="flex items-start gap-3">
                    <span className="w-5 h-5 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-600 font-bold flex items-center justify-center text-[10px] mt-0.5 shrink-0">
                      ✓
                    </span>
                    <span className="text-xs font-semibold text-stone-700 leading-normal">{feat}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white p-6 rounded-3xl border border-stone-200/60 shadow-sm space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-stone-400">Suggested Technology Stack</h3>
              <div className="p-3 bg-stone-50 rounded-2xl border border-stone-100/50 text-xs font-mono text-stone-600 font-semibold">
                {blueprint.tech_stack}
              </div>
            </div>

            {/* Confirm & Proceed to Themes button */}
            <div className="pt-4 pb-8">
              <button
                type="button"
                onClick={() => setViewStage("theme")}
                className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3.5 rounded-2xl shadow-lg shadow-indigo-200 transition-all hover:scale-[1.01] active:scale-[0.99] cursor-pointer text-xs"
              >
                🚀 Confirm & Proceed to Themes
              </button>
              <p className="text-center text-[10px] text-stone-400 mt-2.5 leading-relaxed max-w-xs mx-auto">
                Discuss refinements with Sarthi in chat, or confirm now to choose design theme.
              </p>
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 bg-stone-50/50">
        <div className="text-center max-w-sm">
          <AlertCircle className="w-10 h-10 text-stone-300 mx-auto mb-3" />
          <h4 className="text-sm font-semibold text-stone-700">No project active</h4>
          <p className="text-xs text-stone-400 mt-1">
            Select a project idea suggestion from the landing screen to start.
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
      const res = await fetch(`http://127.0.0.1:8000/api/projects/${activeProj.id}/download`, {
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
      const res = await fetch(`http://127.0.0.1:8000/api/projects/${activeProj.id}/github-push`, {
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
    { label: "Compiled Codebase Draft", minProg: 100, color: "#10b981" },
  ];

  // Animated counter for progress percentage is declared at the top of the component to follow the Rules of Hooks

  return (
    <div className="flex-1 flex flex-col h-full bg-stone-50/30 overflow-hidden transition-colors duration-300">
      {/* Header */}
      <div className="p-6 border-b border-stone-200/60 bg-white/50 backdrop-blur-md flex items-center justify-between shrink-0 transition-colors duration-300">
        <div className="flex items-center gap-3 overflow-hidden">
          <motion.div
            className="p-2 rounded-xl bg-indigo-50 text-indigo-600 border border-indigo-100/50"
            whileHover={{ scale: 1.05, rotate: -3 }}
          >
            <CategoryIcon category={activeProj.category} className="w-5 h-5" />
          </motion.div>
          <div className="overflow-hidden">
            <h2 className="text-lg font-bold font-display text-stone-800 truncate leading-tight">
              {activeProj.name}
            </h2>
            <p className="text-[10px] text-stone-400 capitalize mt-0.5">
              Category: {activeProj.category}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {activeProj.status === "generating" ? (
            <motion.span
              animate={{ opacity: [1, 0.6, 1] }}
              transition={{ duration: 1.5, repeat: Infinity }}
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-50 border border-amber-100 text-amber-700"
            >
              Compiling ({activeProj.progress}%)
            </motion.span>
          ) : (
            <>
              <motion.span
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 border border-emerald-100 text-emerald-700"
              >
                ✓ Generated
              </motion.span>
              <motion.button
                onClick={handleDownloadZip}
                disabled={isDownloading}
                whileHover={{ scale: 1.04 }}
                whileTap={{ scale: 0.96 }}
                title="Download project as ZIP"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm transition-all disabled:opacity-60 cursor-pointer"
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
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-stone-800 hover:bg-stone-900 text-white shadow-sm transition-all disabled:opacity-60 cursor-pointer"
              >
                {isPushingToGithub ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <GitBranch className="w-3.5 h-3.5" />}
                <span>{isPushingToGithub ? "Pushing…" : "GitHub"}</span>
              </motion.button>
            </>
          )}
          <motion.button
            onClick={() => setShowRightPane(false)}
            whileHover={{ scale: 1.1, rotate: 5 }}
            whileTap={{ scale: 0.9 }}
            className="p-1 rounded-lg hover:bg-stone-100 text-stone-400 hover:text-stone-700 transition-colors cursor-pointer"
            title="Collapse Panel"
          >
            <X className="w-4 h-4" />
          </motion.button>
        </div>
      </div>

      {/* Main Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* PROGRESS TRACKER VIEW (when generating) */}
        {activeProj.status === "generating" && (
          <div className="flex-1 flex flex-col items-center justify-center p-8 overflow-y-auto bg-stone-50/30">
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, ease: "easeOut" }}
              className="max-w-md w-full bg-white p-8 rounded-3xl border border-stone-200/60 shadow-sm relative overflow-hidden"
            >
              {/* Top gradient bar */}
              <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-rose-500" />

              {/* Circuit decor top-right */}
              <div className="absolute top-4 right-4 opacity-40">
                <CircuitDecor className="w-20 h-12" />
              </div>

              <div className="text-center mb-6">
                <span className="text-[10px] uppercase font-bold tracking-wider text-indigo-500">Sarthi Compiler</span>
                <h3 className="text-xl font-bold font-display text-stone-800 mt-1">Generating Prototype</h3>
                {/* Typewriter-style current step label */}
                <motion.p
                  key={activeProj.step}
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4 }}
                  className="text-xs text-stone-400 mt-1 truncate flex items-center justify-center gap-1"
                >
                  <span>{activeProj.step}</span>
                  <span className="animate-cursor-blink text-indigo-400 text-sm">|</span>
                </motion.p>
              </div>

              {/* Progress Ring with outer pulsing ring + rotating dashes */}
              <div className="relative w-36 h-36 mx-auto mb-8 flex items-center justify-center">
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

                {/* Counter-rotating inner dashes */}
                <svg className="absolute inset-0 w-full h-full animate-spin-slow-reverse" viewBox="0 0 100 100">
                  <circle
                    cx="50" cy="50" r="44"
                    stroke="rgba(244,63,94,0.10)"
                    strokeWidth="1"
                    fill="none"
                    strokeDasharray="3 10"
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

                {/* Center text — animated count-up */}
                <div className="absolute text-center">
                  <motion.span className="text-2xl font-extrabold text-stone-800 font-display">
                    {progressRounded}
                  </motion.span>
                  <span className="text-[9px] text-stone-400 block font-semibold uppercase tracking-wider">%</span>
                </div>
              </div>

              {/* Vertical connected timeline */}
              <div className="relative">
                {steps.map((st, idx) => {
                  const isDone = activeProj.progress >= st.minProg;
                  const isCurrent = activeProj.progress < st.minProg &&
                    (idx === 0 || activeProj.progress >= steps[idx - 1].minProg);
                  const isLast = idx === steps.length - 1;

                  return (
                    <div key={idx} className="relative flex items-start gap-3 mb-0">
                      {/* Vertical connector line (not on last) */}
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

                      <div className="flex items-center gap-3 py-2.5 z-10">
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
                              className="w-5 h-5 rounded-full border-2 flex items-center justify-center animate-step-scan"
                              style={{ borderColor: st.color }}
                            >
                              <motion.div
                                className="w-2 h-2 rounded-full"
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
                          className={`text-xs transition-all ${
                            isDone ? "line-through decoration-stone-300 decoration-1" : ""
                          }`}
                        >
                          {st.label}
                        </motion.span>

                        {isCurrent && (
                          <motion.span
                            initial={{ opacity: 0, x: -4 }}
                            animate={{ opacity: 1, x: 0 }}
                            className="text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded-full"
                            style={{ backgroundColor: `${st.color}15`, color: st.color }}
                          >
                            Active
                          </motion.span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Bottom live progress bar strip */}
              <div className="mt-6 pt-4 border-t border-stone-100">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-[10px] text-stone-400 font-semibold">Overall Progress</span>
                  <span className="text-[10px] font-bold text-indigo-600">{activeProj.progress}%</span>
                </div>
                <div className="h-1.5 bg-stone-100 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full rounded-full bg-gradient-to-r from-indigo-500 via-purple-500 to-rose-500"
                    animate={{ width: `${activeProj.progress}%` }}
                    transition={{ duration: 0.6, ease: "easeOut" }}
                  />
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
                  : "bg-emerald-50 border-emerald-200 text-emerald-700"
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
            <div className="w-64 border-r border-stone-200/60 bg-white/20 flex flex-col shrink-0 transition-colors duration-300">
              <div className="p-4 border-b border-stone-200/60 shrink-0">
                <span className="text-[10px] font-bold text-stone-400 uppercase tracking-wider block">Generated Files</span>
              </div>
              <div className="flex-1 overflow-y-auto p-3 space-y-1 select-none">
                {(() => {
                  const filesToRender = [...activeProj.codebase];
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
                          ? "bg-indigo-50/50 text-indigo-700 border border-indigo-100/50"
                          : "hover:bg-stone-100/60 border border-transparent text-stone-600"
                          }`}
                      >
                        <motion.span whileHover={{ scale: 1.15, rotate: -5 }} transition={{ duration: 0.2 }}>
                          <FileCode className={`w-4 h-4 shrink-0 ${isSel ? "text-indigo-500" : "text-stone-400"}`} />
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
            </div>

            {/* Right Code Display Pane */}
            <div className="flex-1 flex flex-col overflow-hidden bg-white transition-colors duration-300">
              {selectedFile ? (
                <div className="flex-1 flex flex-col overflow-hidden">
                  {/* File title & Actions */}
                  <div className="px-6 py-3 border-b border-stone-100 flex justify-between items-center bg-stone-50/40 shrink-0 select-none">
                    <span className="text-xs font-mono font-bold text-stone-500">
                      {selectedFile.path}
                    </span>
                    <button
                      onClick={handleCopy}
                      className="inline-flex items-center gap-1 text-[10px] font-semibold text-stone-500 hover:text-stone-800 bg-white border border-stone-200 rounded-lg px-2.5 py-1.5 shadow-sm transition-all hover:bg-stone-50 cursor-pointer"
                    >
                      {copied ? (
                        <>
                          <Check className="w-3.5 h-3.5 text-emerald-500" />
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
                  {/* Code Block Container */}
                  <div className="flex-1 overflow-auto p-6 font-mono text-xs text-stone-700 leading-relaxed bg-stone-900/5 select-text select-all border-b border-transparent">
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
