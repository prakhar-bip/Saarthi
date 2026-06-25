"use client";

import React, { useState, useEffect, useRef } from "react";
import { Sidebar } from "@/components/Sidebar";
import { WorkspaceConsole } from "@/components/WorkspaceConsole";
import { ProjectViewer } from "@/components/ProjectViewer";
import { AuthModal } from "@/components/AuthModal";
import { AboutContactDrawer } from "@/components/AboutContactDrawer";
import { useWorkspace } from "@/context/WorkspaceContext";
import { ChariotSplash } from "@/components/ChariotSplash";
import { AnimatePresence, motion } from "framer-motion";
import { PanelLeft, AlertTriangle, MessageSquare, FolderGit2, FolderPlus, Plus } from "lucide-react";
import { WaveBackground, SarthiLogo } from "@/components/CustomSvgs";
import { CommandMenu } from "@/components/CommandMenu";
import { FeedbackModal } from "@/components/FeedbackModal";

const SandboxWarningModal: React.FC = () => {
  const { user } = useWorkspace();
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const dismissed = localStorage.getItem("sarthi_sandbox_warning_dismissed_v3");
    if (!dismissed && !user) {
      setIsOpen(true);
    } else if (user) {
      setIsOpen(false);
    }
  }, [user]);

  const handleDismiss = () => {
    localStorage.setItem("sarthi_sandbox_warning_dismissed_v3", "true");
    setIsOpen(false);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[110] flex items-center justify-center p-4">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-indigo-950/45 backdrop-blur-md"
          />

          {/* Card */}
          <motion.div
            initial={{ scale: 0.95, opacity: 0, y: 15 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.95, opacity: 0, y: 15 }}
            transition={{ type: "spring", duration: 0.5 }}
            className="relative w-full max-w-md bg-stone-50 border border-stone-200/60 p-6 md:p-8 rounded-3xl shadow-2xl z-10 flex flex-col items-center text-center space-y-5"
          >
            <div className="w-12 h-12 rounded-2xl bg-amber-50 border border-amber-200/50 flex items-center justify-center text-amber-500 animate-bounce">
              <AlertTriangle className="w-6 h-6" />
            </div>

            <div className="space-y-2">
              <h3 className="text-lg font-bold font-display text-stone-850">
                Sarthi Testing Phase Notice
              </h3>
              <p className="text-xs text-stone-500 leading-relaxed font-semibold">
                Sarthi is currently in its active testing stage. To explore, please use the **Demo Credentials** below, or sign up with an email containing <span className="text-indigo-900 font-bold">@sarthi</span> (e.g. <code className="bg-indigo-50 px-1 py-0.5 rounded text-[10px]">yourname@sarthi</code>). Do not use sensitive database or personal credentials.
              </p>
              
              <div className="p-3 bg-indigo-50/60 border border-indigo-100 rounded-2xl text-[11px] font-semibold text-left text-indigo-950 space-y-1 mt-2">
                <p className="text-[10px] text-stone-500 font-bold uppercase tracking-wider">Demo Account Login</p>
                <div className="flex justify-between font-mono">
                  <span>Email:</span>
                  <span className="font-bold">asur@sarthi.com</span>
                </div>
                <div className="flex justify-between font-mono">
                  <span>Password:</span>
                  <span className="font-bold">Asur@123</span>
                </div>
              </div>
            </div>

            <button
              onClick={handleDismiss}
              className="w-full bg-indigo-950 hover:bg-indigo-900 border border-indigo-900/50 text-amber-500 rounded-xl py-3 text-xs font-bold transition-all hover:shadow-md cursor-pointer"
            >
              I Understand & Proceed
            </button>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

export default function Home() {
  const { 
    activeChatId, 
    activeProjectId, 
    showLeftPane, 
    setShowLeftPane, 
    projects, 
    chats, 
    activeWorkspaceTab, 
    setActiveWorkspaceTab, 
    setShowAbout, 
    setShowContact,
    setShowFeedbackModal,
    showSpecsDocs,
    createNewChat
  } = useWorkspace();
  const [showSplash, setShowSplash] = useState(true);
  const [isMobile, setIsMobile] = useState(false);
  const [mobileTab, setMobileTab] = useState<"menu" | "chat" | "build">("chat");

  // Compute finalized state
  const activeChat = chats.find((c) => c.id === activeChatId);
  const activeProj = projects.find((p) => p.id === (activeProjectId || activeChat?.project_id)) ||
    (activeChatId ? projects.find((p) => p.chat_id === activeChatId) : undefined);
  const isProjectFinalized = activeProj?.status === "documents_ready" || activeProj?.status === "waiting_approval" || activeProj?.status === "generating" || activeProj?.status === "completed";
  const shouldBeFullWidth = activeProj?.status === "generating" || activeProj?.status === "completed" || 
                            ((activeProj?.status === "documents_ready" || activeProj?.status === "waiting_approval") && showSpecsDocs);

  // Request notification permissions
  useEffect(() => {
    if (typeof window !== "undefined" && "Notification" in window) {
      if (Notification.permission === "default") {
        Notification.requestPermission();
      }
    }
  }, []);

  // Send notification when work is done
  const prevProjStatusRef = useRef<string | undefined>(undefined);
  useEffect(() => {
    if (activeProj && activeProj.status === "completed" && prevProjStatusRef.current && prevProjStatusRef.current !== "completed") {
      if (typeof window !== "undefined" && "Notification" in window && Notification.permission === "granted") {
        new Notification("Sarthi Project Built", {
          body: `Work is done! The codebase for "${activeProj.name}" has been compiled successfully.`,
          icon: "/icon.svg"
        });
      }
    }
    prevProjStatusRef.current = activeProj?.status;
  }, [activeProj?.status, activeProj?.name]);

  // Mobile navigation tab handlers
  useEffect(() => {
    if (isMobile && activeChatId) {
      setMobileTab("chat");
    }
  }, [activeChatId, isMobile]);

  useEffect(() => {
    const handleChangeTab = (e: Event) => {
      const customEvent = e as CustomEvent;
      if (customEvent.detail) {
        setMobileTab(customEvent.detail);
      }
    };
    window.addEventListener("change-mobile-tab", handleChangeTab);
    return () => window.removeEventListener("change-mobile-tab", handleChangeTab);
  }, []);

  const statusTransitionRef = useRef<string | undefined>(undefined);
  useEffect(() => {
    if (isMobile && activeProj?.status === "generating" && statusTransitionRef.current !== "generating") {
      setMobileTab("build");
    }
    statusTransitionRef.current = activeProj?.status;
  }, [activeProj?.status, isMobile]);

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768);
    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  // Resize Width States
  const [leftWidth, setLeftWidth] = useState<number>(320);
  const [rightWidth, setRightWidth] = useState<number>(550);
  const [isDraggingLeft, setIsDraggingLeft] = useState(false);
  const [isDraggingRight, setIsDraggingRight] = useState(false);

  const leftWidthRef = useRef(leftWidth);
  const rightWidthRef = useRef(rightWidth);

  // Sync refs to avoid listener recreation lag
  useEffect(() => {
    leftWidthRef.current = leftWidth;
  }, [leftWidth]);

  useEffect(() => {
    rightWidthRef.current = rightWidth;
  }, [rightWidth]);

  // Load saved sidebar sizes from localStorage on mount
  useEffect(() => {
    const savedLeft = localStorage.getItem("sidebar_left_width");
    const savedRight = localStorage.getItem("sidebar_right_width");
    if (savedLeft) setLeftWidth(parseInt(savedLeft, 10));
    if (savedRight) setRightWidth(parseInt(savedRight, 10));
  }, []);

  const startResizeLeft = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsDraggingLeft(true);
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
  };

  const startResizeRight = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsDraggingRight(true);
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (isDraggingLeft) {
        // Limit left sidebar between 240px and 480px
        const newWidth = Math.max(240, Math.min(e.clientX, 480));
        setLeftWidth(newWidth);
      } else if (isDraggingRight) {
        // Limit right sidebar between 360px and 70% of screen width
        const newWidth = Math.max(360, Math.min(window.innerWidth - e.clientX, window.innerWidth * 0.7));
        setRightWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      if (isDraggingLeft) {
        setIsDraggingLeft(false);
        localStorage.setItem("sidebar_left_width", leftWidthRef.current.toString());
      }
      if (isDraggingRight) {
        setIsDraggingRight(false);
        localStorage.setItem("sidebar_right_width", rightWidthRef.current.toString());
      }
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };

    if (isDraggingLeft || isDraggingRight) {
      window.addEventListener("mousemove", handleMouseMove);
      window.addEventListener("mouseup", handleMouseUp);
    }

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isDraggingLeft, isDraggingRight]);

  return (
    <>
      {/* Animated Loading Splash Screen */}
      <AnimatePresence mode="wait">
        {showSplash && (
          <ChariotSplash key="splash" onComplete={() => setShowSplash(false)} />
        )}
      </AnimatePresence>

      {!showSplash && (
        <>
          {isMobile ? (
            <div className="flex flex-col h-screen w-screen bg-stone-50 overflow-hidden font-sans text-stone-800 transition-colors duration-300 relative">
              {/* Global Floating Wave Background */}
              <WaveBackground 
                className="fixed inset-0 w-full h-full pointer-events-none -z-10 opacity-70" 
                status={activeProj?.status}
                progress={activeProj?.progress}
              />

              {/* Main Content Area */}
              <div className="flex-1 overflow-hidden relative flex flex-col">
                {mobileTab === "menu" && (
                  <div className="w-full h-full overflow-hidden bg-white/40 backdrop-blur-md">
                    <Sidebar isCollapsed={false} />
                  </div>
                )}
                {mobileTab === "chat" && (
                  <div className="w-full h-full overflow-hidden flex flex-col">
                    <WorkspaceConsole isMinimized={false} />
                  </div>
                )}
                {mobileTab === "build" && (
                  <div className="w-full h-full overflow-hidden">
                    {(activeProj || activeChatId) ? (
                      <ProjectViewer />
                    ) : (
                      <div className="flex-1 flex flex-col items-center justify-center p-8 text-center h-full bg-white/20 backdrop-blur-md space-y-4">
                        <div className="w-16 h-16 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-950 shadow-sm">
                          <FolderPlus className="w-8 h-8" />
                        </div>
                        <div className="space-y-1">
                          <h3 className="font-bold text-stone-850">No Active Project</h3>
                          <p className="text-xs text-stone-500 max-w-xs leading-relaxed font-semibold">
                            No active project found in this workspace. Let's create one.
                          </p>
                        </div>
                        <button
                          onClick={async () => {
                            const newChatId = await createNewChat("other", "New Project");
                            setActiveWorkspaceTab("workspace");
                          }}
                          className="px-6 py-2.5 bg-indigo-950 hover:bg-indigo-900 text-amber-500 font-bold rounded-xl text-xs flex items-center justify-center gap-1.5 transition-all shadow-md cursor-pointer"
                        >
                          <Plus className="w-4 h-4" />
                          <span>Start New Project</span>
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Mobile Bottom Navigation Bar */}
              <div className="h-16 border-t border-stone-200/80 bg-white/80 backdrop-blur-xl flex items-center justify-around shrink-0 z-40 select-none pb-safe">
                {/* Chats Tab */}
                <button
                  onClick={() => setMobileTab("menu")}
                  className={`flex flex-col items-center justify-center gap-1 flex-1 h-full transition-colors cursor-pointer ${
                    mobileTab === "menu" ? "text-indigo-950 font-bold" : "text-stone-400 font-semibold"
                  }`}
                >
                  <MessageSquare className="w-5 h-5" />
                  <span className="text-[10px] tracking-wide font-bold">Chats</span>
                </button>

                {/* Chat Tab */}
                <button
                  onClick={() => setMobileTab("chat")}
                  className={`flex flex-col items-center justify-center gap-1 flex-1 h-full transition-colors cursor-pointer ${
                    mobileTab === "chat" ? "text-indigo-950 font-bold" : "text-stone-400 font-semibold"
                  }`}
                >
                  <SarthiLogo className="w-5 h-5 text-indigo-950" />
                  <span className="text-[10px] tracking-wide font-bold">Charioteer</span>
                </button>

                {/* Build Tab */}
                <button
                  onClick={() => setMobileTab("build")}
                  className={`flex flex-col items-center justify-center gap-1 flex-1 h-full transition-colors cursor-pointer ${
                    mobileTab === "build" ? "text-indigo-950 font-bold" : "text-stone-400 font-semibold"
                  }`}
                >
                  <FolderGit2 className="w-5 h-5" />
                  <span className="text-[10px] tracking-wide font-bold">Workspaces</span>
                </button>
              </div>
            </div>
          ) : (
            <div className="flex h-screen w-screen overflow-hidden bg-transparent font-sans text-stone-800 transition-colors duration-300 relative">
              {/* Global Floating Wave Background */}
              <WaveBackground 
                className="fixed inset-0 w-full h-full pointer-events-none -z-10 opacity-70" 
                status={activeProj?.status}
                progress={activeProj?.progress}
              />

              {/* Full-screen invisible drag overlay to ensure smooth drags over iframes/inputs */}
              {isDraggingLeft && (
                <div className="fixed inset-0 z-50 cursor-col-resize select-none pointer-events-auto" />
              )}

              {/* Sidebar Panel (Left) */}
              <AnimatePresence initial={false}>
                {showLeftPane && (
                  <motion.div
                    initial={{ width: 0, opacity: 0 }}
                    animate={{ width: `${leftWidth}px`, opacity: 1 }}
                    exit={{ width: 0, opacity: 0 }}
                    transition={{ duration: isDraggingLeft ? 0 : 0.3, ease: [0.4, 0, 0.2, 1] }}
                    className="h-full flex shrink-0 overflow-visible relative"
                  >
                    <div className="w-full h-full overflow-hidden">
                      <Sidebar isCollapsed={leftWidth < 200} />
                    </div>

                    {/* Left Resizer Handle (Only on desktop) */}
                    <div
                      onMouseDown={startResizeLeft}
                      onDoubleClick={() => {
                        setLeftWidth(320);
                        localStorage.setItem("sidebar_left_width", "320");
                      }}
                      className="absolute top-0 right-[-3px] w-[6px] h-full cursor-col-resize z-50 group flex items-center justify-center"
                    >
                      {/* The vertical divider line */}
                      <div className="w-[1px] h-full bg-transparent group-hover:bg-indigo-400 group-active:bg-indigo-600 transition-colors" />
                      
                      {/* Visual grab handle */}
                      <div className="absolute top-1/2 right-1/2 translate-x-1/2 -translate-y-1/2 w-3.5 h-8 bg-stone-50 border border-stone-200 rounded-lg shadow-sm opacity-0 group-hover:opacity-100 group-active:opacity-100 transition-opacity flex flex-col items-center justify-center gap-[2.5px] pointer-events-none z-50">
                        <div className="w-1.5 h-[1.5px] bg-stone-400 rounded-full" />
                        <div className="w-1.5 h-[1.5px] bg-stone-400 rounded-full" />
                        <div className="w-1.5 h-[1.5px] bg-stone-400 rounded-full" />
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Unified Center Panel Workspace (Right Panel completely removed) */}
              <div className="flex-1 flex flex-col h-full overflow-hidden relative">
                {/* Unified Header with central tab switcher */}
                <header className="h-16 px-6 border-b border-stone-200/60 bg-white/30 backdrop-blur-md flex items-center justify-between shrink-0 select-none z-10 transition-colors duration-300 relative">
                  <div className="flex items-center gap-2">
                    {!showLeftPane && (
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

                  {/* Central Tab Switcher */}
                  <div className="flex bg-stone-100/80 p-1 rounded-xl border border-stone-200/50">
                    <button
                      onClick={() => setActiveWorkspaceTab("chat")}
                      className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
                        activeWorkspaceTab === "chat"
                          ? "bg-white text-indigo-950 shadow-sm"
                          : "text-stone-500 hover:text-stone-850"
                      }`}
                    >
                      <MessageSquare className="w-3.5 h-3.5" />
                      Chat
                    </button>
                    <button
                      onClick={() => setActiveWorkspaceTab("workspace")}
                      className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
                        activeWorkspaceTab === "workspace"
                          ? "bg-white text-indigo-950 shadow-sm"
                          : "text-stone-500 hover:text-stone-850"
                      }`}
                    >
                      <FolderGit2 className="w-3.5 h-3.5" />
                      Workspace
                      {activeProj && activeProj.status === "generating" && (
                        <span className="w-2 h-2 rounded-full bg-amber-500 animate-ping" />
                      )}
                    </button>
                  </div>

                  <div className="flex items-center gap-4 text-xs font-semibold text-stone-500">
                    <motion.button
                      onClick={() => setShowAbout(true)}
                      whileHover={{ color: "#1c1917" }}
                      className="hover:text-stone-800 transition-colors cursor-pointer"
                    >
                      About
                    </motion.button>
                    <span className="text-stone-300">/</span>
                    <motion.button
                      onClick={() => setShowContact(true)}
                      whileHover={{ color: "#1c1917" }}
                      className="hover:text-stone-800 transition-colors cursor-pointer"
                    >
                      Contact
                    </motion.button>
                    <span className="text-stone-300">/</span>
                    <motion.button
                      onClick={() => setShowFeedbackModal(true)}
                      whileHover={{ color: "#1c1917" }}
                      className="hover:text-indigo-900 text-indigo-650 font-bold transition-colors cursor-pointer"
                    >
                      Feedback
                    </motion.button>
                  </div>
                </header>

                <main className="flex-1 flex overflow-hidden relative">
                  {activeWorkspaceTab === "chat" ? (
                    <WorkspaceConsole 
                      isMinimized={false} 
                    />
                  ) : (
                    <div className="w-full h-full overflow-hidden flex flex-col bg-transparent">
                      {(activeProj || activeChatId) ? (
                        <ProjectViewer />
                      ) : (
                        <div className="flex-1 flex flex-col items-center justify-center p-8 text-center h-full bg-white/20 backdrop-blur-md space-y-4">
                          <div className="w-16 h-16 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-950 shadow-sm">
                            <FolderPlus className="w-8 h-8" />
                          </div>
                          <div className="space-y-1">
                            <h3 className="font-bold text-stone-850">No Active Project</h3>
                            <p className="text-xs text-stone-500 max-w-xs leading-relaxed font-semibold">
                              No active project found in this workspace. Let's create one.
                            </p>
                          </div>
                          <button
                            onClick={async () => {
                              const newChatId = await createNewChat("other", "New Project");
                              setActiveWorkspaceTab("workspace");
                            }}
                            className="px-6 py-2.5 bg-indigo-950 hover:bg-indigo-900 text-amber-500 font-bold rounded-xl text-xs flex items-center justify-center gap-1.5 transition-all shadow-md cursor-pointer"
                          >
                            <Plus className="w-4 h-4" />
                            <span>Start New Project</span>
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </main>
              </div>
            </div>
          )}

          {/* Modals & Slide-out Drawers */}
          <AuthModal />
          <AboutContactDrawer />
          <SandboxWarningModal />
          <CommandMenu />
          <FeedbackModal />
        </>
      )}
    </>
  );
}


