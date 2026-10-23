"use client";

import React, { useState, useMemo } from "react";
import dynamic from "next/dynamic";
import {
  Folder,
  FolderOpen,
  FileCode,
  FileText,
  Copy,
  Check,
  Search,
  Code,
  Box,
  Terminal,
  Loader2,
} from "lucide-react";
import { FileItem } from "../stores/sessionStore";

// Dynamically import Monaco Editor to avoid SSR window errors
const Editor = dynamic(() => import("@monaco-editor/react"), {
  ssr: false,
  loading: () => (
    <div className="h-full flex flex-col items-center justify-center bg-[#0e0e16] text-gray-500">
      <Loader2 className="w-8 h-8 animate-spin text-brand-400 mb-2" />
      <span className="text-xs font-mono">Initializing Monaco Code Editor...</span>
    </div>
  ),
});

interface CodePanelProps {
  files: Array<{ path: string; id: string; type: string }>;
  selectedFile: string | null;
  selectedFileContent: string | null;
  isLoadingContent?: boolean;
  onFileSelect: (path: string, id: string) => void;
}

function detectLanguage(filePath: string): string {
  const ext = filePath.split(".").pop()?.toLowerCase();
  switch (ext) {
    case "ts":
      return "typescript";
    case "tsx":
      return "typescript";
    case "js":
      return "javascript";
    case "jsx":
      return "javascript";
    case "py":
      return "python";
    case "json":
      return "json";
    case "yml":
    case "yaml":
      return "yaml";
    case "md":
      return "markdown";
    case "html":
      return "html";
    case "css":
      return "css";
    case "sql":
      return "sql";
    case "sh":
    case "bash":
      return "shell";
    case "dockerfile":
      return "dockerfile";
    default:
      if (filePath.toLowerCase().includes("dockerfile")) return "dockerfile";
      return "plaintext";
  }
}

