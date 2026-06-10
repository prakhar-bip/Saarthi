"use client";

import React, { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import { useWorkspace } from "@/context/WorkspaceContext";
import { X, User, Briefcase, FileText, Code, Terminal, Users, Globe, AlertCircle, Save } from "lucide-react";

interface ProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ProfileModal: React.FC<ProfileModalProps> = ({ isOpen, onClose }) => {
  const { user, updateProfile } = useWorkspace();
  
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
    if (isOpen && user) {
      setName(user.name || "");
      setTitle(user.title || "");
      setBio(user.bio || "");
      setSkills(user.skills ? user.skills.join(", ") : "");
      setGithub(user.github_url || "");
      setLinkedin(user.linkedin_url || "");
      setPortfolio(user.portfolio_url || "");
      setError("");
      setSuccess(false);
    }
  }, [isOpen, user]);

  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
  }, []);

  if (!isOpen || !user || !mounted) return null;

  const handleSubmit = async (e: React.FormEvent) => {
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
        onClose();
      }, 1500);
    } catch (err: any) {
      setError(err.message || "Failed to update profile.");
    } finally {
      setLoading(false);
    }
  };

  const modalContent = (
    <AnimatePresence>
      <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="absolute inset-0 bg-indigo-900/40 backdrop-blur-sm"
        />

        <motion.div
          initial={{ scale: 0.95, opacity: 0, y: 15 }}
          animate={{ scale: 1, opacity: 1, y: 0 }}
          exit={{ scale: 0.95, opacity: 0, y: 15 }}
          transition={{ type: "spring", duration: 0.5 }}
          className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-3xl border border-stone-200/60 bg-stone-50/95 p-8 shadow-2xl backdrop-blur-xl"
        >
          <button
            onClick={onClose}
            className="absolute top-4 right-4 rounded-full p-1.5 text-stone-400 hover:bg-stone-100 hover:text-stone-700 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>

          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-950 mb-3 border border-indigo-100/50">
              <User className="w-6 h-6" />
            </div>
            <h3 className="text-2xl font-bold font-display text-stone-800">
              My Profile
            </h3>
            <p className="text-sm text-stone-500 mt-1">
              Customize your developer identity for hackathon submissions
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Left Column */}
              <div className="space-y-4">
                <div>
                  <label className="text-[11px] font-semibold text-stone-500 block mb-1 uppercase tracking-wide">
                    Full Name
                  </label>
                  <div className="relative">
                    <User className="absolute left-3.5 top-3.5 w-4 h-4 text-stone-400" />
                    <input
                      type="text"
                      required
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className="w-full bg-white/60 border border-stone-200/80 rounded-xl py-2.5 pl-11 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all text-stone-800"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-[11px] font-semibold text-stone-500 block mb-1 uppercase tracking-wide">
                    Professional Title
                  </label>
                  <div className="relative">
                    <Briefcase className="absolute left-3.5 top-3.5 w-4 h-4 text-stone-400" />
                    <input
                      type="text"
                      placeholder="e.g. Full Stack Developer"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      className="w-full bg-white/60 border border-stone-200/80 rounded-xl py-2.5 pl-11 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all text-stone-800"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-[11px] font-semibold text-stone-500 block mb-1 uppercase tracking-wide">
                    Bio / Description
                  </label>
                  <div className="relative">
                    <FileText className="absolute left-3.5 top-3.5 w-4 h-4 text-stone-400" />
                    <textarea
                      placeholder="Tell us about yourself..."
                      value={bio}
                      onChange={(e) => setBio(e.target.value)}
                      rows={4}
                      className="w-full bg-white/60 border border-stone-200/80 rounded-xl py-2.5 pl-11 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all text-stone-800 resize-none"
                    />
                  </div>
                </div>
              </div>

              {/* Right Column */}
              <div className="space-y-4">
                <div>
                  <label className="text-[11px] font-semibold text-stone-500 block mb-1 uppercase tracking-wide">
                    Skills (comma separated)
                  </label>
                  <div className="relative">
                    <Code className="absolute left-3.5 top-3.5 w-4 h-4 text-stone-400" />
                    <input
                      type="text"
                      placeholder="React, Python, MongoDB"
                      value={skills}
                      onChange={(e) => setSkills(e.target.value)}
                      className="w-full bg-white/60 border border-stone-200/80 rounded-xl py-2.5 pl-11 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all text-stone-800"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-[11px] font-semibold text-stone-500 block mb-1 uppercase tracking-wide">
                    GitHub URL
                  </label>
                  <div className="relative">
                    <Terminal className="absolute left-3.5 top-3.5 w-4 h-4 text-stone-400" />
                    <input
                      type="url"
                      placeholder="https://github.com/yourusername"
                      value={github}
                      onChange={(e) => setGithub(e.target.value)}
                      className="w-full bg-white/60 border border-stone-200/80 rounded-xl py-2.5 pl-11 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all text-stone-800"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-[11px] font-semibold text-stone-500 block mb-1 uppercase tracking-wide">
                    LinkedIn URL
                  </label>
                  <div className="relative">
                    <Users className="absolute left-3.5 top-3.5 w-4 h-4 text-stone-400" />
                    <input
                      type="url"
                      placeholder="https://linkedin.com/in/yourusername"
                      value={linkedin}
                      onChange={(e) => setLinkedin(e.target.value)}
                      className="w-full bg-white/60 border border-stone-200/80 rounded-xl py-2.5 pl-11 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all text-stone-800"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-[11px] font-semibold text-stone-500 block mb-1 uppercase tracking-wide">
                    Portfolio URL
                  </label>
                  <div className="relative">
                    <Globe className="absolute left-3.5 top-3.5 w-4 h-4 text-stone-400" />
                    <input
                      type="url"
                      placeholder="https://yourportfolio.com"
                      value={portfolio}
                      onChange={(e) => setPortfolio(e.target.value)}
                      className="w-full bg-white/60 border border-stone-200/80 rounded-xl py-2.5 pl-11 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all text-stone-800"
                    />
                  </div>
                </div>
              </div>
            </div>

            {error && (
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-100 text-rose-600 text-xs flex items-center gap-2 mt-4">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {success && (
              <div className="p-3 rounded-xl bg-indigo-50 border border-indigo-100 text-indigo-950 text-xs flex items-center justify-center gap-2 mt-4 font-medium">
                <Save className="w-4 h-4 shrink-0" />
                <span>Profile updated successfully!</span>
              </div>
            )}

            <div className="pt-4 flex justify-end gap-3 border-t border-stone-200/60">
              <button
                type="button"
                onClick={onClose}
                className="px-5 py-2.5 rounded-xl text-sm font-semibold text-stone-600 hover:bg-stone-100 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="bg-indigo-950 hover:bg-indigo-900 text-amber-400 rounded-xl px-8 py-2.5 text-sm font-semibold transition-all relative overflow-hidden flex items-center justify-center gap-2 hover:shadow-lg disabled:opacity-70"
              >
                {loading ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-amber-400" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    <span>Saving...</span>
                  </>
                ) : (
                  <span>Save Profile</span>
                )}
              </button>
            </div>
          </form>
        </motion.div>
      </div>
    </AnimatePresence>
  );

  return createPortal(modalContent, document.body);
};
