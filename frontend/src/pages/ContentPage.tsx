import { useEffect, useState } from "react";

import { Card, SectionTitle } from "../components/ui";
import { api } from "../lib/api";
import type { ContentItem } from "../types";

function ContentPage() {
  const [items, setItems] = useState<ContentItem[]>([]);
  useEffect(() => {
    api<ContentItem[]>("/content").then(setItems).catch(console.error);
  }, []);
  return (
    <>
      <SectionTitle title="Content" subtitle="Detected pages and articles ready for AI post generation." />
      <div className="grid gap-3">
        {items.map((item) => (
          <Card key={item.id ?? item._id}>
            <h3 className="font-semibold text-slate-950">{item.title}</h3>
            <p className="mt-1 text-sm text-slate-600">{item.meta_description}</p>
            <p className="mt-3 text-xs text-brand-700">{item.canonical_url}</p>
          </Card>
        ))}
      </div>
    </>
  );
}

export default ContentPage;
