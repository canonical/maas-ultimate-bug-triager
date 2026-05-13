import type { BugSummary } from "../types";
import { TriageStatus } from "../types";

interface BugRowProps {
  bug: BugSummary;
  triageStatus: TriageStatus;
  isSelected: boolean;
  isFocused: boolean;
  onClick: () => void;
  onAnalyze: () => void;
}

function TriageBadge({ status }: { status: TriageStatus }) {
  switch (status) {
    case TriageStatus.NOT_STARTED:
      return (
        <span className="rounded bg-gray-600 px-2 py-0.5 text-xs text-gray-200">
          Not Started
        </span>
      );
    case TriageStatus.ANALYZING:
      return (
        <span className="inline-flex items-center gap-1 rounded bg-blue-600 px-2 py-0.5 text-xs text-white">
          <svg
            className="h-3 w-3 animate-spin"
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
          Analyzing...
        </span>
      );
    case TriageStatus.READY:
      return (
        <span className="rounded bg-green-600 px-2 py-0.5 text-xs text-white">
          Ready
        </span>
      );
    case TriageStatus.APPLIED:
      return (
        <span className="rounded bg-green-800 px-2 py-0.5 text-xs text-white">
          Applied
        </span>
      );
    case TriageStatus.ERROR:
      return (
        <span className="rounded bg-red-600 px-2 py-0.5 text-xs text-white">
          Error
        </span>
      );
  }
}

export default function BugRow({
  bug,
  triageStatus,
  isSelected,
  isFocused,
  onClick,
  onAnalyze,
}: BugRowProps) {
  return (
    <tr
      className={`cursor-pointer border-b border-gray-700 hover:bg-gray-700 ${isSelected ? "bg-gray-700" : ""} ${isFocused ? "ring-1 ring-inset ring-blue-500" : ""}`}
      onClick={onClick}
    >
      <td className="px-3 py-2">
        <a
          href={`https://bugs.launchpad.net/maas/+bug/${bug.id}`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-400 hover:underline"
          onClick={(e) => e.stopPropagation()}
        >
          {bug.id}
        </a>
      </td>
      <td className="max-w-xs truncate px-3 py-2">{bug.title}</td>
      <td className="px-3 py-2">{bug.status}</td>
      <td className="px-3 py-2">{bug.importance}</td>
      <td className="px-3 py-2">{bug.owner}</td>
      <td className="whitespace-nowrap px-3 py-2">
        {new Date(bug.date_created).toLocaleDateString()}
      </td>
      <td className="px-3 py-2">
        <div className="flex flex-wrap gap-1">
          {bug.tags.map((tag) => (
            <span
              key={tag}
              className="rounded bg-gray-600 px-1.5 py-0.5 text-xs text-gray-300"
            >
              {tag}
            </span>
          ))}
        </div>
      </td>
      <td className="px-3 py-2">
        <TriageBadge status={triageStatus} />
      </td>
      <td className="px-3 py-2">
        <button
          className="rounded bg-blue-600 px-2 py-1 text-xs text-white hover:bg-blue-500 disabled:opacity-50"
          onClick={(e) => {
            e.stopPropagation();
            onAnalyze();
          }}
          disabled={triageStatus === TriageStatus.ANALYZING}
        >
          Analyze
        </button>
      </td>
    </tr>
  );
}
