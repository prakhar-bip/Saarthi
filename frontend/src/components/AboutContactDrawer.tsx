"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useWorkspace } from "@/context/WorkspaceContext";
import { X, Send, Info, ShieldCheck, Mail } from "lucide-react";

export const AboutContactDrawer: React.FC = () => {
  const {
    showAbout,
    setShowAbout,
    showContact,
    setShowContact
  } = useWorkspace();

  const [contactName, setContactName] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [contactMessage, setContactMessage] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const handleContactSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setTimeout(() => {
      setSubmitting(false);
      setSubmitted(true);
      setTimeout(() => {
        setSubmitted(false);
        setShowContact(false);
        // Clear
        setContactName("");
        setContactEmail("");
        setContactMessage("");
      }, 2000);
    }, 1200);
  };

  return (
    <>
      <AnimatePresence>
        {/* ABOUT DRAWER */}
        {showAbout && (
          <div className="fixed inset-0 z-50 flex justify-end">
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowAbout(false)}
              className="absolute inset-0 bg-stone-900/20 backdrop-blur-sm"
            />
            {/* Sliding Panel */}
            <motion.div
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              className="relative w-full max-w-md bg-stone-50 border-l border-stone-200 shadow-2xl flex flex-col h-full transition-colors duration-300"
            >
              {/* Header */}
              <div className="p-6 border-b border-stone-100 flex justify-between items-center bg-stone-50/50">
                <div className="flex items-center gap-2 text-indigo-950">
                  <Info className="w-5 h-5" />
                  <h3 className="text-lg font-bold font-display text-stone-800">About Sarthi</h3>
                </div>
                <button
                  onClick={() => setShowAbout(false)}
                  className="p-1 rounded-full text-stone-400 hover:bg-stone-100 hover:text-stone-700 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Scrollable Content */}
              <div className="flex-1 overflow-y-auto p-8 space-y-6">
                <div className="text-center pb-6 border-b border-stone-100">
                  <div className="w-16 h-16 mx-auto mb-4 rounded-3xl bg-indigo-950 border border-indigo-900/50 flex items-center justify-center text-2xl font-bold font-display text-amber-500 shadow-sm">
                    S
                  </div>
                  <h4 className="text-md font-bold text-stone-800">Your Co-Pilot for Innovation</h4>
                  <p className="text-xs text-stone-400 mt-1">Sarthi (Sanskrit: सारथि) — The Charioteer</p>
                </div>

                <div className="space-y-4">
                  <h5 className="text-xs font-bold uppercase tracking-wider text-stone-400">The Problem</h5>
                  <p className="text-xs text-stone-600 leading-relaxed">
                    During hackathons, developers waste hours bootstrapping architectures, selecting color systems, and organizing layouts. Ideas get stalled in configuration.
                  </p>
                </div>

                <div className="space-y-4">
                  <h5 className="text-xs font-bold uppercase tracking-wider text-stone-400">The Solution</h5>
                  <p className="text-xs text-stone-600 leading-relaxed">
                    Sarthi acts as your workspace guide. Selecting specialized domains (Health, Finance, Productivity, Education, Sustainability), Sarthi discusses code logic, compiles file-tree directories, structures requirements, and generates complete frontend source code blocks instantly.
                  </p>
                </div>

                <div className="space-y-3">
                  <h5 className="text-xs font-bold uppercase tracking-wider text-stone-400">Tech Architecture</h5>
                  <div className="grid grid-cols-2 gap-2.5">
                    <div className="p-3 bg-stone-50 rounded-xl border border-stone-200/40 text-center">
                      <span className="text-xs font-bold text-indigo-600 block">Next.js & React</span>
                      <span className="text-[9px] text-stone-400 mt-0.5 block">App Router</span>
                    </div>
                    <div className="p-3 bg-stone-50 rounded-xl border border-stone-200/40 text-center">
                      <span className="text-xs font-bold text-amber-500 block">Tailwind CSS</span>
                      <span className="text-[9px] text-stone-400 mt-0.5 block">Utility Variables</span>
                    </div>
                    <div className="p-3 bg-stone-50 rounded-xl border border-stone-200/40 text-center">
                      <span className="text-xs font-bold text-indigo-950 block">Framer Motion</span>
                      <span className="text-[9px] text-stone-400 mt-0.5 block">Smooth Micro-UX</span>
                    </div>
                    <div className="p-3 bg-stone-50 rounded-xl border border-stone-200/40 text-center">
                      <span className="text-xs font-bold text-amber-600 block">Vector SVGs</span>
                      <span className="text-[9px] text-stone-400 mt-0.5 block">Animated Emblems</span>
                    </div>
                  </div>
                </div>

                <div className="pt-6 border-t border-stone-100 flex items-center justify-center gap-2 text-stone-400 text-xs font-medium">
                  <ShieldCheck className="w-4 h-4 text-amber-500" />
                  <span>Sarthi Hackathon Prototype, May 2026</span>
                </div>
              </div>
            </motion.div>
          </div>
        )}

        {/* CONTACT DRAWER */}
        {showContact && (
          <div className="fixed inset-0 z-50 flex justify-end">
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowContact(false)}
              className="absolute inset-0 bg-stone-900/20 backdrop-blur-sm"
            />
            {/* Sliding Panel */}
            <motion.div
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              className="relative w-full max-w-md bg-stone-50 border-l border-stone-200 shadow-2xl flex flex-col h-full transition-colors duration-300"
            >
              {/* Header */}
              <div className="p-6 border-b border-stone-100 flex justify-between items-center bg-stone-50/50">
                <div className="flex items-center gap-2 text-amber-500">
                  <Mail className="w-5 h-5 text-indigo-950" />
                  <h3 className="text-lg font-bold font-display text-stone-800">Get in Touch</h3>
                </div>
                <button
                  onClick={() => setShowContact(false)}
                  className="p-1 rounded-full text-stone-400 hover:bg-stone-100 hover:text-stone-700 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Scrollable Content */}
              <div className="flex-1 overflow-y-auto p-8">
                <AnimatePresence mode="wait">
                  {submitted ? (
                    <motion.div
                      initial={{ scale: 0.9, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      exit={{ scale: 0.9, opacity: 0 }}
                      className="h-full flex flex-col items-center justify-center text-center space-y-3"
                    >
                      <div className="w-12 h-12 bg-indigo-50 text-indigo-950 rounded-full border border-indigo-100 flex items-center justify-center">
                        <Send className="w-5 h-5" />
                      </div>
                      <h4 className="text-md font-bold text-stone-800">Message Transmitted</h4>
                      <p className="text-xs text-stone-400 max-w-[240px] leading-relaxed">
                        Thank you for reaching out! Sarthi co-pilot team will review your pitch shortly.
                      </p>
                    </motion.div>
                  ) : (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="space-y-6"
                    >
                      <p className="text-xs text-stone-500 leading-relaxed">
                        Have ideas to expand Sarthi's generation templates? Or want to collaborate on the hackathon project? Send us your message!
                      </p>

                      <form onSubmit={handleContactSubmit} className="space-y-4">
                        <div>
                          <label className="text-[10px] font-bold text-stone-500 uppercase tracking-wide block mb-1">
                            Your Name
                          </label>
                          <input
                            type="text"
                            required
                            placeholder="Alex Developer"
                            value={contactName}
                            onChange={(e) => setContactName(e.target.value)}
                            className="w-full bg-stone-50/50 border border-stone-200 rounded-xl py-3 px-4 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/10 focus:border-indigo-500 transition-all text-stone-800"
                          />
                        </div>

                        <div>
                          <label className="text-[10px] font-bold text-stone-500 uppercase tracking-wide block mb-1">
                            Email Address
                          </label>
                          <input
                            type="email"
                            required
                            placeholder="alex@workspace.com"
                            value={contactEmail}
                            onChange={(e) => setContactEmail(e.target.value)}
                            className="w-full bg-stone-50/50 border border-stone-200 rounded-xl py-3 px-4 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/10 focus:border-indigo-500 transition-all text-stone-800"
                          />
                        </div>

                        <div>
                          <label className="text-[10px] font-bold text-stone-500 uppercase tracking-wide block mb-1">
                            Message
                          </label>
                          <textarea
                            required
                            rows={5}
                            placeholder="Explain your request or layout suggestions..."
                            value={contactMessage}
                            onChange={(e) => setContactMessage(e.target.value)}
                            className="w-full bg-stone-50/50 border border-stone-200 rounded-xl py-3 px-4 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/10 focus:border-indigo-500 transition-all text-stone-800 resize-none"
                          />
                        </div>

                        <button
                          type="submit"
                          disabled={submitting}
                          className="w-full bg-indigo-950 hover:bg-indigo-900 text-amber-500 rounded-xl py-3 text-sm font-bold transition-all relative overflow-hidden flex items-center justify-center gap-2 hover:shadow-lg disabled:opacity-50"
                        >
                          {submitting ? (
                            <span>Sending Message...</span>
                          ) : (
                            <>
                              <Send className="w-4 h-4" />
                              <span>Dispatch Request</span>
                            </>
                          )}
                        </button>
                      </form>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
};
