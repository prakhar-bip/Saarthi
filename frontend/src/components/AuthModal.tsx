"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useWorkspace } from "@/context/WorkspaceContext";
import { X, Mail, Lock, User, KeyRound, AlertCircle } from "lucide-react";

export const AuthModal: React.FC = () => {
  const { showAuthModal, setShowAuthModal, authMode, setAuthMode, login, signup } = useWorkspace();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  if (!showAuthModal) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      if (authMode === "signup") {
        await signup(name, email, password);
      } else {
        await login(email, password);
      }
      // Reset inputs
      setName("");
      setEmail("");
      setPassword("");
    } catch (err: any) {
      setError(err.message || "Authentication failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        {/* Backdrop blur */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={() => setShowAuthModal(false)}
          className="absolute inset-0 bg-indigo-900/30 backdrop-blur-md"
        />

        {/* Modal content */}
        <motion.div
          initial={{ scale: 0.95, opacity: 0, y: 15 }}
          animate={{ scale: 1, opacity: 1, y: 0 }}
          exit={{ scale: 0.95, opacity: 0, y: 15 }}
          transition={{ type: "spring", duration: 0.5 }}
          className="relative w-full max-w-md overflow-hidden rounded-3xl border border-stone-200/60 bg-stone-50/95 p-8 shadow-2xl backdrop-blur-xl transition-colors duration-300"
        >
          {/* Close button */}
          <button
            onClick={() => setShowAuthModal(false)}
            className="absolute top-4 right-4 rounded-full p-1.5 text-stone-400 hover:bg-stone-100 hover:text-stone-700 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>

          {/* Modal Header */}
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-950 mb-3 border border-indigo-100/50">
              <KeyRound className="w-6 h-6" />
            </div>
            <h3 className="text-2xl font-bold font-display text-stone-800">
              {authMode === "login" ? "Welcome back" : "Create your account"}
            </h3>
            <p className="text-sm text-stone-500 mt-1">
              {authMode === "login"
                ? "Unlock your Sarthi design & code co-pilot"
                : "Get instant access to generated workspaces"}
            </p>
          </div>

          {/* Tab buttons */}
          <div className="flex bg-stone-100 p-1 rounded-xl mb-6 transition-colors">
            <button
              onClick={() => setAuthMode("login")}
              className={`flex-1 text-center py-2 text-xs font-semibold rounded-lg transition-all relative ${
                authMode === "login" ? "text-stone-800" : "text-stone-500 hover:text-stone-700"
              }`}
            >
              {authMode === "login" && (
                <motion.div
                  layoutId="active-tab"
                  className="absolute inset-0 bg-stone-50 rounded-lg shadow-sm border border-stone-200/40"
                  transition={{ type: "spring", stiffness: 380, damping: 30 }}
                />
              )}
              <span className="relative z-10">Login</span>
            </button>
            <button
              onClick={() => setAuthMode("signup")}
              className={`flex-1 text-center py-2 text-xs font-semibold rounded-lg transition-all relative ${
                authMode === "signup" ? "text-stone-800" : "text-stone-500 hover:text-stone-700"
              }`}
            >
              {authMode === "signup" && (
                <motion.div
                  layoutId="active-tab"
                  className="absolute inset-0 bg-stone-50 rounded-lg shadow-sm border border-stone-200/40"
                  transition={{ type: "spring", stiffness: 380, damping: 30 }}
                />
              )}
              <span className="relative z-10">Sign Up</span>
            </button>
          </div>

          {authMode === "login" && (
            <div className="p-3.5 mb-4 rounded-2xl bg-indigo-50/70 border border-indigo-100/50 text-indigo-950 text-xs space-y-2">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="font-bold">Demo Mode / Quick Access</p>
                  <p className="text-[10px] text-stone-500 mt-0.5">Use default demo credentials to log in instantly:</p>
                  <p className="font-mono text-[10px] mt-1 bg-white/60 p-1.5 rounded-lg border border-stone-200/40">
                    Email: <span className="font-semibold text-indigo-900">asur@sarthi.com</span><br />
                    Password: <span className="font-semibold text-indigo-900">Asur@123</span>
                  </p>
                </div>
              </div>
              <div className="flex items-center pt-1 border-t border-indigo-100/30">
                <button
                  type="button"
                  onClick={() => {
                    setEmail("asur@sarthi.com");
                    setPassword("Asur@123");
                  }}
                  className="px-2.5 py-1 bg-indigo-950 text-white rounded-lg font-bold text-[9px] hover:bg-indigo-900 transition-all cursor-pointer shadow-sm"
                >
                  Use Demo Credentials
                </button>
              </div>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {authMode === "signup" && (
              <div className="relative">
                <label className="text-[11px] font-semibold text-stone-500 block mb-1 uppercase tracking-wide">
                  Full Name
                </label>
                <div className="relative">
                  <User className="absolute left-3.5 top-3.5 w-4 h-4 text-stone-400" />
                  <input
                    type="text"
                    required
                    placeholder="Enter name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full bg-stone-50/50 border border-stone-200/80 rounded-xl py-3 pl-11 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500 transition-all text-stone-800 placeholder:text-stone-400"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="text-[11px] font-semibold text-stone-500 block mb-1 uppercase tracking-wide">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-3.5 w-4 h-4 text-stone-400" />
                <input
                  type="email"
                  required
                  placeholder="name@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-stone-50/50 border border-stone-200/80 rounded-xl py-3 pl-11 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500 transition-all text-stone-800 placeholder:text-stone-400"
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between items-center mb-1">
                <label className="text-[11px] font-semibold text-stone-500 block uppercase tracking-wide">
                  Password
                </label>
                {authMode === "login" && (
                  <a href="#" className="text-xs text-indigo-950 hover:text-indigo-950 hover:underline">
                    Forgot password?
                  </a>
                )}
              </div>
              <div className="relative">
                <Lock className="absolute left-3.5 top-3.5 w-4 h-4 text-stone-400" />
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-stone-50/50 border border-stone-200/80 rounded-xl py-3 pl-11 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500 transition-all text-stone-800 placeholder:text-stone-400"
                />
              </div>
            </div>

            {error && (
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-100 text-rose-600 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-indigo-950 via-indigo-900 to-amber-500 hover:from-indigo-900 hover:via-indigo-900 hover:to-amber-500 text-white rounded-xl py-3 text-sm font-semibold transition-all relative overflow-hidden flex items-center justify-center gap-2 hover:shadow-lg disabled:bg-amber-400"
            >
              {loading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  <span>Authenticating...</span>
                </>
              ) : (
                <span>{authMode === "login" ? "Sign In" : "Get Started"}</span>
              )}
            </button>
          </form>

          {/* Prompt to switch */}
          <div className="text-center mt-6 text-xs text-stone-500">
            {authMode === "login" ? (
              <span>
                Don't have an account?{" "}
                <button onClick={() => setAuthMode("signup")} className="text-indigo-950 hover:text-indigo-950 font-semibold underline">
                  Sign up
                </button>
              </span>
            ) : (
              <span>
                Already have an account?{" "}
                <button onClick={() => setAuthMode("login")} className="text-indigo-950 hover:text-indigo-950 font-semibold underline">
                  Log in
                </button>
              </span>
            )}
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
