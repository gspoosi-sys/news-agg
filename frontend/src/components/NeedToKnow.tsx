"use client";

import { useState } from "react";
import type { Article } from "@/lib/api";
import ArticleCard from "./ArticleCard";

interface Props {
  articles: Article[];
}

export default function NeedToKnow({ articles }: Props) {
  const [open, setOpen] = useState(true);

  if (articles.length === 0) return null;

  return (
    <section className="mb-8">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between mb-3 group"
        aria-expanded={open}
      >
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-slate-400" aria-hidden="true" />
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">
            Need to Know
          </h2>
          <span className="text-xs text-gray-400 font-normal normal-case">
            ({articles.length} key {articles.length === 1 ? "story" : "stories"})
          </span>
        </div>
        <span className="text-gray-400 text-xs group-hover:text-gray-600 transition-colors">
          {open ? "Hide" : "Show"}
        </span>
      </button>

      {open && (
        <div className="space-y-2">
          <p className="text-xs text-gray-400 mb-3">
            Objective summaries of major political and global events — no sensationalism.
          </p>
          {articles.map((article) => (
            <ArticleCard key={article.id} article={article} variant="political" />
          ))}
        </div>
      )}
    </section>
  );
}
