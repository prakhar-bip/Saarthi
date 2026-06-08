"use client";

import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AnimatedChariot } from "./CustomSvgs";

interface ChariotSplashProps {
  onComplete: () => void;
}

export const ChariotSplash: React.FC<ChariotSplashProps> = ({ onComplete }) => {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState("Preparing workspace...");

  useEffect(() => {
    // Increment progress mockingly
    const duration = 2500; // 2.5 seconds total
    const intervalTime = 25; // Update every 25ms
    const step = 100 / (duration / intervalTime);

    const timer = setInterval(() => {
      setProgress((prev) => {
        const next = prev + step;
        if (next >= 100) {
          clearInterval(timer);
          // Small delay before finishing to let the user see 100%
          setTimeout(() => {
            onComplete();
          }, 200);
          return 100;
        }
        return next;
      });
    }, intervalTime);

    // Update status text dynamically
    const statusTimeouts = [
      setTimeout(() => setStatus("Igniting Sarthi AI engine..."), 600),
      setTimeout(() => setStatus("Configuring domain environments..."), 1200),
      setTimeout(() => setStatus("Readying co-pilot console..."), 1900),
    ];

    return () => {
      clearInterval(timer);
      statusTimeouts.forEach(clearTimeout);
    };
  }, [onComplete]);

  return (
    <motion.div
      initial={{ opacity: 1 }}
      exit={{ opacity: 0, transition: { duration: 0.6, ease: "easeInOut" } }}
      className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-stone-50 select-none overflow-hidden"
    >
      {/* Decorative Glow Blobs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full bg-indigo-500/10 blur-3xl animate-bg-glow" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 rounded-full bg-rose-500/10 blur-3xl animate-bg-glow" style={{ animationDelay: "4s" }} />

      <div className="max-w-md w-full px-8 text-center flex flex-col items-center relative z-10">
        {/* Sarthi Animated Logo */}
        <motion.div
          animate={{
            scale: [1, 1.05, 1],
            boxShadow: [
              "0 10px 25px -5px rgba(99, 102, 241, 0.25), 0 8px 10px -6px rgba(244, 63, 94, 0.15)",
              "0 20px 35px -5px rgba(99, 102, 241, 0.4), 0 12px 15px -6px rgba(244, 63, 94, 0.25)",
              "0 10px 25px -5px rgba(99, 102, 241, 0.25), 0 8px 10px -6px rgba(244, 63, 94, 0.15)"
            ]
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: "easeInOut"
          }}
          className="mb-8 w-28 h-28 rounded-2xl overflow-hidden border border-stone-200/50 bg-white relative flex items-center justify-center shadow-lg"
        >
          <motion.div
            className="absolute inset-0 bg-gradient-to-tr from-indigo-500/20 via-transparent to-rose-500/20 mix-blend-overlay"
            animate={{ rotate: 360 }}
            transition={{ duration: 6, repeat: Infinity, ease: "linear" }}
          />
          <img
            src="/logo.png"
            alt="Sarthi Logo"
            className="w-20 h-20 object-contain pointer-events-none"
          />
        </motion.div>

        {/* Title */}
        <motion.h1
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2, duration: 0.6 }}
          className="text-4xl font-extrabold font-display tracking-widest text-stone-800"
        >
          SARTHI
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.6 }}
          className="text-xs font-semibold uppercase tracking-widest text-indigo-600 mt-1"
        >
          Your Intelligent Guide
        </motion.p>

        {/* Progress Bar Container */}
        <motion.div
          initial={{ width: 0, opacity: 0 }}
          animate={{ width: "100%", opacity: 1 }}
          transition={{ delay: 0.4, duration: 0.6 }}
          className="w-full mt-10 space-y-3"
        >
          {/* Progress Bar Track */}
          <div className="h-1.5 w-full bg-stone-200 rounded-full overflow-hidden relative">
            <motion.div
              className="absolute left-0 top-0 bottom-0 bg-gradient-to-r from-indigo-500 via-purple-500 to-rose-500 rounded-full"
              style={{ width: `${progress}%` }}
              transition={{ ease: "easeOut" }}
            />
          </div>

          {/* Progress Percent and Status */}
          <div className="flex justify-between items-center text-[11px] font-semibold text-stone-500">
            <span className="font-mono">{status}</span>
            <span className="font-mono text-stone-700">
              {Math.round(progress)}%
            </span>
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
};
