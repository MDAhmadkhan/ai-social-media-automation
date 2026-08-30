import { useEffect, useState } from "react";

import { Button, Card, Input, SectionTitle, Select } from "../components/ui";
import { api } from "../lib/api";
import type { Platform, SocialAccount } from "../types";

function AccountsPage() {
  const [items, setItems] = useState<SocialAccount[]>([]);
  const [form, setForm] = useState({ platform: "facebook" as Platform, display_name: "", external_id: "", access_token: "" });
  const externalIdLabel = form.platform === "facebook"
    ? "Facebook Page ID"
    : form.platform === "instagram"
      ? "Instagram Business Account ID"
      : form.platform === "website"
        ? "Website API endpoint or site ID"
        : "External page/channel/org ID";
  const tokenLabel = form.platform === "website" ? "Website API token" : "Access token";
  async function load() {
    setItems(await api<SocialAccount[]>("/social-accounts"));
  }
  useEffect(() => {
    load().catch(console.error);
  }, []);
  async function submit(event: React.FormEvent) {
    event.preventDefault();
    await api("/social-accounts", { method: "POST", body: JSON.stringify(form) });
    setForm({ platform: "facebook", display_name: "", external_id: "", access_token: "" });
    await load();
  }
  return (
    <>
      <SectionTitle title="Connected Accounts" subtitle="Connect Facebook Pages, Instagram Business accounts, websites, and other publishing targets." />
      <Card className="mb-5">
        <div className="mb-4 grid gap-3 md:grid-cols-2">
          <div className="rounded-md bg-blue-50 p-3 text-sm text-blue-900">
            <p className="font-semibold">Facebook Page</p>
            <p className="mt-1">Use a Page access token with `pages_manage_posts`, `pages_read_engagement`, and `pages_show_list` permissions.</p>
          </div>
          <div className="rounded-md bg-pink-50 p-3 text-sm text-pink-900">
            <p className="font-semibold">Instagram Business</p>
            <p className="mt-1">Use the connected Instagram Business Account ID and a valid Meta token. Instagram publishing requires an image URL reachable from Meta.</p>
          </div>
        </div>
        <form onSubmit={submit} className="grid gap-3 md:grid-cols-[160px_1fr_1fr_1fr_auto]">
          <Select value={form.platform} onChange={(e) => setForm({ ...form, platform: e.target.value as Platform })}>
            {["website", "facebook", "instagram", "linkedin", "twitter", "threads", "pinterest", "telegram"].map((item) => <option key={item}>{item}</option>)}
          </Select>
          <Input placeholder="Display name" value={form.display_name} onChange={(e) => setForm({ ...form, display_name: e.target.value })} required />
          <Input placeholder={externalIdLabel} value={form.external_id} onChange={(e) => setForm({ ...form, external_id: e.target.value })} required />
          <Input placeholder={tokenLabel} value={form.access_token} onChange={(e) => setForm({ ...form, access_token: e.target.value })} required />
          <Button>Add</Button>
        </form>
      </Card>
      <div className="mt-5 grid gap-3">
        {items.map((item) => (
          <Card key={item.id ?? item._id}>
            <p className="font-semibold text-slate-950">{item.display_name}</p>
            <p className="text-sm capitalize text-slate-600">{item.platform} · {item.external_id}</p>
          </Card>
        ))}
      </div>
    </>
  );
}

export default AccountsPage;
