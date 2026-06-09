import type { Metadata } from "next";
import "./globals.css";
import { WorkspaceProvider } from "@/context/WorkspaceContext";

export const metadata: Metadata = {
  title: "Sarthi - Gemini Agent Builder Workspace",
  description: "Build hackathon-ready action agents with Gemini orchestration, MongoDB MCP evidence, requirements docs, and runnable prototypes.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col font-sans selection:bg-indigo-100 selection:text-indigo-900">
        <WorkspaceProvider>{children}</WorkspaceProvider>
      </body>
    </html>
  );
}
