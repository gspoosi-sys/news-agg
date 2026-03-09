import { getNeedToKnow, getFeed } from "@/lib/api";
import Header from "@/components/Header";
import NeedToKnow from "@/components/NeedToKnow";
import PositiveFeed from "@/components/PositiveFeed";

export const revalidate = 300; // ISR: revalidate every 5 minutes

export default async function HomePage() {
  const [needToKnow, feed] = await Promise.allSettled([getNeedToKnow(), getFeed(1, 20)]);

  const politicalArticles =
    needToKnow.status === "fulfilled" ? needToKnow.value.articles : [];
  const feedData =
    feed.status === "fulfilled"
      ? feed.value
      : { articles: [], total: 0, page: 1, limit: 20 };

  return (
    <>
      <Header />
      <main className="max-w-4xl mx-auto px-4 py-6">
        <NeedToKnow articles={politicalArticles} />
        <PositiveFeed initialData={feedData} />
      </main>
    </>
  );
}
