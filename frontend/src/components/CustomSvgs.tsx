"use client";

import React from "react";
import { motion } from "framer-motion";

// 1. Sarthi Animated Logo (Peacock Script Theme)
export const SarthiLogo: React.FC<{ className?: string }> = ({ className = "text-3xl" }) => {
  return (
    <motion.div
      className={`font-[family-name:var(--font-dancing-script)] font-bold select-none whitespace-nowrap bg-gradient-to-r from-[#1e1b4b] via-[#0f766e] to-[#4338ca] bg-clip-text text-transparent drop-shadow-sm ${className}`}
      style={{ backgroundSize: "200% auto" }}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
    >
      Sarthi
    </motion.div>
  );
};

// 2. Premium Lock & Unlock Icon (Dynamic transitions)
export const AnimatedLock: React.FC<{ isLocked: boolean; className?: string }> = ({
  isLocked,
  className = "w-12 h-12"
}) => {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={`${className} text-stone-400`}
    >
      {/* Shackle */}
      <motion.path
        d="M7 11V7a5 5 0 0 1 10 0v4"
        animate={isLocked ? { d: "M7 11V7a5 5 0 0 1 10 0v4" } : { d: "M7 11V7a5 5 0 0 1 9.9-1V4" }}
        transition={{ duration: 0.5, ease: "easeInOut" }}
      />
      {/* Body */}
      <rect x="3" y="11" width="18" height="11" rx="2" ry="2" fill="currentColor" fillOpacity="0.05" />
      {/* Keyhole */}
      <path d="M12 15v3" />
      <circle cx="12" cy="15" r="1" />
    </svg>
  );
};

// 3. Category Icons (Custom vector designs, no generic icons)
export const CategoryIcon: React.FC<{ category: string; className?: string }> = ({
  category,
  className = "w-5 h-5"
}) => {
  const norm = category.toLowerCase();

  if (norm === "startup") {
    return (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
        <path d="M4.5 16.5c-1.5 1.25-2.5 3.5-2.5 3.5s2.25-1 3.5-2.5M15 3h6v6M10 14L21 3M10 14a3.5 3.5 0 1 1-5-5l5-5c2.5 0 5 1.5 6 4s0 5-2 6Z" />
      </svg>
    );
  }

  if (norm === "finance") {
    return (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
        <circle cx="12" cy="12" r="10" />
        <path d="M12 6v12M15 9H10.5a2.5 2.5 0 0 0 0 5H14a2.5 2.5 0 0 1 0 5H9" />
      </svg>
    );
  }

  if (norm === "health") {
    return (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
        <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
      </svg>
    );
  }

  if (norm === "education") {
    return (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
        <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z" />
        <path d="M6 6h10M6 10h10" />
      </svg>
    );
  }

  if (norm === "productivity") {
    return (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
        <rect x="3" y="3" width="18" height="18" rx="2" />
        <path d="M9 17H5M19 17h-4M9 12H5M19 12h-4M9 7H5M19 7h-4" />
      </svg>
    );
  }

  if (norm === "sustainability") {
    return (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
        <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 3.5 0 8.5C17 15.5 13 20 11 20Z" />
        <path d="M19 2c-2.26 4.33-5.27 7.14-8 10" />
      </svg>
    );
  }

  // "other" or fallback
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
      <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
    </svg>
  );
};

