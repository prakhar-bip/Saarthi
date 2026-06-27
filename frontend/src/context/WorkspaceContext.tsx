"use client";

import React, { createContext, useContext, useState, useEffect, useRef, useMemo, useCallback } from "react";
import confetti from "canvas-confetti";

export interface Message {
  id: string;
  sender: "user" | "ai";
  text: string;
  timestamp: string;
}

export interface ProjectSuggestion {
  name: string;
  idea: string;
  features: string[];
  tech_stack: string;
  category?: string;
  hitl_enabled?: boolean;
  generation_type?: string;
}

export interface ChatSession {
  id: string;
  title: string;
  category: string;
  messages: Message[];
  created: string;
  selected_project: ProjectSuggestion | null;
  is_confirmed: boolean;
  project_id: string | null;
  is_paused?: boolean;
}

export interface CodeFile {
  name: string;
  path: string;
  content: string;
  language: string;
}

export interface Project {
  id: string;
  name: string;
  category: string;
  status: "idle" | "generating" | "completed" | "failed" | "documents_ready" | "waiting_approval" | "paused";
  progress: number;
  step: string;
  generation_type?: string;
  summary: string;
  codebase: CodeFile[];
  created: string;
  chat_id: string;
  requirements?: any;
  planning?: any;
  db_architecture?: any;
  backend_architecture?: any;
  api_architecture?: any;
  frontend_architecture?: any;
  theme_styling?: any;
  auth_architecture?: any;
  realtime_architecture?: any;
  state_management?: any;
  devops_architecture?: any;
  security_architecture?: any;
  testing_architecture?: any;
  validation_architecture?: any;
  optimization_architecture?: any;
  code_generation_plan?: any;
  database_model_generation?: any;
  backend_code_generation?: any;
  api_implementation?: any;
  frontend_code_generation?: any;
  ui_component_generation?: any;
  state_implementation?: any;
  integration_generation?: any;
  build_compilation?: any;
  error_correction?: any;
  project_export?: any;
  agent_context?: any;
  hackathon_metadata?: any;
  mcp_evidence?: any;
  prd?: string;
  mrd?: string;
  trd?: string;
  hitl_enabled?: boolean;
  hitl_approved?: boolean;
  implementation_plan?: any;
  validation_logs?: any[];
  blueprint?: any;
  api_contract_design?: any;
  database_architecture?: any;
  blueprint_planner?: any;
  requirement_analyzer?: any;
  theme?: string;
  theme_palette?: any;
}

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

interface WorkspaceContextType {
  user: {
    id: string;
    name: string;
    email: string;
    bio?: string;
    title?: string;
    skills?: string[];
    github_url?: string;
    linkedin_url?: string;
    portfolio_url?: string;
  } | null;
  login: (email: string, password: string) => Promise<void>;
  signup: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  updateProfile: (data: any) => Promise<void>;
  
  chats: ChatSession[];
  setChats: React.Dispatch<React.SetStateAction<ChatSession[]>>;
  activeChatId: string | null;
  setActiveChatId: (id: string | null) => void;
  createNewChat: (category: string, title: string, selectedProject?: ProjectSuggestion) => Promise<string>;
  addMessageToChat: (chatId: string, sender: "user" | "ai", text: string) => Promise<void>;
  editMessageText: (chatId: string, messageId: string, newText: string) => Promise<void>;
  deleteChat: (chatId: string) => Promise<void>;
  renameChat: (chatId: string, newTitle: string) => Promise<void>;
  updateChatCategory: (chatId: string, newCategory: string) => Promise<void>;
  updateChatSelectedProject: (chatId: string, selectedProject: ProjectSuggestion) => Promise<void>;
  togglePauseChat: (chatId: string) => Promise<void>;
  stopChatGeneration: (chatId: string) => void;

  projects: Project[];
  activeProjectId: string | null;
  setActiveProjectId: (id: string | null) => void;
  generateProject: (
    chatId: string,
    projectName: string,
    category: string,
    theme?: string,
    blueprint?: any,
    themePalette?: any,
    hitlEnabled?: boolean,
    generationType?: string
  ) => Promise<void>;
  compileProjectCodebase: (projectId: string, chatId: string) => Promise<void>;
  pauseProjectCodebase: (projectId: string) => Promise<void>;
  resumeProjectCodebase: (projectId: string) => Promise<void>;
  generateDocuments: (projectName: string, prompt: string) => Promise<void>;
  deleteProject: (projectId: string) => Promise<void>;
  renameProject: (projectId: string, newTitle: string) => Promise<void>;
  updateProject: (projectId: string, updates: Partial<Project>) => void;
  approveProjectPlan: (projectId: string, chatId: string, edits?: any) => Promise<void>;
  updateProjectHitl: (projectId: string, hitlEnabled: boolean) => Promise<void>;

  showAuthModal: boolean;
  setShowAuthModal: (show: boolean) => void;
  authMode: "login" | "signup";
  setAuthMode: (mode: "login" | "signup") => void;

