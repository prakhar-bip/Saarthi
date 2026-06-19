"use client";

import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence, useDragControls } from "framer-motion";
import { useWorkspace, Message, API_BASE } from "@/context/WorkspaceContext";
import { CategoryIcon, LockIllustration, SarthiLogo, WaveBackground, AiTypingWave, CircuitDecor, EmptyStateIllustration, FloatingBot, MorpankhBg } from "./CustomSvgs";
import { Send, Sparkles, BookOpen, AlertCircle, ChevronDown, Cpu, ShieldAlert, PanelRight, ChevronLeft, ChevronRight, PanelLeft, RefreshCw, Pause, Play, Square, FolderPlus } from "lucide-react";
import { MarkdownRenderer } from "./MarkdownRenderer";

const slideVariants = {
  enter: (direction: number) => ({
    x: direction > 0 ? 80 : -80,
    opacity: 0,
    scale: 0.97
  }),
  center: {
    x: 0,
    opacity: 1,
    scale: 1,
    transition: {
      x: { type: "spring" as const, stiffness: 320, damping: 32 },
      opacity: { duration: 0.22 },
      scale: { duration: 0.22 }
    }
  },
  exit: (direction: number) => ({
    x: direction < 0 ? 80 : -80,
    opacity: 0,
    scale: 0.97,
    transition: {
      x: { type: "spring" as const, stiffness: 320, damping: 32 },
      opacity: { duration: 0.18 },
      scale: { duration: 0.18 }
    }
  })
} as const;

const msgVariants = {
  initial: { opacity: 0, y: 12, scale: 0.98 },
  animate: { opacity: 1, y: 0, scale: 1, transition: { type: "spring" as const, stiffness: 380, damping: 28 } },
};