export function CodePanel({
  files,
  selectedFile,
  selectedFileContent,
  isLoadingContent = false,
  onFileSelect,
}: CodePanelProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [copied, setCopied] = useState(false);

  const filteredFiles = useMemo(() => {
    if (!searchQuery.trim()) return files;
    return files.filter((f) =>
      f.path.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [files, searchQuery]);

  // Group files by top-level or sub-folder
  const groupedFiles = useMemo(() => {
    const groups: Record<string, typeof files> = {};
    for (const file of filteredFiles) {
      const parts = file.path.replace(/^[./]+/, "").split("/");
      const folder = parts.length > 1 ? parts.slice(0, -1).join("/") : "root";
      if (!groups[folder]) groups[folder] = [];
      groups[folder].push(file);
    }
    return groups;
  }, [filteredFiles]);

  const copyToClipboard = () => {
    if (!selectedFileContent) return;
    navigator.clipboard.writeText(selectedFileContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getBadgeForType = (type: string) => {
    switch (type.toLowerCase()) {
      case "test":
        return {
          label: "TEST",
          className: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
        };
      case "devops":
        return {
          label: "DEVOPS",
          className: "bg-orange-500/10 text-orange-400 border-orange-500/20",
        };
      case "docs":
        return {
          label: "DOCS",
          className: "bg-purple-500/10 text-purple-400 border-purple-500/20",
        };
      case "source":
      default:
        return {
          label: "SRC",
          className: "bg-blue-500/10 text-blue-400 border-blue-500/20",
        };
    }
  };

  return (
    <div className="flex h-full w-full bg-[#0d0d14] rounded-xl border border-gray-800/80 overflow-hidden">
      {/* LEFT SIDEBAR: File Tree Explorer */}
      <div className="w-64 sm:w-72 md:w-80 border-r border-gray-800/80 flex flex-col bg-[#11111a] shrink-0">
        <div className="p-3 border-b border-gray-800/80">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-300 flex items-center gap-1.5">
              <Box className="w-3.5 h-3.5 text-brand-400" />
              Project Files ({files.length})
            </span>
          </div>

          <div className="relative">
            <Search className="w-3.5 h-3.5 text-gray-500 absolute left-2.5 top-2.5" />
            <input
              type="text"
              placeholder="Filter files..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-[#181824] text-xs text-gray-200 placeholder-gray-500 pl-8 pr-3 py-1.5 rounded-lg border border-gray-700/60 focus:outline-none focus:border-brand-500"
            />
          </div>
        </div>

        {/* Tree Content */}
        <div className="flex-1 overflow-y-auto p-2 space-y-3">
          {files.length === 0 ? (
            <div className="p-4 text-center text-xs text-gray-500">
              No files generated yet. Code files generated by agents will appear
              here in real time.
            </div>
          ) : Object.keys(groupedFiles).length === 0 ? (
            <div className="p-4 text-center text-xs text-gray-500">
              No matching files found.
            </div>
          ) : (
            Object.entries(groupedFiles).map(([folder, folderFiles]) => (
              <div key={folder} className="space-y-1">
                <div className="flex items-center gap-1.5 px-2 py-1 text-[11px] font-mono text-gray-400 uppercase tracking-wider">
                  <FolderOpen className="w-3.5 h-3.5 text-brand-400" />
                  <span>{folder}</span>
                </div>

                <div className="pl-2 space-y-0.5">
                  {folderFiles.map((file) => {
                    const isSelected = selectedFile === file.path;
                    const badge = getBadgeForType(file.type);
                    const filename = file.path.split("/").pop() || file.path;

                    return (
                      <button
                        key={file.id || file.path}
                        type="button"
                        onClick={() => onFileSelect(file.path, file.id)}
                        className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs font-mono transition-all text-left group ${
                          isSelected
                            ? "bg-brand-600/20 text-brand-200 border border-brand-500/40"
                            : "text-gray-400 hover:text-gray-200 hover:bg-[#181826]"
                        }`}
                      >
                        <div className="flex items-center gap-2 truncate min-w-0 pr-2">
                          <FileCode
                            className={`w-3.5 h-3.5 shrink-0 ${
                              isSelected ? "text-brand-400" : "text-gray-500"
                            }`}
                          />
                          <span className="truncate">{filename}</span>
                        </div>

                        <span
                          className={`text-[9px] font-sans font-bold px-1.5 py-0.2 rounded border shrink-0 ${badge.className}`}
                        >
                          {badge.label}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* RIGHT SIDE: Monaco Editor / Viewer */}
      <div className="flex-1 flex flex-col bg-[#0e0e16] min-w-0">
        {selectedFile ? (
          <>
            {/* Editor Top Bar */}
            <div className="h-10 px-4 border-b border-gray-800/80 flex items-center justify-between bg-[#12121a]">
              <div className="flex items-center gap-2 min-w-0">
                <Terminal className="w-3.5 h-3.5 text-brand-400 shrink-0" />
                <span className="text-xs font-mono text-gray-200 truncate">
                  {selectedFile}
                </span>
                <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-gray-800 text-gray-400 border border-gray-700">
                  {detectLanguage(selectedFile)}
                </span>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={copyToClipboard}
                  disabled={!selectedFileContent}
                  className="flex items-center gap-1.5 px-2.5 py-1 rounded text-xs text-gray-300 hover:text-white bg-gray-800 hover:bg-gray-700 transition-colors border border-gray-700"
                >
                  {copied ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                      <span className="text-emerald-400">Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5 text-gray-400" />
                      <span>Copy</span>
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Monaco Container */}
            <div className="flex-1 relative overflow-hidden">
              {isLoadingContent ? (
                <div className="h-full flex flex-col items-center justify-center text-gray-500">
                  <Loader2 className="w-8 h-8 animate-spin text-brand-400 mb-2" />
                  <span className="text-xs font-mono">Loading file content...</span>
                </div>
              ) : selectedFileContent !== null ? (
                <Editor
                  height="100%"
                  language={detectLanguage(selectedFile)}
                  theme="vs-dark"
                  value={selectedFileContent}
                  options={{
                    readOnly: true,
                    minimap: { enabled: true },
                    fontSize: 13,
                    lineNumbers: "on",
                    scrollBeyondLastLine: false,
                    automaticLayout: true,
                    fontFamily:
                      "JetBrains Mono, Menlo, Monaco, 'Courier New', monospace",
                    renderWhitespace: "selection",
                    smoothScrolling: true,
                    cursorBlinking: "smooth",
                    padding: { top: 12, bottom: 12 },
                  }}
                />
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-gray-500">
                  <FileText className="w-8 h-8 opacity-40 mb-2" />
                  <span className="text-xs font-mono">File content is empty</span>
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-center p-8 text-gray-500">
            <Code className="w-12 h-12 mb-3 text-gray-700" />
            <h4 className="text-sm font-medium text-gray-300 mb-1">
              No File Selected
            </h4>
            <p className="text-xs text-gray-500 max-w-sm">
              Select a file from the explorer on the left to inspect syntax-highlighted code.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
