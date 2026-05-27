"use client";

import React from "react";

interface MarkdownRendererProps {
  text: string;
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ text }) => {
  if (!text) return null;

  // Split content by segments (normal paragraphs, lists, tables)
  const lines = text.split("\n");
  const elements: React.ReactNode[] = [];
  
  let currentTableRows: string[][] = [];
  let isInsideTable = false;

  let currentListItems: string[] = [];
  let isInsideList = false;

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
      <div key={`table-${key}`} className="my-4 overflow-x-auto rounded-xl border border-stone-200/80 shadow-sm max-w-full">
        <table className="w-full border-collapse text-left text-xs text-stone-600">
          <thead>
            <tr className="bg-stone-100 border-b border-stone-200">
              {headers.map((h, i) => (
                <th key={`th-${i}`} className="px-4 py-3 font-semibold text-stone-700 font-display capitalize">
                  {renderTextWithFormatting(h)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-stone-200/60 bg-white">
            {dataRows.map((row, rowIndex) => (
              <tr key={`tr-${rowIndex}`} className="hover:bg-indigo-50/20 even:bg-stone-50/20 transition-colors">
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
      <ul key={`list-${key}`} className="list-disc pl-5 my-2 space-y-1.5 text-xs text-stone-600 leading-relaxed">
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
    const line = lines[idx].trim();

    // 1. Table Parsing
    if (line.startsWith("|")) {
      // If we were in a list, close it
      if (isInsideList) {
        elements.push(renderCurrentList(idx));
        currentListItems = [];
        isInsideList = false;
      }

      isInsideTable = true;
      // Split the line by "|" and clean empty outer elements
      const cells = line.split("|").map(c => c.trim());
      // Clean leading and trailing empty entries because the string starts and ends with "|"
      if (cells[0] === "") cells.shift();
      if (cells[cells.length - 1] === "") cells.pop();

      currentTableRows.push(cells);
      continue;
    } else if (isInsideTable) {
      // Line is no longer part of a table, render the collected table
      elements.push(renderCurrentTable(idx));
      currentTableRows = [];
      isInsideTable = false;
    }

    // 2. List Parsing (items starting with "- ", "* ", "• ")
    const listMatch = line.match(/^([-\*•])\s+(.+)$/);
    if (listMatch) {
      isInsideList = true;
      currentListItems.push(listMatch[2]);
      continue;
    } else if (isInsideList) {
      // Line is no longer part of a list, render the collected list
      elements.push(renderCurrentList(idx));
      currentListItems = [];
      isInsideList = false;
    }

    // 3. Normal paragraph
    if (line !== "") {
      elements.push(
        <p key={`p-${idx}`} className="text-xs leading-relaxed my-2 text-stone-600">
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

  return <div className="space-y-1">{elements}</div>;
};

// Helper function to render text containing Bold (**) and line-breaks (<br>)
function renderTextWithFormatting(str: string): React.ReactNode {
  if (!str) return "";

  // 1. Handle <br> tags (split by <br> or <br/>)
  const brSegments = str.split(/<br\s*\/?>/i);
  return brSegments.map((segment, sIdx) => {
    // 2. Parse Bold formatting **text**
    const boldRegex = /\*\*(.*?)\*\*/g;
    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = boldRegex.exec(segment)) !== null) {
      const matchIndex = match.index;
      // Add text before bold match
      if (matchIndex > lastIndex) {
        parts.push(segment.substring(lastIndex, matchIndex));
      }
      // Add bold node
      parts.push(
        <strong key={`b-${matchIndex}`} className="font-bold text-stone-800">
          {match[1]}
        </strong>
      );
      lastIndex = boldRegex.lastIndex;
    }

    if (lastIndex < segment.length) {
      parts.push(segment.substring(lastIndex));
    }

    return (
      <React.Fragment key={`br-${sIdx}`}>
        {parts}
        {sIdx < brSegments.length - 1 && <br />}
      </React.Fragment>
    );
  });
}
