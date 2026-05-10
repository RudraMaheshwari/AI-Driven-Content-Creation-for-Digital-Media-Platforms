import { API_BASE, ContentResponse, resolveImageUrl } from "@/lib/api";

async function loadHistory(): Promise<ContentResponse[]> {
  try {
    const res = await fetch(`${API_BASE}/history?limit=60`, { cache: "no-store" });
    if (!res.ok) return [];
    const data = await res.json();
    return data.items as ContentResponse[];
  } catch {
    return [];
  }
}

export default async function HistoryPage() {
  const items = await loadHistory();
  return (
    <div className="space-y-8">
      <section className="space-y-3">
        <span className="eyebrow">Archive</span>
        <h1 className="font-serif text-4xl tracking-tight">Past compositions</h1>
        <p className="max-w-2xl text-base text-ink-700">
          Every piece composed in this studio, with its illustration and editor scores.
        </p>
      </section>

      {items.length === 0 ? (
        <div className="deck p-8 text-sm text-ink-500">
          Nothing yet. Head to <a className="underline" href="/">the studio</a> and compose something.
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          {items.map((item) => {
            const imageUrl = resolveImageUrl(item.image_url);
            const preview =
              item.final_output && item.final_output.length > 280
                ? item.final_output.slice(0, 280) + "…"
                : item.final_output;
            return (
              <article key={item.id} className="deck overflow-hidden">
                <div className="aspect-[16/9] w-full bg-paper-100">
                  {imageUrl ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={imageUrl}
                      alt={item.image_prompt || item.original_prompt}
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    <div className="flex h-full w-full items-center justify-center text-xs text-ink-300">
                      no illustration
                    </div>
                  )}
                </div>
                <div className="space-y-3 p-6">
                  <div className="flex flex-wrap items-center gap-2 text-[11px]">
                    <span className="eyebrow">{item.platform}</span>
                    <span className="tag">{item.content_type}</span>
                    <span className="tag">{item.tone}</span>
                    {item.quality_score !== null && (
                      <span className="tag-accent">
                        q {item.quality_score?.toFixed(2)}
                      </span>
                    )}
                    <span className="ml-auto text-ink-500">
                      {new Date(item.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <p className="text-xs italic text-ink-500 line-clamp-2">
                    {item.original_prompt}
                  </p>
                  <div className="article-body text-[15px] leading-[1.65]">
                    {preview || (
                      <span className="text-ink-300">{item.status}</span>
                    )}
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}
