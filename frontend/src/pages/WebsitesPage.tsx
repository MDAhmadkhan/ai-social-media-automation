import { useEffect, useState } from "react";

import { Button, Card, Input, SectionTitle, Select } from "../components/ui";
import { api } from "../lib/api";
import type { Website, WebsiteType } from "../types";

function WebsitesPage() {
  const [items, setItems] = useState<Website[]>([]);
  const [form, setForm] = useState({ name: "", url: "", type: "rss" as WebsiteType });
  const [scanningId, setScanningId] = useState<string | null>(null);
  const [message, setMessage] = useState("");

  async function load() {
    setItems(await api<Website[]>("/websites"));
  }
  useEffect(() => {
    load().catch(console.error);
  }, []);

  async function create(event: React.FormEvent) {
    event.preventDefault();
    setMessage("");
    try {
      await api("/websites", { method: "POST", body: JSON.stringify(form) });
      setForm({ name: "", url: "", type: "rss" });
      await load();
      setMessage("Website added. Use Scan to detect content.");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Unable to add website");
    }
  }

  async function scan(id: string) {
    setScanningId(id);
    setMessage("");
    try {
      const result = await api<{ message: string }>(`/websites/${id}/scan`, { method: "POST" });
      setMessage(result.message);
    } finally {
      setScanningId(null);
    }
  }

  return (
    <>
      <SectionTitle title="Websites" subtitle="Connect WordPress, RSS feeds, sitemaps, webhooks, and custom sources." />
      <Card>
        <form onSubmit={create} className="grid gap-3 md:grid-cols-[1fr_1fr_180px_auto]">
          <Input placeholder="Website name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          <Input placeholder="https://example.com/feed.xml" value={form.url} onChange={(e) => setForm({ ...form, url: e.target.value })} required />
          <Select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value as WebsiteType })}>
            <option value="wordpress">WordPress</option>
            <option value="rss">RSS Feed</option>
            <option value="custom">Custom</option>
            <option value="sitemap">Sitemap XML</option>
            <option value="webhook">Webhook</option>
          </Select>
          <Button>Add</Button>
        </form>
        {message ? <p className="mt-3 rounded-md bg-brand-50 px-3 py-2 text-sm font-medium text-brand-700">{message}</p> : null}
      </Card>
      <div className="mt-5 grid gap-3">
        {items.map((item) => (
          <Card key={item.id ?? item._id} className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 className="font-semibold text-slate-950">{item.name}</h3>
              <p className="text-sm text-slate-600">{item.url}</p>
            </div>
            <Button disabled={scanningId === (item.id ?? item._id)} onClick={() => scan((item.id ?? item._id)!)}>
              {scanningId === (item.id ?? item._id) ? "Scanning..." : "Scan"}
            </Button>
          </Card>
        ))}
      </div>
    </>
  );
}

export default WebsitesPage;
