interface SkeletonProps {
  className?: string;
}

function SkeletonBlock({ className = "" }: SkeletonProps) {
  return (
    <div
      className={`animate-skeleton-pulse rounded bg-gray-700 ${className}`}
    />
  );
}

export function CommentsSkeleton() {
  return (
    <div className="space-y-0">
      {[1, 2, 3].map((i) => (
        <div key={i} className="flex gap-3">
          <div className="flex flex-col items-center">
            <SkeletonBlock className="h-8 w-8 shrink-0 rounded-full" />
            <div className="flex-1 w-px bg-gray-700" />
          </div>
          <div className="flex-1 pb-4">
            <div className="flex items-center gap-2">
              <SkeletonBlock className="h-4 w-24" />
              <SkeletonBlock className="h-3 w-32" />
            </div>
            <SkeletonBlock className="mt-2 h-4 w-full" />
            <SkeletonBlock className="mt-1 h-4 w-4/5" />
            <SkeletonBlock className="mt-1 h-4 w-3/5" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function AnalysisSkeleton() {
  return (
    <div className="rounded border border-gray-700 bg-gray-800 p-4">
      <SkeletonBlock className="h-4 w-3/4" />
      <SkeletonBlock className="mt-3 h-4 w-full" />
      <SkeletonBlock className="mt-2 h-4 w-full" />
      <SkeletonBlock className="mt-2 h-4 w-5/6" />
      <SkeletonBlock className="mt-2 h-4 w-2/3" />
    </div>
  );
}

export function DetailSkeleton() {
  return (
    <div className="space-y-6 animate-skeleton-pulse">
      {/* Title area */}
      <div>
        <SkeletonBlock className="h-7 w-3/4" />
        <div className="mt-2 flex items-center gap-2">
          <SkeletonBlock className="h-5 w-16" />
          <SkeletonBlock className="h-5 w-20" />
          <SkeletonBlock className="h-5 w-20" />
          <SkeletonBlock className="h-4 w-24" />
          <SkeletonBlock className="h-4 w-28" />
        </div>
        <div className="mt-3 rounded border border-gray-700 bg-gray-800 p-3">
          <SkeletonBlock className="h-4 w-full" />
          <SkeletonBlock className="mt-2 h-4 w-full" />
          <SkeletonBlock className="mt-2 h-4 w-5/6" />
          <SkeletonBlock className="mt-2 h-4 w-2/3" />
        </div>
      </div>
      {/* Comments */}
      <div>
        <SkeletonBlock className="h-6 w-28 mb-3" />
        <CommentsSkeleton />
      </div>
      {/* AI Analysis */}
      <div>
        <SkeletonBlock className="h-6 w-24 mb-3" />
        <AnalysisSkeleton />
      </div>
    </div>
  );
}
