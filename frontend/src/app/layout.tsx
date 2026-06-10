import type { Metadata } from "next";
import { Dancing_Script, Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";
import { WorkspaceProvider } from "@/context/WorkspaceContext";

const dancingScript = Dancing_Script({
  subsets: ["latin"],
  variable: "--font-dancing-script",
});

const plusJakartaSans = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-plus-jakarta-sans",
});

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
    <html lang="en" className={`h-full antialiased ${dancingScript.variable} ${plusJakartaSans.variable}`}>
      <body className={`min-h-full flex flex-col font-[family-name:var(--font-plus-jakarta-sans)] selection:bg-indigo-100 selection:text-indigo-900`}>
        <WorkspaceProvider>{children}</WorkspaceProvider>
      </body>
    </html>
  );
}
