"use client";

import React, { useState, useMemo } from "react";
import {
  Download,
  FileCode,
  FileText,
  Search,
  ExternalLink,
  Layers,
  Box,
  Terminal,
  Clock,
  HardDrive,
} from "lucide-react";
import { FileItem } from "../stores/sessionStore";
import { api } from "../lib/api";
import { formatBytes } from "../lib/utils";

interface ArtifactListProps {
  sessionId: string;
  files: FileItem[];
  onViewFile: (path: string, id: string) => void;
}

export function ArtifactList({ sessionId, files, onViewFile }: ArtifactListProps) {
  const [filterType, setFilterType] = useState<string>("ALL");
  const [search, setSearch] = useState("");

  const downloadAllUrl = api.downloadArtifacts(sessionId);

  const filteredFiles = useMemo(() => {
    return files.filter((f) => {
      const matchesSearch = f.path.toLowerCase().includes(search.toLowerCase());
      if (!matchesSearch) return false;
      if (filterType === "ALL") return true;
      return f.type.toLowerCase() === filterType.toLowerCase();
    });
  }, [files, search, filterType]);

  const totalSize = useMemo(() => {
    return files.reduce((acc, f) => acc + (f.size || 0), 0);
  }, [files]);

  const getTypeBadge = (type: string) => {
    switch (type.toLowerCase()) {
      case "test":
        return {
          label: "TEST",
          className: "bg-emerald-500/10 text-emerald-300 border-emerald-500/30",
        };
      case "devops":
        return {
          label: "DEVOPS",
          className: "bg-orange-500/10 text-orange-300 border-orange-500/30",
        };
      case "docs":
        return {
          label: "DOCS",
          className: "bg-purple-500/10 text-purple-300 border-purple-500/30",
        };
      case "source":
      default:
        return {
          label: "SOURCE",
          className: "bg-blue-500/10 text-blue-300 border-blue-500/30",
        };
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#101018] rounded-xl border border-gray-800/80 overflow-hidden">
      {/* Top Banner */}
      <div className="p-4 bg-[#141420] border-b border-gray-800/80 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-bold text-gray-100">
              Generated System Artifacts
            </h3>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-brand-500/15 text-brand-300 border border-brand-500/30">
              {files.length} artifacts
            </span>
          </div>
          <p className="text-xs text-gray-400 mt-0.5">
            Full production output package ready for compilation, testing, and deployment.
          </p>
        </div>

        {/* Download All Button */}
        <a
          href={downloadAllUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold bg-brand-600 hover:bg-brand-500 text-white shadow-lg shadow-brand-500/20 transition-all active:scale-95 shrink-0"
        >
          <Download className="w-4 h-4" />
          Download All (.ZIP)
        </a>
      </div>

      {/* Filter and Search Bar */}
      <div className="px-4 py-2.5 bg-[#12121c] border-b border-gray-800/80 flex flex-col sm:flex-row items-center justify-between gap-2">
        <div className="flex items-center gap-1.5 w-full sm:w-auto overflow-x-auto">
          {["ALL", "SOURCE", "TEST", "DEVOPS", "DOCS"].map((tab) => (
            <button
              key={tab}
              type="button"
              onClick={() => setFilterType(tab)}
              className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                filterType === tab
                  ? "bg-brand-600 text-white"
                  : "text-gray-400 hover:text-gray-200 hover:bg-gray-800/60"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-64">
          <Search className="w-3.5 h-3.5 text-gray-500 absolute left-2.5 top-2.5" />
          <input
            type="text"
            placeholder="Search artifacts..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-[#181824] text-xs text-gray-200 placeholder-gray-500 pl-8 pr-3 py-1.5 rounded-lg border border-gray-700/60 focus:outline-none focus:border-brand-500"
          />
        </div>
      </div>

      {/* Artifacts Table */}
      <div className="flex-1 overflow-y-auto">
        {filteredFiles.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center p-8 text-center text-gray-500">
            <Box className="w-12 h-12 text-gray-700 mb-2" />
            <span className="text-sm font-medium text-gray-300">
              No artifacts match your filter
            </span>
            <span className="text-xs text-gray-500 mt-1">
              Artifacts created by agents will automatically appear here.
            </span>
          </div>
        ) : (
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-gray-800/80 bg-[#12121c] text-gray-400 text-[11px] uppercase tracking-wider font-semibold select-none">
                <th className="py-2.5 px-4">Artifact Path</th>
                <th className="py-2.5 px-4">Category</th>
                <th className="py-2.5 px-4 hidden sm:table-cell">Size</th>
                <th className="py-2.5 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/40">
              {filteredFiles.map((file) => {
                const badge = getTypeBadge(file.type);
                const isCode =
                  file.path.endsWith(".ts") ||
                  file.path.endsWith(".tsx") ||
                  file.path.endsWith(".py") ||
                  file.path.endsWith(".js") ||
                  file.path.endsWith(".json");

                return (
                  <tr
                    key={file.id || file.path}
                    className="hover:bg-white/[0.02] transition-colors group"
                  >
                    <td className="py-2.5 px-4">
                      <div className="flex items-center gap-2.5">
                        {isCode ? (
                          <FileCode className="w-4 h-4 text-brand-400 shrink-0" />
                        ) : (
                          <FileText className="w-4 h-4 text-gray-400 shrink-0" />
                        )}
                        <span className="font-mono text-gray-200 group-hover:text-brand-300 transition-colors truncate max-w-xs sm:max-w-md">
                          {file.path}
                        </span>
                      </div>
                    </td>

                    <td className="py-2.5 px-4">
                      <span
                        className={`text-[10px] font-sans font-bold px-2 py-0.5 rounded border ${badge.className}`}
                      >
                        {badge.label}
                      </span>
                    </td>

                    <td className="py-2.5 px-4 font-mono text-gray-400 hidden sm:table-cell">
                      {file.size ? formatBytes(file.size) : "Dynamic"}
                    </td>

                    <td className="py-2.5 px-4 text-right">
                      <button
                        type="button"
                        onClick={() => onViewFile(file.path, file.id)}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs font-medium text-brand-300 hover:text-white bg-brand-500/10 hover:bg-brand-500/30 border border-brand-500/30 transition-all active:scale-95"
                      >
                        <ExternalLink className="w-3 h-3" />
                        Inspect
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Footer Summary */}
      <div className="p-3 bg-[#13131e] border-t border-gray-800/80 flex items-center justify-between text-xs text-gray-500">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1">
            <HardDrive className="w-3.5 h-3.5" />
            Total Packaged: {totalSize > 0 ? formatBytes(totalSize) : `${files.length} items`}
          </span>
        </div>
        <span className="font-mono text-[11px]">Ready for deployment</span>
      </div>
    </div>
  );
}
