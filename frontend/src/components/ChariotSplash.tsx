"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { SarthiLogo } from "./CustomSvgs";

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
      <div className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full bg-amber-500/10 blur-3xl animate-bg-glow" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 rounded-full bg-rose-500/10 blur-3xl animate-bg-glow" style={{ animationDelay: "4s" }} />

      <div className="max-w-md w-full px-8 text-center flex flex-col items-center relative z-10">
        {/* Sarthi Peacock Script Logo */}
        <motion.div
          initial={{ y: 20, opacity: 0, scale: 0.9 }}
          animate={{ y: 0, opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="mb-4"
        >
          <SarthiLogo className="text-7xl md:text-8xl" />
        </motion.div>

        {/* Subtitle */}
        <motion.p
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.6 }}
          className="text-xs font-semibold uppercase tracking-widest text-indigo-950 mt-1"
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
              className="absolute left-0 top-0 bottom-0 bg-gradient-to-r from-amber-500 via-indigo-500 to-purple-600 rounded-full"
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