export const WorkspaceConsole: React.FC<{ isMinimized?: boolean }> = ({ isMinimized = false }) => {
  const {
    user,
    chats,
    setChats,
    activeChatId,
    setActiveChatId,
    activeProjectId,
    setActiveProjectId,
    createNewChat,
    addMessageToChat,
    editMessageText,
    updateChatSelectedProject,
    togglePauseChat,
    stopChatGeneration,
    generateProject,
    generateDocuments,
    setShowAuthModal,
    setAuthMode,
    showAbout,
    showContact,
    setShowAbout,
    setShowContact,
    isGeneratingProject,
    showRightPane,
    setShowRightPane,
    suggestions,
    isFetchingSuggestions,
    fetchSuggestions,
    clearSuggestions,
    showLeftPane,
    setShowLeftPane,
    projects,
    setShowFeedbackModal
  } = useWorkspace();

  const activeChat = chats.find((c) => c.id === activeChatId);
  const activeProj = projects.find((p) => p.id === (activeProjectId || activeChat?.project_id)) ||
    (activeChatId ? projects.find((p) => p.chat_id === activeChatId) : undefined);

  const [currentCategory, setCurrentCategory] = useState<string>("");
  const [currentInput, setCurrentInput] = useState<string>("");
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768);
    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);
  const [showCategoryDropdown, setShowCategoryDropdown] = useState(false);
  const [validationError, setValidationError] = useState(false);
  const [aiTyping, setAiTyping] = useState(false);
  const [shakeLock, setShakeLock] = useState(false);
  const [projectNameInput, setProjectNameInput] = useState("");
  const [isFloatingExpanded, setIsFloatingExpanded] = useState(false);
  const dragControls = useDragControls();

  // Floating Create Project Modal states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [modalPrompt, setModalPrompt] = useState("");
  const [modalName, setModalName] = useState("");
  const [modalIdea, setModalIdea] = useState("");
  const [modalFeatures, setModalFeatures] = useState<string[]>(["", "", ""]);
  const [modalTechStack, setModalTechStack] = useState("React, Tailwind CSS, FastAPI, MongoDB");
  const [modalHitlEnabled, setModalHitlEnabled] = useState(true);
  const [modalGenType, setModalGenType] = useState<string>("full_stack");
  const [isSuggesting, setIsSuggesting] = useState(false);

  // Document Architect states
  const [workspaceMode, setWorkspaceMode] = useState<"compiler" | "docs">("compiler");
  const [docProjectName, setDocProjectName] = useState("");
  const [docPrompt, setDocPrompt] = useState("");
  const [loadingStep, setLoadingStep] = useState(0);

  const docLoadingSteps = [
    "Analyzing project scope & objectives...",
    "Drafting Product Requirement Document (PRD)...",
    "Formulating Market Requirement Document (MRD)...",
    "Structuring Technical Design & Architecture (TRD)...",
    "Writing final schemas & formatting markdown..."
  ];

  useEffect(() => {
    let interval: any;
    if (isGeneratingProject && workspaceMode === "docs") {
      setLoadingStep(0);
      interval = setInterval(() => {
        setLoadingStep((prev) => (prev < 4 ? prev + 1 : prev));
      }, 3000);
    } else {
      setLoadingStep(0);
    }
    return () => clearInterval(interval);
  }, [isGeneratingProject, workspaceMode]);

  const [editingMessageId, setEditingMessageId] = useState<string | null>(null);
  const [editingText, setEditingText] = useState("");
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);

  const [currentSlideIndex, setCurrentSlideIndex] = useState(0);
  const [direction, setDirection] = useState(0);
  const [inputFocused, setInputFocused] = useState(false);

  useEffect(() => {
    setCurrentSlideIndex(0);
    setDirection(0);
  }, [suggestions]);

  const handleCopyMessage = (messageId: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedMessageId(messageId);
    setTimeout(() => setCopiedMessageId(null), 2000);
  };

  const chatEndRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [activeChat?.messages?.length, aiTyping]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [activeChat?.messages?.length, aiTyping, isFloatingExpanded]);

  useEffect(() => {
    if (!activeChatId) {
      setCurrentCategory("");
      setCurrentInput("");
    }
  }, [activeChatId]);

  const categories = [
    { id: "startup", label: "Startup & SaaS", desc: "Pitch drafts, MVP architecture & business models" },
    { id: "finance", label: "Finance & Budgets", desc: "Investment structures & transaction monitors" },
    { id: "health", label: "Health & Wellness", desc: "Fitness routines, breathing guides & trackers" },
    { id: "education", label: "Education & Learning", desc: "Spaced repetition quiz builders & note logs" },
    { id: "productivity", label: "Productivity", desc: "Task logs, workspace managers & timeline lists" },
    { id: "sustainability", label: "Sustainability", desc: "Carbon footprint grids & emission gauges" },
    { id: "other", label: "Other / Custom", desc: "Custom modules & prototype draft structures" },
  ];

  const categoryAccents: Record<string, string> = {
    startup: "#6366f1",
    finance: "#eab308",
    health: "#f43f5e",
    education: "#f59e0b",
    productivity: "#8b5cf6",
    sustainability: "#06b6d4",
    other: "#78716c",
  };

  const handleLockClick = () => {
    setShakeLock(true);
    setTimeout(() => setShakeLock(false), 450);
    setAuthMode("login");
    setShowAuthModal(true);
  };

  const handleCategorySelect = (catId: string) => {
    setCurrentCategory(catId);
    setValidationError(false);
    setShowCategoryDropdown(false);
    setActiveChatId(null);
    setActiveProjectId(null);
    fetchSuggestions(catId);
    setCurrentSlideIndex(0);
    setDirection(0);
  };

  const handleSelectSuggestion = async (suggestion: any) => {
    if (!currentCategory) return;
    setAiTyping(true);
    try {
      await createNewChat(currentCategory, suggestion.name, suggestion);
    } catch (e) {
      console.error("Create chat failed:", e);
    } finally {
      setAiTyping(false);
    }
  };

  const detectCategory = (text: string): string => {
    const t = text.toLowerCase();
    if (/\b(startup|saas|mvp|pitch|business|product|client|customer|revenue|monetize|funding|marketing|b2b|mrr|churn)\b/.test(t)) {
      return "startup";
    }
    if (/\b(finance|budget|money|invest|crypto|stock|wallet|expense|transaction|pay|payment|bank|saving|tax|ledger)\b/.test(t)) {
      return "finance";
    }
    if (/\b(health|wellness|fitness|gym|workout|routine|exercise|breath|meditat|doctor|medical|diet|food|nutrition|sleep|hydrate|water)\b/.test(t)) {
      return "health";
    }
    if (/\b(education|learn|study|quiz|course|school|teach|note|flashcard|memory|repetition|student|class|practice|code)\b/.test(t)) {
      return "education";
    }
    if (/\b(productivity|task|todo|schedule|calendar|timeline|manage|organize|time|focus|work|efficient|habit|standup|sprint)\b/.test(t)) {
      return "productivity";
    }
    if (/\b(sustainability|carbon|eco|green|recycle|nature|emission|climate|environment|waste|energy|solar|farmers|market|conserve)\b/.test(t)) {
      return "sustainability";
    }
    return "other";
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(e);
    }
  };

  const handleSendMessage = async (e?: React.FormEvent | React.KeyboardEvent) => {
    if (e) e.preventDefault();
    if (!user) return;
    if (!currentInput.trim()) return;
    if (aiTyping) return;

    const textSent = currentInput;
    setCurrentInput(""); // Clear the input immediately!
    const textarea = document.getElementById("chat-input-bar");
    if (textarea) textarea.style.height = "auto";
    setAiTyping(true);

    let targetCategory = currentCategory;
    if (!targetCategory) {
      targetCategory = detectCategory(textSent);
      setCurrentCategory(targetCategory);
    }

    const targetChatId = activeChatId;
    if (!activeChat) {
      // Optimistically create temporary chat session so the user message appears instantly
      const tempChatId = `chat-temp-${Date.now()}`;
      const chatTitle = textSent.length > 25 ? `${textSent.slice(0, 25)}...` : textSent;
      const time = new Date().toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
      const tempMsg = { id: `m-temp-${Date.now()}`, sender: "user" as const, text: textSent, timestamp: time };
      
      const tempChat: any = {
        id: tempChatId,
        title: chatTitle,
        category: targetCategory,
        messages: [tempMsg],
        created: new Date().toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }),
        selected_project: null,
        is_confirmed: false,
        project_id: null
      };

      setChats((prev) => [tempChat, ...prev]);
      setActiveChatId(tempChatId);
      setActiveProjectId(null);
      setShowRightPane(false);

      // Now create on backend
      try {
        const token = localStorage.getItem("token");
        if (!token) {
          setAiTyping(false);
          return;
        }
        
        const res = await fetch(`${API_BASE}/api/chats`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
          },
          body: JSON.stringify({ 
            category: targetCategory, 
            title: chatTitle, 
            selected_project: null 
          })
        });
        if (res.ok) {
          const newChat = await res.json();
          // Swap temp ID with real ID, clearing messages so addMessageToChat doesn't duplicate them
          setChats((prev) => 
            prev.map((c) => c.id === tempChatId ? { ...newChat, messages: [] } : c)
          );
          setActiveChatId(newChat.id);
          // Send to trigger AI response
          await addMessageToChat(newChat.id, "user", textSent);
        } else {
          throw new Error("Failed to create chat");
        }
      } catch (err) {
        console.error("Optimistic chat creation failed:", err);
        // Rollback
        setChats((prev) => prev.filter((c) => c.id !== tempChatId));
        setActiveChatId(null);
        setCurrentInput(textSent);
      } finally {
        setAiTyping(false);
      }
    } else {
      // Regular message sending
      try {
        await addMessageToChat(targetChatId!, "user", textSent);
      } catch (e) {
        console.error("Send message failed:", e);
      } finally {
        setAiTyping(false);
      }
    }
  };

  const handleGenerateClick = async (category: string) => {
    if (!activeChatId) return;
    const name = projectNameInput.trim() || `${category.charAt(0).toUpperCase() + category.slice(1)} Workspace`;
    await generateProject(activeChatId, name, category, undefined, undefined, undefined, true, "full_stack");
    setProjectNameInput("");
  };

  const handleSuggestProject = async () => {
    if (!modalPrompt.trim()) return;
    setIsSuggesting(true);
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API_BASE}/api/projects/suggest-blueprint`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          idea: modalPrompt.trim(),
          generation_type: modalGenType
        })
      });
      if (res.ok) {
        const blueprint = await res.json();
        setModalName(blueprint.name || "");
        setModalIdea(blueprint.idea || "");
        if (blueprint.features && Array.isArray(blueprint.features)) {
          const feats = [...blueprint.features];
          while (feats.length < 3) feats.push("");
          setModalFeatures(feats.slice(0, 3));
        }
        setModalTechStack(blueprint.tech_stack || "React, Tailwind CSS, FastAPI, MongoDB");
      } else {
        console.error("Failed to suggest project details");
      }
    } catch (err) {
      console.error("Error suggesting project details:", err);
    } finally {
      setIsSuggesting(false);
    }
  };

  const handleModalSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!modalName.trim() || !modalIdea.trim()) return;
    if (!activeChatId) return;

    const blueprintData = {
      name: modalName.trim(),
      idea: modalIdea.trim(),
      features: modalFeatures.map(f => f.trim()).filter(Boolean),
      tech_stack: modalTechStack.trim(),
      hitl_enabled: modalHitlEnabled,
      generation_type: modalGenType
    };

    try {
      await updateChatSelectedProject(activeChatId, blueprintData);
      setActiveProjectId(null);
      setShowRightPane(true);
      setShowCreateModal(false);
      // Reset modal fields for next time
      setModalPrompt("");
      setModalName("");
      setModalIdea("");
      setModalFeatures(["", "", ""]);
      setModalTechStack("React, Tailwind CSS, FastAPI, MongoDB");
      setModalHitlEnabled(true);
      setModalGenType("full_stack");
    } catch (err) {
      console.error("Failed to submit modal blueprint:", err);
    }
  };

  if (isMinimized && !isMobile) {
    return (
      <motion.div 
        drag 
        dragMomentum={false} 
        dragListener={false} 
        dragControls={dragControls}
        dragConstraints={{ left: -1000, right: 10, top: -1000, bottom: 10 }}
        className="absolute bottom-6 right-8 z-50 flex flex-col items-end gap-4 pointer-events-none"
      >
        {/* Expanded Chat Overlay */}
        <AnimatePresence>
          {isFloatingExpanded && (
            <motion.div
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 20, scale: 0.95 }}
              transition={{ duration: 0.2, ease: "easeOut" }}
              className="w-[380px] h-[500px] max-w-[calc(100vw-3rem)] max-h-[calc(100vh-8rem)] bg-gradient-to-br from-indigo-950 via-teal-900 to-indigo-950 rounded-2xl shadow-2xl border border-amber-500/40 overflow-hidden flex flex-col pointer-events-auto"
            >
              <div 
                onPointerDown={(e) => dragControls.start(e)}
                className="h-14 border-b border-amber-500/20 bg-black/20 flex items-center justify-between px-4 shrink-0 cursor-grab active:cursor-grabbing"
              >
                <div className="flex items-center gap-2">
                  <FloatingBot className="w-8 h-8 drop-shadow-md" />
                  <span className="text-sm font-bold text-amber-500">Sarthi</span>
                  {aiTyping && <AiTypingWave className="flex items-center gap-0.5 ml-1" />}
                </div>
                <button onClick={() => setIsFloatingExpanded(false)} className="text-stone-300 hover:text-white transition-colors">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
                </button>
              </div>
              
              {/* Messages Area */}
              <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4 bg-transparent scrollbar-thin scrollbar-thumb-white/20">
                <AnimatePresence initial={false}>
                  {activeChat?.messages.map((msg, idx) => {
                    const isUserMsg = msg.sender === "user";
                    return (
                      <motion.div
                        key={msg.id || idx}
                        variants={msgVariants}
                        initial="initial"
                        animate="animate"
                        className={`flex flex-col max-w-[85%] ${isUserMsg ? "self-end" : "self-start"}`}
                      >
                        <div className={`p-3 rounded-2xl text-[13px] leading-relaxed shadow-sm ${isUserMsg ? "bg-indigo-950/95 text-amber-500 border border-indigo-500/50 shadow-inner backdrop-blur-sm rounded-tr-sm" : "bg-stone-50 text-stone-800 border border-stone-200/60 shadow-md rounded-tl-sm"}`}>
                          <MarkdownRenderer text={msg.text} />
                        </div>
                      </motion.div>
                    );
                  })}
                  {aiTyping && (
                    <motion.div variants={msgVariants} initial="initial" animate="animate" className="self-start">
                      <div className="p-4 rounded-2xl rounded-tl-sm bg-stone-50 text-stone-800 border border-stone-200/60 shadow-md flex items-center gap-2">
                        <FloatingBot className="w-5 h-5 opacity-80" />
                        <AiTypingWave />
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
                <div ref={messagesEndRef} />
              </div>

              {/* Input Area */}
              <div className="p-3 bg-black/20 border-t border-amber-500/20 shrink-0">
                <form onSubmit={handleSendMessage} className="flex items-center gap-2">
                  <textarea
                    rows={1}
                    placeholder={aiTyping ? "Sarthi is thinking..." : "Message Sarthi..."}
                    value={currentInput}
                    onChange={(e) => setCurrentInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={aiTyping}
                    onFocus={() => setInputFocused(true)}
                    onBlur={() => setInputFocused(false)}
                    className="flex-1 bg-white/10 backdrop-blur-md border border-white/20 rounded-xl px-3 py-2 text-xs text-white placeholder:text-stone-300 focus:outline-none focus:border-amber-500 transition-colors resize-none overflow-y-auto"
                  />
                  <button
                    type="submit"
                    disabled={!currentInput.trim() || aiTyping}
                    className="p-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-indigo-950 font-bold border border-amber-300 shadow-sm transition-colors disabled:opacity-50 shrink-0"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </form>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Floating Action Button (FAB) */}
        <motion.button
          layout
          onPointerDown={(e) => dragControls.start(e)}
          onClick={() => setIsFloatingExpanded(!isFloatingExpanded)}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="w-14 h-14 bg-stone-50 rounded-full shadow-lg border border-stone-200/60 flex items-center justify-center pointer-events-auto relative overflow-hidden group cursor-grab active:cursor-grabbing"
        >
          <div className="absolute inset-0 bg-indigo-50/50 opacity-0 group-hover:opacity-100 transition-opacity" />
          <FloatingBot className="w-10 h-10 relative z-10 pointer-events-none" />
        </motion.button>
      </motion.div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-full bg-transparent relative overflow-hidden transition-colors duration-300 z-0">
      {/* Actual Morpankh (Peacock Feather) Global Animated Motif */}
      <MorpankhBg />

      {/* Top Header */}
      <header className="h-16 px-6 border-b border-stone-200/60 bg-white/30 backdrop-blur-md flex items-center justify-between shrink-0 select-none z-10 transition-colors duration-300 relative">
        <div className="flex items-center gap-2">
          {!showLeftPane && !isMobile && (
            <motion.button
              type="button"
              onClick={() => setShowLeftPane(true)}
              whileHover={{ scale: 1.06 }}
              whileTap={{ scale: 0.93 }}
              className="p-1.5 rounded-lg border border-indigo-200 bg-indigo-50/50 text-indigo-950 transition-all flex items-center justify-center cursor-pointer mr-2"
              title="Expand Sidebar"
            >
              <PanelLeft className="w-4 h-4" />
            </motion.button>
          )}
          <SarthiLogo className="text-2xl" />
        </div>

        <div className="flex items-center gap-4 text-xs font-semibold text-stone-500">
          <motion.button
            onClick={() => setShowAbout(true)}
            whileHover={{ color: "#1c1917" }}
            className="hover:text-stone-800 transition-colors"
          >
            About
          </motion.button>
          <span className="text-stone-300">/</span>
          <motion.button
            onClick={() => setShowContact(true)}
            whileHover={{ color: "#1c1917" }}
            className="hover:text-stone-800 transition-colors"
          >
            Contact
          </motion.button>
          <span className="text-stone-300">/</span>
          <motion.button
            onClick={() => setShowFeedbackModal(true)}
            whileHover={{ color: "#1c1917" }}
            className="hover:text-indigo-900 text-indigo-650 font-bold transition-colors"
          >
            Feedback
          </motion.button>


          <div className="flex items-center gap-2 border-l border-stone-200/60 pl-4 ml-1">
            {(activeProjectId || (activeChatId && activeChat?.selected_project)) && !isMobile && (
              <motion.button
                type="button"
                onClick={() => setShowRightPane(!showRightPane)}
                whileHover={{ scale: 1.06 }}
                whileTap={{ scale: 0.93 }}
                className={`p-1.5 rounded-lg border transition-all duration-300 flex items-center justify-center cursor-pointer ${showRightPane
                  ? "border-stone-200 bg-stone-50 text-stone-500 hover:text-stone-800"
                  : "border-indigo-200 bg-indigo-50/50 text-indigo-950"
                  }`}
                title={showRightPane ? "Collapse Project Panel" : "Expand Project Panel"}
              >
                <motion.div
                  animate={{ rotate: showRightPane ? 0 : 180 }}
                  transition={{ duration: 0.35, ease: [0.4, 0, 0.2, 1] }}
                >
                  <PanelRight className="w-4 h-4" />
                </motion.div>
              </motion.button>
            )}
          </div>
        </div>
      </header>

      {/* Main Container Workspace */}
      <div className="flex-1 overflow-y-auto flex flex-col relative bg-transparent">
        {/* LOCK SCREEN OVERLAY */}
        {!user && (
          <div
            onClick={handleLockClick}
            className="absolute inset-0 bg-white/20 backdrop-blur-lg z-20 flex flex-col items-center justify-center p-8 cursor-pointer select-none overflow-hidden"
          >
            {/* Animated wave background */}
            <WaveBackground 
              className="absolute inset-0 w-full h-full pointer-events-none" 
              status={activeProj?.status}
              progress={activeProj?.progress}
            />

            <motion.div
              animate={shakeLock ? { x: [-6, 6, -6, 6, 0] } : {}}
              transition={{ duration: 0.4 }}
              className="max-w-md w-full text-center space-y-5 relative z-10"
            >
              {/* Floating lock card */}
              <motion.div
                animate={{ y: [-6, 6, -6] }}
                transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
              >
                <LockIllustration className="mx-auto" />
              </motion.div>

              <h3 className="text-xl font-bold font-display text-stone-800">
                Unlock Workspace Co-Pilot
              </h3>
              <p className="text-xs text-stone-500 leading-relaxed max-w-sm mx-auto">
                Sarthi is currently locked. Register or sign in with your email to launch project generation panels and interact with the AI co-pilot.
              </p>

              {/* Shimmer CTA button */}
              <motion.button
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
                className="relative overflow-hidden bg-indigo-900 hover:bg-stone-800 text-white text-xs font-bold px-8 py-3.5 rounded-xl transition-all shadow-md"
              >
                <motion.span
                  className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent"
                  animate={{ x: ["-100%", "200%"] }}
                  transition={{ duration: 2, repeat: Infinity, ease: "linear", repeatDelay: 1 }}
                />
                Access Sarthi Sandbox
              </motion.button>

              {/* Circuit decor */}
              <div className="flex justify-center mt-2 opacity-60">
                <CircuitDecor className="w-24 h-14" />
              </div>
            </motion.div>
          </div>
        )}

        {/* 1. Landing Welcome layout */}
        {!activeChat ? (
          isGeneratingProject && workspaceMode === "docs" ? (
            <div className="flex-1 flex flex-col justify-center items-center p-8 select-none">
              <div className="max-w-md w-full text-center space-y-6">
                <div className="relative w-20 h-20 mx-auto">
                  <span className="absolute inset-0 rounded-full border-4 border-indigo-100 animate-pulse" />
                  <span className="absolute inset-0 rounded-full border-4 border-t-indigo-700 border-r-transparent border-b-transparent border-l-transparent animate-spin" />
                </div>
                <div className="space-y-2">
                  <h3 className="text-lg font-bold text-stone-850">Compiling Product Requirements</h3>
                  <p className="text-xs text-stone-500 font-semibold animate-pulse h-8">
                    {docLoadingSteps[loadingStep]}
                  </p>
                </div>
                <div className="w-full h-1.5 bg-stone-100 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-indigo-950 rounded-full"
                    animate={{ width: `${(loadingStep + 1) * 20}%` }}
                    transition={{ duration: 0.8, ease: "easeOut" }}
                  />
                </div>
                <span className="text-[10px] uppercase font-bold tracking-widest text-amber-500">
                  Sarthi documents compiler v1.0
                </span>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex flex-col justify-center items-center p-8 select-none overflow-y-auto bg-transparent relative z-10">
              <div className="max-w-2xl w-full text-center space-y-8 my-auto">
                <motion.div
                  initial={{ scale: 0.9, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ duration: 0.5, ease: "easeOut" }}
                  className="mx-auto flex justify-center items-center mb-6"
                >
                  <SarthiLogo className="text-6xl drop-shadow-lg" />
                </motion.div>

                <motion.div
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: 0.1, ease: "easeOut" }}
                >
                  <h1 className="text-3xl font-extrabold font-display text-stone-850 tracking-tight">
                    Sarthi AI Workspace
                  </h1>
                  <p className="text-xs text-stone-450 mt-2 max-w-md mx-auto leading-relaxed font-semibold">
                    Build action-taking agents with Gemini orchestration, MongoDB MCP evidence, PRD/MRD/TRD specs, and runnable Flask prototypes.
                  </p>
                </motion.div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 max-w-xl mx-auto pt-2">
                  {[
                    {
                      title: "Fraud Review Agent",
                      desc: "Route suspicious transactions into approval workflows.",
                      prompt: "Build a financial services fraud review agent that stores transactions, flags suspicious activity, opens human approval tasks, and records every decision for audit review using MongoDB."
                    },
                    {
                      title: "World Cup Fan Ops",
                      desc: "Coordinate match-day travel, queues, and alerts.",
                      prompt: "Create a 2026 World Cup fan logistics agent that plans stadium arrival windows, tracks crowd alerts, recommends transit routes, and updates a MongoDB-backed itinerary checklist."
                    },
                    {
                      title: "Mall Ops Agent",
                      desc: "Automate tenant campaigns and facility tasks.",
                      prompt: "Build a brick-and-mortar mall operations agent that logs maintenance requests, schedules tenant promotions, monitors shopper traffic surges, and assigns follow-up tasks."
                    },
                    {
                      title: "Local Business Surge",
                      desc: "Help stores react to tourist demand spikes.",
                      prompt: "Design a local business surge assistant that forecasts tourist demand, creates staffing checklists, records inventory risks, and drafts hyper-local campaign actions."
                    }
                  ].map((item, idx) => (
                    <motion.button
                      key={idx}
                      initial={{ opacity: 0, y: 12 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.4, delay: 0.15 + idx * 0.05 }}
                      whileHover={{ y: -2, scale: 1.01 }}
                      whileTap={{ scale: 0.99 }}
                      type="button"
                      onClick={() => {
                        setCurrentInput(item.prompt);
                        const inputEl = document.getElementById("chat-input-bar");
                        if (inputEl) {
                          inputEl.focus();
                        }
                      }}
                      className="p-4 text-left bg-white border border-stone-200/60 rounded-2xl shadow-sm hover:shadow-[0_8px_30px_rgb(0,0,0,0.06)] hover:border-indigo-200 transition-all cursor-pointer flex flex-col justify-between relative z-10 group"
                    >
                      <span className="text-xs font-bold text-indigo-950 mb-1">{item.title}</span>
                      <span className="text-[10px] text-stone-500 font-semibold leading-relaxed">{item.desc}</span>
                    </motion.button>
                  ))}
                </div>
              </div>
            </div>
          )
        ) : (
          /* 2. Active Chat Messages list */
          <div className="flex-1 p-3 md:p-6 space-y-4 md:space-y-6 overflow-y-auto bg-transparent relative z-10">
            {activeChat.messages.map((m, idx) => {
              const isUser = m.sender === "user";
              const blueprintMatch = m.text.match(/<blueprint>([\s\S]*?)<\/blueprint>/);
              let blueprintData = null;
              if (blueprintMatch) {
                try {
                  let jsonString = blueprintMatch[1].trim();
                  // Remove markdown backticks if AI added them
                  if (jsonString.startsWith("```json")) {
                    jsonString = jsonString.replace(/^```json\s*/, "").replace(/\s*```$/, "");
                  } else if (jsonString.startsWith("```")) {
                    jsonString = jsonString.replace(/^```\s*/, "").replace(/\s*```$/, "");
                  }
                  blueprintData = JSON.parse(jsonString);
                } catch (e) {
                  // Ignore parsing errors silently (expected during streaming/typing)
                }
              }
              const cleanedText = m.text.replace(/<blueprint>[\s\S]*?<\/blueprint>/g, "").trim();
              
              if (!cleanedText && !blueprintData && !isUser) return null; // FIX: Prevent empty AI bubbles

              return (
                <motion.div
                  key={m.id}
                  variants={msgVariants}
                  initial="initial"
                  animate="animate"
                  className={`flex gap-3 max-w-[85%] md:max-w-xl ${isUser ? "ml-auto flex-row-reverse" : ""}`}
                >
                  {/* Avatar */}
                  {isUser ? (
                    <div className="w-7 h-7 rounded-lg shrink-0 flex items-center justify-center font-bold text-[10px] text-white uppercase shadow-sm bg-gradient-to-tr from-amber-500 to-rose-500 select-none">
                      {user?.name?.charAt(0)}
                    </div>
                  ) : (
                    <SarthiLogo className="w-7 h-7 shrink-0" />
                  )}

                  <div className="space-y-1 w-full">
                    <div
                      className={`p-3.5 rounded-2xl text-xs leading-relaxed select-text ${editingMessageId === m.id ? "w-full" : ""
                        } ${isUser
                          ? "bg-indigo-950 text-stone-100 border border-indigo-900 shadow-sm rounded-tr-none"
                          : "bg-white text-stone-800 border border-stone-200 shadow-sm rounded-tl-none"
                        }`}
                    >
                      {editingMessageId === m.id ? (
                        <div className="flex flex-col gap-2 w-full">
                          <textarea
                            value={editingText}
                            onChange={(e) => setEditingText(e.target.value)}
                            className={`w-full border rounded-xl p-2.5 text-xs font-sans leading-relaxed resize-y min-h-[140px] focus:outline-none focus:ring-2 ${isUser
                              ? "bg-indigo-950 text-white border-amber-500 focus:ring-white/20"
                              : "bg-stone-50 text-stone-850 border-stone-200 focus:ring-amber-500/20 focus:border-amber-500"
                              }`}
                          />
                          <div className="flex justify-end gap-2">
                            <button
                              type="button"
                              onClick={() => setEditingMessageId(null)}
                              className={`px-2.5 py-1 rounded-lg text-[10px] font-semibold transition-colors cursor-pointer ${isUser
                                ? "bg-indigo-950/50 hover:bg-indigo-950 text-indigo-100 hover:text-white"
                                : "bg-stone-100 hover:bg-stone-200 text-stone-600"
                                }`}
                            >
                              Cancel
                            </button>
                            <button
                              type="button"
                              onClick={async () => {
                                if (editingText.trim()) {
                                  await editMessageText(activeChatId!, m.id, editingText.trim());
                                  setEditingMessageId(null);
                                }
                              }}
                              className={`px-2.5 py-1 rounded-lg text-[10px] font-semibold transition-colors cursor-pointer ${isUser
                                ? "bg-stone-50 hover:bg-indigo-50 text-indigo-950"
                                : "bg-gradient-to-r from-indigo-950 via-indigo-900 to-amber-500 hover:from-indigo-900 hover:via-indigo-900 hover:to-amber-500 text-white"
                                }`}
                            >
                              Save
                            </button>
                          </div>
                        </div>
                      ) : isUser ? (
                        <div className="whitespace-pre-line text-stone-100 font-medium break-words leading-relaxed select-text">{cleanedText}</div>
                      ) : (
                        <div className="space-y-2">
                          {cleanedText && <MarkdownRenderer text={cleanedText} />}
                          {blueprintData && (
                            <div className="mt-2 p-3.5 bg-stone-50 border border-indigo-100/80 rounded-xl shadow-[0_2px_10px_-4px_rgba(79,70,229,0.1)] hover:shadow-md hover:border-indigo-200 transition-all">
                              <div className="flex items-center justify-between mb-2.5">
                                <div className="flex items-center gap-1.5">
                                  <span className="w-4 h-4 rounded bg-indigo-50 flex items-center justify-center text-[9px] text-indigo-950 font-bold border border-indigo-100">B</span>
                                  <h4 className="text-[10px] font-bold text-indigo-950 uppercase tracking-wider">Suggested Blueprint</h4>
                                </div>
                                <button 
                                  onClick={() => {
                                    if (blueprintData && activeChatId) {
                                      updateChatSelectedProject(activeChatId, blueprintData);
                                    }
                                    setActiveProjectId(null);
                                    setShowRightPane(true);
                                  }}
                                  className="text-[9px] bg-indigo-950 text-white px-2.5 py-1 rounded-md shadow-sm font-bold hover:bg-indigo-900 transition-colors flex items-center gap-1"
                                >
                                  Confirm Blueprint
                                </button>
                              </div>
                              <p className="text-xs font-bold text-stone-850 leading-tight">{blueprintData.name}</p>
                              <p className="text-[10px] text-stone-500 mt-1 leading-relaxed line-clamp-2">{blueprintData.idea}</p>
                              {blueprintData.features && Array.isArray(blueprintData.features) && (
                                <div className="mt-3 flex flex-wrap gap-1.5">
                                  {blueprintData.features.slice(0, 3).map((f: string, i: number) => (
                                    <span key={i} className="px-2 py-1 bg-stone-50 text-stone-600 border border-stone-200/60 rounded-md text-[9px] font-medium leading-none">{f}</span>
                                  ))}
                                  {blueprintData.features.length > 3 && (
                                    <span className="px-2 py-1 bg-stone-50 text-stone-600 border border-stone-200/60 rounded-md text-[9px] font-medium leading-none">
                                      +{blueprintData.features.length - 3} more
                                    </span>
                                  )}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      )}
                    </div>

                    <div className={`flex items-center gap-2 mt-1 ${isUser ? "justify-end" : "justify-start"}`}>
                      <span className="text-[9px] text-stone-400">{m.timestamp}</span>
                      <span className="text-stone-300 text-[8px] select-none">•</span>
                      <button
                        type="button"
                        onClick={() => handleCopyMessage(m.id, cleanedText)}
                        className="text-[9px] text-stone-400 hover:text-stone-700 hover:underline transition-colors font-medium cursor-pointer"
                      >
                        {copiedMessageId === m.id ? "Copied!" : "Copy"}
                      </button>
                      <span className="text-stone-300 text-[8px] select-none">•</span>
                      <button
                        type="button"
                        onClick={() => {
                          setEditingMessageId(m.id);
                          setEditingText(cleanedText);
                        }}
                        className="text-[9px] text-stone-400 hover:text-stone-700 hover:underline transition-colors font-medium cursor-pointer"
                      >
                        Edit
                      </button>
                    </div>
                  </div>
                </motion.div>
              );
            })}

            {/* AI Typing — wave bars */}
            {aiTyping && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex gap-3 max-w-xl"
              >
                <SarthiLogo className="w-7 h-7 shrink-0" />
                <div className="bg-stone-50 text-stone-600 border border-stone-200/60 px-4 py-3 rounded-2xl rounded-tl-none flex items-center gap-2 shrink-0 shadow-sm">
                  <AiTypingWave />
                  <span className="text-[10px] text-stone-500 font-medium ml-1 animate-pulse">Sarthi is thinking...</span>
                  <span className="animate-cursor-blink text-amber-500 text-xs font-bold">|</span>
                </div>
              </motion.div>
            )}

            <div ref={chatEndRef} />
          </div>
        )}
      </div>

      {/* Input Area Console */}
      <footer className="p-4 border-t border-stone-200/60 bg-stone-50/40 backdrop-blur-md shrink-0 relative select-none transition-colors duration-300">
        <div className="max-w-3xl mx-auto flex flex-col gap-2">
          {/* Create Project Helper / Tip Bar */}
          {user && activeChatId && (
            <div className="text-[10px] text-stone-500 font-medium flex items-center gap-1.5 px-1 pb-1">
              <Sparkles className="w-3.5 h-3.5 text-indigo-600 animate-pulse" />
              <span>Click <strong className="text-indigo-950 font-bold">Create Project</strong> to open the wizard, suggest details using AI, and configure your blueprint to build.</span>
            </div>
          )}
          
          <form 
            onSubmit={user ? handleSendMessage : (e) => { e.preventDefault(); handleLockClick(); }}
            onClick={!user ? handleLockClick : undefined}
            className={`flex items-center gap-3 w-full ${!user ? 'cursor-pointer' : ''}`}
          >
            {/* Text Input with focus glow */}
            <div className="flex-1 relative">
              <textarea
                id="chat-input-bar"
                rows={1}
                placeholder={!user ? "Please sign in or sign up to start chatting with Sarthi..." : activeChat?.is_paused ? "Chat is paused. Click 'Resume' to send messages..." : "Share your project idea here (features, tech stack, or vision)..."}
                value={currentInput}
                readOnly={!user}
                onChange={(e) => {
                  if (!user) return;
                  setCurrentInput(e.target.value);
                  e.target.style.height = 'auto';
                  e.target.style.height = `${Math.min(e.target.scrollHeight, 160)}px`;
                }}
                onKeyDown={user ? handleKeyDown : undefined}
                disabled={activeChat?.is_paused}
                onFocus={() => {
                  if (!user) {
                    handleLockClick();
                    return;
                  }
                  setInputFocused(true);
                }}
                onBlur={() => setInputFocused(false)}
                className={`w-full bg-stone-50 border border-stone-200 rounded-xl pl-4 pr-12 py-2.5 text-xs text-stone-800 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 transition-all duration-300 resize-none overflow-y-auto scrollbar-none max-h-[160px] align-middle ${!user ? 'cursor-pointer' : ''}`}
              />
              {/* Focus glow ring */}
              <AnimatePresence>
                {inputFocused && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.98 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.98 }}
                    className="absolute inset-0 rounded-xl ring-2 ring-indigo-400/20 pointer-events-none"
                  />
                )}
              </AnimatePresence>

              {/* Pause/Resume button inside chatbox */}
              {user && activeChatId && !aiTyping && (
                <button
                  type="button"
                  onClick={() => activeChat && togglePauseChat(activeChat.id)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-lg hover:bg-stone-200/60 text-stone-605 transition-all cursor-pointer z-20 flex items-center justify-center"
                  title={activeChat?.is_paused ? "Resume Chat" : "Pause Chat"}
                >
                  {activeChat?.is_paused ? <Play className="w-4 h-4 text-emerald-600 animate-pulse" /> : <Pause className="w-4 h-4 text-amber-600" />}
                </button>
              )}
            </div>

            {/* Create Project button */}
            {user && activeChatId && (
              <button
                type="button"
                onClick={() => setShowCreateModal(true)}
                className="p-2.5 sm:px-4 sm:py-2.5 rounded-xl border border-indigo-200 bg-indigo-50 hover:bg-indigo-100 text-indigo-950 font-bold transition-colors shadow-sm flex items-center gap-2 cursor-pointer shrink-0"
                title="Create Project: Open the project creator wizard and describe your idea."
              >
                <FolderPlus className="w-4 h-4 text-indigo-950" />
                <span className="hidden sm:inline text-xs">Create Project</span>
              </button>
            )}

            {/* Stop button */}
            {user && activeChatId && aiTyping && (
              <button
                type="button"
                onClick={() => stopChatGeneration(activeChatId)}
                className="p-2.5 rounded-xl border border-rose-200 bg-rose-50 hover:bg-rose-100 text-rose-700 transition-colors shadow-sm flex items-center justify-center cursor-pointer shrink-0"
                title="Stop Generation"
              >
                <Square className="w-4 h-4" />
              </button>
            )}

            {/* Send button */}
            <motion.button
              type="submit"
              disabled={!!user && (!currentInput.trim() || aiTyping || activeChat?.is_paused)}
              whileHover={!user || (currentInput.trim() && !aiTyping && !activeChat?.is_paused) ? { scale: 1.08, rotate: -8 } : {}}
              whileTap={!user || (currentInput.trim() && !aiTyping && !activeChat?.is_paused) ? { scale: 0.92 } : {}}
              transition={{ type: "spring", stiffness: 400, damping: 22 }}
              className="p-2.5 rounded-xl bg-indigo-950 hover:bg-indigo-900 text-amber-500 font-bold tracking-wide border border-indigo-900/50 shadow-inner transition-colors disabled:opacity-50"
            >
              <Send className="w-4 h-4" />
            </motion.button>
          </form>
        </div>
      </footer>

      {/* Floating Create Project Modal */}
      <AnimatePresence>
        {showCreateModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowCreateModal(false)}
              className="absolute inset-0 bg-stone-900/60 backdrop-blur-sm"
            />

            {/* Modal Body */}
            <motion.div
              initial={{ scale: 0.95, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.95, opacity: 0, y: 20 }}
              transition={{ type: "spring", stiffness: 350, damping: 30 }}
              className="relative w-full max-w-xl bg-white border border-stone-200/80 rounded-2xl shadow-2xl z-10 flex flex-col max-h-[85vh] overflow-hidden"
            >
              {/* Header */}
              <div className="p-5 border-b border-stone-100 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-indigo-50 flex items-center justify-center border border-indigo-100">
                    <FolderPlus className="w-4 h-4 text-indigo-950" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-stone-850">Create New Project</h3>
                    <p className="text-[10px] text-stone-500">Configure your project blueprint manually or use AI suggestions.</p>
                  </div>
                </div>
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="p-1.5 hover:bg-stone-100 rounded-lg text-stone-400 hover:text-stone-700 transition-colors"
                >
                  <ChevronDown className="w-4 h-4 rotate-90" />
                </button>
              </div>

              {/* Form Content */}
              <div className="flex-1 overflow-y-auto p-6 space-y-5">
                {/* Generation Scope (Project Type Selection) */}
                <div className="space-y-2">
                  <label className="text-[10px] font-bold uppercase tracking-wider text-indigo-950 flex items-center gap-1.5">
                    1. Select Generation Scope
                  </label>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    {[
                      { id: "full_stack", label: "Full Stack", desc: "API + UI + DB" },
                      { id: "frontend_only", label: "Frontend Only", desc: "UI Components" },
                      { id: "backend_only", label: "Backend Only", desc: "API & Models" },
                      { id: "microservice", label: "Microservice", desc: "API Service / Worker" }
                    ].map((item) => (
                      <button
                        key={item.id}
                        type="button"
                        onClick={() => {
                          setModalGenType(item.id);
                          if (item.id === "frontend_only") {
                            setModalTechStack("Next.js, Tailwind CSS");
                          } else if (item.id === "backend_only") {
                            setModalTechStack("FastAPI, MongoDB");
                          } else if (item.id === "microservice") {
                            setModalTechStack("FastAPI, Docker, Redis");
                          } else {
                            setModalTechStack("React, Tailwind CSS, FastAPI, MongoDB");
                          }
                        }}
                        className={`flex flex-col items-center justify-center p-3 rounded-xl border text-center transition-all cursor-pointer ${
                          modalGenType === item.id
                            ? "border-indigo-950 bg-indigo-50/50 text-indigo-950 shadow-sm ring-1 ring-indigo-950/20"
                            : "border-stone-200 bg-stone-50 hover:bg-stone-100 text-stone-600"
                        }`}
                      >
                        <span className="text-xs font-bold">{item.label}</span>
                        <span className="text-[8px] mt-0.5 opacity-80">{item.desc}</span>
                      </button>
                    ))}
                  </div>
                </div>

                <div className="border-t border-stone-100 my-1" />

                {/* AI Suggestion Section */}
                <div className="p-4 bg-indigo-50/40 border border-indigo-100/60 rounded-xl space-y-3">
                  <div className="flex items-center justify-between">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-indigo-950 flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5 text-indigo-650 animate-pulse" />
                      2. Describe Project Idea
                    </label>
                  </div>
                  <div className="flex flex-col sm:flex-row gap-3">
                    <textarea
                      placeholder="Describe your project idea in a sentence or two... (e.g. 'A payment validation microservice that consumes stripe webhook payloads, validates signature, and publishes to RabbitMQ')"
                      value={modalPrompt}
                      onChange={(e) => setModalPrompt(e.target.value)}
                      rows={4}
                      className="flex-1 bg-white border border-stone-200 rounded-xl px-3 py-2 text-xs text-stone-800 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 transition-all font-medium resize-none leading-relaxed"
                    />
                    <button
                      type="button"
                      onClick={handleSuggestProject}
                      disabled={isSuggesting || !modalPrompt.trim()}
                      className="px-5 py-3 sm:py-2 bg-indigo-950 hover:bg-indigo-900 text-white font-bold rounded-xl text-xs flex items-center justify-center gap-1.5 transition-colors disabled:opacity-50 shrink-0 cursor-pointer sm:self-stretch animate-pulse-subtle"
                    >
                      {isSuggesting ? (
                        <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      ) : (
                        <Sparkles className="w-3.5 h-3.5" />
                      )}
                      <span>Suggest</span>
                    </button>
                  </div>
                </div>

                <div className="border-t border-stone-100 my-1" />

                {/* Editable Fields */}
                <form onSubmit={handleModalSubmit} className="space-y-4">
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-stone-450">Project Name</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. 'Habit Tracker Pro'"
                      value={modalName}
                      onChange={(e) => setModalName(e.target.value)}
                      className="w-full bg-stone-50 border border-stone-200 rounded-xl px-3 py-2 text-xs text-stone-800 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 transition-all font-semibold"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-stone-450">Core Idea / Description</label>
                    <textarea
                      required
                      rows={5}
                      placeholder="Refined vision and description of the app..."
                      value={modalIdea}
                      onChange={(e) => setModalIdea(e.target.value)}
                      className="w-full bg-stone-50 border border-stone-200 rounded-xl px-3 py-2 text-xs text-stone-850 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 transition-all resize-none font-medium leading-relaxed"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-stone-450">Key Features</label>
                    <div className="space-y-2">
                      {modalFeatures.map((f, idx) => (
                        <input
                          key={idx}
                          type="text"
                          placeholder={`Feature ${idx + 1} (e.g. 'Daily streak charts')`}
                          value={f}
                          onChange={(e) => {
                            const updated = [...modalFeatures];
                            updated[idx] = e.target.value;
                            setModalFeatures(updated);
                          }}
                          className="w-full bg-stone-50 border border-stone-200 rounded-xl px-3 py-2 text-xs text-stone-800 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 transition-all font-medium"
                        />
                      ))}
                    </div>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-stone-450">Tech Stack</label>
                    <input
                      type="text"
                      required
                      placeholder="React, FastAPI, MongoDB"
                      value={modalTechStack}
                      onChange={(e) => setModalTechStack(e.target.value)}
                      className="w-full bg-stone-50 border border-stone-200 rounded-xl px-3 py-2 text-xs text-stone-800 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 transition-all font-semibold"
                    />
                  </div>

                  {/* HITL Toggle Button */}
                  <div className="flex items-center justify-between p-3.5 bg-indigo-50/40 border border-indigo-100/60 rounded-xl">
                    <div className="flex flex-col text-left">
                      <span className="text-[10px] font-bold text-indigo-950 uppercase tracking-wider">Review Planning Blueprint</span>
                      <span className="text-[8px] text-stone-500 mt-0.5 leading-tight">Review file modification blueprint before building codebase</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => setModalHitlEnabled(!modalHitlEnabled)}
                      className="focus:outline-none cursor-pointer"
                    >
                      <svg width="36" height="20" viewBox="0 0 36 20" fill="none" className="transition-all duration-300">
                        <rect
                          width="36"
                          height="20"
                          rx="10"
                          fill={modalHitlEnabled ? "#312e81" : "#e7e5e4"}
                          className="transition-colors duration-300"
                        />
                        <circle
                          cx={modalHitlEnabled ? "26" : "10"}
                          cy="10"
                          r="7"
                          fill="white"
                          className="transition-all duration-300"
                        />
                      </svg>
                    </button>
                  </div>

                  {/* Submit Actions */}
                  <div className="flex items-center justify-end gap-3 pt-3 border-t border-stone-100">
                    <button
                      type="button"
                      onClick={() => setShowCreateModal(false)}
                      className="px-4 py-2 border border-stone-200 rounded-xl text-stone-600 hover:bg-stone-55 hover:text-stone-800 text-xs font-bold transition-all cursor-pointer"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={!modalName.trim() || !modalIdea.trim()}
                      className="px-5 py-2 bg-indigo-950 hover:bg-indigo-900 text-amber-500 font-bold rounded-xl text-xs transition-all disabled:opacity-50 cursor-pointer shadow-md"
                    >
                      Confirm & Create Project
                    </button>
                  </div>
                </form>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};
