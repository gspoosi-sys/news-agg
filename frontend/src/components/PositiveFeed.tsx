"use client";

import { useState } from "react";
import useSWR from "swr";
import type { FeedResponse } from "@/lib/api";
import ArticleCard from "./ArticleCard";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const fetcher = (url: string) => fetch(url).then((r) => r.json());

function CardSkeleton() {
  return (
    <div className="rounded-xl border border-gray-100 bg-white p-4 animate-pulse">
      <div className="flex gap-3">
        <div className="w-20 h-20 bg-gray-200 rounded-lg flex-shrink-0" />
        <div className="flex-1 space-y-2">
          <div className="h-3 bg-gray-200 rounded w-1/3" />
          <div className="h-4 bg-gray-200 rounded w-3/4" />
          <div className="h-3 bg-gray-200 rounded w-full" />
          <div className="h-3 bg-gray-200 rounded w-5/6" />
        </div>
      </div>
    </div>
  );
}

export default function PositiveFeed({ initialData }: { initialData: FeedResponse }) {
  const [page, setPage] = useState(1);
  const [allArticles, setAllArticles] = useState(initialData.articles);
  const [hasMore, setHasMore] = useState(initialData.total > initialData.limit);
  const [loading, setLoading] = useState(false);

  const loadMore = async () => {
    if (loading || !hasMore) return;
    setLoading(true);
    try {
      const nextPage = page + 1;
      const res = await fetch(`${API_BASE}/api/feed?page=${nextPage}&limit=20`);
      const data: FeedResponse = await res.json();
      setAllArticles((prev) => [...prev, ...data.articles]);
      setPage(nextPage);
      setHasMore(nextPage * data.limit < data.total);
    } catch {
      // silently fail — user can retry
    } finally {
      setLoading(false);
    }
  };

  return (
    <section>
      <div className="flex items-center gap-2 mb-3">
        <span className="w-2 h-2 rounded-full bg-emerald-400" aria-hidden="true" />
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">
          Good News Feed
        </h2>
      </div>

      {allArticles.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p className="text-4xl mb-3">🌱</p>
          <p className="text-sm">Positive stories are being collected. Check back soon!</p>
        </div>
      ) : (
        <div className="space-y-3">
          {allArticles.map((article) => (
            <ArticleCard key={article.id} article={article} variant="positive" />
          ))}

          {loading && (
            <>
              <CardSkeleton />
              <CardSkeleton />
            </>
          )}

          {hasMore && !loading && (
            <button
              onClick={loadMore}
              className="w-full py-3 text-sm text-emerald-600 font-medium hover:text-emerald-700 hover:bg-emerald-50 rounded-xl border border-emerald-100 transition-colors"
            >
              Load more stories
            </button>
          )}

          {!hasMore && allArticles.length > 0 && (
            <p className="text-center text-xs text-gray-400 py-4">
              You&apos;re all caught up for now.
            </p>
          )}
        </div>
      )}
    </section>
  );
}
