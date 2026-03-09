import Link from "next/link";
import type { Article } from "@/lib/api";

interface Props {
  article: Article;
  variant?: "political" | "positive";
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "";
  try {
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date(dateStr));
  } catch {
    return "";
  }
}

export default function ArticleCard({ article, variant = "positive" }: Props) {
  const isPolitical = variant === "political";

  return (
    <Link href={`/article/${article.id}`} className="block group">
      <article
        className={`rounded-xl border p-4 transition-all duration-200 group-hover:shadow-md ${
          isPolitical
            ? "bg-gray-50 border-gray-200 group-hover:border-gray-300"
            : "bg-white border-gray-100 group-hover:border-green-200"
        }`}
      >
        <div className="flex gap-3">
          {article.image_url && !isPolitical && (
            <div className="flex-shrink-0">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={article.image_url}
                alt=""
                className="w-20 h-20 object-cover rounded-lg bg-gray-100"
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = "none";
                }}
              />
            </div>
          )}

          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2 mb-1.5">
              <span
                className={`inline-block text-xs font-medium px-2 py-0.5 rounded-full ${
                  isPolitical
                    ? "bg-slate-200 text-slate-600"
                    : "bg-emerald-100 text-emerald-700"
                }`}
              >
                {article.source}
              </span>
              {article.published_at && (
                <span className="text-xs text-gray-400 flex-shrink-0">
                  {formatDate(article.published_at)}
                </span>
              )}
            </div>

            <h3
              className={`font-semibold text-sm leading-snug mb-1.5 line-clamp-2 ${
                isPolitical ? "text-gray-700" : "text-gray-900"
              }`}
            >
              {article.title}
            </h3>

            <p className={`text-sm leading-relaxed line-clamp-3 ${
              isPolitical ? "text-gray-500" : "text-gray-600"
            }`}>
              {article.tldr}
            </p>
          </div>
        </div>
      </article>
    </Link>
  );
}
