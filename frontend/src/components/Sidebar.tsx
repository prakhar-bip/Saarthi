"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useWorkspace } from "@/context/WorkspaceContext";
import { SarthiLogo, CategoryIcon, EmptyStateIllustration } from "./CustomSvgs";
import { MessageSquare, FolderGit2, Trash2, LogOut, LogIn, Sparkles, PanelLeftClose, Edit2 } from "lucide-react";

export const Sidebar: React.FC = () => {
  const {
    user,
    logout,
    chats,
    activeChatId,
    setActiveChatId,
    deleteChat,
    projects,
    activeProjectId,
    setActiveProjectId,
    deleteProject,
    setShowAuthModal,
    setAuthMode,
    isGeneratingProject,
    setCurrentCategory,
    clearSuggestions,
    showLeftPane,
    setShowLeftPane,
    renameChat,
    renameProject
  } = useWorkspace();

  const [activeTab, setActiveTab] = useState<"chats" | "projects">("chats");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");

  const handleAuthClick = () => {
    setAuthMode("login");
    setShowAuthModal(true);
  };

  return (
    <aside className="w-full border-r border-stone-200/60 bg-white/50 backdrop-blur-md flex flex-col h-full select-none transition-colors duration-300">
      {/* Header / Logo */}
      <div className="p-6 border-b border-stone-200/60 flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <SarthiLogo className="w-9 h-9" />
          <div>
            <h1 className="text-xl font-bold font-display text-stone-800 tracking-tight flex items-center gap-1.5">
              Sarthi
              <motion.span
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: 0.3, type: "spring", stiffness: 400 }}
                className="text-[10px] font-sans font-extrabold uppercase px-1.5 py-0.5 rounded bg-indigo-50 border border-indigo-100 text-indigo-600 tracking-wider"
              >
                v1.0
              </motion.span>
            </h1>
            <p className="text-[10px] text-stone-400 font-medium tracking-wide">
              Intelligent Hackathon Partner
            </p>
          </div>
        </div>
        <motion.button
          type="button"
          onClick={() => setShowLeftPane(false)}
          whileHover={{ scale: 1.1, rotate: -5 }}
          whileTap={{ scale: 0.9 }}
          className="p-1 rounded-lg hover:bg-stone-100 text-stone-400 hover:text-stone-700 transition-colors cursor-pointer"
          title="Collapse Sidebar"
        >
          <PanelLeftClose className="w-4 h-4" />
        </motion.button>
      </div>

      {/* Main Tab Switcher */}
      <div className="px-6 pt-6 pb-2">
        <div className="flex bg-stone-100 p-1 rounded-xl transition-colors duration-300">
          <button
            onClick={() => setActiveTab("chats")}
            className={`flex-1 flex items-center justify-center gap-2 py-2 text-xs font-semibold rounded-lg transition-all relative ${activeTab === "chats" ? "text-stone-800" : "text-stone-500 hover:text-stone-700"
              }`}
          >
            {activeTab === "chats" && (
              <motion.div
                layoutId="sidebar-tab"
                className="absolute inset-0 bg-white rounded-lg shadow-sm border border-stone-200/40"
                transition={{ type: "spring", stiffness: 380, damping: 30 }}
              />
            )}
            <MessageSquare className="w-3.5 h-3.5 relative z-10" />
            <span className="relative z-10">Chats</span>
            {chats.length > 0 && (
              <motion.span
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="relative z-10 ml-0.5 text-[9px] font-bold bg-indigo-100 text-indigo-600 px-1.5 py-0.5 rounded-full"
              >
                {chats.length}
              </motion.span>
            )}
          </button>
          <button
            onClick={() => setActiveTab("projects")}
            className={`flex-1 flex items-center justify-center gap-2 py-2 text-xs font-semibold rounded-lg transition-all relative ${activeTab === "projects" ? "text-stone-800" : "text-stone-500 hover:text-stone-700"
              }`}
          >
            {activeTab === "projects" && (
              <motion.div
                layoutId="sidebar-tab"
                className="absolute inset-0 bg-white rounded-lg shadow-sm border border-stone-200/40"
                transition={{ type: "spring", stiffness: 380, damping: 30 }}
              />
            )}
            <FolderGit2 className="w-3.5 h-3.5 relative z-10" />
            <span className="relative z-10">Projects</span>
            {projects.length > 0 && (
              <motion.span
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="relative z-10 ml-0.5 text-[9px] font-bold bg-indigo-100 text-indigo-600 px-1.5 py-0.5 rounded-full"
              >
                {projects.length}
              </motion.span>
            )}
          </button>
        </div>
      </div>

      {/* History Lists */}
      <div className="flex-1 overflow-y-auto px-4 py-2 space-y-1">
        {/* Unauthenticated Prompt */}
        {!user && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="p-4 text-center mt-6"
          >
            <EmptyStateIllustration className="w-28 h-28 mx-auto mb-2" />
            <h4 className="text-xs font-semibold text-stone-700">Workspace Locked</h4>
            <p className="text-[11px] text-stone-400 mt-1 max-w-[200px] mx-auto leading-relaxed">
              Login to view and manage your generated project directories and chat records.
            </p>
            <motion.button
              onClick={handleAuthClick}
              whileHover={{ scale: 1.04 }}
              whileTap={{ scale: 0.96 }}
              className="mt-4 bg-indigo-50 border border-indigo-100 hover:bg-indigo-100 text-indigo-600 text-xs font-semibold px-4 py-2 rounded-xl transition-all cursor-pointer"
            >
              Sign In Now
            </motion.button>
          </motion.div>
        )}

        {/* Authenticated — Chats */}
        {user && activeTab === "chats" && (
          <div className="flex flex-col w-full h-full">
            <motion.button
              onClick={() => {
                setActiveChatId(null);
                setActiveProjectId(null);
                setCurrentCategory("");
                clearSuggestions();
              }}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.97 }}
              className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold py-2.5 rounded-xl transition-all shadow-sm mb-3 cursor-pointer relative overflow-hidden group"
            >
              {/* Shimmer sweep */}
              <motion.span
                className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent"
                animate={{ x: ["-100%", "200%"] }}
                transition={{ duration: 2.5, repeat: Infinity, ease: "linear", repeatDelay: 2 }}
              />
              <span className="relative z-10">+ Start New Chat</span>
            </motion.button>

            <AnimatePresence initial={false}>
              {chats.length === 0 ? (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex flex-col items-center py-8"
                >
                  <EmptyStateIllustration className="w-28 h-24" />
                  <p className="text-stone-400 text-xs mt-2">No chats yet — start one above</p>
                </motion.div>
              ) : (
                chats.map((c, idx) => {
                  const isActive = activeChatId === c.id && !activeProjectId;
                  return (
                    <motion.div
                      key={c.id}
                      initial={{ opacity: 0, x: -12 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -12, height: 0, marginBottom: 0 }}
                      transition={{ delay: idx * 0.04, duration: 0.3 }}
                      whileHover={{ x: 2 }}
                      className={`group flex items-center justify-between p-3 rounded-xl cursor-pointer transition-all ${isActive
                        ? "bg-indigo-50/50 border border-indigo-100/50 text-indigo-900"
                        : "hover:bg-stone-50 border border-transparent text-stone-600"
                        }`}
                      onClick={() => {
                        setActiveChatId(c.id);
                        setActiveProjectId(null);
                      }}
                    >
                      <div className="flex items-center gap-3 overflow-hidden">
                        <motion.div
                          className={`p-1.5 rounded-lg ${isActive ? "bg-indigo-100 text-indigo-700" : "bg-stone-100 text-stone-500"
                            }`}
                          whileHover={{ rotate: [-3, 3, 0] }}
                          transition={{ duration: 0.3 }}
                        >
                          <CategoryIcon category={c.category} className="w-4 h-4" />
                        </motion.div>
                        <div className="overflow-hidden flex-1">
                          {editingId === c.id ? (
                            <input 
                              type="text"
                              value={editValue}
                              onChange={(e) => setEditValue(e.target.value)}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                  renameChat(c.id, editValue);
                                  setEditingId(null);
                                } else if (e.key === 'Escape') {
                                  setEditingId(null);
                                }
                              }}
                              onClick={(e) => e.stopPropagation()}
                              autoFocus
                              className="w-full bg-white border border-indigo-200 rounded px-1.5 py-0.5 text-xs text-stone-800 outline-none focus:ring-1 focus:ring-indigo-400"
                            />
                          ) : (
                            <p className="text-xs font-semibold truncate leading-tight" title={c.title}>{c.title}</p>
                          )}
                          <span className="text-[9px] text-stone-400 block mt-0.5">{c.created}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <motion.button
                          onClick={(e) => {
                            e.stopPropagation();
                            if (editingId === c.id) {
                              renameChat(c.id, editValue);
                              setEditingId(null);
                            } else {
                              setEditingId(c.id);
                              setEditValue(c.title);
                            }
                          }}
                          whileHover={{ scale: 1.15 }}
                          whileTap={{ scale: 0.85 }}
                          className="p-1 rounded-md text-stone-400 hover:text-indigo-500 hover:bg-indigo-50 transition-all cursor-pointer"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </motion.button>
                        <motion.button
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteChat(c.id);
                          }}
                          whileHover={{ scale: 1.15 }}
                          whileTap={{ scale: 0.85 }}
                          className="p-1 rounded-md text-stone-400 hover:text-rose-500 hover:bg-rose-50 transition-all cursor-pointer"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </motion.button>
                      </div>
                    </motion.div>
                  );
                })
              )}
            </AnimatePresence>
          </div>
        )}

        {/* Authenticated — Projects */}
        {user && activeTab === "projects" && (
          <AnimatePresence initial={false}>
            {projects.length === 0 ? (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex flex-col items-center py-8"
              >
                <EmptyStateIllustration className="w-28 h-24" />
                <p className="text-stone-400 text-xs mt-2">No projects compiled yet</p>
              </motion.div>
            ) : (
              projects.map((p, idx) => {
                const isActive = activeProjectId === p.id;
                const isCompiling = p.status === "generating";
                return (
                  <motion.div
                    key={p.id}
                    initial={{ opacity: 0, x: -12 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -12 }}
                    transition={{ delay: idx * 0.04, duration: 0.3 }}
                    whileHover={{ x: 2 }}
                    className={`group flex items-center justify-between p-3 rounded-xl cursor-pointer transition-all ${isActive
                      ? "bg-indigo-50/50 border border-indigo-100/50 text-indigo-900"
                      : "hover:bg-stone-50 border border-transparent text-stone-600"
                      }`}
                    onClick={() => {
                      if (!isGeneratingProject) {
                        setActiveProjectId(p.id);
                      }
                    }}
                  >
                    <div className="flex items-center gap-3 overflow-hidden flex-1 min-w-0">
                      <div
                        className={`p-1.5 rounded-lg shrink-0 ${isActive ? "bg-indigo-100 text-indigo-700" : "bg-stone-100 text-stone-500"
                          }`}
                      >
                        <CategoryIcon category={p.category} className="w-4 h-4" />
                      </div>
                      <div className="overflow-hidden flex-1 min-w-0">
                        {editingId === p.id ? (
                          <input 
                            type="text"
                            value={editValue}
                            onChange={(e) => setEditValue(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') {
                                renameProject(p.id, editValue);
                                setEditingId(null);
                              } else if (e.key === 'Escape') {
                                setEditingId(null);
                              }
                            }}
                            onClick={(e) => e.stopPropagation()}
                            autoFocus
                            className="w-full bg-white border border-indigo-200 rounded px-1.5 py-0.5 text-xs text-stone-800 outline-none focus:ring-1 focus:ring-indigo-400 mb-1"
                          />
                        ) : (
                          <p className="text-xs font-semibold truncate leading-tight" title={p.name}>{p.name}</p>
                        )}
                        {isCompiling ? (
                          <div className="mt-1">
                            {/* Live progress bar strip */}
                            <div className="w-full h-1.5 bg-stone-200 rounded-full overflow-hidden">
                              <motion.div
                                className="h-full rounded-full bg-gradient-to-r from-amber-400 to-amber-500"
                                animate={{ width: `${p.progress}%` }}
                                transition={{ duration: 0.6, ease: "easeOut" }}
                              />
                            </div>
                            <span className="text-[9px] text-amber-500 font-semibold mt-0.5 block">
                              {p.progress}% — Compiling
                            </span>
                          </div>
                        ) : (
                          <span className="text-[9px] text-stone-400 block mt-0.5">{p.created}</span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <motion.button
                        onClick={(e) => {
                          e.stopPropagation();
                          if (editingId === p.id) {
                            renameProject(p.id, editValue);
                            setEditingId(null);
                          } else {
                            setEditingId(p.id);
                            setEditValue(p.name);
                          }
                        }}
                        whileHover={{ scale: 1.15 }}
                        whileTap={{ scale: 0.85 }}
                        className="p-1 rounded-md text-stone-400 hover:text-indigo-500 hover:bg-indigo-50 transition-all cursor-pointer"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </motion.button>
                      <motion.button
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteProject(p.id);
                        }}
                        whileHover={{ scale: 1.15 }}
                        whileTap={{ scale: 0.85 }}
                        className="p-1 rounded-md text-stone-400 hover:text-rose-500 hover:bg-rose-50 transition-all cursor-pointer"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </motion.button>
                    </div>
                  </motion.div>
                );
              })
            )}
          </AnimatePresence>
        )}
      </div>

      {/* User Section (Bottom) */}
      <div className="p-4 border-t border-stone-200/60 bg-white/20 transition-colors duration-300">
        {user ? (
          <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center justify-between bg-stone-50 p-2.5 rounded-xl border border-stone-200/40"
          >
            <div className="flex items-center gap-2 overflow-hidden">
              <motion.div
                className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-500 to-rose-500 text-white font-bold flex items-center justify-center text-xs shrink-0 shadow-sm uppercase select-none"
                whileHover={{ scale: 1.08, rotate: -3 }}
                transition={{ type: "spring", stiffness: 400 }}
              >
                {user.name.charAt(0)}
              </motion.div>
              <div className="overflow-hidden">
                <p className="text-xs font-bold text-stone-700 truncate">{user.name}</p>
                <p className="text-[9px] text-stone-400 truncate">{user.email}</p>
              </div>
            </div>
            <motion.button
              onClick={logout}
              whileHover={{ scale: 1.12, rotate: 5 }}
              whileTap={{ scale: 0.88 }}
              className="p-1.5 rounded-lg text-stone-400 hover:text-stone-700 hover:bg-stone-200/50 transition-colors cursor-pointer"
              title="Logout"
            >
              <LogOut className="w-4 h-4" />
            </motion.button>
          </motion.div>
        ) : (
          <motion.button
            onClick={handleAuthClick}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.97 }}
            className="w-full flex items-center justify-center gap-2 bg-stone-900 hover:bg-stone-850 text-white text-xs font-semibold py-2.5 rounded-xl transition-all shadow-sm cursor-pointer relative overflow-hidden"
          >
            <motion.span
              className="absolute inset-0 bg-gradient-to-r from-transparent via-white/8 to-transparent"
              animate={{ x: ["-100%", "200%"] }}
              transition={{ duration: 2.5, repeat: Infinity, ease: "linear", repeatDelay: 2 }}
            />
            <LogIn className="w-4 h-4 relative z-10" />
            <span className="relative z-10">Sign In / Sign Up</span>
          </motion.button>
        )}
      </div>
    </aside>
  );
};
