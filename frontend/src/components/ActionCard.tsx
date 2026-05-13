import type { Action } from "../types";
import { ActionType } from "../types";

const VALID_STATUSES = [
  "New",
  "Incomplete",
  "Triaged",
  "Invalid",
  "Won't Fix",
  "Opinion",
  "Confirmed",
];

const VALID_IMPORTANCES = [
  "Undecided",
  "Low",
  "Medium",
  "High",
  "Critical",
  "Wishlist",
];

const ACTION_LABELS: Record<ActionType, string> = {
  [ActionType.ADD_COMMENT]: "Add Comment",
  [ActionType.SET_STATUS]: "Set Status",
  [ActionType.SET_IMPORTANCE]: "Set Importance",
  [ActionType.ADD_TAG]: "Add Tag",
  [ActionType.REMOVE_TAG]: "Remove Tag",
};

interface ActionCardProps {
  action: Action;
  isAiSuggested: boolean;
  onChange: (updated: Action) => void;
  onRemove: () => void;
}

export default function ActionCard({
  action,
  isAiSuggested,
  onChange,
  onRemove,
}: ActionCardProps) {
  const borderColor = isAiSuggested
    ? "border-l-blue-500"
    : "border-l-orange-500";

  return (
    <div
      className={`relative rounded border border-gray-700 border-l-4 bg-gray-800 p-4 ${borderColor}`}
    >
      <div className="flex items-start justify-between">
        <h4 className="text-sm font-medium text-white">
          {ACTION_LABELS[action.type]}
        </h4>
        <button
          className="text-gray-400 hover:text-red-400"
          onClick={onRemove}
        >
          <svg
            className="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>

      <div className="mt-2">
        {action.type === ActionType.ADD_COMMENT && (
          <textarea
            className="w-full rounded border border-gray-600 bg-gray-900 p-2 text-sm text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none"
            rows={4}
            value={action.content}
            onChange={(e) =>
              onChange({ ...action, content: e.target.value })
            }
            placeholder="Enter comment..."
          />
        )}

        {action.type === ActionType.SET_STATUS && (
          <select
            className="w-full rounded border border-gray-600 bg-gray-900 p-2 text-sm text-white focus:border-blue-500 focus:outline-none"
            value={action.status}
            onChange={(e) =>
              onChange({ ...action, status: e.target.value })
            }
          >
            {VALID_STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        )}

        {action.type === ActionType.SET_IMPORTANCE && (
          <select
            className="w-full rounded border border-gray-600 bg-gray-900 p-2 text-sm text-white focus:border-blue-500 focus:outline-none"
            value={action.importance}
            onChange={(e) =>
              onChange({ ...action, importance: e.target.value })
            }
          >
            {VALID_IMPORTANCES.map((imp) => (
              <option key={imp} value={imp}>
                {imp}
              </option>
            ))}
          </select>
        )}

        {action.type === ActionType.ADD_TAG && (
          <input
            className="w-full rounded border border-gray-600 bg-gray-900 p-2 text-sm text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none"
            type="text"
            value={action.tag}
            onChange={(e) =>
              onChange({ ...action, tag: e.target.value })
            }
            placeholder="Enter tag..."
          />
        )}

        {action.type === ActionType.REMOVE_TAG && (
          <input
            className="w-full rounded border border-gray-600 bg-gray-900 p-2 text-sm text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none"
            type="text"
            value={action.tag}
            onChange={(e) =>
              onChange({ ...action, tag: e.target.value })
            }
            placeholder="Enter tag to remove..."
          />
        )}
      </div>
    </div>
  );
}
