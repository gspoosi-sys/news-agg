const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface Article {
  id: number;
  title: string;
  source: string;
  url: string;
  image_url: string | null;
  category: string;
  sentiment_score: number;
  tldr: string;
  published_at: string | null;
}

export interface ArticleDetail extends Article {
  description: string | null;
}

export interface FeedResponse {
  articles: Article[];
  total: number;
  page: number;
  limit: number;
}

export interface NeedToKnowResponse {
  articles: Article[];
}

export async function getNeedToKnow(): Promise<NeedToKnowResponse> {
  const res = await fetch(`${API_BASE}/api/need-to-know`, { next: { revalidate: 300 } });
  if (!res.ok) throw new Error("Failed to fetch Need to Know");
  return res.json();
}

export async function getFeed(page = 1, limit = 20): Promise<FeedResponse> {
  const res = await fetch(`${API_BASE}/api/feed?page=${page}&limit=${limit}`, {
    next: { revalidate: 300 },
  });
  if (!res.ok) throw new Error("Failed to fetch feed");
  return res.json();
}

export async function getArticle(id: number): Promise<ArticleDetail> {
  const res = await fetch(`${API_BASE}/api/articles/${id}`, { next: { revalidate: 600 } });
  if (!res.ok) throw new Error("Article not found");
  return res.json();
}
