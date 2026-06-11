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
import { PanelLeft, AlertTriangle, Monitor, RefreshCw, Zap } from "lucide-react";
import { WaveBackground } from "@/components/CustomSvgs";
import { CommandMenu } from "@/components/CommandMenu";
import { MOCK_USER, MOCK_CHATS, MOCK_PROJECTS } from "@/utils/demoData";

const SandboxWarningModal: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const dismissed = localStorage.getItem("sarthi_sandbox_warning_dismissed");
    if (!dismissed) {
      setIsOpen(true);
    }
  }, []);

  const handleDismiss = () => {
    localStorage.setItem("sarthi_sandbox_warning_dismissed", "true");
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
                Sarthi Sandbox Notice
              </h3>
              <p className="text-xs text-stone-500 leading-relaxed font-semibold">
                Sarthi is currently in its active testing and prototype phase. Please do not input original or sensitive database credentials, API keys, or personal information. Use mock details for all chat conversations and sandbox setups.
              </p>
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
    showRightPane, 
    showLeftPane, 
    setShowLeftPane, 
    projects, 
    chats,
    loadDemoData, 
    setUser, 
    setChats, 
    setProjects, 
    setActiveChatId, 
    setActiveProjectId,
    setShowRightPane,
    setShowAuthModal,
    setAuthMode,
    user
  } = useWorkspace();
  const [showSplash, setShowSplash] = useState(true);
  const [isMobile, setIsMobile] = useState(false);
  const [activeScreen, setActiveScreen] = useState("select");

  const handleScreenShift = (screenKey: string) => {
    setActiveScreen(screenKey);

    // 1. If not logged out, ensure demo data is loaded first
    if (screenKey !== "welcome_splash" && screenKey !== "logged_out_chat" && screenKey !== "auth_login_modal" && screenKey !== "auth_signup_modal") {
      if (!user || chats.length === 0 || projects.length === 0) {
        loadDemoData();
      }
    }

    // Close modals
    setShowAuthModal(false);
    window.dispatchEvent(new CustomEvent("open-profile-modal", { detail: { close: true } }));
    window.dispatchEvent(new CustomEvent("set-splash-screen", { detail: { show: false } }));

    switch (screenKey) {
      case "welcome_splash":
        window.dispatchEvent(new CustomEvent("set-splash-screen", { detail: { show: true } }));
        break;

      case "logged_out_chat":
        setUser(null);
        setActiveChatId(null);
        setActiveProjectId(null);
        setShowRightPane(false);
        break;

      case "logged_in_fresh":
        setUser(MOCK_USER);
        setActiveChatId(null);
        setActiveProjectId(null);
        setShowRightPane(false);
        break;

      case "design_blueprint":
        setUser(MOCK_USER);
        setActiveChatId("chat-1");
        setActiveProjectId(null);
        setShowRightPane(true);
        setTimeout(() => {
          window.dispatchEvent(new CustomEvent("set-project-viewer-stage", { detail: { stage: "blueprint" } }));
        }, 50);
        break;

      case "theme_selector":
        setUser(MOCK_USER);
        setActiveChatId("chat-1");
        setActiveProjectId(null);
        setShowRightPane(true);
        setChats(prev => prev.map(c => c.id === "chat-1" ? { ...c, selected_project: { ...c.selected_project!, name: c.selected_project?.name || "CalmPath Breathing App" } } : c));
        setTimeout(() => {
          window.dispatchEvent(new CustomEvent("set-project-viewer-stage", { detail: { stage: "theme" } }));
        }, 50);
        break;

      case "spec_documents":
        setUser(MOCK_USER);
        setActiveChatId("chat-2");
        setActiveProjectId("proj-1");
        setShowRightPane(true);
        setTimeout(() => {
          window.dispatchEvent(new CustomEvent("set-project-viewer-doc-tab", { detail: { tab: "prd" } }));
        }, 50);
        break;

      case "compiler_progress":
        setUser(MOCK_USER);
        setActiveChatId("chat-3");
        setActiveProjectId("proj-2");
        setShowRightPane(true);
        break;

      case "failed_build":
        setUser(MOCK_USER);
        setActiveChatId("chat-4");
        setActiveProjectId("proj-3");
        setShowRightPane(true);
        break;

      case "code_viewer":
        setUser(MOCK_USER);
        setActiveChatId("chat-5");
        setActiveProjectId("proj-4");
        setShowRightPane(true);
        setTimeout(() => {
          window.dispatchEvent(new CustomEvent("set-project-viewer-tab", { detail: { tab: "files" } }));
        }, 50);
        break;

      case "vyuh_map":
        setUser(MOCK_USER);
        setActiveChatId("chat-5");
        setActiveProjectId("proj-4");
        setShowRightPane(true);
        setTimeout(() => {
          window.dispatchEvent(new CustomEvent("set-project-viewer-tab", { detail: { tab: "vyuh" } }));
        }, 50);
        break;

      case "profile_modal":
        setUser(MOCK_USER);
        window.dispatchEvent(new CustomEvent("open-profile-modal", { detail: { tab: "profile" } }));
        break;

      case "help_modal":
        setUser(MOCK_USER);
        window.dispatchEvent(new CustomEvent("open-profile-modal", { detail: { tab: "help" } }));
        break;

      case "auth_login_modal":
        setUser(null);
        setShowAuthModal(true);
        setAuthMode("login");
        break;

      case "auth_signup_modal":
        setUser(null);
        setShowAuthModal(true);
        setAuthMode("signup");
        break;

      default:
        break;
    }
  };

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768);
    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  useEffect(() => {
    const handleSetSplash = (e: Event) => {
      const customEvent = e as CustomEvent;
      if (customEvent.detail && customEvent.detail.show !== undefined) {
        setShowSplash(customEvent.detail.show);
      }
    };
    window.addEventListener("set-splash-screen", handleSetSplash);
    return () => window.removeEventListener("set-splash-screen", handleSetSplash);
  }, []);

  // Compute finalized state
  const activeChat = chats.find((c) => c.id === activeChatId);
  const activeProj = projects.find((p) => p.id === (activeProjectId || activeChat?.project_id)) ||
    (activeChatId ? projects.find((p) => p.chat_id === activeChatId) : undefined);
  const isProjectFinalized = activeProj?.status === "documents_ready" || activeProj?.status === "generating" || activeProj?.status === "completed";

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
        <div className="flex h-screen w-screen overflow-hidden bg-transparent font-sans text-stone-800 transition-colors duration-300 relative">
          {/* Global Floating Wave Background */}
          <WaveBackground 
            className="fixed inset-0 w-full h-full pointer-events-none -z-10 opacity-70" 
            status={activeProj?.status}
            progress={activeProj?.progress}
          />

          {/* Full-screen invisible drag overlay to ensure smooth drags over iframes/inputs */}
          {(isDraggingLeft || isDraggingRight) && (
            <div className="fixed inset-0 z-50 cursor-col-resize select-none pointer-events-auto" />
          )}

          {/* Sidebar Panel (Left) */}
          <AnimatePresence initial={false}>
            {showLeftPane && (
              <>
                {/* Mobile Backdrop overlay */}
                {isMobile && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    onClick={() => setShowLeftPane(false)}
                    className="fixed inset-0 bg-stone-900/40 backdrop-blur-sm z-[35] pointer-events-auto"
                  />
                )}
                <motion.div
                  initial={isMobile ? { x: "-100%", opacity: 0 } : { width: 0, opacity: 0 }}
                  animate={isMobile ? { x: 0, opacity: 1, width: "280px" } : { width: `${leftWidth}px`, opacity: 1 }}
                  exit={isMobile ? { x: "-100%", opacity: 0 } : { width: 0, opacity: 0 }}
                  transition={{ duration: isDraggingLeft ? 0 : 0.3, ease: [0.4, 0, 0.2, 1] }}
                  className={`h-full flex shrink-0 overflow-visible ${isMobile ? "fixed top-0 left-0 z-40 bg-stone-50" : "relative"}`}
                >
                  <div className="w-full h-full overflow-hidden">
                    <Sidebar isCollapsed={leftWidth < 200 && !isMobile} />
                  </div>

                  {/* Left Resizer Handle (Only on desktop) */}
                  {!isMobile && (
                    <div
                      onMouseDown={startResizeLeft}
                      onDoubleClick={() => {
                        setLeftWidth(320);
                        localStorage.setItem("sidebar_left_width", "320");
                      }}
                      className="absolute top-0 right-[-3px] w-[6px] h-full cursor-col-resize z-50 group flex items-center justify-center"
                    >
                      {/* The vertical divider line */}
                      <div className="w-[1px] h-full bg-stone-200/60 group-hover:bg-indigo-400 group-active:bg-indigo-600 transition-colors" />
                      
                      {/* Visual grab handle */}
                      <div className="absolute top-1/2 right-1/2 translate-x-1/2 -translate-y-1/2 w-3.5 h-8 bg-stone-50 border border-stone-200 rounded-lg shadow-sm opacity-0 group-hover:opacity-100 group-active:opacity-100 transition-opacity flex flex-col items-center justify-center gap-[2.5px] pointer-events-none z-50">
                        <div className="w-1.5 h-[1.5px] bg-stone-400 rounded-full" />
                        <div className="w-1.5 h-[1.5px] bg-stone-400 rounded-full" />
                        <div className="w-1.5 h-[1.5px] bg-stone-400 rounded-full" />
                      </div>
                    </div>
                  )}
                </motion.div>
              </>
            )}
          </AnimatePresence>

          {/* Main Console Arena */}
          <main className="flex-1 flex overflow-hidden relative">
            {/* Global restore left pane button when minimized/hidden */}
            {(!showLeftPane && isProjectFinalized) && (
              <motion.button
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                whileHover={{ scale: 1.06 }}
                whileTap={{ scale: 0.93 }}
                onClick={() => setShowLeftPane(true)}
                className="absolute top-[26px] left-6 z-50 p-1.5 rounded-lg border border-indigo-200 bg-indigo-50/50 text-indigo-950 transition-all shadow-sm flex items-center justify-center cursor-pointer"
                title="Expand Sidebar"
              >
                <PanelLeft className="w-4 h-4" />
              </motion.button>
            )}

            {/* Chat / Interaction Console (Center) */}
            <WorkspaceConsole isMinimized={isProjectFinalized} />

            {/* Dynamic Project Details / Compiling Board (Right pane) */}
            <AnimatePresence initial={false}>
              {(activeProjectId || activeChatId) && showRightPane && (
                <motion.div
                  initial={isMobile ? { x: "100%", opacity: 0 } : { width: 0, opacity: 0 }}
                  animate={isMobile ? { x: 0, opacity: 1, width: "100%" } : (isProjectFinalized ? { width: "100%", opacity: 1 } : { width: `${rightWidth}px`, opacity: 1 })}
                  exit={isMobile ? { x: "100%", opacity: 0 } : { width: 0, opacity: 0 }}
                  transition={{ duration: isDraggingRight ? 0 : 0.4, ease: [0.4, 0, 0.2, 1] }}
                  className={`${isMobile ? "fixed inset-0 z-30 bg-stone-50" : (isProjectFinalized ? "w-full" : "border-l border-stone-200/60")} h-full flex shrink-0 overflow-visible relative`}
                  style={!isMobile && isProjectFinalized ? { flex: 1 } : {}}
                >
                  {/* Right Resizer Handle (Only show if not finalized and not mobile) */}
                  {!isProjectFinalized && !isMobile && (
                    <div
                      onMouseDown={startResizeRight}
                      onDoubleClick={() => {
                        setRightWidth(550);
                        localStorage.setItem("sidebar_right_width", "550");
                      }}
                      className="absolute top-0 left-[-3px] w-[6px] h-full cursor-col-resize z-50 group flex items-center justify-center"
                    >
                      {/* The vertical divider line */}
                      <div className="w-[1px] h-full bg-stone-200/60 group-hover:bg-indigo-400 group-active:bg-indigo-600 transition-colors" />

                      {/* Visual grab handle */}
                      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-3.5 h-8 bg-stone-50 border border-stone-200 rounded-lg shadow-sm opacity-0 group-hover:opacity-100 group-active:opacity-100 transition-opacity flex flex-col items-center justify-center gap-[2.5px] pointer-events-none z-50">
                        <div className="w-1.5 h-[1.5px] bg-stone-400 rounded-full" />
                        <div className="w-1.5 h-[1.5px] bg-stone-400 rounded-full" />
                        <div className="w-1.5 h-[1.5px] bg-stone-400 rounded-full" />
                      </div>
                    </div>
                  )}

                  <div className="w-full h-full overflow-hidden">
                    <ProjectViewer />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </main>

          {/* Modals & Slide-out Drawers */}
          <AuthModal />
          <AboutContactDrawer />
          <SandboxWarningModal />
          <CommandMenu />

          {/* Temporary Screen Navigator Toolbar for screenshots */}
          <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-[100] px-4 py-2 bg-stone-950/85 backdrop-blur-md border border-stone-850 text-white rounded-2xl shadow-2xl flex items-center gap-3 text-xs max-w-[95vw] overflow-x-auto whitespace-nowrap scrollbar-none transition-all duration-300">
            <div className="flex items-center gap-2 border-r border-stone-800 pr-3 shrink-0">
              <Zap className="w-4 h-4 text-amber-500 fill-amber-500 animate-pulse animate-duration-1000" />
              <span className="font-extrabold text-[10px] tracking-wider uppercase text-stone-300">Screen Navigator</span>
            </div>
            
            <button
              onClick={loadDemoData}
              className="px-2.5 py-1.5 bg-amber-500 hover:bg-amber-400 text-stone-950 rounded-lg text-[10px] font-extrabold tracking-wide flex items-center gap-1 transition-all active:scale-95 cursor-pointer shrink-0"
            >
              <RefreshCw className="w-3 h-3 shrink-0" />
              Seed Demo Data
            </button>

            <div className="relative shrink-0">
              <select
                value={activeScreen}
                onChange={(e) => handleScreenShift(e.target.value)}
                className="bg-stone-900 border border-stone-800 rounded-lg px-2 py-1.5 text-[10px] font-bold text-stone-200 outline-none cursor-pointer focus:ring-1 focus:ring-amber-500/50 appearance-none pr-6"
              >
                <option value="select" disabled>-- Switch Screen View --</option>
                <option value="welcome_splash">Screen 1: Welcome Splash</option>
                <option value="logged_out_chat">Screen 2: Chat Console (Logged Out)</option>
                <option value="logged_in_fresh">Screen 3: Chat Console (Logged In - Fresh)</option>
                <option value="design_blueprint">Screen 4: Design Blueprint Editor</option>
                <option value="theme_selector">Screen 5: Theme & Palette Selector</option>
                <option value="spec_documents">Screen 6: Requirements Specs (PRD/MRD/TRD)</option>
                <option value="compiler_progress">Screen 7: Code Compiler (Generating)</option>
                <option value="failed_build">Screen 8: Failed Build / Correction</option>
                <option value="code_viewer">Screen 9: Completed Code Editor (Files)</option>
                <option value="vyuh_map">Screen 10: Vyuh Mandala Graph</option>
                <option value="profile_modal">Screen 11: Developer Profile Modal</option>
                <option value="help_modal">Screen 12: Help & Support Guide Modal</option>
                <option value="auth_login_modal">Screen 13: Auth Modal (Login Mode)</option>
                <option value="auth_signup_modal">Screen 14: Auth Modal (Signup Mode)</option>
              </select>
              <div className="absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none text-[8px] text-stone-400 select-none">
                ▼
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}


