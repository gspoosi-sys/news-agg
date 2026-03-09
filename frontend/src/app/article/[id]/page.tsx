import Link from "next/link";
import { notFound } from "next/navigation";
import { getArticle } from "@/lib/api";

export const revalidate = 600;

interface Props {
  params: { id: string };
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "";
  try {
    return new Intl.DateTimeFormat("en-US", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    }).format(new Date(dateStr));
  } catch {
    return "";
  }
}

function SentimentBadge({ score }: { score: number }) {
  if (score >= 0.5) return <span className="text-emerald-600 font-medium">Very Positive</span>;
  if (score >= 0.2) return <span className="text-green-600 font-medium">Positive</span>;
  if (score >= -0.2) return <span className="text-gray-500 font-medium">Neutral</span>;
  return <span className="text-amber-600 font-medium">Mixed</span>;
}

export default async function ArticlePage({ params }: Props) {
  const id = parseInt(params.id, 10);
  if (isNaN(id)) notFound();

  let article;
  try {
    article = await getArticle(id);
  } catch {
    notFound();
  }

  const isPolitical = article.category === "political";

  return (
    <div className="min-h-screen bg-[#f8f7f4]">
      <header className="bg-white/80 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-2xl mx-auto px-4 py-3 flex items-center gap-3">
          <Link
            href="/"
            className="text-gray-500 hover:text-gray-800 transition-colors text-sm flex items-center gap-1"
          >
            <span aria-hidden="true">←</span> Back
          </Link>
          <span className="text-gray-300">|</span>
          <span className="text-sm font-bold text-gray-800 tracking-tight">Balanced News</span>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-8">
        {/* Category badge */}
        <div className="flex items-center gap-2 mb-4">
          <span
            className={`text-xs font-medium px-2.5 py-1 rounded-full ${
              isPolitical
                ? "bg-slate-100 text-slate-600"
                : "bg-emerald-100 text-emerald-700"
            }`}
          >
            {isPolitical ? "Need to Know" : "Positive Story"}
          </span>
          <span className="text-xs text-gray-400">{article.source}</span>
          {article.published_at && (
            <>
              <span className="text-gray-300">·</span>
              <span className="text-xs text-gray-400">{formatDate(article.published_at)}</span>
            </>
          )}
        </div>

        {/* Title */}
        <h1 className="text-2xl font-bold text-gray-900 leading-tight mb-4">
          {article.title}
        </h1>

        {/* Image */}
        {article.image_url && !isPolitical && (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={article.image_url}
            alt=""
            className="w-full h-56 object-cover rounded-xl mb-6 bg-gray-100"
            onError={() => {}}
          />
        )}

        {/* TL;DR box */}
        <div
          className={`rounded-xl p-5 mb-6 ${
            isPolitical
              ? "bg-slate-50 border border-slate-200"
              : "bg-emerald-50 border border-emerald-100"
          }`}
        >
          <p className="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-2">
            AI Summary (TL;DR)
          </p>
          <p className="text-gray-700 leading-relaxed">{article.tldr}</p>
        </div>

        {/* Sentiment */}
        <div className="flex items-center gap-4 text-sm text-gray-500 mb-6">
          <span>
            Tone: <SentimentBadge score={article.sentiment_score} />
          </span>
        </div>

        {/* Original article link */}
        <div className="border-t border-gray-200 pt-6">
          <p className="text-sm text-gray-500 mb-3">Want the full story?</p>
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-gray-900 text-white text-sm font-medium rounded-lg hover:bg-gray-700 transition-colors"
          >
            Read original article
            <span aria-hidden="true">→</span>
          </a>
        </div>
      </main>
    </div>
  );
}
