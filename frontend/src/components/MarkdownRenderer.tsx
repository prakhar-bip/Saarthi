"use client";

import React from "react";

interface MarkdownRendererProps {
  text: string;
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ text }) => {
  if (!text) return null;

  // Split content by segments (normal paragraphs, lists, tables, code blocks, headings)
  const lines = text.split("\n");
  const elements: React.ReactNode[] = [];
  
  let currentTableRows: string[][] = [];
  let isInsideTable = false;

  let currentListItems: string[] = [];
  let isInsideList = false;

  let currentCodeBlockLines: string[] = [];
  let isInsideCodeBlock = false;

  const renderCurrentTable = (key: number) => {
    if (currentTableRows.length === 0) return null;
    
    // The first row is the header
    const headers = currentTableRows[0];
    // The remaining rows are data (filtering out separator rows like |---|---|)
    const dataRows = currentTableRows.slice(1).filter(row => {
      const combined = row.join("").trim();
      return combined !== "" && !/^[|\s:-]+$/.test(combined);
    });

    return (
      <div key={`table-${key}`} className="my-4 overflow-x-auto rounded-xl border border-current/20 shadow-sm max-w-full">
        <table className="w-full border-collapse text-left text-xs">
          <thead>
            <tr className="border-b border-current/20">
              {headers.map((h, i) => (
                <th key={`th-${i}`} className="px-4 py-3 font-semibold font-display capitalize">
                  {renderTextWithFormatting(h)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-current/10">
            {dataRows.map((row, rowIndex) => (
              <tr key={`tr-${rowIndex}`} className="hover:bg-current/5 transition-colors">
                {row.map((cell, cellIndex) => (
                  <td key={`td-${cellIndex}`} className="px-4 py-3 leading-relaxed whitespace-pre-line align-top">
                    {renderTextWithFormatting(cell)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderCurrentList = (key: number) => {
    if (currentListItems.length === 0) return null;
    return (
      <ul key={`list-${key}`} className="list-disc pl-5 my-2 space-y-1.5 text-xs leading-relaxed">
        {currentListItems.map((item, idx) => (
          <li key={`li-${idx}`} className="pl-1">
            {renderTextWithFormatting(item)}
          </li>
        ))}
      </ul>
    );
  };

  // Process line by line
  for (let idx = 0; idx < lines.length; idx++) {
    const rawLine = lines[idx];
    const line = rawLine.trim();

    // 0. Code block toggle
    if (line.startsWith("```")) {
      if (isInsideList) {
        elements.push(renderCurrentList(idx));
        currentListItems = [];
        isInsideList = false;
      }
      if (isInsideTable) {
        elements.push(renderCurrentTable(idx));
        currentTableRows = [];
        isInsideTable = false;
      }
      if (isInsideCodeBlock) {
        elements.push(
          <pre key={`code-${idx}`} className="my-3 p-4 bg-stone-900 text-stone-100 rounded-xl overflow-x-auto text-[11px] font-mono leading-relaxed border border-stone-800 shadow-sm">
            <code>{currentCodeBlockLines.join("\n")}</code>
          </pre>
        );
        currentCodeBlockLines = [];
        isInsideCodeBlock = false;
      } else {
        isInsideCodeBlock = true;
      }
      continue;
    }

    if (isInsideCodeBlock) {
      currentCodeBlockLines.push(rawLine); // Keep spacing inside code block
      continue;
    }

    // 1. Table Parsing
    if (line.startsWith("|")) {
      if (isInsideList) {
        elements.push(renderCurrentList(idx));
        currentListItems = [];
        isInsideList = false;
      }

      isInsideTable = true;
      const cells = line.split("|").map(c => c.trim());
      if (cells[0] === "") cells.shift();
      if (cells[cells.length - 1] === "") cells.pop();

      currentTableRows.push(cells);
      continue;
    } else if (isInsideTable) {
      elements.push(renderCurrentTable(idx));
      currentTableRows = [];
      isInsideTable = false;
    }

    // 2. Heading Parsing
    const headingMatch = line.match(/^(#{1,6})\s+(.+)$/);
    if (headingMatch) {
      if (isInsideList) {
        elements.push(renderCurrentList(idx));
        currentListItems = [];
        isInsideList = false;
      }
      const level = headingMatch[1].length;
      const content = headingMatch[2];
      const headingClasses = [
        "", // 0
        "text-xl font-bold mt-6 mb-3 font-display border-b border-current/20 pb-1.5 block", // h1
        "text-lg font-bold mt-5 mb-2.5 font-display block", // h2
        "text-base font-semibold mt-4 mb-2 block", // h3
        "text-sm font-semibold mt-3 mb-1.5 block", // h4
        "text-xs font-semibold mt-2 mb-1 block", // h5
        "text-xs font-medium mt-2 mb-1 block", // h6
      ];
      const Tag = `h${level}` as any;
      elements.push(
        <Tag key={`h-${idx}`} className={headingClasses[level] || headingClasses[6]}>
          {renderTextWithFormatting(content)}
        </Tag>
      );
      continue;
    }

    // 3. Blockquote Parsing
    if (line.startsWith(">")) {
      if (isInsideList) {
        elements.push(renderCurrentList(idx));
        currentListItems = [];
        isInsideList = false;
      }
      const content = line.substring(1).trim();
      elements.push(
        <blockquote key={`quote-${idx}`} className="pl-4 border-l-4 border-current/50 my-3 italic opacity-90 py-1 pr-2 block">
          {renderTextWithFormatting(content)}
        </blockquote>
      );
      continue;
    }

    // 4. List Parsing (items starting with "- ", "* ", "• ")
    const listMatch = line.match(/^([-\*•])\s+(.+)$/);
    if (listMatch) {
      isInsideList = true;
      currentListItems.push(listMatch[2]);
      continue;
    } else if (isInsideList) {
      elements.push(renderCurrentList(idx));
      currentListItems = [];
      isInsideList = false;
    }

    // 5. Normal paragraph
    if (line !== "") {
      elements.push(
        <p key={`p-${idx}`} className="text-xs leading-relaxed my-2">
          {renderTextWithFormatting(line)}
        </p>
      );
    }
  }

  // Close remaining tags at the end of the loop
  if (isInsideTable) {
    elements.push(renderCurrentTable(lines.length));
  }
  if (isInsideList) {
    elements.push(renderCurrentList(lines.length));
  }
  if (isInsideCodeBlock) {
    elements.push(
      <pre key={`code-end`} className="my-3 p-4 bg-stone-900 text-stone-100 rounded-xl overflow-x-auto text-[11px] font-mono leading-relaxed border border-stone-800 shadow-sm">
        <code>{currentCodeBlockLines.join("\n")}</code>
      </pre>
    );
  }

  return <div className="space-y-1">{elements}</div>;
};

// Helper function to render text containing Bold (**) and line-breaks (<br>)
function renderTextWithFormatting(str: string): React.ReactNode {
  if (!str) return "";

  // 1. Handle <br> tags (split by <br> or <br/>)
  const brSegments = str.split(/<br\s*\/?>/i);
  return brSegments.map((segment, sIdx) => {
    // 2. Parse Inline Code `code` and Bold **text**
    // First we parse inline code, then bold.
    const parseFormatting = (text: string) => {
      const codeRegex = /`([^`]+)`/g;
      const nodes: React.ReactNode[] = [];
      let lastIdx = 0;
      let match;

      while ((match = codeRegex.exec(text)) !== null) {
        if (match.index > lastIdx) {
          nodes.push(...parseBold(text.substring(lastIdx, match.index)));
        }
        nodes.push(
          <code key={`code-${match.index}`} className="px-1.5 py-0.5 bg-stone-200 text-stone-800 rounded font-mono text-[11px]">
            {match[1]}
          </code>
        );
        lastIdx = codeRegex.lastIndex;
      }
      if (lastIdx < text.length) {
        nodes.push(...parseBold(text.substring(lastIdx)));
      }
      return nodes;
    };

    const parseBold = (text: string) => {
      const boldRegex = /\*\*(.*?)\*\*/g;
      const nodes: React.ReactNode[] = [];
      let lastIdx = 0;
      let match;

      while ((match = boldRegex.exec(text)) !== null) {
        if (match.index > lastIdx) {
          nodes.push(text.substring(lastIdx, match.index));
        }
        nodes.push(
          <strong key={`b-${match.index}`} className="font-bold">
            {match[1]}
          </strong>
        );
        lastIdx = boldRegex.lastIndex;
      }
      if (lastIdx < text.length) {
        nodes.push(text.substring(lastIdx));
      }
      return nodes;
    };

    return (
      <React.Fragment key={`br-${sIdx}`}>
        {parseFormatting(segment)}
        {sIdx < brSegments.length - 1 && <br />}
      </React.Fragment>
    );
  });
}
