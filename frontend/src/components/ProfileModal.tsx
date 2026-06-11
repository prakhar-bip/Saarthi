"use client";

import React, { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import { useWorkspace } from "@/context/WorkspaceContext";
import { 
  X, User, Briefcase, FileText, Code, Terminal, Users, Globe, 
  AlertCircle, Save, HelpCircle, Sparkles, Check, Info
} from "lucide-react";

interface ProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialTab?: "profile" | "help";
}

export const ProfileModal: React.FC<ProfileModalProps> = ({ isOpen, onClose, initialTab = "profile" }) => {
  const { user, updateProfile } = useWorkspace();
  
  const [activeTab, setActiveTab] = useState<"profile" | "help">("profile");

  // Profile Form states
  const [name, setName] = useState("");
  const [title, setTitle] = useState("");
  const [bio, setBio] = useState("");
  const [skills, setSkills] = useState("");
  const [github, setGithub] = useState("");
  const [linkedin, setLinkedin] = useState("");
  const [portfolio, setPortfolio] = useState("");
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setActiveTab(initialTab);
      setSuccess(false);
      setError("");
      
      if (user) {
        setName(user.name || "");
        setTitle(user.title || "");
        setBio(user.bio || "");
        setSkills(user.skills ? user.skills.join(", ") : "");
        setGithub(user.github_url || "");
        setLinkedin(user.linkedin_url || "");
        setPortfolio(user.portfolio_url || "");
      }
    }
  }, [isOpen, user, initialTab]);

  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
  }, []);

  if (!isOpen || !user || !mounted) return null;

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setSuccess(false);
    
    try {
      const skillsArray = skills.split(",").map((s) => s.trim()).filter((s) => s.length > 0);
      await updateProfile({
        name,
        title,
        bio,
        skills: skillsArray,
        github_url: github,
        linkedin_url: linkedin,
        portfolio_url: portfolio
      });
      setSuccess(true);
      setTimeout(() => {
        setSuccess(false);
      }, 2000);
    } catch (err: any) {
      setError(err.message || "Failed to update profile.");
    } finally {
      setLoading(false);
    }
  };

  const modalContent = (
    <AnimatePresence>
      <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="absolute inset-0 bg-indigo-900/40 backdrop-blur-sm"
        />

        {/* Modal Container */}
        <motion.div
          initial={{ scale: 0.95, opacity: 0, y: 15 }}
          animate={{ scale: 1, opacity: 1, y: 0 }}
          exit={{ scale: 0.95, opacity: 0, y: 15 }}
          transition={{ type: "spring", duration: 0.5 }}
          className="relative w-full max-w-3xl max-h-[90vh] overflow-hidden rounded-3xl border border-stone-200/60 bg-stone-50/95 shadow-2xl backdrop-blur-xl flex flex-col"
        >
          {/* Close button */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 rounded-full p-1.5 text-stone-400 hover:bg-stone-100 hover:text-stone-700 transition-colors z-50 cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>

          {/* Modal Header */}
          <div className="p-6 border-b border-stone-200/60 flex items-center gap-3 shrink-0">
            <div className="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-indigo-50 text-indigo-950 border border-indigo-100/50">
              {activeTab === "profile" && <User className="w-5 h-5" />}
              {activeTab === "help" && <HelpCircle className="w-5 h-5" />}
            </div>
            <div>
              <h3 className="text-lg font-bold font-display text-stone-800">
                {activeTab === "profile" && "Developer Profile"}
                {activeTab === "help" && "Help & Support Guide"}
              </h3>
              <p className="text-xs text-stone-400 mt-0.5">
                {activeTab === "profile" && "Customize your developer credentials and contact links"}
                {activeTab === "help" && "Learn the concept of Sarthi and access workspace shortcuts"}
              </p>
            </div>
          </div>

          {/* Main Body with Sidebar Tab Menu */}
          <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
            {/* Left Sidebar Menu */}
            <div className="w-full md:w-52 border-r border-stone-200/60 bg-stone-100/40 p-4 flex flex-row md:flex-col gap-1 overflow-x-auto md:overflow-x-visible shrink-0 select-none">
              <button
                type="button"
                onClick={() => setActiveTab("profile")}
                className={`flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-xs font-bold transition-all text-left cursor-pointer w-full whitespace-nowrap ${
                  activeTab === "profile"
                    ? "bg-indigo-950 text-amber-500 shadow-sm border border-indigo-900/50"
                    : "text-stone-600 hover:bg-stone-100 border border-transparent"
                }`}
              >
                <User className="w-4 h-4 shrink-0" />
                Profile Info
              </button>

              <button
                type="button"
                onClick={() => setActiveTab("help")}
                className={`flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-xs font-bold transition-all text-left cursor-pointer w-full whitespace-nowrap ${
                  activeTab === "help"
                    ? "bg-indigo-950 text-amber-500 shadow-sm border border-indigo-900/50"
                    : "text-stone-600 hover:bg-stone-100 border border-transparent"
                }`}
              >
                <HelpCircle className="w-4 h-4 shrink-0" />
                Help & Guide
              </button>
            </div>

            {/* Right Tab Content Container */}
            <div className="flex-1 overflow-y-auto p-6 md:p-8">
              
              {/* TAB 1: PROFILE INFO FORM */}
              {activeTab === "profile" && (
                <form onSubmit={handleProfileSubmit} className="space-y-5">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-4">
                      <div>
                        <label className="text-[10px] font-bold text-stone-500 block mb-1 uppercase tracking-wide">
                          Full Name
                        </label>
                        <div className="relative">
                          <User className="absolute left-3 top-3 w-4 h-4 text-stone-400" />
                          <input
                            type="text"
                            required
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            className="w-full bg-white/60 border border-stone-200 rounded-xl py-2 pl-10 pr-4 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/10 focus:border-indigo-500 transition-all text-stone-850"
                          />
                        </div>
                      </div>

                      <div>
                        <label className="text-[10px] font-bold text-stone-500 block mb-1 uppercase tracking-wide">
                          Professional Title
                        </label>
                        <div className="relative">
                          <Briefcase className="absolute left-3 top-3 w-4 h-4 text-stone-400" />
                          <input
                            type="text"
                            placeholder="e.g. Full Stack Developer"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            className="w-full bg-white/60 border border-stone-200 rounded-xl py-2 pl-10 pr-4 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/10 focus:border-indigo-500 transition-all text-stone-850"
                          />
                        </div>
                      </div>

                      <div>
                        <label className="text-[10px] font-bold text-stone-500 block mb-1 uppercase tracking-wide">
                          Bio / Dev Motto
                        </label>
                        <div className="relative">
                          <FileText className="absolute left-3 top-3.5 w-4 h-4 text-stone-400" />
                          <textarea
                            placeholder="Tell Sarthi about your developer experience..."
                            value={bio}
                            onChange={(e) => setBio(e.target.value)}
                            rows={3}
                            className="w-full bg-white/60 border border-stone-200 rounded-xl py-2 pl-10 pr-4 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/10 focus:border-indigo-500 transition-all text-stone-850 resize-none leading-relaxed"
                          />
                        </div>
                      </div>
                    </div>

                    <div className="space-y-4">
                      <div>
                        <label className="text-[10px] font-bold text-stone-500 block mb-1 uppercase tracking-wide">
                          Skills (comma separated)
                        </label>
                        <div className="relative">
                          <Code className="absolute left-3 top-3 w-4 h-4 text-stone-400" />
                          <input
                            type="text"
                            placeholder="React, Python, MongoDB"
                            value={skills}
                            onChange={(e) => setSkills(e.target.value)}
                            className="w-full bg-white/60 border border-stone-200 rounded-xl py-2 pl-10 pr-4 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/10 focus:border-indigo-500 transition-all text-stone-850"
                          />
                        </div>
                      </div>

                      <div>
                        <label className="text-[10px] font-bold text-stone-500 block mb-1 uppercase tracking-wide">
                          GitHub Username or URL
                        </label>
                        <div className="relative">
                          <Terminal className="absolute left-3 top-3 w-4 h-4 text-stone-400" />
                          <input
                            type="text"
                            placeholder="https://github.com/username"
                            value={github}
                            onChange={(e) => setGithub(e.target.value)}
                            className="w-full bg-white/60 border border-stone-200 rounded-xl py-2 pl-10 pr-4 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/10 focus:border-indigo-500 transition-all text-stone-850"
                          />
                        </div>
                      </div>

                      <div>
                        <label className="text-[10px] font-bold text-stone-500 block mb-1 uppercase tracking-wide">
                          LinkedIn URL
                        </label>
                        <div className="relative">
                          <Users className="absolute left-3 top-3 w-4 h-4 text-stone-400" />
                          <input
                            type="url"
                            placeholder="https://linkedin.com/in/username"
                            value={linkedin}
                            onChange={(e) => setLinkedin(e.target.value)}
                            className="w-full bg-white/60 border border-stone-200 rounded-xl py-2 pl-10 pr-4 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/10 focus:border-indigo-500 transition-all text-stone-850"
                          />
                        </div>
                      </div>
                    </div>
                  </div>

                  {error && (
                    <div className="p-3 rounded-xl bg-rose-50 border border-rose-100 text-rose-600 text-xs flex items-center gap-2">
                      <AlertCircle className="w-4 h-4 shrink-0" />
                      <span>{error}</span>
                    </div>
                  )}

                  {success && (
                    <div className="p-3 rounded-xl bg-indigo-50 border border-indigo-100 text-indigo-950 text-xs flex items-center justify-center gap-2 font-bold">
                      <Check className="w-4 h-4 text-amber-500" />
                      <span>Profile info synchronized successfully!</span>
                    </div>
                  )}

                  <div className="pt-3 flex justify-end gap-2 border-t border-stone-200/60">
                    <button
                      type="submit"
                      disabled={loading}
                      className="bg-indigo-950 hover:bg-indigo-900 text-amber-500 border border-indigo-900/50 rounded-xl px-6 py-2 text-xs font-bold transition-all flex items-center justify-center gap-1.5 hover:shadow-md disabled:opacity-70 cursor-pointer"
                    >
                      <Save className="w-3.5 h-3.5" />
                      {loading ? "Syncing..." : "Sync Credentials"}
                    </button>
                  </div>
                </form>
              )}

              {/* TAB 2: HELP & SUPPORT GUIDE */}
              {activeTab === "help" && (
                <div className="space-y-6 text-stone-700 leading-relaxed text-xs">
                  
                  {/* Concept Section */}
                  <div className="p-4 rounded-2xl bg-indigo-50/40 border border-indigo-100/50 space-y-2">
                    <h4 className="font-bold text-indigo-950 flex items-center gap-1.5">
                      <Sparkles className="w-4 h-4 text-amber-500" />
                      The Chariot Concept (Sarthi Analogy)
                    </h4>
                    <p className="text-[11px] text-stone-600 leading-relaxed">
                      Sarthi (सारथि) represents the charioteer. Just as Sri Krishna guided Arjuna on the battlefield of Kurukshetra, Sarthi guides you through the complex arena of software assembly. Sarthi manages the tedious, heavy setup of folders, databases, and configuration layout, allowing you to focus purely on wielding the bow of your developer logic.
                    </p>
                  </div>

                  {/* Quick Guide */}
                  <div className="space-y-2.5">
                    <h4 className="font-bold text-stone-800 uppercase tracking-wide text-[10px]">Quick Start Workflow</h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                      <div className="p-3 bg-white/40 border border-stone-200 rounded-xl space-y-1">
                        <span className="text-[10px] font-extrabold text-indigo-700 block">1. Converse & Brainstorm</span>
                        <span className="text-[10px] text-stone-500 block leading-normal">Pitch your product idea. Sarthi will clarify scope and categorize details.</span>
                      </div>
                      <div className="p-3 bg-white/40 border border-stone-200 rounded-xl space-y-1">
                        <span className="text-[10px] font-extrabold text-amber-600 block">2. Review Blueprints</span>
                        <span className="text-[10px] text-stone-500 block leading-normal">Wait for Sarthi to generate specs (PRD, MRD, TRD) and sync the sandbox.</span>
                      </div>
                      <div className="p-3 bg-white/40 border border-stone-200 rounded-xl space-y-1">
                        <span className="text-[10px] font-extrabold text-indigo-950 block">3. Wield the Code</span>
                        <span className="text-[10px] text-stone-500 block leading-normal">Click 'Proceed to Build' to compile the codebase, explore components, and review structures.</span>
                      </div>
                    </div>
                  </div>

                  {/* Shortcuts & Support */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                    {/* Shortcuts */}
                    <div className="space-y-2">
                      <h4 className="font-bold text-stone-800 uppercase tracking-wide text-[10px]">Workspace Shortcuts</h4>
                      <table className="w-full text-left border-collapse">
                        <tbody>
                          <tr className="border-b border-stone-200/40">
                            <td className="py-1.5 text-stone-500 font-medium text-[10px]">Send Input</td>
                            <td className="py-1.5 text-right font-mono text-[10px] text-stone-800"><kbd className="bg-stone-200 px-1 py-0.5 rounded border">Enter</kbd></td>
                          </tr>
                          <tr className="border-b border-stone-200/40">
                            <td className="py-1.5 text-stone-500 font-medium text-[10px]">New Line in Chat</td>
                            <td className="py-1.5 text-right font-mono text-[10px] text-stone-800"><kbd className="bg-stone-200 px-1 py-0.5 rounded border">Shift+Enter</kbd></td>
                          </tr>
                          <tr>
                            <td className="py-1.5 text-stone-500 font-medium text-[10px]">Close Modals</td>
                            <td className="py-1.5 text-right font-mono text-[10px] text-stone-800"><kbd className="bg-stone-200 px-1 py-0.5 rounded border">Esc</kbd></td>
                          </tr>
                        </tbody>
                      </table>
                    </div>

                    {/* Support contact info */}
                    <div className="space-y-2">
                      <h4 className="font-bold text-stone-800 uppercase tracking-wide text-[10px]">Support & Outreach</h4>
                      <div className="p-3 bg-white/40 border border-stone-200 rounded-xl flex items-start gap-2.5">
                        <Info className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
                        <div>
                          <p className="text-[11px] text-stone-600 leading-normal">
                            Need help deploying your custom Flask sandbox or configuring database credentials?
                          </p>
                          <a href="mailto:sarthi.ai.charioteer@gmail.com" className="text-[10px] text-indigo-950 font-bold hover:underline mt-1 block">
                            sarthi.ai.charioteer@gmail.com
                          </a>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );

  return createPortal(modalContent, document.body);
};