// 4. Custom illustration for landing / lock screen
export const LockIllustration: React.FC<{ className?: string }> = ({ className = "w-40 h-40" }) => {
  return (
    <svg
      viewBox="0 0 200 200"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <circle cx="100" cy="100" r="80" fill="url(#ill-grad-bg)" opacity="0.4" />

      {/* Floating particles */}
      <motion.circle
        cx="40"
        cy="70"
        r="4"
        fill="#f43f5e"
        animate={{ y: [-5, 5, -5] }}
        transition={{ duration: 3, repeat: Infinity }}
      />
      <motion.circle
        cx="160"
        cy="130"
        r="6"
        fill="#6366f1"
        animate={{ y: [5, -5, 5] }}
        transition={{ duration: 4, repeat: Infinity }}
      />
      <motion.circle
        cx="150"
        cy="60"
        r="3"
        fill="#eab308"
        animate={{ scale: [1, 1.4, 1] }}
        transition={{ duration: 2.5, repeat: Infinity }}
      />

      {/* Abstract Grid Mesh inside circle */}
      <path d="M60 100 H140M100 60 V140" stroke="rgba(120, 113, 108, 0.15)" strokeWidth="1.5" />
      <circle cx="100" cy="100" r="40" stroke="rgba(120, 113, 108, 0.1)" strokeWidth="1.5" />

      {/* Shield */}
      <motion.path
        d="M100 50 L140 65 V110 C140 140 100 155 100 155 C100 155 60 140 60 110 V65 Z"
        fill="url(#shield-grad)"
        stroke="#e7e5e4"
        strokeWidth="2.5"
        animate={{ y: [-3, 3, -3] }}
        transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
      />

      {/* Lock Core */}
      <g transform="translate(86, 88)">
        <rect x="0" y="8" width="28" height="20" rx="3" fill="#fafaf9" stroke="#78716c" strokeWidth="2" />
        <path d="M6 8V5a8 8 0 0 1 16 0v3" stroke="#78716c" strokeWidth="2" strokeLinecap="round" />
        <circle cx="14" cy="18" r="2" fill="#78716c" />
      </g>

      <defs>
        <radialGradient id="ill-grad-bg" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#8b5cf6" stopOpacity="0.2" />
          <stop offset="100%" stopColor="#fafaf9" stopOpacity="0" />
        </radialGradient>
        <linearGradient id="shield-grad" x1="100" y1="50" x2="100" y2="155" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#ffffff" />
          <stop offset="100%" stopColor="#f5f5f4" />
        </linearGradient>
      </defs>
    </svg>
  );
};

