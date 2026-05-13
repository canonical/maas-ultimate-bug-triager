import { useState, useRef, useEffect } from "react";
import type { Action } from "../types";
import { ActionType } from "../types";
import { TriageStatus } from "../types";
import ActionCard from "./ActionCard";

const ACTION_TYPE_OPTIONS: { value: ActionType; label: string }[] = [
  { value: ActionType.ADD_COMMENT, label: "Add Comment" },
  { value: ActionType.SET_STATUS, label: "Set Status" },
  { value: ActionType.SET_IMPORTANCE, label: "Set Importance" },
  { value: ActionType.ADD_TAG, label: "Add Tag" },
  { value: ActionType.REMOVE_TAG, label: "Remove Tag" },
];

function createDefaultAction(type: ActionType): Action {
  switch (type) {
    case ActionType.ADD_COMMENT:
      return { type, content: "" };
    case ActionType.SET_STATUS:
      return { type, status: "New" };
    case ActionType.SET_IMPORTANCE:
      return { type, importance: "Undecided" };
    case ActionType.ADD_TAG:
      return { type, tag: "" };
    case ActionType.REMOVE_TAG:
      return { type, tag: "" };
  }
}

interface ActionEditorProps {
  actions: Action[];
  aiActionCount: number;
  triageStatus: TriageStatus;
  onEditAction: (index: number, updated: Action) => void;
  onRemoveAction: (index: number) => void;
  onAddAction: (action: Action) => void;
  onApplyActions: () => Promise<void>;
}

export default function ActionEditor({
  actions,
  aiActionCount,
  triageStatus,
  onEditAction,
  onRemoveAction,
  onAddAction,
  onApplyActions,
}: ActionEditorProps) {
  const [showAddMenu, setShowAddMenu] = useState(false);
  const [applying, setApplying] = useState(false);
  const addMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (
        addMenuRef.current &&
        !addMenuRef.current.contains(e.target as Node)
      ) {
        setShowAddMenu(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleAddAction = (type: ActionType) => {
    onAddAction(createDefaultAction(type));
    setShowAddMenu(false);
  };

  const handleApply = async () => {
    setApplying(true);
    try {
      await onApplyActions();
    } catch {
      // Error handled via toast
    } finally {
      setApplying(false);
    }
  };

  const isDisabled =
    actions.length === 0 ||
    triageStatus === TriageStatus.APPLIED ||
    applying;

  return (
    <div className="space-y-3">
      {actions.map((action, index) => (
        <ActionCard
          key={index}
          action={action}
          isAiSuggested={index < aiActionCount}
          onChange={(updated) => onEditAction(index, updated)}
          onRemove={() => onRemoveAction(index)}
        />
      ))}

      <div className="relative" ref={addMenuRef}>
        <button
          className="flex w-full items-center justify-center gap-1 rounded border border-dashed border-gray-600 px-3 py-2 text-sm text-gray-400 hover:border-gray-500 hover:text-gray-300"
          onClick={() => setShowAddMenu(!showAddMenu)}
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
              d="M12 4v16m8-8H4"
            />
          </svg>
          Add Action
        </button>
        {showAddMenu && (
          <div className="absolute left-0 right-0 top-full z-10 mt-1 rounded border border-gray-700 bg-gray-800 py-1 shadow-lg">
            {ACTION_TYPE_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                className="block w-full px-3 py-2 text-left text-sm text-gray-300 hover:bg-gray-700"
                onClick={() => handleAddAction(opt.value)}
              >
                {opt.label}
              </button>
            ))}
          </div>
        )}
      </div>

      <button
        className="w-full rounded bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
        onClick={handleApply}
        disabled={isDisabled}
      >
        {applying ? (
          <span className="inline-flex items-center gap-2">
            <svg
              className="h-4 w-4 animate-spin"
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
            Applying...
          </span>
        ) : (
          "Apply Actions"
        )}
      </button>
    </div>
  );
}
