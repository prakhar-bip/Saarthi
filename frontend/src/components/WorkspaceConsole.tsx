"use client";

import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useWorkspace, Message } from "@/context/WorkspaceContext";
import { CategoryIcon, LockIllustration, SarthiLogo, WaveBackground, AiTypingWave, CircuitDecor, EmptyStateIllustration } from "./CustomSvgs";
import { Send, Sparkles, BookOpen, AlertCircle, ChevronDown, Cpu, ShieldAlert, PanelRight, ChevronLeft, ChevronRight, PanelLeft } from "lucide-react";
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

export const WorkspaceConsole: React.FC = () => {
  const {
    user,
    chats,
    activeChatId,
    setActiveChatId,
    activeProjectId,
    setActiveProjectId,
    createNewChat,
    addMessageToChat,
    editMessageText,
    generateProject,
    currentCategory,
    setCurrentCategory,
    currentInput,
    setCurrentInput,
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
  } = useWorkspace();

  const [showCategoryDropdown, setShowCategoryDropdown] = useState(false);
  const [validationError, setValidationError] = useState(false);
  const [aiTyping, setAiTyping] = useState(false);
  const [shakeLock, setShakeLock] = useState(false);
  const [projectNameInput, setProjectNameInput] = useState("");

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
  const activeChat = chats.find((c) => c.id === activeChatId);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [activeChat?.messages?.length, aiTyping]);

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
    finance: "#10b981",
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

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;
    if (!currentInput.trim()) return;
    if (!currentCategory) {
      setValidationError(true);
      return;
    }

    let targetChatId = activeChatId;
    if (!activeChat) {
      const chatTitle = currentInput.length > 25 ? `${currentInput.slice(0, 25)}...` : currentInput;
      targetChatId = await createNewChat(currentCategory, chatTitle);
    }

    if (targetChatId) {
      const textSent = currentInput;
      setCurrentInput("");
      setAiTyping(true);
      try {
        await addMessageToChat(targetChatId, "user", textSent);
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
    await generateProject(activeChatId, name, category);
    setProjectNameInput("");
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-white relative overflow-hidden transition-colors duration-300">
      {/* Top Header */}
      <header className="h-16 px-6 border-b border-stone-200/60 bg-white/55 backdrop-blur-md flex items-center justify-between shrink-0 select-none z-10 transition-colors duration-300">
        <div className="flex items-center gap-2">
          {!showLeftPane && (
            <motion.button
              type="button"
              onClick={() => setShowLeftPane(true)}
              whileHover={{ scale: 1.06 }}
              whileTap={{ scale: 0.93 }}
              className="p-1.5 rounded-lg border border-indigo-200 bg-indigo-50/50 text-indigo-600 transition-all flex items-center justify-center cursor-pointer mr-2"
              title="Expand Sidebar"
            >
              <PanelLeft className="w-4 h-4" />
            </motion.button>
          )}
          <span className="w-2.5 h-2.5 rounded-full bg-indigo-500 animate-pulse-ring" />
          <h2 className="text-xs font-bold uppercase tracking-wider text-stone-500">Sarthi Workspace</h2>
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
          {user && (
            <>
              <span className="text-stone-300">/</span>
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex items-center gap-1.5 text-indigo-600 bg-indigo-50/50 border border-indigo-100/50 px-2.5 py-1 rounded-lg"
              >
                <Sparkles className="w-3 h-3" />
                <span>Hackathon Mode</span>
              </motion.div>
            </>
          )}

          <div className="flex items-center gap-2 border-l border-stone-200/60 pl-4 ml-1">
            {(activeProjectId || (activeChatId && activeChat?.selected_project)) && (
              <motion.button
                type="button"
                onClick={() => setShowRightPane(!showRightPane)}
                whileHover={{ scale: 1.06 }}
                whileTap={{ scale: 0.93 }}
                className={`p-1.5 rounded-lg border transition-all duration-300 flex items-center justify-center cursor-pointer ${showRightPane
                  ? "border-stone-200 bg-stone-50 text-stone-500 hover:text-stone-800"
                  : "border-indigo-200 bg-indigo-50/50 text-indigo-600"
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
      <div className="flex-1 overflow-y-auto flex flex-col relative bg-white">
        {/* LOCK SCREEN OVERLAY */}
        {!user && (
          <div
            onClick={handleLockClick}
            className="absolute inset-0 bg-white/80 backdrop-blur-lg z-20 flex flex-col items-center justify-center p-8 cursor-pointer select-none overflow-hidden"
          >
            {/* Animated wave background */}
            <WaveBackground className="absolute inset-0 w-full h-full pointer-events-none" />

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
                className="relative overflow-hidden bg-stone-900 hover:bg-stone-800 text-white text-xs font-bold px-8 py-3.5 rounded-xl transition-all shadow-md"
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
          !currentCategory ? (
            <div className="flex-1 flex flex-col justify-center items-center p-8 select-none">
              <div className="max-w-xl text-center space-y-8">
                <motion.div
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, ease: "easeOut" }}
                >
                  <span className="inline-flex items-center gap-1 bg-indigo-50 text-indigo-600 border border-indigo-100/40 text-[10px] uppercase font-bold tracking-widest px-2.5 py-1 rounded-full">
                    <Sparkles className="w-3 h-3" />
                    Your AI Development Guide
                  </span>
                  <h1 className="text-3xl font-bold font-display text-stone-850 mt-3 tracking-tight">
                    Design & Build Faster with Sarthi
                  </h1>
                  <p className="text-xs text-stone-400 mt-2 max-w-sm mx-auto leading-relaxed">
                    Select a category domain to brainstorm project suggestions and compile complete prototypes.
                  </p>
                </motion.div>

                {/* Category Grid */}
                <div className="grid grid-cols-2 gap-3">
                  {categories.map((cat, idx) => (
                    <motion.button
                      key={cat.id}
                      initial={{ opacity: 0, y: 16 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.4, delay: 0.06 * idx, ease: "easeOut" }}
                      whileHover={{ y: -3, scale: 1.02, transition: { type: "spring", stiffness: 400, damping: 20 } }}
                      whileTap={{ scale: 0.97 }}
                      onClick={() => handleCategorySelect(cat.id)}
                      className="relative p-4 text-left rounded-2xl border border-stone-200/50 bg-stone-50/20 text-stone-700 hover:bg-white hover:shadow-md hover:border-stone-200 transition-all cursor-pointer overflow-hidden group"
                    >
                      {/* Colored left-border accent on hover */}
                      <motion.div
                        className="absolute left-0 top-0 bottom-0 w-0.5 rounded-full"
                        style={{ backgroundColor: categoryAccents[cat.id] ?? "#6366f1" }}
                        initial={{ scaleY: 0 }}
                        whileHover={{ scaleY: 1 }}
                        transition={{ duration: 0.25 }}
                      />
                      <div className="flex items-center gap-2">
                        <motion.div
                          className="p-1.5 rounded-lg bg-stone-100 text-stone-500 group-hover:bg-indigo-50 group-hover:text-indigo-600 transition-colors duration-200"
                          whileHover={{ rotate: [0, -8, 8, 0] }}
                          transition={{ duration: 0.4 }}
                        >
                          <CategoryIcon category={cat.id} className="w-4 h-4" />
                        </motion.div>
                        <span className="text-xs font-bold truncate">{cat.label}</span>
                      </div>
                      <p className="text-[10px] text-stone-400 mt-2 leading-relaxed truncate">
                        {cat.desc}
                      </p>
                    </motion.button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex flex-col p-8 overflow-y-auto max-w-4xl mx-auto w-full select-none justify-center">
              <div className="w-full space-y-6">
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.35 }}
                  className="flex items-center justify-between"
                >
                  <div>
                    <h2 className="text-xl font-bold font-display text-stone-850">
                      Project Blueprints
                    </h2>
                    <p className="text-xs text-stone-400 mt-1">
                      Choose an idea in <span className="capitalize font-bold text-indigo-600">{currentCategory}</span> to start interactive discussion
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <motion.button
                      type="button"
                      onClick={() => fetchSuggestions(currentCategory)}
                      disabled={isFetchingSuggestions}
                      whileHover={{ scale: 1.03 }}
                      whileTap={{ scale: 0.96 }}
                      className="px-3.5 py-2 border border-indigo-200 bg-indigo-50/50 rounded-xl text-[10px] font-bold text-indigo-600 hover:text-indigo-800 hover:bg-indigo-100/55 transition-all cursor-pointer shadow-sm flex items-center gap-1"
                    >
                      <motion.span
                        animate={isFetchingSuggestions ? { rotate: 360 } : {}}
                        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                      >
                        <Sparkles className="w-3 h-3" />
                      </motion.span>
                      <span>{isFetchingSuggestions ? "Suggesting..." : "Suggest More"}</span>
                    </motion.button>
                    <motion.button
                      type="button"
                      onClick={() => {
                        setCurrentCategory("");
                        clearSuggestions();
                      }}
                      whileHover={{ scale: 1.03 }}
                      whileTap={{ scale: 0.96 }}
                      className="px-3.5 py-2 border border-stone-200 rounded-xl text-[10px] font-bold text-stone-500 hover:text-stone-800 hover:bg-stone-50 transition-all cursor-pointer shadow-sm"
                    >
                      ← Back to Categories
                    </motion.button>
                  </div>
                </motion.div>

                {isFetchingSuggestions ? (
                  <div className="flex flex-col items-center justify-center p-8 bg-stone-50/10 border border-stone-200/60 rounded-3xl min-h-[380px] max-w-2xl mx-auto w-full space-y-6">
                    <div className="h-6 bg-stone-200 rounded-md w-1/3 animate-shimmer" />
                    <div className="h-8 bg-stone-200 rounded-md w-3/4 animate-shimmer" />
                    <div className="h-4 bg-stone-100 rounded-md w-full animate-shimmer" />
                    <div className="h-4 bg-stone-100 rounded-md w-5/6 animate-shimmer" />
                    <div className="w-full pt-6 border-t border-stone-100 flex gap-3">
                      <div className="h-8 bg-stone-100 rounded-lg w-20 animate-shimmer" />
                      <div className="h-8 bg-stone-100 rounded-lg w-28 animate-shimmer" />
                    </div>
                  </div>
                ) : suggestions.length > 0 ? (
                  <div className="flex flex-col items-center justify-center py-4 w-full max-w-4xl mx-auto space-y-6">
                    <div className="flex items-center gap-4 w-full">
                      <motion.button
                        type="button"
                        onClick={() => {
                          setDirection(-1);
                          setCurrentSlideIndex((prev) => (prev - 1 + suggestions.length) % suggestions.length);
                        }}
                        whileHover={{ scale: 1.08, x: -2 }}
                        whileTap={{ scale: 0.92 }}
                        className="p-3 border border-stone-200 rounded-2xl bg-white text-stone-600 hover:text-stone-850 hover:bg-stone-50 hover:border-stone-300 transition-all cursor-pointer flex items-center justify-center shrink-0 shadow-sm"
                        aria-label="Previous Suggestion"
                      >
                        <ChevronLeft className="w-5 h-5" />
                      </motion.button>

                      <div className="flex-1 relative min-h-[420px] flex items-center justify-center overflow-hidden">
                        <AnimatePresence initial={false} custom={direction} mode="wait">
                          <motion.div
                            key={currentSlideIndex}
                            custom={direction}
                            variants={slideVariants}
                            initial="enter"
                            animate="center"
                            exit="exit"
                            className="w-full bg-white border border-stone-200/80 rounded-3xl p-8 shadow-sm flex flex-col justify-between h-full min-h-[420px]"
                          >
                            <div className="space-y-5">
                              <div className="flex items-center justify-between">
                                <span className="text-xs font-bold uppercase tracking-wider text-indigo-600 bg-indigo-50/60 px-3 py-1.5 rounded-md">
                                  Blueprint {currentSlideIndex + 1} of {suggestions.length}
                                </span>
                                <span className="text-xs text-stone-455 capitalize font-semibold bg-stone-50 border border-stone-100 px-2.5 py-1 rounded-md">
                                  Category: {currentCategory}
                                </span>
                              </div>

                              <h3 className="text-2xl font-extrabold text-stone-850 font-display leading-tight tracking-tight">
                                {suggestions[currentSlideIndex].name}
                              </h3>

                              <p className="text-base text-stone-600 leading-relaxed font-normal">
                                {suggestions[currentSlideIndex].idea}
                              </p>

                              <div className="pt-5 border-t border-stone-100 space-y-4">
                                <div>
                                  <span className="text-xs font-bold uppercase tracking-wider text-stone-450 block mb-2.5">Key Features</span>
                                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                    {suggestions[currentSlideIndex].features.map((feat, fidx) => (
                                      <motion.div
                                        key={fidx}
                                        initial={{ opacity: 0, x: -8 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{ delay: fidx * 0.06, duration: 0.3 }}
                                        className="flex items-center gap-2"
                                      >
                                        <span className="w-2.5 h-2.5 rounded-full bg-indigo-500 shrink-0" />
                                        <span className="text-sm font-semibold text-stone-800 leading-relaxed">{feat}</span>
                                      </motion.div>
                                    ))}
                                  </div>
                                </div>

                                <div className="pt-2">
                                  <span className="text-xs font-bold uppercase tracking-wider text-stone-450 block mb-2">Suggested Tech Stack</span>
                                  <div className="text-sm font-mono font-semibold text-indigo-655 bg-indigo-50/30 border border-indigo-100/40 px-3.5 py-2 rounded-xl inline-block">
                                    {suggestions[currentSlideIndex].tech_stack}
                                  </div>
                                </div>
                              </div>
                            </div>

                            <div className="mt-8 pt-5 border-t border-stone-100 flex items-center justify-end">
                              <motion.button
                                type="button"
                                onClick={() => handleSelectSuggestion(suggestions[currentSlideIndex])}
                                whileHover={{ scale: 1.03, boxShadow: "0 8px 24px -4px rgba(99,102,241,0.35)" }}
                                whileTap={{ scale: 0.97 }}
                                className="px-6 py-3.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-bold shadow-md shadow-indigo-100 transition-all cursor-pointer flex items-center gap-2"
                              >
                                <span>Select & Start Discussion</span>
                                <span className="text-base">→</span>
                              </motion.button>
                            </div>
                          </motion.div>
                        </AnimatePresence>
                      </div>

                      <motion.button
                        type="button"
                        onClick={() => {
                          setDirection(1);
                          setCurrentSlideIndex((prev) => (prev + 1) % suggestions.length);
                        }}
                        whileHover={{ scale: 1.08, x: 2 }}
                        whileTap={{ scale: 0.92 }}
                        className="p-3 border border-stone-200 rounded-2xl bg-white text-stone-600 hover:text-stone-855 hover:bg-stone-50 hover:border-stone-300 transition-all cursor-pointer flex items-center justify-center shrink-0 shadow-sm"
                        aria-label="Next Suggestion"
                      >
                        <ChevronRight className="w-5 h-5" />
                      </motion.button>
                    </div>

                    {/* Dot indicators */}
                    <div className="flex items-center gap-2.5 select-none">
                      {suggestions.map((_, idx) => {
                        const isActive = idx === currentSlideIndex;
                        return (
                          <motion.button
                            key={idx}
                            type="button"
                            onClick={() => {
                              setDirection(idx > currentSlideIndex ? 1 : -1);
                              setCurrentSlideIndex(idx);
                            }}
                            animate={isActive ? { width: 28 } : { width: 10 }}
                            transition={{ type: "spring", stiffness: 400, damping: 28 }}
                            className={`h-2.5 rounded-full transition-colors duration-300 cursor-pointer ${isActive ? "bg-indigo-600" : "bg-stone-200 hover:bg-stone-350"
                              }`}
                            aria-label={`Go to slide ${idx + 1}`}
                          />
                        );
                      })}
                    </div>
                  </div>
                ) : (
                  <div className="text-center text-stone-400 text-xs py-8">No suggestions found</div>
                )}
              </div>
            </div>
          )
        ) : (
          /* 2. Active Chat Messages list */
          <div className="flex-1 p-6 space-y-6 overflow-y-auto bg-white">
            {activeChat.messages.map((m, idx) => {
              const isUser = m.sender === "user";
              return (
                <motion.div
                  key={m.id}
                  variants={msgVariants}
                  initial="initial"
                  animate="animate"
                  className={`flex gap-3 max-w-xl ${isUser ? "ml-auto flex-row-reverse" : ""}`}
                >
                  {/* Avatar */}
                  {isUser ? (
                    <div className="w-7 h-7 rounded-lg shrink-0 flex items-center justify-center font-bold text-[10px] text-white uppercase shadow-sm bg-gradient-to-tr from-indigo-500 to-rose-500 select-none">
                      {user?.name?.charAt(0)}
                    </div>
                  ) : (
                    <SarthiLogo className="w-7 h-7 shrink-0" />
                  )}

                  <div className="space-y-1 w-full">
                    <div
                      className={`p-3.5 rounded-2xl text-xs leading-relaxed select-text ${editingMessageId === m.id ? "w-full" : ""
                        } ${isUser
                          ? "bg-indigo-600 text-white rounded-tr-none"
                          : "bg-stone-50 text-stone-700 border border-stone-200/60 rounded-tl-none"
                        }`}
                    >
                      {editingMessageId === m.id ? (
                        <div className="flex flex-col gap-2 w-full">
                          <textarea
                            value={editingText}
                            onChange={(e) => setEditingText(e.target.value)}
                            className={`w-full border rounded-xl p-2.5 text-xs font-sans leading-relaxed resize-y min-h-[140px] focus:outline-none focus:ring-2 ${isUser
                              ? "bg-indigo-700 text-white border-indigo-500 focus:ring-white/20"
                              : "bg-white text-stone-850 border-stone-200 focus:ring-indigo-500/20 focus:border-indigo-500"
                              }`}
                          />
                          <div className="flex justify-end gap-2">
                            <button
                              type="button"
                              onClick={() => setEditingMessageId(null)}
                              className={`px-2.5 py-1 rounded-lg text-[10px] font-semibold transition-colors cursor-pointer ${isUser
                                ? "bg-indigo-700/50 hover:bg-indigo-700 text-indigo-100 hover:text-white"
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
                                ? "bg-white hover:bg-indigo-50 text-indigo-700"
                                : "bg-indigo-600 hover:bg-indigo-700 text-white"
                                }`}
                            >
                              Save
                            </button>
                          </div>
                        </div>
                      ) : (
                        <MarkdownRenderer text={m.text} />
                      )}
                    </div>

                    <div className={`flex items-center gap-2 mt-1 ${isUser ? "justify-end" : "justify-start"}`}>
                      <span className="text-[9px] text-stone-400">{m.timestamp}</span>
                      <span className="text-stone-300 text-[8px] select-none">•</span>
                      <button
                        type="button"
                        onClick={() => handleCopyMessage(m.id, m.text)}
                        className="text-[9px] text-stone-400 hover:text-stone-700 hover:underline transition-colors font-medium cursor-pointer"
                      >
                        {copiedMessageId === m.id ? "Copied!" : "Copy"}
                      </button>
                      <span className="text-stone-300 text-[8px] select-none">•</span>
                      <button
                        type="button"
                        onClick={() => {
                          setEditingMessageId(m.id);
                          setEditingText(m.text);
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
                <div className="bg-stone-50 text-stone-600 border border-stone-200/60 px-4 py-3 rounded-2xl rounded-tl-none flex items-center gap-2 shrink-0">
                  <AiTypingWave />
                  <span className="text-[10px] text-stone-400 font-medium ml-1">Sarthi is thinking</span>
                  <span className="animate-cursor-blink text-stone-400 text-xs">|</span>
                </div>
              </motion.div>
            )}

            <div ref={chatEndRef} />
          </div>
        )}
      </div>

      {/* Input Area Console */}
      <footer className="p-4 border-t border-stone-200/60 bg-white/40 backdrop-blur-md shrink-0 relative select-none transition-colors duration-300">
        <form onSubmit={handleSendMessage} className="max-w-3xl mx-auto flex items-center gap-3">
          {/* Category Dropdown Selector */}
          <div className="relative shrink-0">
            <motion.button
              type="button"
              onClick={() => setShowCategoryDropdown(!showCategoryDropdown)}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.97 }}
              className={`flex items-center gap-1.5 px-3 py-2.5 rounded-xl text-xs font-semibold border transition-all ${validationError
                ? "border-rose-400 bg-rose-50 text-rose-700 animate-lock-shake"
                : currentCategory
                  ? "border-indigo-100 bg-indigo-50/50 text-indigo-700"
                  : "border-stone-200 bg-stone-50 hover:bg-stone-100 text-stone-500"
                }`}
            >
              {currentCategory ? (
                <>
                  <CategoryIcon category={currentCategory} className="w-3.5 h-3.5" />
                  <span className="capitalize">{currentCategory}</span>
                </>
              ) : (
                <span>Choose Category</span>
              )}
              <motion.span animate={{ rotate: showCategoryDropdown ? 180 : 0 }} transition={{ duration: 0.25 }}>
                <ChevronDown className="w-3.5 h-3.5" />
              </motion.span>
            </motion.button>

            {validationError && (
              <motion.div
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                className="absolute bottom-full left-0 mb-2 w-48 p-2 bg-stone-900 text-white rounded-lg text-[10px] leading-relaxed flex items-start gap-1.5 shadow-md z-30"
              >
                <AlertCircle className="w-3.5 h-3.5 text-rose-400 shrink-0 mt-0.5" />
                <span>You must select a category domain to message Sarthi!</span>
              </motion.div>
            )}

            <AnimatePresence>
              {showCategoryDropdown && (
                <motion.div
                  initial={{ opacity: 0, y: 8, scale: 0.97 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 8, scale: 0.97 }}
                  transition={{ duration: 0.18, ease: "easeOut" }}
                  className="absolute bottom-full left-0 mb-2 w-56 bg-white border border-stone-200/80 rounded-2xl p-2 shadow-xl z-30"
                >
                  {categories.map((c, i) => (
                    <motion.button
                      key={c.id}
                      type="button"
                      onClick={() => handleCategorySelect(c.id)}
                      initial={{ opacity: 0, x: -6 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.04 }}
                      className={`w-full flex items-center gap-2.5 p-2 rounded-xl text-left hover:bg-stone-50 transition-colors ${currentCategory === c.id ? "bg-indigo-50/50 text-indigo-700" : "text-stone-600"
                        }`}
                    >
                      <div className="p-1 rounded bg-stone-100 text-stone-500">
                        <CategoryIcon category={c.id} className="w-3.5 h-3.5" />
                      </div>
                      <span className="text-xs font-semibold capitalize">{c.id}</span>
                    </motion.button>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Suggest More Button near input box */}
          {!activeChat && currentCategory && (
            <motion.button
              type="button"
              onClick={() => fetchSuggestions(currentCategory)}
              disabled={isFetchingSuggestions}
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.96 }}
              className="flex items-center gap-1.5 px-3 py-2.5 rounded-xl text-xs font-semibold border border-indigo-200 bg-indigo-50/50 text-indigo-600 hover:bg-indigo-100/50 hover:text-indigo-700 disabled:opacity-50 transition-all cursor-pointer shrink-0 shadow-sm"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>{isFetchingSuggestions ? "Suggesting..." : "Suggest More"}</span>
            </motion.button>
          )}

          {/* Text Input with focus glow */}
          <div className="flex-1 relative">
            <input
              type="text"
              placeholder={
                currentCategory
                  ? `Discuss your ${currentCategory} project milestones...`
                  : "Select a category first to launch Sarthi..."
              }
              value={currentInput}
              onChange={(e) => setCurrentInput(e.target.value)}
              disabled={aiTyping}
              onFocus={() => setInputFocused(true)}
              onBlur={() => setInputFocused(false)}
              className="w-full bg-stone-50 border border-stone-200 rounded-xl px-4 py-2.5 text-xs text-stone-800 placeholder:text-stone-455 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 transition-all duration-300"
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
          </div>

          {/* Send button */}
          <motion.button
            type="submit"
            disabled={!currentInput.trim() || aiTyping}
            whileHover={currentInput.trim() && !aiTyping ? { scale: 1.08, rotate: -8 } : {}}
            whileTap={currentInput.trim() && !aiTyping ? { scale: 0.92 } : {}}
            transition={{ type: "spring", stiffness: 400, damping: 22 }}
            className="p-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white transition-colors disabled:opacity-50"
          >
            <Send className="w-4 h-4" />
          </motion.button>
        </form>
      </footer>
    </div>
  );
};
