"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useWorkspace } from "@/context/WorkspaceContext";
import { SarthiLogo, CategoryIcon, EmptyStateIllustration } from "./CustomSvgs";
import { MessageSquare, FolderGit2, Trash2, LogOut, LogIn, Sparkles, PanelLeftClose, Edit2, User, Settings, HelpCircle, ChevronUp } from "lucide-react";
import { ProfileModal } from "./ProfileModal";

export const Sidebar: React.FC<{ isCollapsed?: boolean }> = ({ isCollapsed = false }) => {
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
    clearSuggestions,
    showLeftPane,
    setShowLeftPane,
    renameChat,
    renameProject,
    setShowRightPane
  } = useWorkspace();

  const [activeTab, setActiveTab] = useState<"chats" | "projects">("chats");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [profileModalTab, setProfileModalTab] = useState<"profile" | "settings" | "help">("profile");

  const handleAuthClick = () => {
    setAuthMode("login");
    setShowAuthModal(true);
  };

  return (
    <aside className="w-full border-r border-stone-200/60 bg-white/30 backdrop-blur-lg flex flex-col h-full select-none transition-colors duration-300">
      {/* Header / Logo */}
      <div className="p-6 border-b border-stone-200/60 flex items-center justify-between gap-3">
        <div className="flex flex-col gap-0.5">
          <div className="flex items-center gap-2">
            {isCollapsed ? <div className="w-8 h-8 rounded-full bg-indigo-950 flex items-center justify-center text-amber-500 font-bold font-display text-lg">S</div> : <SarthiLogo className="text-4xl" />}
            {!isCollapsed && (
            <motion.span
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.3, type: "spring", stiffness: 400 }}
              className="text-[10px] font-sans font-extrabold uppercase px-1.5 py-0.5 rounded bg-indigo-50/50 border border-indigo-200/50 text-indigo-950 tracking-wider mt-1"
            >
              v1.0
            </motion.span>
          )}
          </div>
          {!isCollapsed && (
          <p className="text-[10px] text-stone-400 font-medium tracking-wide pl-1">
            Intelligent Coding Charioteer
          </p>
          )}
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
                className="relative z-10 ml-0.5 text-[9px] font-bold bg-indigo-100 text-indigo-950 px-1.5 py-0.5 rounded-full"
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
                className="relative z-10 ml-0.5 text-[9px] font-bold bg-indigo-100 text-indigo-950 px-1.5 py-0.5 rounded-full"
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
              className="mt-4 bg-indigo-50/50 border border-indigo-200/50 hover:bg-indigo-100 text-indigo-950 text-xs font-semibold px-4 py-2 rounded-xl transition-all cursor-pointer"
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
                clearSuggestions();
              }}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.97 }}
              className="w-full flex items-center justify-center gap-2 bg-indigo-950 hover:bg-indigo-900 text-amber-500 font-bold tracking-wide border border-indigo-900/50 shadow-inner text-xs font-bold py-2.5 rounded-xl transition-all shadow-sm mb-3 cursor-pointer relative overflow-hidden group"
            >
              {/* Shimmer sweep */}
              <motion.span
                className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent"
                animate={{ x: ["-100%", "200%"] }}
                transition={{ duration: 2.5, repeat: Infinity, ease: "linear", repeatDelay: 2 }}
              />
              <MessageSquare className="w-4 h-4 relative z-10" />
              <span className={`relative z-10 ${isCollapsed ? "hidden group-hover:block absolute left-14 bg-stone-900 text-white px-2 py-1 rounded shadow-md whitespace-nowrap" : "block"}`}>Start New Chat</span>
            </motion.button>

            <AnimatePresence initial={false}>
              {chats.filter(c => !c.is_confirmed && !c.project_id).length === 0 ? (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex flex-col items-center py-8"
                >
                  <EmptyStateIllustration className="w-28 h-24" />
                  <p className="text-stone-400 text-xs mt-2">No active chats yet — start one above</p>
                </motion.div>
              ) : (
                chats.filter(c => !c.is_confirmed && !c.project_id).map((c, idx) => {
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
                        ? "bg-indigo-50 border border-indigo-100 text-indigo-900"
                        : "hover:bg-stone-50 border border-transparent text-stone-600"
                        }`}
                      onClick={() => {
                        setActiveChatId(c.id);
                        setActiveProjectId(null);
                        setShowRightPane(true);
                      }}
                    >
                      <div className="flex items-center gap-3 overflow-hidden">
                        <motion.div
                          className={`p-1.5 rounded-lg ${isActive ? "bg-indigo-100 text-indigo-950" : "bg-stone-100 text-stone-500"
                            }`}
                          whileHover={{ rotate: [-3, 3, 0] }}
                          transition={{ duration: 0.3 }}
                        >
                          <CategoryIcon category={c.category} className="w-4 h-4" />
                        </motion.div>
                        {!isCollapsed && (
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
                                className="w-full bg-white border border-indigo-200 rounded px-1.5 py-0.5 text-xs text-stone-800 outline-none focus:ring-1 focus:ring-amber-400"
                              />
                            ) : (
                              <p className="text-xs font-semibold truncate leading-tight" title={c.title}>{c.title}</p>
                            )}
                            <span className="text-[9px] text-stone-400 block mt-0.5">{c.created}</span>
                          </div>
                        )}
                      </div>
                      {!isCollapsed && (
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
                            className="p-1 rounded-md text-stone-400 hover:text-amber-500 hover:bg-indigo-50 transition-all cursor-pointer"
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
                      )}
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
                      ? "bg-indigo-50 border border-indigo-100 text-indigo-900"
                      : "hover:bg-stone-50 border border-transparent text-stone-600"
                      }`}
                    onClick={() => {
                      if (!isGeneratingProject) {
                        setActiveProjectId(p.id);
                        if (p.chat_id) {
                          setActiveChatId(p.chat_id);
                        }
                        setShowRightPane(true);
                      }
                    }}
                  >
                    <div className="flex items-center gap-3 overflow-hidden flex-1 min-w-0">
                      <div
                        className={`p-1.5 rounded-lg shrink-0 ${isActive ? "bg-indigo-100 text-indigo-950" : "bg-stone-100 text-stone-500"
                          }`}
                      >
                        <CategoryIcon category={p.category} className="w-4 h-4" />
                      </div>
                      {!isCollapsed && (
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
                              className="w-full bg-white border border-indigo-200 rounded px-1.5 py-0.5 text-xs text-stone-800 outline-none focus:ring-1 focus:ring-amber-400 mb-1"
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
                      )}
                    </div>
                    {!isCollapsed && (
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
                          className="p-1 rounded-md text-stone-400 hover:text-amber-500 hover:bg-indigo-50 transition-all cursor-pointer"
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
                    )}
                  </motion.div>
                );
              })
            )}
          </AnimatePresence>
        )}
      </div>

      {/* User Section (Bottom) */}
      <div className="p-4 border-t border-stone-200/60 bg-white/20 transition-colors duration-300 relative">
        <AnimatePresence>
          {showProfileMenu && user && !isCollapsed && (
            <motion.div
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 10, scale: 0.95 }}
              transition={{ duration: 0.2 }}
              className="absolute bottom-[calc(100%-1rem)] left-4 right-4 mb-2 bg-white rounded-xl shadow-[0_4px_20px_-4px_rgba(0,0,0,0.1)] border border-stone-200/60 overflow-hidden z-50"
            >
              <div className="p-3 border-b border-stone-100 bg-stone-50/50">
                <p className="text-xs font-bold text-stone-800">{user.name}</p>
                <p className="text-[10px] text-stone-500 truncate">{user.email}</p>
              </div>
              <div className="p-1.5 flex flex-col gap-0.5">
                <button 
                  onClick={() => {
                    setShowProfileMenu(false);
                    setProfileModalTab("profile");
                    setShowProfileModal(true);
                  }}
                  className="flex items-center gap-2 w-full p-2 text-xs font-medium text-stone-600 hover:text-stone-900 hover:bg-stone-50 rounded-lg transition-colors text-left cursor-pointer"
                >
                  <User className="w-3.5 h-3.5" />
                  My Profile
                </button>
                <button 
                  onClick={() => {
                    setShowProfileMenu(false);
                    setProfileModalTab("settings");
                    setShowProfileModal(true);
                  }}
                  className="flex items-center gap-2 w-full p-2 text-xs font-medium text-stone-600 hover:text-stone-900 hover:bg-stone-50 rounded-lg transition-colors text-left cursor-pointer"
                >
                  <Settings className="w-3.5 h-3.5" />
                  Settings & API Keys
                </button>
                <button 
                  onClick={() => {
                    setShowProfileMenu(false);
                    setProfileModalTab("help");
                    setShowProfileModal(true);
                  }}
                  className="flex items-center gap-2 w-full p-2 text-xs font-medium text-stone-600 hover:text-stone-900 hover:bg-stone-50 rounded-lg transition-colors text-left cursor-pointer"
                >
                  <HelpCircle className="w-3.5 h-3.5" />
                  Help & Support
                </button>
                <div className="h-px bg-stone-100 my-1 mx-1" />
                <button 
                  onClick={() => {
                    setShowProfileMenu(false);
                    logout();
                  }}
                  className="flex items-center gap-2 w-full p-2 text-xs font-medium text-rose-600 hover:text-rose-700 hover:bg-rose-50 rounded-lg transition-colors text-left"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  Sign Out
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {user ? (
          <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            onClick={() => setShowProfileMenu(!showProfileMenu)}
            className="flex items-center justify-between bg-stone-50 hover:bg-stone-100 p-2.5 rounded-xl border border-stone-200/40 cursor-pointer transition-colors"
          >
            <div className="flex items-center gap-2 overflow-hidden">
              <motion.div
                className="w-8 h-8 rounded-lg bg-gradient-to-tr from-amber-500 to-rose-500 text-white font-bold flex items-center justify-center text-xs shrink-0 shadow-sm uppercase select-none"
                whileHover={{ scale: 1.08, rotate: -3 }}
                transition={{ type: "spring", stiffness: 400 }}
              >
                {user.name.charAt(0)}
              </motion.div>
              {!isCollapsed && (
              <div className="overflow-hidden">
                <p className="text-xs font-bold text-stone-700 truncate">{user.name}</p>
                <p className="text-[9px] text-stone-400 truncate">Free Plan</p>
              </div>
              )}
            </div>
            {!isCollapsed && (
              <motion.div
                animate={{ rotate: showProfileMenu ? 180 : 0 }}
                className="p-1 text-stone-400"
              >
                <ChevronUp className="w-4 h-4" />
              </motion.div>
            )}
          </motion.div>
        ) : (
          <motion.button
            onClick={handleAuthClick}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.97 }}
            className="w-full flex items-center justify-center gap-2 bg-indigo-900 hover:bg-indigo-950 text-white text-xs font-semibold py-2.5 rounded-xl transition-all shadow-sm cursor-pointer relative overflow-hidden"
          >
            <motion.span
              className="absolute inset-0 bg-gradient-to-r from-transparent via-white/8 to-transparent"
              animate={{ x: ["-100%", "200%"] }}
              transition={{ duration: 2.5, repeat: Infinity, ease: "linear", repeatDelay: 2 }}
            />
            <LogIn className="w-4 h-4 relative z-10 shrink-0" />
            <span className={`relative z-10 ${isCollapsed ? "hidden group-hover:block absolute left-14 bg-stone-900 text-white px-2 py-1 rounded shadow-md whitespace-nowrap" : "block"}`}>Sign In / Sign Up</span>
          </motion.button>
        )}
      </div>

      <ProfileModal 
        isOpen={showProfileModal} 
        onClose={() => setShowProfileModal(false)} 
        initialTab={profileModalTab}
      />
    </aside>
  );
};