  showAbout: boolean;
  setShowAbout: (show: boolean) => void;
  showContact: boolean;
  setShowContact: (show: boolean) => void;
  
  isGeneratingProject: boolean;
  setIsGeneratingProject: (generating: boolean) => void;
  activeWorkspaceTab: "chat" | "workspace";
  setActiveWorkspaceTab: (tab: "chat" | "workspace") => void;

  showRightPane: boolean;
  setShowRightPane: (show: boolean) => void;

  showLeftPane: boolean;
  setShowLeftPane: (show: boolean) => void;

  showSpecsDocs: boolean;
  setShowSpecsDocs: (show: boolean) => void;

  suggestions: ProjectSuggestion[];
  isFetchingSuggestions: boolean;
  fetchSuggestions: (category: string) => Promise<void>;
  clearSuggestions: () => void;

  showFeedbackModal: boolean;
  setShowFeedbackModal: (show: boolean) => void;
  compilationLogs: Record<string, any[]>;
  setCompilationLogs: React.Dispatch<React.SetStateAction<Record<string, any[]>>>;
}

const WorkspaceContext = createContext<WorkspaceContextType | undefined>(undefined);

export const WorkspaceProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<{ id: string; name: string; email: string } | null>(null);
  
  const [chats, setChats] = useState<ChatSession[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);

  const activeSocketsRef = useRef<Record<string, WebSocket>>({});
  const activeIntervalsRef = useRef<Record<string, NodeJS.Timeout>>({});
  const abortControllersRef = useRef<Record<string, AbortController>>({});

  const [showAuthModal, setShowAuthModal] = useState<boolean>(false);
  const [authMode, setAuthMode] = useState<"login" | "signup">("login");

  const [showAbout, setShowAbout] = useState<boolean>(false);
  const [showContact, setShowContact] = useState<boolean>(false);
  const [showFeedbackModal, setShowFeedbackModal] = useState<boolean>(false);
  
  const [isGeneratingProject, setIsGeneratingProject] = useState<boolean>(false);
  const [activeWorkspaceTab, setActiveWorkspaceTab] = useState<"chat" | "workspace">("chat");
  const [showRightPane, setShowRightPane] = useState<boolean>(true);
  const [showLeftPane, setShowLeftPane] = useState<boolean>(true);
  const [showSpecsDocs, setShowSpecsDocs] = useState<boolean>(true);

  const [suggestions, setSuggestions] = useState<ProjectSuggestion[]>([]);
  const [isFetchingSuggestions, setIsFetchingSuggestions] = useState<boolean>(false);
  const [compilationLogs, setCompilationLogs] = useState<Record<string, any[]>>({});

  const fetchSuggestions = useCallback(async (category: string) => {
    setIsFetchingSuggestions(true);
    setSuggestions([]);
    const token = localStorage.getItem("token");
    if (!token) {
      setIsFetchingSuggestions(false);
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/projects/suggestions?category=${category}`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setSuggestions(data);
      }
    } catch (e) {
      console.error("Fetch suggestions failed:", e);
    } finally {
      setIsFetchingSuggestions(false);
    }
  }, []);

  const clearSuggestions = useCallback(() => {
    setSuggestions([]);
  }, []);

  // Fetch functions helper
  const fetchChats = useCallback(async (token: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/chats`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setChats(data);
        if (data.length > 0 && !activeChatId) {
          setActiveChatId(data[0].id);
        }
      }
    } catch (e) {
      console.error("Fetch chats failed:", e);
    }
  }, [activeChatId]);

  const fetchProjects = useCallback(async (token: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/projects`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setProjects(data);
      }
    } catch (e) {
      console.error("Fetch projects failed:", e);
    }
  }, []);

  // Check auth on mount
  useEffect(() => {
    const checkUser = async () => {
      const token = localStorage.getItem("token");
      if (token) {
        try {
          const res = await fetch(`${API_BASE}/api/auth/me`, {
            headers: { "Authorization": `Bearer ${token}` }
          });
          if (res.ok) {
            const data = await res.json();
            setUser(data);
            fetchChats(token);
            fetchProjects(token);
          } else {
            localStorage.removeItem("token");
          }
        } catch (e) {
          // Use console.warn instead of console.error to prevent Next.js from
          // showing the red error overlay during local development when backend is down.
          console.warn("Auth verify failed (backend may be offline or CORS error). Logging out.", e);
          localStorage.removeItem("token");
        }
      }
    };
    checkUser();
  }, []);

  // Clean up all sockets & intervals on unmount
  useEffect(() => {
    return () => {
      Object.values(activeSocketsRef.current).forEach((ws) => {
        try {
          ws.close();
        } catch {}
      });
      Object.values(activeIntervalsRef.current).forEach((interval) => {
        clearInterval(interval);
      });
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const res = await fetch(`${API_BASE}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });
    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(errorData.detail || "Invalid credentials");
    }
    const data = await res.json();
    localStorage.setItem("token", data.access_token);
    setUser(data.user);
    setShowAuthModal(false);
    fetchChats(data.access_token);
    fetchProjects(data.access_token);
  }, [fetchChats, fetchProjects]);

  const signup = useCallback(async (name: string, email: string, password: string) => {
    const res = await fetch(`${API_BASE}/api/auth/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password })
    });
    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(errorData.detail || "Registration failed");
    }
    const data = await res.json();
    localStorage.setItem("token", data.access_token);
    setUser(data.user);
    setShowAuthModal(false);
    fetchChats(data.access_token);
    fetchProjects(data.access_token);
  }, [fetchChats, fetchProjects]);

  const logout = useCallback(() => {
    localStorage.removeItem("token");
    setUser(null);
    setChats([]);
    setProjects([]);
    setActiveChatId(null);
    setActiveProjectId(null);
  }, []);

  const updateProfile = useCallback(async (data: any) => {
    const token = localStorage.getItem("token");
    if (!token) throw new Error("Not authenticated");
    const res = await fetch(`${API_BASE}/api/auth/profile`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
      body: JSON.stringify(data)
    });
    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(errorData.detail || "Profile update failed");
    }
    const updatedUser = await res.json();
    setUser(updatedUser);
  }, []);

  const updateChatSelectedProject = useCallback(async (chatId: string, selectedProject: ProjectSuggestion) => {
    setChats((prev) =>
      prev.map((c) => (c.id === chatId ? { ...c, selected_project: selectedProject } : c))
    );
    const token = localStorage.getItem("token");
    if (!token) return;
    try {
      await fetch(`${API_BASE}/api/chats/${chatId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ selected_project: selectedProject })
      });
    } catch (e) {
      console.error("Update chat selected project failed:", e);
    }
  }, []);

  const togglePauseChat = useCallback(async (chatId: string) => {
    const chat = chats.find((c) => c.id === chatId);
    if (!chat) return;

    const newPauseState = !chat.is_paused;
    setChats((prev) =>
      prev.map((c) => (c.id === chatId ? { ...c, is_paused: newPauseState } : c))
    );

    const token = localStorage.getItem("token");
    if (!token) return;

    try {
      await fetch(`${API_BASE}/api/chats/${chatId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ is_paused: newPauseState })
      });
    } catch (e) {
      console.error("Failed to toggle pause chat status:", e);
    }
  }, [chats]);

  const stopChatGeneration = useCallback((chatId: string) => {
    if (abortControllersRef.current[chatId]) {
      abortControllersRef.current[chatId].abort();
      delete abortControllersRef.current[chatId];
    }
  }, []);

  const createNewChat = useCallback(async (category: string, title: string, selectedProject?: ProjectSuggestion): Promise<string> => {
    const token = localStorage.getItem("token");
    if (!token) return "";
    try {
      const res = await fetch(`${API_BASE}/api/chats`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ 
          category, 
          title, 
          selected_project: selectedProject || null 
        })
      });
      if (res.ok) {
        const newChat = await res.json();
        setChats((prev) => [newChat, ...prev]);
        setActiveChatId(newChat.id);
        setActiveProjectId(null);
        if (selectedProject) {
          setShowRightPane(true);
        } else {
          setShowRightPane(false);
        }
        return newChat.id;
      }
    } catch (e) {
      console.error("Create chat failed:", e);
    }
    return "";
  }, []);

  const addMessageToChat = useCallback(async (chatId: string, sender: "user" | "ai", text: string) => {
    if (sender !== "user") return;
    
    if (abortControllersRef.current[chatId]) {
      abortControllersRef.current[chatId].abort();
    }
    const controller = new AbortController();
    abortControllersRef.current[chatId] = controller;

    const tempUserMsgId = `m-temp-${Date.now()}`;
    const time = new Date().toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
    const userMsg: Message = { id: tempUserMsgId, sender: "user", text, timestamp: time };
    
    setChats((prev) =>
      prev.map((c) => {
        if (c.id === chatId) {
          return { ...c, messages: [...c.messages, userMsg] };
        }
        return c;
      })
    );
    
    const token = localStorage.getItem("token");
    if (!token) {
      delete abortControllersRef.current[chatId];
      return;
    }
    
    try {
      const res = await fetch(`${API_BASE}/api/chats/${chatId}/messages?stream=true`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ text }),
        signal: controller.signal
      });
      if (!res.ok) {
        if (res.status === 401) {
          console.error("Unauthorized: Token might be expired.");
          localStorage.removeItem("token");
          window.location.reload();
          return;
        }
        throw new Error(`API returned status: ${res.status}`);
      }
      
      const reader = res.body?.getReader();
      if (!reader) return;
      
      const decoder = new TextDecoder();
      let buffer = "";
      const aiMessageId = `ai-temp-${Date.now()}`;
      let aiText = "";
      
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        // Keep the last partial line in the buffer
        buffer = lines.pop() || "";
        
        for (const line of lines) {
          const trimmedLine = line.trim();
          if (trimmedLine.startsWith("data: ")) {
            const jsonStr = trimmedLine.slice(6).trim();
            if (!jsonStr) continue;
            
            try {
              const payload = JSON.parse(jsonStr);
              if (payload.type === "user_msg") {
                const savedUserMsg = payload.message;
                setChats((prev) =>
                  prev.map((c) => {
                    if (c.id === chatId) {
                      return {
                        ...c,
                        messages: c.messages.map((m) =>
                          m.id === tempUserMsgId ? savedUserMsg : m
                        )
                      };
                    }
                    return c;
                  })
                );
              } else if (payload.type === "chunk") {
                const chunkText = payload.text;
                aiText += chunkText;
                
                setChats((prev) =>
                  prev.map((c) => {
                    if (c.id === chatId) {
                      const hasAiMessage = c.messages.some((m) => m.id === aiMessageId);
                      if (hasAiMessage) {
                        return {
                          ...c,
                          messages: c.messages.map((m) =>
                            m.id === aiMessageId ? { ...m, text: aiText } : m
                          )
                        };
                      } else {
                        const newAiMsg = {
                          id: aiMessageId,
                          sender: "ai" as const,
                          text: aiText,
                          timestamp: new Date().toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })
                        };
                        return {
                          ...c,
                          messages: [...c.messages, newAiMsg]
                        };
                      }
                    }
                    return c;
                  })
                );
              } else if (payload.type === "ai_msg") {
                const savedAiMsg = payload.message;
                setChats((prev) =>
                  prev.map((c) => {
                    if (c.id === chatId) {
                      // Filter out the temp AI message and add the saved one
                      const filtered = c.messages.filter((m) => m.id !== aiMessageId);
                      return {
                        ...c,
                        messages: [...filtered, savedAiMsg]
                      };
                    }
                    return c;
                  })
                );
                
                // Parse blueprint and update selected project
                const bpMatch = savedAiMsg.text.match(/<blueprint>([\s\S]*?)<\/blueprint>/);
                if (bpMatch && bpMatch[1]) {
                  try {
                    const parsed = JSON.parse(bpMatch[1].trim());
                    if (parsed.name || parsed.idea || parsed.features) {
                      const bp: ProjectSuggestion = {
                        name: parsed.name || "",
                        idea: parsed.idea || "",
                        features: parsed.features || [],
                        tech_stack: parsed.tech_stack || "Flask, HTML, CSS"
                      };
                      updateChatSelectedProject(chatId, bp);
                      setShowRightPane(true);
                    }
                  } catch {
                    // Ignore silently
                  }
                }
              }
            } catch (e) {
              console.error("Failed to parse stream chunk:", jsonStr, e);
            }
          }
        }
      }
    } catch (e: any) {
      if (e.name === "AbortError") {
        console.log("Generation aborted for chat", chatId);
      } else {
        console.error("Send message failed:", e);
      }
    } finally {
      if (abortControllersRef.current[chatId] === controller) {
        delete abortControllersRef.current[chatId];
      }
    }
  }, [updateChatSelectedProject]);

  const editMessageText = useCallback(async (chatId: string, messageId: string, newText: string) => {
    // Update local state immediately
    setChats((prev) =>
      prev.map((c) => {
        if (c.id === chatId) {
          return {
            ...c,
            messages: c.messages.map((m) =>
              m.id === messageId ? { ...m, text: newText } : m
            )
          };
        }
        return c;
      })
    );

    const token = localStorage.getItem("token");
    if (!token) return;

    try {
      await fetch(`${API_BASE}/api/chats/${chatId}/messages/${messageId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ text: newText })
      });
    } catch (e) {
      console.error("Edit message failed:", e);
    }
  }, []);

  const deleteChat = useCallback(async (chatId: string) => {
    const token = localStorage.getItem("token");
    if (!token) return;

    const chatToRestore = chats.find((c) => c.id === chatId);
    const originalActiveId = activeChatId;
    const projectsToRestore = projects.filter((p) => p.chat_id === chatId);
    const originalActiveProjectId = activeProjectId;

    // Optimistic UI Update for instant deletion
    setChats((prev) => prev.filter((c) => c.id !== chatId));
    setProjects((prev) => prev.filter((p) => p.chat_id !== chatId));
    if (activeChatId === chatId) {
      setActiveChatId(null);
    }
    if (projectsToRestore.some((p) => p.id === activeProjectId)) {
      setActiveProjectId(null);
    }

    try {
      const res = await fetch(`${API_BASE}/api/chats/${chatId}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (!res.ok) {
        const errorText = await res.text().catch(() => "No response body");
        throw new Error(`Server rejected deletion (Status: ${res.status}): ${errorText}`);
      }
    } catch (e) {
      console.error("Delete chat failed:", e);
      // Rollback
      if (chatToRestore) {
        setChats((prev) => {
          if (prev.some((c) => c.id === chatId)) return prev;
          return [...prev, chatToRestore];
        });
      }
      setProjects((prev) => {
        const uniqueProjects = [...prev];
        projectsToRestore.forEach((p) => {
          if (!uniqueProjects.some((exist) => exist.id === p.id)) {
            uniqueProjects.push(p);
          }
        });
        return uniqueProjects;
      });
      if (originalActiveId === chatId) {
        setActiveChatId(originalActiveId);
      }
      if (projectsToRestore.some((p) => p.id === originalActiveProjectId)) {
        setActiveProjectId(originalActiveProjectId);
      }
      alert("Failed to delete chat. Please try again.");
    }
  }, [chats, activeChatId, projects, activeProjectId, setActiveProjectId]);

  const renameChat = useCallback(async (chatId: string, newTitle: string) => {
    const token = localStorage.getItem("token");
    if (!token) return;

    const chatToRestore = chats.find((c) => c.id === chatId);
    const originalTitle = chatToRestore ? chatToRestore.title : "";

    // Optimistic UI Update
    setChats((prev) => prev.map((c) => c.id === chatId ? { ...c, title: newTitle } : c));
    try {
      const res = await fetch(`${API_BASE}/api/chats/${chatId}`, {
        method: "PUT",
        headers: { 
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ title: newTitle })
      });
      if (!res.ok) {
        throw new Error("Server rejected rename");
      }
    } catch (e) {
      console.error("Rename chat failed:", e);
      // Rollback
      if (originalTitle) {
        setChats((prev) => prev.map((c) => c.id === chatId ? { ...c, title: originalTitle } : c));
      }
      alert("Failed to rename chat. Please try again.");
    }
  }, [chats]);

  const updateChatCategory = useCallback(async (chatId: string, newCategory: string) => {
    const token = localStorage.getItem("token");
    if (!token) return;

    setChats((prev) => prev.map((c) => c.id === chatId ? { ...c, category: newCategory } : c));
    try {
      const res = await fetch(`${API_BASE}/api/chats/${chatId}`, {
        method: "PUT",
        headers: { 
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ category: newCategory })
      });
      if (!res.ok) {
        console.error("Server rejected category update");
      }
    } catch (e) {
      console.error("Update chat category failed:", e);
    }
  }, []);

  const deleteProject = useCallback(async (projectId: string) => {
    const token = localStorage.getItem("token");
    if (!token) return;

    const projectToRestore = projects.find((p) => p.id === projectId);
    const originalActiveId = activeProjectId;

    // Optimistic UI Update
    setProjects((prev) => prev.filter((p) => p.id !== projectId));
    if (activeProjectId === projectId) {
      setActiveProjectId(null);
    }
    if (projectToRestore && projectToRestore.chat_id) {
      setChats((prev) =>
        prev.map((c) =>
          c.id === projectToRestore.chat_id
            ? { ...c, is_confirmed: false, project_id: null }
            : c
        )
      );
    }

    try {
      const res = await fetch(`${API_BASE}/api/projects/${projectId}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (!res.ok) {
        throw new Error("Server rejected deletion");
      }
    } catch (e) {
      console.error("Delete project failed:", e);
      // Rollback
      if (projectToRestore) {
        setProjects((prev) => {
          if (prev.some((p) => p.id === projectId)) return prev;
          return [...prev, projectToRestore];
        });
        if (projectToRestore.chat_id) {
          setChats((prev) =>
            prev.map((c) =>
              c.id === projectToRestore.chat_id
                ? { ...c, is_confirmed: true, project_id: projectId }
                : c
            )
          );
        }
      }
      if (originalActiveId === projectId) {
        setActiveProjectId(originalActiveId);
      }
      alert("Failed to delete project. Please try again.");
    }
  }, [projects, activeProjectId, setChats]);

  const renameProject = useCallback(async (projectId: string, newTitle: string) => {
    const token = localStorage.getItem("token");
    if (!token) return;

    const projectToRestore = projects.find((p) => p.id === projectId);
    const originalName = projectToRestore ? projectToRestore.name : "";

    // Optimistic UI Update
    setProjects((prev) => prev.map((p) => p.id === projectId ? { ...p, name: newTitle } : p));
    try {
      const res = await fetch(`${API_BASE}/api/projects/${projectId}`, {
        method: "PUT",
        headers: { 
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ title: newTitle })
      });
      if (!res.ok) {
        throw new Error("Server rejected rename");
      }
    } catch (e) {
      console.error("Rename project failed:", e);
      // Rollback
      if (originalName) {
        setProjects((prev) => prev.map((p) => p.id === projectId ? { ...p, name: originalName } : p));
      }
      alert("Failed to rename project. Please try again.");
    }
  }, [projects]);

  const updateProject = useCallback((projectId: string, updates: Partial<Project>) => {
    setProjects((prev) =>
      prev.map((p) => (p.id === projectId ? { ...p, ...updates } : p))
    );
  }, []);

  const monitorProjectProgress = (projectId: string) => {
    if (activeSocketsRef.current[projectId] || activeIntervalsRef.current[projectId]) {
      return;
    }

    const token = localStorage.getItem("token");
    if (!token) {
      setIsGeneratingProject(false);
      return;
    }

    let ws: WebSocket | null = null;

    const cleanupWatchers = () => {
      if (activeIntervalsRef.current[projectId]) {
        clearInterval(activeIntervalsRef.current[projectId]);
        delete activeIntervalsRef.current[projectId];
      }
      if (activeSocketsRef.current[projectId]) {
        try {
          activeSocketsRef.current[projectId].close();
        } catch {}
        delete activeSocketsRef.current[projectId];
      }
    };

    const startPollingFallback = () => {
      if (activeIntervalsRef.current[projectId]) return;
      console.log(`Starting polling fallback for project: ${projectId}`);
      const interval = setInterval(async () => {
        const currentToken = localStorage.getItem("token");
        if (!currentToken) {
          clearInterval(interval);
          delete activeIntervalsRef.current[projectId];
          setIsGeneratingProject(false);
          return;
        }
        try {
          const res = await fetch(`${API_BASE}/api/projects/${projectId}`, {
            headers: { "Authorization": `Bearer ${currentToken}` }
          });
          if (res.ok) {
            const updatedProj = await res.json();
            setProjects((prev) =>
              prev.map((p) => (p.id === projectId ? updatedProj : p))
            );

            if (updatedProj.status === "completed") {
              clearInterval(interval);
              delete activeIntervalsRef.current[projectId];
              setIsGeneratingProject(false);
              fetchChats(currentToken);
              confetti({
                particleCount: 120,
                spread: 80,
                origin: { y: 0.6 },
                colors: ["#6366f1", "#f43f5e", "#eab308", "#fbbf24"],
              });
            } else if (updatedProj.status === "failed") {
              clearInterval(interval);
              delete activeIntervalsRef.current[projectId];
              setIsGeneratingProject(false);
            } else if (updatedProj.status === "waiting_approval" || updatedProj.status === "paused") {
              setIsGeneratingProject(false);
            }
          }
        } catch (e) {
          console.error("Polling project failed:", e);
          clearInterval(interval);
          delete activeIntervalsRef.current[projectId];
          setIsGeneratingProject(false);
        }
      }, 2000);

      activeIntervalsRef.current[projectId] = interval;
    };

    try {
      const wsProto = window.location.protocol === "https:" ? "wss:" : "ws:";
      let wsHost = API_BASE.replace(/^https?:\/\//, "");
      if (API_BASE.startsWith("/")) {
        wsHost = window.location.host;
      }
      const wsUrl = `${wsProto}//${wsHost}/ws/projects/${projectId}?token=${token}`;

      console.log(`Connecting to progress WebSocket: ${wsUrl}`);
      ws = new WebSocket(wsUrl);
      activeSocketsRef.current[projectId] = ws;

      ws.onopen = () => {
        console.log(`WebSocket connected for project: ${projectId}`);
        if (activeIntervalsRef.current[projectId]) {
          clearInterval(activeIntervalsRef.current[projectId]);
          delete activeIntervalsRef.current[projectId];
        }
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === "progress" && msg.project_id === projectId) {
            setProjects((prev) =>
              prev.map((p) =>
                p.id === projectId
                  ? {
                      ...p,
                      progress: msg.progress ?? p.progress,
                      step: msg.step ?? p.step,
                      status: msg.status ?? p.status,
                    }
                  : p
              )
            );

            if (msg.status === "waiting_approval") {
              setIsGeneratingProject(false);
              const currentToken = localStorage.getItem("token") || token;
              fetch(`${API_BASE}/api/projects/${projectId}`, {
                headers: { "Authorization": `Bearer ${currentToken}` }
              })
              .then((res) => (res.ok ? res.json() : null))
              .then((updatedProj) => {
                if (updatedProj) {
                  setProjects((prev) =>
                    prev.map((p) => (p.id === projectId ? updatedProj : p))
                  );
                }
              })
              .catch((err) => console.error("Failed to fetch project on waiting_approval:", err));
            } else if (msg.status === "paused") {
              setIsGeneratingProject(false);
            } else if (msg.status === "completed") {
              cleanupWatchers();
              setIsGeneratingProject(false);
              const currentToken = localStorage.getItem("token") || token;
              fetchChats(currentToken);
              confetti({
                particleCount: 120,
                spread: 80,
                origin: { y: 0.6 },
                colors: ["#6366f1", "#f43f5e", "#eab308", "#fbbf24"],
              });
            } else if (msg.status === "failed") {
              cleanupWatchers();
              setIsGeneratingProject(false);
            }
          } else if (msg.type === "log" && msg.project_id === projectId) {
            setCompilationLogs((prev) => ({
              ...prev,
              [projectId]: [...(prev[projectId] || []), msg]
            }));
          }
        } catch (e) {
          console.error("Failed to parse WS message:", e);
        }
      };

      ws.onerror = (err) => {
        console.error("WS error, falling back to polling:", err);
        startPollingFallback();
      };

      ws.onclose = (event) => {
        console.log(`WebSocket closed for project ${projectId}. Code: ${event.code}`);
        delete activeSocketsRef.current[projectId];
        
        setProjects((prev) => {
          const currentProj = prev.find((p) => p.id === projectId);
          if (currentProj && currentProj.status !== "completed" && currentProj.status !== "failed") {
            setTimeout(() => {
              startPollingFallback();
            }, 0);
          } else {
            setIsGeneratingProject(false);
          }
          return prev;
        });
      };

    } catch (e) {
      console.error("Failed to initialize WebSocket, falling back to polling:", e);
      startPollingFallback();
    }
  };

  useEffect(() => {
    const activeProjForChat = projects.find((p) => p.chat_id === activeChatId);
    if (activeProjForChat && activeProjForChat.status === "generating") {
      setIsGeneratingProject(true);
      monitorProjectProgress(activeProjForChat.id);
    } else {
      setIsGeneratingProject(false);
    }
  }, [projects, activeChatId]);

  const generateProject = useCallback(async (
    chatId: string,
    projectName: string,
    category: string,
    theme?: string,
    blueprint?: any,
    themePalette?: any,
    hitlEnabled: boolean = false,
    generationType: string = "full_stack"
  ) => {
    if (isGeneratingProject) return;
    setIsGeneratingProject(true);
    setActiveProjectId(null);
    setShowRightPane(true);

    const token = localStorage.getItem("token");
    if (!token) {
      setIsGeneratingProject(false);
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/api/projects`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          chat_id: chatId,
          name: projectName,
          category,
          theme,
          blueprint,
          theme_palette: themePalette,
          hitl_enabled: hitlEnabled,
          generation_type: generationType
        })
      });
      if (res.ok) {
        const newProj = await res.json();
        setProjects((prev) => [newProj, ...prev]);
        setActiveProjectId(newProj.id);
        setShowSpecsDocs(true);
        setActiveWorkspaceTab("workspace");
        setChats((prev) =>
          prev.map((c) =>
            c.id === chatId
              ? { ...c, is_confirmed: true, project_id: newProj.id }
              : c
          )
        );
        if (newProj.status === "documents_ready" || newProj.status === "waiting_approval") {
          setIsGeneratingProject(false);
        } else {
          monitorProjectProgress(newProj.id);
        }
      } else {
        setIsGeneratingProject(false);
      }
    } catch (e) {
      console.error("Generate project failed:", e);
      setIsGeneratingProject(false);
    }
  }, [isGeneratingProject, setShowSpecsDocs, monitorProjectProgress]);

  const compileProjectCodebase = useCallback(async (projectId: string, chatId: string) => {
    if (isGeneratingProject) return;
    setIsGeneratingProject(true);

    const token = localStorage.getItem("token");
    if (!token) {
      setIsGeneratingProject(false);
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/api/projects/${projectId}/compile`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`
        }
      });
      if (res.ok) {
        const updatedProj = await res.json();
        setProjects((prev) =>
          prev.map((p) => (p.id === projectId ? updatedProj : p))
        );
        monitorProjectProgress(projectId);
      } else {
        setIsGeneratingProject(false);
      }
    } catch (e) {
      console.error("Compile project codebase failed:", e);
      setIsGeneratingProject(false);
    }
  }, [isGeneratingProject, monitorProjectProgress]);

  const pauseProjectCodebase = useCallback(async (projectId: string) => {
    const token = localStorage.getItem("token");
    if (!token) return;

    try {
      const res = await fetch(`${API_BASE}/api/projects/${projectId}/pause`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`
        }
      });
      if (res.ok) {
        const updatedProj = await res.json();
        setProjects((prev) =>
          prev.map((p) => (p.id === projectId ? updatedProj : p))
        );
        setIsGeneratingProject(false);
      }
    } catch (e) {
      console.error("Pause project failed:", e);
    }
  }, []);

  const resumeProjectCodebase = useCallback(async (projectId: string) => {
    if (isGeneratingProject) return;
    setIsGeneratingProject(true);

    const token = localStorage.getItem("token");
    if (!token) {
      setIsGeneratingProject(false);
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/api/projects/${projectId}/resume`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`
        }
      });
      if (res.ok) {
        const updatedProj = await res.json();
        setProjects((prev) =>
          prev.map((p) => (p.id === projectId ? updatedProj : p))
        );
        monitorProjectProgress(projectId);
      } else {
        setIsGeneratingProject(false);
      }
    } catch (e) {
      console.error("Resume project failed:", e);
      setIsGeneratingProject(false);
    }
  }, [isGeneratingProject, monitorProjectProgress]);

  const generateDocuments = useCallback(async (projectName: string, prompt: string) => {
    if (isGeneratingProject) return;
    setIsGeneratingProject(true);
    setActiveProjectId(null);
    setShowRightPane(true);

    const token = localStorage.getItem("token");
    if (!token) {
      setIsGeneratingProject(false);
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/api/projects/generate-documents`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          name: projectName,
          prompt
        })
      });
      if (res.ok) {
        const newProj = await res.json();
        setProjects((prev) => [newProj, ...prev]);
        setActiveProjectId(newProj.id);
        confetti({
          particleCount: 150,
          spread: 80,
          origin: { y: 0.6 }
        });
      }
    } catch (e) {
      console.error("Generate documents failed:", e);
    } finally {
      setIsGeneratingProject(false);
    }
  }, [isGeneratingProject]);

  const approveProjectPlan = useCallback(async (projectId: string, chatId: string, edits?: any) => {
    if (isGeneratingProject) return;
    setIsGeneratingProject(true);

    const token = localStorage.getItem("token");
    if (!token) {
      setIsGeneratingProject(false);
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/api/projects/${projectId}/approve`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          implementation_plan: edits
        })
      });
      if (res.ok) {
        const updatedProj = await res.json();
        setProjects((prev) =>
          prev.map((p) => (p.id === projectId ? updatedProj : p))
        );
        monitorProjectProgress(projectId);
      } else {
        setIsGeneratingProject(false);
      }
    } catch (e) {
      console.error("Approve project plan failed:", e);
      setIsGeneratingProject(false);
    }
  }, [isGeneratingProject]);

  const updateProjectHitl = useCallback(async (projectId: string, hitlEnabled: boolean) => {
    const token = localStorage.getItem("token");
    if (!token) return;

    try {
      const res = await fetch(`${API_BASE}/api/projects/${projectId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          hitl_enabled: hitlEnabled
        })
      });
      if (res.ok) {
        setProjects((prev) =>
          prev.map((p) => (p.id === projectId ? { ...p, hitl_enabled: hitlEnabled } : p))
        );
      }
    } catch (e) {
      console.error("Failed to update HITL settings:", e);
    }
  }, []);


  const contextValue = useMemo(() => ({
    user,
    login,
    signup,
    logout,
    updateProfile,
    chats,
    setChats,
    activeChatId,
    setActiveChatId,
    createNewChat,
    addMessageToChat,
    editMessageText,
    deleteChat,
    renameChat,
    updateChatSelectedProject,
    updateChatCategory,
    togglePauseChat,
    stopChatGeneration,
    projects,
    activeProjectId,
    setActiveProjectId,
    generateProject,
    compileProjectCodebase,
    pauseProjectCodebase,
    resumeProjectCodebase,
    generateDocuments,
    deleteProject,
    renameProject,
    updateProject,
    approveProjectPlan,
    updateProjectHitl,
    showAuthModal,
    setShowAuthModal,
    authMode,
    setAuthMode,
    showAbout,
    setShowAbout,
    showContact,
    setShowContact,
    isGeneratingProject,
    setIsGeneratingProject,
    activeWorkspaceTab,
    setActiveWorkspaceTab,
    showRightPane,
    setShowRightPane,
    showLeftPane,
    setShowLeftPane,
    showSpecsDocs,
    setShowSpecsDocs,
    suggestions,
    isFetchingSuggestions,
    fetchSuggestions,
    clearSuggestions,
    showFeedbackModal,
    setShowFeedbackModal,
    compilationLogs,
    setCompilationLogs,
  }), [
    user,
    login,
    signup,
    logout,
    chats,
    setChats,
    activeChatId,
    createNewChat,
    addMessageToChat,
    editMessageText,
    deleteChat,
    renameChat,
    updateChatSelectedProject,
    updateChatCategory,
    togglePauseChat,
    stopChatGeneration,
    projects,
    activeProjectId,
    generateProject,
    compileProjectCodebase,
    pauseProjectCodebase,
    resumeProjectCodebase,
    generateDocuments,
    deleteProject,
    renameProject,
    updateProject,
    approveProjectPlan,
    updateProjectHitl,
    showAuthModal,
    authMode,
    showAbout,
    showContact,
    isGeneratingProject,
    setIsGeneratingProject,
    activeWorkspaceTab,
    showRightPane,
    showLeftPane,
    showSpecsDocs,
    suggestions,
    isFetchingSuggestions,
    fetchSuggestions,
    clearSuggestions,
    showFeedbackModal,
    compilationLogs,
  ]);

  return (
    <WorkspaceContext.Provider value={contextValue}>
      {children}
    </WorkspaceContext.Provider>
  );
};

export const useWorkspace = () => {
  const context = useContext(WorkspaceContext);
  if (context === undefined) {
    throw new Error("useWorkspace must be used within a WorkspaceProvider");
  }
  return context;
};