// 5. High-Fidelity Animated Chariot (Sarthi emblem)
export const AnimatedChariot: React.FC<{ className?: string }> = ({ className = "w-64 h-40" }) => {
  return (
    <div className={`relative flex items-center justify-center overflow-hidden ${className}`}>
      <svg
        viewBox="0 0 180 120"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-full text-indigo-600"
      >
        {/* Ground Line */}
        <line x1="10" y1="90" x2="170" y2="90" stroke="currentColor" strokeWidth="2" opacity="0.3" strokeDasharray="4 4" />

        {/* Speed lines on ground */}
        <motion.line
          x1="160" y1="90" x2="175" y2="90"
          stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"
          animate={{ x: [-200, 20] }}
          transition={{ duration: 1.2, repeat: Infinity, ease: "linear" }}
        />
        <motion.line
          x1="120" y1="90" x2="140" y2="90"
          stroke="currentColor" strokeWidth="2" strokeLinecap="round"
          animate={{ x: [-200, 20] }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear", delay: 0.3 }}
        />
        <motion.line
          x1="70" y1="90" x2="85" y2="90"
          stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"
          animate={{ x: [-200, 20] }}
          transition={{ duration: 1.5, repeat: Infinity, ease: "linear", delay: 0.6 }}
        />

        {/* Chariot & Horse Group (Bounces as it travels) */}
        <motion.g
          animate={{ y: [0, -3, 0] }}
          transition={{ duration: 0.45, repeat: Infinity, ease: "easeInOut" }}
        >
          {/* Shaft connecting chariot to horse */}
          <line x1="55" y1="73" x2="105" y2="73" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />

          {/* Reins */}
          <path d="M 45 52 Q 85 54 118 48" stroke="currentColor" strokeWidth="1.2" fill="none" opacity="0.8" />

          {/* Chariot Body */}
          <path
            d="M 22 50 L 52 50 C 58 50 60 55 58 64 L 54 78 C 53 80 50 82 46 82 L 20 82 C 16 82 14 78 14 74 L 14 56 C 14 52 18 50 22 50 Z"
            fill="currentColor"
            fillOpacity="0.1"
            stroke="currentColor"
            strokeWidth="3"
            strokeLinejoin="round"
          />

          {/* Driver Silhouette */}
          <circle cx="40" cy="38" r="5" stroke="currentColor" strokeWidth="2" fill="currentColor" fillOpacity="0.2" />
          <path d="M 38 43 L 42 43 L 45 58 L 35 58 Z" stroke="currentColor" strokeWidth="2.5" strokeLinejoin="round" fill="currentColor" fillOpacity="0.1" />

          {/* Horse */}
          <g transform="translate(10, 0)">
            {/* Horse Body */}
            <path
              d="M 98 48 L 125 48 C 132 48 135 52 135 60 L 132 75 L 94 75 L 94 62 C 94 54 96 48 98 48 Z"
              fill="currentColor"
              fillOpacity="0.1"
              stroke="currentColor"
              strokeWidth="3"
              strokeLinejoin="round"
            />
            {/* Horse Neck & Head */}
            <path
              d="M 124 48 L 136 28 C 137 26 140 26 141 28 L 143 30 C 144 32 142 34 139 35 L 132 50 Z"
              fill="currentColor"
              fillOpacity="0.1"
              stroke="currentColor"
              strokeWidth="3"
              strokeLinejoin="round"
            />
            {/* Mane */}
            <path d="M 126 44 L 122 36 M 129 40 L 125 32" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />

            {/* Galloping Legs - Front */}
            <motion.path
              d="M 128 73 L 138 90 L 148 84"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              animate={{ rotate: [-20, 20, -20] }}
              transition={{ duration: 0.3, repeat: Infinity, ease: "easeInOut" }}
              style={{ originX: "128px", originY: "73px" }}
            />
            <motion.path
              d="M 122 73 L 130 88 L 138 82"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              animate={{ rotate: [20, -20, 20] }}
              transition={{ duration: 0.3, repeat: Infinity, ease: "easeInOut", delay: 0.15 }}
              style={{ originX: "122px", originY: "73px" }}
            />

            {/* Galloping Legs - Back */}
            <motion.path
              d="M 98 73 L 88 88 L 78 84"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              animate={{ rotate: [20, -20, 20] }}
              transition={{ duration: 0.3, repeat: Infinity, ease: "easeInOut" }}
              style={{ originX: "98px", originY: "73px" }}
            />
            <motion.path
              d="M 104 73 L 96 90 L 86 86"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              animate={{ rotate: [-20, 20, -20] }}
              transition={{ duration: 0.3, repeat: Infinity, ease: "easeInOut", delay: 0.15 }}
              style={{ originX: "104px", originY: "73px" }}
            />
          </g>

          {/* Rotating Chariot Wheel */}
          <g transform="translate(34, 82)">
            <motion.circle
              cx="0"
              cy="0"
              r="14"
              stroke="currentColor"
              strokeWidth="3.5"
              fill="currentColor"
              fillOpacity="0.05"
              animate={{ rotate: 360 }}
              transition={{ duration: 0.9, repeat: Infinity, ease: "linear" }}
            />
            {/* Wheel Spokes */}
            <motion.g
              animate={{ rotate: 360 }}
              transition={{ duration: 0.9, repeat: Infinity, ease: "linear" }}
            >
              <line x1="0" y1="-14" x2="0" y2="14" stroke="currentColor" strokeWidth="2" />
              <line x1="-14" y1="0" x2="14" y2="0" stroke="currentColor" strokeWidth="2" />
              <line x1="-10" y1="-10" x2="10" y2="10" stroke="currentColor" strokeWidth="1.5" />
              <line x1="-10" y1="10" x2="10" y2="-10" stroke="currentColor" strokeWidth="1.5" />
            </motion.g>
          </g>
        </motion.g>
      </svg>
    </div>
  );
};

// 6. Empty State Illustration — minimal animated nodes for empty chat/history
export const EmptyStateIllustration: React.FC<{ className?: string }> = ({ className = "w-40 h-40" }) => (
  <svg viewBox="0 0 160 140" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
    {/* Soft base circle */}
    <circle cx="80" cy="75" r="52" fill="rgba(99,102,241,0.04)" />
    <circle cx="80" cy="75" r="38" stroke="rgba(99,102,241,0.10)" strokeWidth="1.5" strokeDasharray="4 5" />

    {/* Floating nodes */}
    <motion.circle cx="80" cy="38" r="5" fill="rgba(99,102,241,0.18)" stroke="#6366f1" strokeWidth="1.5"
      animate={{ y: [-3, 3, -3] }} transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }} />
    <motion.circle cx="112" cy="68" r="4" fill="rgba(244,63,94,0.15)" stroke="#f43f5e" strokeWidth="1.5"
      animate={{ y: [3, -3, 3] }} transition={{ duration: 3.5, repeat: Infinity, ease: "easeInOut" }} />
    <motion.circle cx="48" cy="68" r="4" fill="rgba(139,92,246,0.15)" stroke="#8b5cf6" strokeWidth="1.5"
      animate={{ y: [-2, 4, -2] }} transition={{ duration: 2.8, repeat: Infinity, ease: "easeInOut" }} />
    <motion.circle cx="80" cy="110" r="4" fill="rgba(6,182,212,0.15)" stroke="#06b6d4" strokeWidth="1.5"
      animate={{ y: [3, -3, 3] }} transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }} />

    {/* Connector lines */}
    <line x1="80" y1="43" x2="80" y2="60" stroke="rgba(99,102,241,0.15)" strokeWidth="1.5" strokeDasharray="3 3" />
    <line x1="108" y1="70" x2="95" y2="75" stroke="rgba(244,63,94,0.15)" strokeWidth="1.5" strokeDasharray="3 3" />
    <line x1="52" y1="70" x2="65" y2="75" stroke="rgba(139,92,246,0.15)" strokeWidth="1.5" strokeDasharray="3 3" />
    <line x1="80" y1="105" x2="80" y2="90" stroke="rgba(6,182,212,0.15)" strokeWidth="1.5" strokeDasharray="3 3" />

    {/* Central icon — message bubble outline */}
    <rect x="60" y="60" width="40" height="30" rx="8" stroke="rgba(99,102,241,0.25)" strokeWidth="1.5" fill="rgba(99,102,241,0.04)" />
    <line x1="68" y1="71" x2="92" y2="71" stroke="rgba(99,102,241,0.25)" strokeWidth="1.5" strokeLinecap="round" />
    <line x1="68" y1="79" x2="84" y2="79" stroke="rgba(99,102,241,0.18)" strokeWidth="1.5" strokeLinecap="round" />
  </svg>
);

