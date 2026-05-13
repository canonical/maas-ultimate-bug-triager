import { useState, useMemo, useEffect, useRef, useCallback } from "react";
import { useBugs } from "../hooks/useBugs";
import { useAppContext } from "../context/AppContext";
import { useToast } from "../hooks/useToast";
import { TriageStatus } from "../types";
import BugRow from "./BugRow";

type SortField =
  | "id"
  | "title"
  | "status"
  | "importance"
  | "owner"
  | "date_created";
type SortDirection = "asc" | "desc";

const STATUS_FILTERS = ["All", "New", "Incomplete"] as const;

const SORT_LABELS: Record<SortField, string> = {
  id: "Bug ID",
  title: "Title",
  status: "Status",
  importance: "Importance",
  owner: "Reporter",
  date_created: "Date Created",
};

const SORTABLE_FIELDS: SortField[] = [
  "id",
  "title",
  "status",
  "importance",
  "owner",
  "date_created",
];

export default function BugList() {
  const {
    bugs,
    triageStatuses,
    loading,
    error,
    loadBugs,
    analyzeBug,
    analyzeAll,
  } = useBugs();
  const { selectedBugId, selectBug, refreshBugs } = useAppContext();
  const { addToast } = useToast();
  const [statusFilter, setStatusFilter] = useState<string>("All");
  const [sortField, setSortField] = useState<SortField>("date_created");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");
  const [focusedIndex, setFocusedIndex] = useState<number>(-1);
  const tableRef = useRef<HTMLTableElement>(null);

  useEffect(() => {
    const interval = setInterval(() => {
      refreshBugs().catch(() => {
        addToast("Failed to refresh bugs", "error");
      });
    }, 300000);
    return () => clearInterval(interval);
  }, [refreshBugs, addToast]);

  useEffect(() => {
    if (error) {
      addToast(error, "error");
    }
  }, [error, addToast]);

  useEffect(() => {
    setFocusedIndex(-1);
  }, [statusFilter]);

  const filteredBugs = useMemo(() => {
    if (statusFilter === "All") return bugs;
    return bugs.filter((b) => b.status === statusFilter);
  }, [bugs, statusFilter]);

  const sortedBugs = useMemo(() => {
    return [...filteredBugs].sort((a, b) => {
      const aVal = a[sortField];
      const bVal = b[sortField];
      let cmp = 0;
      if (typeof aVal === "number" && typeof bVal === "number") {
        cmp = aVal - bVal;
      } else if (typeof aVal === "string" && typeof bVal === "string") {
        cmp = aVal.localeCompare(bVal);
      }
      return sortDirection === "asc" ? cmp : -cmp;
    });
  }, [filteredBugs, sortField, sortDirection]);

  const handleSort = (field: SortField) => {
    if (field === sortField) {
      setSortDirection((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  };

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (sortedBugs.length === 0) return;
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setFocusedIndex((prev) => Math.min(prev + 1, sortedBugs.length - 1));
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setFocusedIndex((prev) => Math.max(prev - 1, 0));
      } else if (e.key === "Enter" && focusedIndex >= 0) {
        const bug = sortedBugs[focusedIndex];
        if (bug) {
          selectBug(bug.id);
        }
      }
    },
    [focusedIndex, sortedBugs, selectBug],
  );

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <svg
          className="h-8 w-8 animate-spin text-blue-400"
          viewBox="0 0 24 24"
          fill="none"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
          />
        </svg>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center gap-4 p-8">
        <div className="rounded bg-red-900/50 px-4 py-2 text-red-300">
          {error}
        </div>
        <button
          className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-500"
          onClick={loadBugs}
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-gray-700 pb-3">
        <div className="flex items-center gap-2">
          {STATUS_FILTERS.map((status) => (
            <button
              key={status}
              className={`rounded px-3 py-1 text-sm ${
                statusFilter === status
                  ? "bg-blue-600 text-white"
                  : "bg-gray-700 text-gray-300 hover:bg-gray-600"
              }`}
              onClick={() => setStatusFilter(status)}
            >
              {status}
            </button>
          ))}
        </div>
        <button
          className="rounded bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-500"
          onClick={analyzeAll}
        >
          Analyze All
        </button>
      </div>
      <div className="flex-1 overflow-auto">
        <table
          ref={tableRef}
          className="w-full border-collapse text-sm"
          tabIndex={0}
          onKeyDown={handleKeyDown}
        >
          <thead className="sticky top-0 bg-gray-800">
            <tr>
              {SORTABLE_FIELDS.map((field) => (
                <th
                  key={field}
                  className="cursor-pointer px-3 py-2 text-left text-xs font-medium uppercase tracking-wide text-gray-400 hover:text-gray-200"
                  onClick={() => handleSort(field)}
                >
                  <span className="inline-flex items-center gap-1">
                    {SORT_LABELS[field]}
                    {sortField === field && (
                      <span className="text-blue-400">
                        {sortDirection === "asc" ? "↑" : "↓"}
                      </span>
                    )}
                  </span>
                </th>
              ))}
              <th className="px-3 py-2 text-left text-xs font-medium uppercase tracking-wide text-gray-400">
                Tags
              </th>
              <th className="px-3 py-2 text-left text-xs font-medium uppercase tracking-wide text-gray-400">
                Triage Status
              </th>
              <th className="px-3 py-2" />
            </tr>
          </thead>
          <tbody>
            {sortedBugs.map((bug, index) => (
              <BugRow
                key={bug.id}
                bug={bug}
                triageStatus={
                  triageStatuses.get(bug.id) ?? TriageStatus.NOT_STARTED
                }
                isSelected={selectedBugId === bug.id}
                isFocused={index === focusedIndex}
                onClick={() => {
                  setFocusedIndex(index);
                  selectBug(bug.id);
                }}
                onAnalyze={() => analyzeBug(bug.id)}
              />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
