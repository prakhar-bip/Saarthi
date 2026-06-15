"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useWorkspace, API_BASE } from "@/context/WorkspaceContext";
import { X, Star, CheckCircle2, MessageSquare, AlertCircle, Loader2 } from "lucide-react";

export const FeedbackModal: React.FC = () => {
  const { showFeedbackModal, setShowFeedbackModal, user } = useWorkspace();
  const [category, setCategory] = useState<"bug" | "feature" | "uiux" | "other">("uiux");
  const [rating, setRating] = useState<number>(5);
  const [hoverRating, setHoverRating] = useState<number | null>(null);
  const [message, setMessage] = useState("");
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  if (!showFeedbackModal) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;
    setLoading(true);
    setError("");

    try {
      const finalEmail = email.trim() || (user ? user.email : "");
      const res = await fetch(`${API_BASE}/api/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          category,
          rating,
          message: message.trim(),
          email: finalEmail || null
        })
      });

      if (res.ok) {
        setSuccess(true);
        setTimeout(() => {
          setSuccess(false);
          setShowFeedbackModal(false);
          // Reset form
          setCategory("uiux");
          setRating(5);
          setMessage("");
          setEmail("");
        }, 2500);
      } else {
        const errData = await res.json();
        throw new Error(errData.detail || "Submission failed");
      }
    } catch (err: any) {
      setError(err.message || "Failed to submit feedback. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-[120] flex items-center justify-center p-4">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={() => !loading && setShowFeedbackModal(false)}
          className="absolute inset-0 bg-indigo-950/40 backdrop-blur-md"
        />

        {/* Modal container */}
        <motion.div
          initial={{ scale: 0.95, opacity: 0, y: 15 }}
          animate={{ scale: 1, opacity: 1, y: 0 }}
          exit={{ scale: 0.95, opacity: 0, y: 15 }}
          transition={{ type: "spring", duration: 0.45 }}
          className="relative w-full max-w-md overflow-hidden rounded-3xl border border-stone-200/60 bg-stone-50/95 p-8 shadow-2xl backdrop-blur-xl transition-all"
        >
          {/* Close button */}
          {!loading && (
            <button
              onClick={() => setShowFeedbackModal(false)}
              className="absolute top-4 right-4 rounded-full p-1.5 text-stone-400 hover:bg-stone-100 hover:text-stone-700 transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          )}

          {success ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="text-center py-8 space-y-4 flex flex-col items-center justify-center"
            >
              <motion.div
                animate={{ scale: [1, 1.2, 1], rotate: [0, 10, -10, 0] }}
                transition={{ duration: 0.6, ease: "easeOut" }}
                className="w-16 h-16 rounded-full bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-500 shadow-sm"
              >
                <CheckCircle2 className="w-9 h-9" />
              </motion.div>
              <div className="space-y-1">
                <h3 className="text-lg font-bold text-stone-850">Thank you!</h3>
                <p className="text-xs text-stone-500 font-semibold max-w-[280px]">
                  Your feedback helps us guide Sarthi's chariot in the right direction. We appreciate it! 🙏
                </p>
              </div>
            </motion.div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Header */}
              <div className="text-center mb-1">
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-950 mb-3 border border-indigo-100/50">
                  <MessageSquare className="w-6 h-6 text-indigo-950" />
                </div>
                <h3 className="text-xl font-bold font-display text-stone-800">
                  Share Your Feedback
                </h3>
                <p className="text-xs text-stone-500 mt-1 font-semibold leading-relaxed">
                  Encountered a bug or want to suggest a feature? Tell Sarthi.
                </p>
              </div>

              {/* Category Picker */}
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold text-stone-500 uppercase tracking-wide block">
                  Category
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { id: "uiux", label: "🎨 UI / UX" },
                    { id: "bug", label: "🐛 Bug Report" },
                    { id: "feature", label: "✨ Feature Request" },
                    { id: "other", label: "📝 Other" },
                  ].map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => setCategory(item.id as any)}
                      className={`py-2 px-3 rounded-xl border text-xs font-bold text-center transition-all cursor-pointer ${
                        category === item.id
                          ? "bg-indigo-950 border-indigo-950 text-amber-500 shadow-sm"
                          : "bg-white border-stone-200 text-stone-600 hover:border-indigo-100 hover:bg-stone-50/50"
                      }`}
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Rating Selector */}
              <div className="space-y-1.5 text-center">
                <label className="text-[10px] font-bold text-stone-500 uppercase tracking-wide block text-left">
                  Rating
                </label>
                <div className="flex items-center justify-center gap-2 py-1 bg-white border border-stone-200 rounded-2xl">
                  {[1, 2, 3, 4, 5].map((star) => {
                    const isActive = star <= (hoverRating !== null ? hoverRating : rating);
                    return (
                      <button
                        key={star}
                        type="button"
                        onMouseEnter={() => setHoverRating(star)}
                        onMouseLeave={() => setHoverRating(null)}
                        onClick={() => setRating(star)}
                        className="p-1 hover:scale-110 transition-transform cursor-pointer"
                      >
                        <Star
                          className={`w-6 h-6 transition-colors ${
                            isActive
                              ? "fill-amber-500 text-amber-500"
                              : "text-stone-300"
                          }`}
                        />
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Email (Optional, if guest) */}
              {!user && (
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-stone-500 uppercase tracking-wide block">
                    Your Email (Optional)
                  </label>
                  <input
                    type="email"
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full bg-white border border-stone-200 rounded-xl px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/10 focus:border-indigo-500 transition-all text-stone-850"
                  />
                </div>
              )}

              {/* Message */}
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-stone-500 uppercase tracking-wide block">
                  Comments / Description
                </label>
                <textarea
                  required
                  placeholder="What was your experience? Be as detailed as you like..."
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  rows={4}
                  className="w-full bg-white border border-stone-200 rounded-xl px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/10 focus:border-indigo-500 transition-all text-stone-850 resize-none font-medium leading-relaxed"
                />
              </div>

              {error && (
                <div className="p-3 rounded-xl bg-rose-50 border border-rose-100 text-rose-600 text-xs flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <div className="flex justify-end gap-2 border-t border-stone-200/60 pt-3">
                <button
                  type="submit"
                  disabled={loading || !message.trim()}
                  className="w-full bg-indigo-950 hover:bg-indigo-900 border border-indigo-900/50 text-amber-500 rounded-xl py-3 text-xs font-bold transition-all flex items-center justify-center gap-1.5 hover:shadow-md disabled:opacity-50 cursor-pointer"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Submitting...</span>
                    </>
                  ) : (
                    <span>Submit Feedback</span>
                  )}
                </button>
              </div>
            </form>
          )}
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