// 7. Wave Background — subtle animated wave for lock screen / empty states
export const WaveBackground: React.FC<{ 
  className?: string; 
  status?: string; 
  progress?: number;
}> = ({ className = "absolute inset-0 w-full h-full", status = "idle", progress = 0 }) => {
  // Shifting aura gradient stop colors
  let stop1 = "rgba(99,102,241,0.06)"; // indigo
  let stop2 = "rgba(139,92,246,0.08)"; // purple
  let stop3 = "rgba(244,63,94,0.04)";  // rose

  if (status === "generating") {
    if (progress < 20) {
      // Specs compilation: Slate-blue compilation aura
      stop1 = "rgba(99,102,241,0.08)";
      stop2 = "rgba(71,85,105,0.08)";
      stop3 = "rgba(148,163,184,0.04)";
    } else if (progress < 40) {
      // Database & Models: Violet & lavender schemas aura
      stop1 = "rgba(139,92,246,0.10)";
      stop2 = "rgba(167,139,250,0.08)";
      stop3 = "rgba(232,121,249,0.04)";
    } else if (progress < 85) {
      // Backend & UI: Teal, amber, and gold controllers aura
      stop1 = "rgba(13,148,136,0.10)";
      stop2 = "rgba(245,158,11,0.08)";
      stop3 = "rgba(251,191,36,0.04)";
    } else {
      // Final Assembly: Celestial violet & rose aura
      stop1 = "rgba(124,58,237,0.10)";
      stop2 = "rgba(244,63,94,0.08)";
      stop3 = "rgba(251,113,133,0.04)";
    }
  } else if (status === "completed") {
    // Glowing emerald & gold success aurora
    stop1 = "rgba(16,185,129,0.10)";
    stop2 = "rgba(245,158,11,0.08)";
    stop3 = "rgba(52,211,153,0.04)";
  } else if (status === "failed") {
    // Crimson & slate-grey warning aurora
    stop1 = "rgba(239,68,68,0.10)";
    stop2 = "rgba(75,85,99,0.08)";
    stop3 = "rgba(248,113,113,0.04)";
  }

  return (
    <svg viewBox="0 0 800 400" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg" className={className}>
      <defs>
        <linearGradient id="wave-grad-1" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor={stop1} className="transition-all duration-1000" />
          <stop offset="50%" stopColor={stop2} className="transition-all duration-1000" />
          <stop offset="100%" stopColor={stop3} className="transition-all duration-1000" />
        </linearGradient>
      </defs>
      <motion.path
        d="M0,200 C150,120 350,280 500,200 C650,120 750,250 800,200 L800,400 L0,400 Z"
        fill="url(#wave-grad-1)"
        animate={{ d: [
          "M0,200 C150,120 350,280 500,200 C650,120 750,250 800,200 L800,400 L0,400 Z",
          "M0,220 C100,160 300,260 520,190 C680,130 760,230 800,180 L800,400 L0,400 Z",
          "M0,200 C150,120 350,280 500,200 C650,120 750,250 800,200 L800,400 L0,400 Z",
        ]}}
        transition={{ duration: 3.2, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.path
        d="M0,260 C200,180 400,330 600,250 C720,200 780,280 800,260 L800,400 L0,400 Z"
        fill={status === "completed" ? "rgba(16,185,129,0.05)" : status === "failed" ? "rgba(239,68,68,0.05)" : "rgba(99,102,241,0.04)"}
        className="transition-all duration-1000"
        animate={{ d: [
          "M0,260 C200,180 400,330 600,250 C720,200 780,280 800,260 L800,400 L0,400 Z",
          "M0,240 C180,200 380,310 620,240 C740,190 790,270 800,240 L800,400 L0,400 Z",
          "M0,260 C200,180 400,330 600,250 C720,200 780,280 800,260 L800,400 L0,400 Z",
        ]}}
        transition={{ duration: 4.5, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
      />
    </svg>
  );
};

// 8. Circuit Decor — small decorative circuit-line accent
export const CircuitDecor: React.FC<{ className?: string }> = ({ className = "w-20 h-14" }) => (
  <svg viewBox="0 0 80 56" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
    <path d="M4 28 H22 L28 16 H42 L48 28 H56 L62 20 H76" stroke="rgba(99,102,241,0.20)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M4 36 H18 L24 44 H36" stroke="rgba(139,92,246,0.15)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    <circle cx="22" cy="28" r="2.5" fill="rgba(99,102,241,0.25)" />
    <circle cx="56" cy="28" r="2.5" fill="rgba(244,63,94,0.25)" />
    <circle cx="42" cy="28" r="2" fill="rgba(139,92,246,0.20)" />
    <circle cx="18" cy="36" r="2" fill="rgba(6,182,212,0.20)" />
    <motion.circle cx="76" cy="20" r="3" fill="rgba(99,102,241,0.30)"
      animate={{ scale: [1, 1.4, 1], opacity: [1, 0.6, 1] }}
      transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
    />
    <motion.circle cx="36" cy="44" r="3" fill="rgba(244,63,94,0.30)"
      animate={{ scale: [1, 1.4, 1], opacity: [1, 0.6, 1] }}
      transition={{ duration: 2.5, repeat: Infinity, ease: "easeInOut", delay: 0.8 }}
    />
  </svg>
);

// 9. AI Typing Wave — wave-bar animation for AI thinking indicator
export const AiTypingWave: React.FC<{ className?: string }> = ({ className = "flex items-center gap-0.5" }) => {
  const bars = [0, 1, 2, 3, 4];
  return (
    <div className={className}>
      {bars.map((i) => (
        <motion.span
          key={i}
          className="w-0.5 rounded-full bg-stone-400"
          style={{ height: 12 }}
          animate={{ scaleY: [1, 2, 1] }}
          transition={{
            duration: 0.7,
            repeat: Infinity,
            ease: "easeInOut",
            delay: i * 0.1,
          }}
        />
      ))}
    </div>
  );
};

// 10. Floating Bot GIF / SVG replacement
export const FloatingBot: React.FC<{ className?: string }> = ({ className = "w-10 h-10" }) => (
  <motion.div
    className={`relative flex items-center justify-center ${className}`}
    animate={{ y: [-3, 3, -3] }}
    transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
  >
    <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-full drop-shadow-md">
      {/* Bot Body */}
      <rect x="25" y="35" width="50" height="40" rx="10" fill="url(#bot-grad)" stroke="#4f46e5" strokeWidth="2" />
      {/* Bot Screen/Eye container */}
      <rect x="35" y="45" width="30" height="15" rx="5" fill="#1e1b4b" />
      {/* Animated Eyes */}
      <motion.circle cx="43" cy="52.5" r="3" fill="#60a5fa"
        animate={{ scaleY: [1, 0.1, 1], opacity: [1, 0.8, 1] }}
        transition={{ duration: 3, repeat: Infinity, times: [0, 0.1, 0.2] }}
      />
      <motion.circle cx="57" cy="52.5" r="3" fill="#60a5fa"
        animate={{ scaleY: [1, 0.1, 1], opacity: [1, 0.8, 1] }}
        transition={{ duration: 3, repeat: Infinity, times: [0, 0.1, 0.2] }}
      />
      {/* Antenna */}
      <line x1="50" y1="35" x2="50" y2="20" stroke="#4f46e5" strokeWidth="2" strokeLinecap="round" />
      <motion.circle cx="50" cy="16" r="4" fill="#fbbf24"
        animate={{ scale: [1, 1.2, 1], opacity: [0.8, 1, 0.8] }}
        transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
      />
      {/* Little floating orbs around the bot */}
      <motion.circle cx="15" cy="45" r="2" fill="#818cf8"
        animate={{ y: [-5, 5, -5] }} transition={{ duration: 2, repeat: Infinity }} />
      <motion.circle cx="85" cy="55" r="2" fill="#34d399"
        animate={{ y: [5, -5, 5] }} transition={{ duration: 2.5, repeat: Infinity }} />
      <defs>
        <linearGradient id="bot-grad" x1="25" y1="35" x2="75" y2="75" gradientUnits="userSpaceOnUse">
          <stop stopColor="#e0e7ff" />
          <stop offset="1" stopColor="#c7d2fe" />
        </linearGradient>
      </defs>
</svg>
  </motion.div>
);

// 11. Morpankh (Peacock Feather) Global Animated Background
export const MorpankhBg: React.FC<{ className?: string }> = ({ className = "" }) => {
  return (
    <div className={`absolute inset-0 pointer-events-none overflow-hidden z-0 bg-transparent ${className}`}>
      {/* Subtle abstract CSS gradients representing Morpankh colors without any heavy images */}
      <div className="absolute top-0 left-0 w-full h-full opacity-40 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-200 via-stone-50 to-transparent" />
      <div className="absolute top-0 left-0 w-full h-full opacity-30 bg-[radial-gradient(ellipse_at_bottom_left,_var(--tw-gradient-stops))] from-teal-200 via-transparent to-transparent" />
      <div className="absolute top-0 left-0 w-full h-full opacity-20 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-amber-200 via-transparent to-transparent" />
    </div>
  );
};
