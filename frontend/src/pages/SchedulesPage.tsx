import { useEffect, useState } from "react";

import { Button, Card, Input, SectionTitle, Select } from "../components/ui";
import { api } from "../lib/api";
import type { GeneratedPost, ScheduledPost, SocialAccount } from "../types";

function SchedulesPage() {
  const [items, setItems] = useState<ScheduledPost[]>([]);
  const [posts, setPosts] = useState<GeneratedPost[]>([]);
  const [accounts, setAccounts] = useState<SocialAccount[]>([]);
  const [form, setForm] = useState({ generated_post_id: "", social_account_id: "", mode: "specific", scheduled_for: "", recurring_cron: "" });
  const [message, setMessage] = useState("");
  const selectedPost = posts.find((post) => (post.id ?? post._id) === form.generated_post_id);
  const matchingAccounts = selectedPost ? accounts.filter((account) => account.platform === selectedPost.platform) : accounts;
  async function load() {
    const [schedules, generated, socialAccounts] = await Promise.all([
      api<ScheduledPost[]>("/schedules"),
      api<GeneratedPost[]>("/ai/generated-posts"),
      api<SocialAccount[]>("/social-accounts")
    ]);
    setItems(schedules);
    setPosts(generated);
    setAccounts(socialAccounts);
    setForm((current) => ({
      ...current,
      generated_post_id: current.generated_post_id || (generated[0]?.id ?? generated[0]?._id ?? ""),
      social_account_id: current.social_account_id || (socialAccounts[0]?.id ?? socialAccounts[0]?._id ?? "")
    }));
  }
  useEffect(() => {
    load().catch(console.error);
  }, []);
  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setMessage("");
    if (!form.generated_post_id) {
      setMessage("Generate at least one post in AI Studio first.");
      return;
    }
    if (!form.social_account_id) {
      setMessage("Connect a social account before scheduling.");
      return;
    }
    await api("/schedules", {
      method: "POST",
      body: JSON.stringify({
        generated_post_id: form.generated_post_id,
        social_account_id: form.social_account_id,
        mode: form.mode,
        scheduled_for: form.mode === "specific" && form.scheduled_for ? new Date(form.scheduled_for).toISOString() : null,
        recurring_cron: form.mode === "recurring" ? form.recurring_cron : null,
        approval_required: form.mode === "approval"
      })
    });
    setMessage("Post scheduled successfully.");
    await load();
  }
  return (
    <>
      <SectionTitle title="Scheduled Posts" subtitle="Immediate, specific-time, recurring, draft, approval, and auto-publish queue." />
      <Card className="mb-5">
        <form onSubmit={submit} className="grid gap-3 md:grid-cols-[1fr_1fr_150px_220px_auto]">
          <Select value={form.generated_post_id} onChange={(e) => {
            const post = posts.find((item) => (item.id ?? item._id) === e.target.value);
            const account = accounts.find((item) => item.platform === post?.platform);
            setForm({ ...form, generated_post_id: e.target.value, social_account_id: account?.id ?? account?._id ?? "" });
          }}>
            {posts.map((post) => (
              <option key={post.id ?? post._id} value={post.id ?? post._id}>
                {post.platform}: {post.text.slice(0, 70)}
              </option>
            ))}
          </Select>
          <Select value={form.social_account_id} onChange={(e) => setForm({ ...form, social_account_id: e.target.value })}>
            {matchingAccounts.map((account) => (
              <option key={account.id ?? account._id} value={account.id ?? account._id}>
                {account.platform}: {account.display_name}
              </option>
            ))}
          </Select>
          <Select value={form.mode} onChange={(e) => setForm({ ...form, mode: e.target.value })}>
            <option value="immediate">Immediate</option>
            <option value="specific">Specific</option>
            <option value="recurring">Recurring</option>
            <option value="draft">Draft</option>
            <option value="approval">Approval</option>
          </Select>
          {form.mode === "recurring" ? (
            <Input placeholder="Cron, e.g. 0 9 * * 1-5" value={form.recurring_cron} onChange={(e) => setForm({ ...form, recurring_cron: e.target.value })} required />
          ) : (
            <Input type="datetime-local" value={form.scheduled_for} onChange={(e) => setForm({ ...form, scheduled_for: e.target.value })} required={form.mode === "specific"} />
          )}
          <Button disabled={!form.generated_post_id || !form.social_account_id}>Schedule</Button>
        </form>
        {message ? <p className="mt-3 rounded-md bg-brand-50 px-3 py-2 text-sm font-medium text-brand-700">{message}</p> : null}
        {!accounts.length ? <p className="mt-3 text-sm text-slate-600">No connected social accounts yet. Add one from the Accounts tab to enable scheduling.</p> : null}
      </Card>
      <div className="grid gap-3">
        {items.map((item) => (
          <Card key={item.id ?? item._id} className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="font-semibold capitalize text-slate-950">{item.platform}</p>
              <p className="text-sm text-slate-600">{item.scheduled_for ? new Date(item.scheduled_for).toLocaleString() : item.mode}</p>
              {item.failure_reason ? <p className="mt-1 text-sm text-red-600">{item.failure_reason}</p> : null}
            </div>
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold capitalize text-slate-700">{item.status.replace("_", " ")}</span>
          </Card>
        ))}
      </div>
    </>
  );
}

export default SchedulesPage;
