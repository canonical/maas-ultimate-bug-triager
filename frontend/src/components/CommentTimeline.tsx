import { useState } from "react";
import type { Comment } from "../types";

interface CommentTimelineProps {
  comments: Comment[];
}

function CommentItem({ comment }: { comment: Comment }) {
  const [expanded, setExpanded] = useState(false);
  const lines = comment.content.split("\n");
  const isLong = lines.length > 5;
  const displayedLines = expanded ? lines : lines.slice(0, 5);
  const initial = comment.author.charAt(0).toUpperCase();

  return (
    <div className="flex gap-3">
      <div className="flex flex-col items-center">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-600 text-sm font-bold text-white">
          {initial}
        </div>
        <div className="flex-1 w-px bg-gray-700" />
      </div>
      <div className="flex-1 pb-4">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-white">
            {comment.author}
          </span>
          <span className="text-xs text-gray-400">
            {new Date(comment.date).toLocaleString()}
          </span>
        </div>
        <pre className="mt-1 whitespace-pre-wrap break-words text-sm text-gray-300">
          {displayedLines.join("\n")}
        </pre>
        {isLong && (
          <button
            className="mt-1 text-xs text-blue-400 hover:underline"
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? "Show less" : "Show more"}
          </button>
        )}
      </div>
    </div>
  );
}

export default function CommentTimeline({ comments }: CommentTimelineProps) {
  if (comments.length === 0) {
    return (
      <p className="text-sm text-gray-500">No comments yet.</p>
    );
  }

  return (
    <div className="space-y-0">
      {comments.map((comment, index) => (
        <CommentItem key={index} comment={comment} />
      ))}
    </div>
  );
}
