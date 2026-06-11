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
import { PanelLeft } from "lucide-react";
import { WaveBackground } from "@/components/CustomSvgs";


export default function Home() {
  const { activeChatId, activeProjectId, showRightPane, showLeftPane, setShowLeftPane, projects, chats } = useWorkspace();
  const [showSplash, setShowSplash] = useState(true);

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
          <WaveBackground className="fixed inset-0 w-full h-full pointer-events-none -z-10 opacity-70" />

          {/* Full-screen invisible drag overlay to ensure smooth drags over iframes/inputs */}
          {(isDraggingLeft || isDraggingRight) && (
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

                {/* Left Resizer Handle */}
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
              </motion.div>
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
                  initial={{ width: 0, opacity: 0 }}
                  animate={isProjectFinalized ? { width: "100%", opacity: 1 } : { width: `${rightWidth}px`, opacity: 1 }}
                  exit={{ width: 0, opacity: 0 }}
                  transition={{ duration: isDraggingRight ? 0 : 0.4, ease: [0.4, 0, 0.2, 1] }}
                  className={`${isProjectFinalized ? "w-full" : "border-l"} border-stone-200/60 h-full flex shrink-0 overflow-visible relative`}
                  style={isProjectFinalized ? { flex: 1 } : {}}
                >
                  {/* Right Resizer Handle (Only show if not finalized) */}
                  {!isProjectFinalized && (
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
        </div>
      )}
    </>
  );
}


