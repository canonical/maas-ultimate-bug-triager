import { useEffect, useRef, useCallback } from "react";
import { useAppContext } from "../context/AppContext";
import { useBugAnalysis } from "../hooks/useBugAnalysis";
import { useToast } from "../hooks/useToast";
import { TriageStatus } from "../types";
import CommentTimeline from "./CommentTimeline";
import ActionEditor from "./ActionEditor";
import { CommentsSkeleton, AnalysisSkeleton, DetailSkeleton } from "./Skeleton";

function StatusBadge({ status }: { status: string }) {
  const colorMap: Record<string, string> = {
    New: "bg-blue-600",
    Incomplete: "bg-yellow-600",
    Triaged: "bg-green-600",
    Invalid: "bg-gray-600",
    "Won't Fix": "bg-red-600",
    Opinion: "bg-purple-600",
    Confirmed: "bg-green-700",
  };
  const color = colorMap[status] ?? "bg-gray-600";
  return (
    <span className={`rounded px-2 py-0.5 text-xs font-medium text-white ${color}`}>
      {status}
    </span>
  );
}

function ImportanceBadge({ importance }: { importance: string }) {
  const colorMap: Record<string, string> = {
    Critical: "bg-red-600",
    High: "bg-orange-600",
    Medium: "bg-yellow-600",
    Low: "bg-green-600",
    Undecided: "bg-gray-600",
    Wishlist: "bg-blue-600",
  };
  const color = colorMap[importance] ?? "bg-gray-600";
  return (
    <span className={`rounded px-2 py-0.5 text-xs font-medium text-white ${color}`}>
      {importance}
    </span>
  );
}

function ContentTypeBadge({ contentType }: { contentType: string }) {
  return (
    <span className="rounded bg-gray-600 px-2 py-0.5 text-xs text-gray-300">
      {contentType}
    </span>
  );
}

export default function BugTriageView() {
  const { selectedBugId, triageStatuses } = useAppContext();
  const { addToast } = useToast();
  const topRef = useRef<HTMLDivElement>(null);
  const {
    bugDetail,
    analysis,
    editedActions,
    loading,
    error,
    editAction,
    removeAction,
    addAction,
    applyActions,
  } = useBugAnalysis(selectedBugId);

  useEffect(() => {
    topRef.current?.scrollIntoView({ block: "start" });
  }, [selectedBugId]);

  const prevStatusRef = useRef<TriageStatus | undefined>(undefined);
  useEffect(() => {
    if (selectedBugId === null) return;
    const currentStatus =
      triageStatuses.get(selectedBugId) ?? TriageStatus.NOT_STARTED;
    if (
      currentStatus === TriageStatus.APPLIED &&
      prevStatusRef.current !== TriageStatus.APPLIED
    ) {
      addToast("Actions applied successfully", "success");
    }
    if (
      currentStatus === TriageStatus.ERROR &&
      prevStatusRef.current !== TriageStatus.ERROR
    ) {
      addToast("Failed to apply actions", "error");
    }
    prevStatusRef.current = currentStatus;
  }, [triageStatuses, selectedBugId, addToast]);

  const applyActionsWithToast = useCallback(async () => {
    try {
      await applyActions();
      addToast("Actions applied successfully", "success");
    } catch {
      addToast("Failed to apply actions", "error");
    }
  }, [applyActions, addToast]);

  if (selectedBugId === null) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-lg text-gray-500">Select a bug to triage</p>
      </div>
    );
  }

  if (loading && !bugDetail) {
    return <DetailSkeleton />;
  }

  if (error) {
    return (
      <div className="flex flex-col items-center gap-4 p-8">
        <div className="rounded bg-red-900/50 px-4 py-2 text-red-300">
          {error}
        </div>
        <button
          className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-500"
          onClick={() => window.location.reload()}
        >
          Retry
        </button>
      </div>
    );
  }

  if (!bugDetail) {
    return null;
  }

  const triageStatus = triageStatuses.get(selectedBugId) ?? TriageStatus.NOT_STARTED;
  const aiActionCount = analysis?.suggested_actions.length ?? 0;

  return (
    <div className="space-y-6">
      <div ref={topRef} />
      <div>
        <h2 className="text-xl font-bold text-white">{bugDetail.title}</h2>
        <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-gray-400">
          <a
            href={`https://bugs.launchpad.net/maas/+bug/${bugDetail.id}`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-400 hover:underline"
          >
            #{bugDetail.id}
          </a>
          <StatusBadge status={bugDetail.status} />
          <ImportanceBadge importance={bugDetail.importance} />
          <span>by {bugDetail.owner}</span>
          <span>{new Date(bugDetail.date_created).toLocaleDateString()}</span>
        </div>
        {bugDetail.tags.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {bugDetail.tags.map((tag) => (
              <span
                key={tag}
                className="rounded bg-gray-700 px-2 py-0.5 text-xs text-gray-300"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
        <div className="mt-3 max-h-64 overflow-y-auto rounded border border-gray-700 bg-gray-800 p-3">
          <pre className="whitespace-pre-wrap break-words text-sm text-gray-300">
            {bugDetail.description}
          </pre>
        </div>
      </div>

      <div>
        <h3 className="mb-3 text-lg font-semibold text-white">Comments</h3>
        {loading ? <CommentsSkeleton /> : <CommentTimeline comments={bugDetail.comments} />}
      </div>

      <div>
        <h3 className="mb-3 text-lg font-semibold text-white">Attachments</h3>
        {bugDetail.attachments.length === 0 ? (
          <p className="text-sm text-gray-500">No attachments.</p>
        ) : (
          <ul className="space-y-2">
            {bugDetail.attachments.map((att) => (
              <li key={att.id} className="flex items-center gap-2">
                <span className="text-sm text-gray-300">{att.title}</span>
                <ContentTypeBadge contentType={att.content_type} />
                <span className="text-xs text-gray-500">
                  ({(att.size / 1024).toFixed(1)} KB)
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div>
        <h3 className="mb-3 text-lg font-semibold text-white">AI Analysis</h3>
        {loading ? (
          <AnalysisSkeleton />
        ) : analysis ? (
          <div className="rounded border border-gray-700 bg-gray-800 p-4">
            <p className="whitespace-pre-wrap text-sm text-gray-300">
              {analysis.reasoning}
            </p>
          </div>
        ) : (
          <p className="text-sm text-gray-500">No analysis available.</p>
        )}
      </div>

      {analysis && (
        <div>
          <h3 className="mb-3 text-lg font-semibold text-white">Suggested Actions</h3>
          <ActionEditor
            actions={editedActions}
            aiActionCount={aiActionCount}
            triageStatus={triageStatus}
            onEditAction={editAction}
            onRemoveAction={removeAction}
            onAddAction={addAction}
            onApplyActions={applyActionsWithToast}
          />
        </div>
      )}
    </div>
  );
}
