"use client";

import React, { useState, useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import { useWorkspace } from "@/context/WorkspaceContext";
import { 
  Search, Terminal, User, HelpCircle, Settings, X, Play, 
  ArrowRight, FolderGit2, Sidebar as SidebarIcon,
  PanelRight, Keyboard, Sparkles
} from "lucide-react";

export const CommandMenu: React.FC = () => {
  const {
    chats,
    activeChatId,
    projects,
    activeProjectId,
    showLeftPane,
    setShowLeftPane,
    showRightPane,
    setShowRightPane,
    compileProjectCodebase
  } = useWorkspace();

  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);

  const inputRef = useRef<HTMLInputElement>(null);

  // Compute active project
  const activeChat = chats.find((c) => c.id === activeChatId);
  const activeProj = projects.find((p) => p.id === (activeProjectId || activeChat?.project_id)) ||
    (activeChatId ? projects.find((p) => p.chat_id === activeChatId) : undefined);

  // Keyboard shortcut listener to toggle Cmd+K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setIsOpen((prev) => !prev);
        setSearchQuery("");
        setSelectedIndex(0);
      }
      if (e.key === "Escape" && isOpen) {
        setIsOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen]);

  // Focus input on open
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => {
        inputRef.current?.focus();
      }, 50);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  // List of general actions
  const actions = [
    {
      id: "toggle-sidebar",
      title: "Steer Chariot Left (Toggle Sidebar)",
      desc: "Expand or collapse the left history navigation pane.",
      icon: <SidebarIcon className="w-4 h-4 text-indigo-500" />,
      action: () => setShowLeftPane(!showLeftPane)
    },
    {
      id: "toggle-right-pane",
      title: "Open Right Panel (Toggle Code Viewer)",
      desc: "Open or close the specifications and codebase explorer.",
      icon: <PanelRight className="w-4 h-4 text-indigo-500" />,
      action: () => setShowRightPane(!showRightPane)
    },
    {
      id: "open-profile",
      title: "Open Developer Profile",
      desc: "Edit your developer name, biography, and credentials.",
      icon: <User className="w-4 h-4 text-amber-500" />,
      action: () => {
        window.dispatchEvent(new CustomEvent("open-profile-modal", { detail: { tab: "profile" } }));
      }
    },
    {
      id: "open-settings",
      title: "Open Workspace Settings",
      desc: "Configure Gemini orchestration models and sound chimes.",
      icon: <Settings className="w-4 h-4 text-amber-500" />,
      action: () => {
        window.dispatchEvent(new CustomEvent("open-profile-modal", { detail: { tab: "settings" } }));
      }
    },
    {
      id: "open-help",
      title: "View Concept Guide & Help Support",
      desc: "Read Sri Sri Krishna-Arjuna analogy guide and keyboard shortcuts.",
      icon: <HelpCircle className="w-4 h-4 text-emerald-500" />,
      action: () => {
        window.dispatchEvent(new CustomEvent("open-profile-modal", { detail: { tab: "help" } }));
      }
    }
  ];

  // If compilation is ready, add proceed to build codebase option
  if (activeProj && activeProj.status === "documents_ready") {
    actions.unshift({
      id: "proceed-build",
      title: "Proceed to Build Codebase",
      desc: `Compile specifications for ${activeProj.name} and assemble code modules.`,
      icon: <Play className="w-4 h-4 text-rose-500 animate-pulse" />,
      action: () => compileProjectCodebase(activeProj.id, activeProj.chat_id)
    });
  }

  // Pre-defined template arrows (prompts)
  const prompts = [
    {
      id: "prompt-fraud",
      title: "Task: Build Fraud Review Agent",
      desc: "stores transactions, flags activity, assigns approval tasks using MongoDB.",
      text: "Build a financial services fraud review agent that stores transactions, flags suspicious activity, opens human approval tasks, and records every decision for audit review using MongoDB."
    },
    {
      id: "prompt-fan",
      title: "Task: Create World Cup Fan Ops",
      desc: "coordinates matches, transit routes, and updates MongoDB itinerary.",
      text: "Create a 2026 World Cup fan logistics agent that plans stadium arrival windows, tracks crowd alerts, recommends transit routes, and updates a MongoDB-backed itinerary checklist."
    },
    {
      id: "prompt-mongo",
      title: "Code: Add MongoDB Schema & Indexes",
      desc: "Add a database schema script and define index strategies.",
      text: "Add a new MongoDB collection schema config, write model schemas in Python/FastAPI, and define indexing strategies."
    },
    {
      id: "prompt-auth",
      title: "Code: JWT Protection guards",
      desc: "Implement auth middleware routes and protective guards.",
      text: "Write auth protection middleware logic for routes, defining JWT tokens decoding and role guards."
    }
  ];

  // List of active codebase files if project is completed
  const codebaseFiles = activeProj?.status === "completed" && activeProj.codebase
    ? activeProj.codebase.map((file) => ({
        id: `file-${file.path}`,
        title: `File: ${file.name}`,
        desc: file.path,
        icon: <FolderGit2 className="w-4 h-4 text-amber-500" />,
        action: () => {
          // Find standard project viewer file dispatcher or dispatch event
          window.dispatchEvent(new CustomEvent("select-codebase-file", { detail: { file } }));
          setShowRightPane(true);
        }
      }))
    : [];

  // Combine items and filter by query
  const allItems = [
    ...actions,
    ...codebaseFiles,
    ...prompts.map((p) => ({
      id: p.id,
      title: p.title,
      desc: p.desc,
      icon: <Sparkles className="w-4 h-4 text-purple-500" />,
      action: () => {
        // Find input box and insert text
        const inputEl = document.getElementById("chat-input-bar") as HTMLTextAreaElement;
        if (inputEl) {
          inputEl.value = p.text;
          // Trigger React input change dispatch
          const event = new Event("input", { bubbles: true });
          inputEl.dispatchEvent(event);
          inputEl.focus();
        }
      }
    }))
  ];

  const filteredItems = allItems.filter(
    (item) =>
      item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.desc.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % Math.max(1, filteredItems.length));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 + filteredItems.length) % Math.max(1, filteredItems.length));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (filteredItems[selectedIndex]) {
        filteredItems[selectedIndex].action();
        setIsOpen(false);
      }
    }
  };

  return createPortal(
    <AnimatePresence>
      <div className="fixed inset-0 z-[200] flex items-start justify-center pt-[12vh] px-4 overflow-hidden select-none">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={() => setIsOpen(false)}
          className="absolute inset-0 bg-indigo-950/40 backdrop-blur-md"
        />

        {/* Dialog Window */}
        <motion.div
          initial={{ y: -20, opacity: 0, scale: 0.97 }}
          animate={{ y: 0, opacity: 1, scale: 1 }}
          exit={{ y: -20, opacity: 0, scale: 0.97 }}
          transition={{ type: "spring", duration: 0.45 }}
          className="relative w-full max-w-xl bg-indigo-950/90 border border-indigo-500/30 rounded-3xl shadow-[0_25px_60px_-15px_rgba(0,0,0,0.5)] backdrop-blur-xl overflow-hidden z-10 flex flex-col max-h-[60vh] text-white"
          onKeyDown={handleKeyDown}
        >
          {/* Header search bar */}
          <div className="flex items-center gap-3 px-5 py-4 border-b border-indigo-500/20 shrink-0">
            <Search className="w-5 h-5 text-indigo-400/80 shrink-0" />
            <input
              ref={inputRef}
              type="text"
              placeholder="Search actions, workspace nodes, files..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setSelectedIndex(0);
              }}
              className="flex-1 bg-transparent border-none outline-none text-xs text-white placeholder-indigo-300/60 font-semibold focus:ring-0"
            />
            <button
              onClick={() => setIsOpen(false)}
              className="p-1 rounded-lg hover:bg-indigo-500/20 text-indigo-300 transition-colors cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Results List */}
          <div className="flex-1 overflow-y-auto p-2.5 space-y-1 scrollbar-thin scrollbar-thumb-indigo-900/60">
            {filteredItems.length > 0 ? (
              filteredItems.map((item, idx) => {
                const isSelected = idx === selectedIndex;
                return (
                  <button
                    key={item.id}
                    onClick={() => {
                      item.action();
                      setIsOpen(false);
                    }}
                    onMouseEnter={() => setSelectedIndex(idx)}
                    className={`w-full flex items-center justify-between p-3 rounded-2xl text-left transition-all outline-none border border-transparent cursor-pointer ${
                      isSelected
                        ? "bg-gradient-to-r from-indigo-900/90 to-indigo-950 border-indigo-500/30 shadow-md text-amber-500"
                        : "text-indigo-200 hover:text-white"
                    }`}
                  >
                    <div className="flex items-center gap-3 overflow-hidden pr-2">
                      <div className={`p-2 rounded-xl shrink-0 ${isSelected ? "bg-indigo-950 text-amber-500" : "bg-indigo-900/40 text-indigo-300"}`}>
                        {item.icon || <Terminal className="w-4 h-4" />}
                      </div>
                      <div className="overflow-hidden">
                        <p className={`text-xs font-bold ${isSelected ? "text-amber-500" : "text-white"}`}>
                          {item.title}
                        </p>
                        <p className="text-[9px] text-indigo-300/80 mt-0.5 truncate font-semibold">
                          {item.desc}
                        </p>
                      </div>
                    </div>
                    {isSelected && (
                      <motion.div
                        initial={{ x: -4, opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        className="flex items-center gap-1 text-[9px] font-bold text-amber-500 shrink-0 select-none uppercase tracking-wider pl-1"
                      >
                        <span>Run</span>
                        <ArrowRight className="w-3 h-3" />
                      </motion.div>
                    )}
                  </button>
                );
              })
            ) : (
              <div className="p-8 text-center text-indigo-300/60">
                <Keyboard className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-xs font-semibold">No commands matching &quot;{searchQuery}&quot;</p>
              </div>
            )}
          </div>

          {/* Footer keyboard guide */}
          <div className="px-5 py-3 border-t border-indigo-500/20 bg-indigo-950/45 shrink-0 flex items-center justify-between text-[8px] font-bold text-indigo-400 uppercase tracking-widest">
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1">
                <span className="px-1.5 py-0.5 bg-indigo-900/85 border border-indigo-500/30 rounded text-white font-mono font-normal">↑↓</span>
                Navigate
              </span>
              <span className="flex items-center gap-1">
                <span className="px-1.5 py-0.5 bg-indigo-900/85 border border-indigo-500/30 rounded text-white font-mono font-normal">↵</span>
                Select
              </span>
            </div>
            <span className="flex items-center gap-1">
              <span className="px-1.5 py-0.5 bg-indigo-900/85 border border-indigo-500/30 rounded text-white font-mono font-normal">ESC</span>
              Close
            </span>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>,
    document.body
  );
};
