import { useEffect, useState } from "react";

import { Button, Card, Input, SectionTitle, Select, Textarea } from "../components/ui";
import { api } from "../lib/api";
import type { ContentItem, GeneratedPost, Platform, SocialAccount } from "../types";

const platforms: Platform[] = ["facebook", "instagram"];

function AIStudioPage() {
  const [content, setContent] = useState<ContentItem[]>([]);
  const [accounts, setAccounts] = useState<SocialAccount[]>([]);
  const [contentId, setContentId] = useState("");
  const [selected, setSelected] = useState<Platform[]>(["facebook"]);
  const [promptForm, setPromptForm] = useState({
    title: "",
    prompt: "",
    schedule_enabled: false,
    scheduled_for: "",
    social_account_id: "",
    schedule_all_accounts: true,
    gap_hours: 24
  });
  const [posts, setPosts] = useState<GeneratedPost[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    api<ContentItem[]>("/content").then((items) => {
      setContent(items);
      setContentId((items[0]?.id ?? items[0]?._id) || "");
    });
    api<SocialAccount[]>("/social-accounts").then((items) => {
      setAccounts(items);
      setPromptForm((current) => ({ ...current, social_account_id: current.social_account_id || (items[0]?.id ?? items[0]?._id ?? "") }));
    }).catch(console.error);
  }, []);

  async function generate() {
    setLoading(true);
    setMessage("");
    try {
      setPosts(
        await api<GeneratedPost[]>("/ai/generate", {
          method: "POST",
          body: JSON.stringify({ content_item_id: contentId, platforms: selected, generate_images: false })
        })
      );
      setMessage("Posts generated successfully.");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Unable to generate posts");
    } finally {
      setLoading(false);
    }
  }

  async function generateAll() {
    setLoading(true);
    setMessage("");
    try {
      const result = await api<{ generated_count: number; errors: Array<{ title: string; error: string }>; posts: GeneratedPost[] }>("/ai/generate-bulk", {
        method: "POST",
        body: JSON.stringify({ platforms: selected, generate_images: false, limit: 50 })
      });
      setPosts(result.posts);
      setMessage(`Generated ${result.generated_count} posts${result.errors.length ? `, ${result.errors.length} items failed` : ""}.`);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Unable to generate posts");
    } finally {
      setLoading(false);
    }
  }

  async function generateFromPrompt(event: React.FormEvent) {
    event.preventDefault();
    await createSingleFromPrompt();
  }

  async function createSingleFromPrompt() {
    setLoading(true);
    setMessage("");
    try {
      const created = await api<GeneratedPost[]>("/ai/generate-from-prompt", {
        method: "POST",
        body: JSON.stringify({
          title: promptForm.title || null,
          prompt: promptForm.prompt || `Create a professional Facebook post about: ${promptForm.title}`,
          image_prompt: null,
          platforms: selected,
          generate_images: false
        })
      });
      setPosts(created);
      if (promptForm.schedule_enabled) {
        const accountsToUse = promptForm.schedule_all_accounts
          ? accounts.filter((account) => created.some((post) => post.platform === account.platform))
          : accounts.filter((account) => (account.id ?? account._id) === promptForm.social_account_id);
        if (!accountsToUse.length) {
          setMessage("Post created. Connect an account first, then schedule it from Schedules.");
          return;
        }
        let scheduledCount = 0;
        for (const account of accountsToUse) {
          const post = created.find((item) => item.platform === account.platform);
          if (post) {
            await api("/schedules", {
              method: "POST",
              body: JSON.stringify({
                generated_post_id: post.id ?? post._id,
                social_account_id: account.id ?? account._id,
                mode: promptForm.scheduled_for ? "specific" : "draft",
                scheduled_for: promptForm.scheduled_for ? new Date(promptForm.scheduled_for).toISOString() : null,
                recurring_cron: null,
                approval_required: false
              })
            });
            scheduledCount += 1;
          }
        }
        setMessage(`Prompt post created. ${scheduledCount} matching account${scheduledCount === 1 ? "" : "s"} ${promptForm.scheduled_for ? "scheduled" : "saved as draft"}.`);
      } else {
        setMessage("Prompt post created. You can schedule it from Schedules.");
      }
      setPromptForm((current) => ({ ...current, title: "", prompt: "" }));
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Unable to create prompt post");
    } finally {
      setLoading(false);
    }
  }

  async function generateTopicPack(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    setMessage("");
    try {
      const created = await api<GeneratedPost[]>("/ai/generate-topic-pack", {
        method: "POST",
        body: JSON.stringify({
          topic: promptForm.title,
          platforms: selected,
          count: 10
        })
      });
      setPosts(created);
      if (promptForm.schedule_enabled) {
        const startDate = promptForm.scheduled_for ? new Date(promptForm.scheduled_for) : new Date();
        const accountsToUse = promptForm.schedule_all_accounts
          ? accounts.filter((account) => created.some((post) => post.platform === account.platform))
          : accounts.filter((account) => (account.id ?? account._id) === promptForm.social_account_id);
        if (!accountsToUse.length) {
          setMessage("10 post ideas created. Connect Facebook or Instagram account first, then schedule them from Schedules.");
          return;
        }
        let scheduledCount = 0;
        for (const account of accountsToUse) {
          const platformPosts = created.filter((post) => post.platform === account.platform);
          for (let index = 0; index < platformPosts.length; index += 1) {
            const post = platformPosts[index];
            const scheduledFor = new Date(startDate.getTime() + index * Number(promptForm.gap_hours || 24) * 60 * 60 * 1000);
            await api("/schedules", {
              method: "POST",
              body: JSON.stringify({
                generated_post_id: post.id ?? post._id,
                social_account_id: account.id ?? account._id,
                mode: "specific",
                scheduled_for: scheduledFor.toISOString(),
                recurring_cron: null,
                approval_required: false
              })
            });
            scheduledCount += 1;
          }
        }
        setMessage(`Created 10 post ideas with ${created.length} platform drafts. Scheduled ${scheduledCount} posts.`);
      } else {
        setMessage(`Created 10 post ideas with ${created.length} Facebook/Instagram drafts. Schedule them from Schedules when ready.`);
      }
      setPromptForm((current) => ({ ...current, title: "", prompt: "" }));
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Unable to create post pack");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <SectionTitle title="AI Studio" subtitle="Create text-only Facebook and Instagram post packs from a niche or post name, then schedule them for publishing." />
      <Card className="mb-5">
        <form onSubmit={generateTopicPack} className="grid gap-3">
          <Input placeholder="Niche or post name, e.g. Free PDF tools for students" value={promptForm.title} onChange={(e) => setPromptForm({ ...promptForm, title: e.target.value })} required />
          <Textarea
            rows={5}
            placeholder="Optional notes for one custom post. Use Create Full Post for a single post, or Create 10 Posts for a full pack."
            value={promptForm.prompt}
            onChange={(e) => setPromptForm({ ...promptForm, prompt: e.target.value })}
          />
          <div className="grid gap-3 md:grid-cols-[1fr_220px_140px_1fr]">
            <Select disabled={promptForm.schedule_all_accounts} value={promptForm.social_account_id} onChange={(e) => setPromptForm({ ...promptForm, social_account_id: e.target.value })}>
              <option value="">Choose publish account</option>
              {accounts.map((account) => (
                <option key={account.id ?? account._id} value={account.id ?? account._id}>
                  {account.platform}: {account.display_name}
                </option>
              ))}
            </Select>
            <Input type="datetime-local" value={promptForm.scheduled_for} onChange={(e) => setPromptForm({ ...promptForm, scheduled_for: e.target.value })} />
            <Input type="number" min="1" max="168" value={promptForm.gap_hours} onChange={(e) => setPromptForm({ ...promptForm, gap_hours: Number(e.target.value) })} />
            <label className="flex items-center gap-2 rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-700">
              <input type="checkbox" checked={promptForm.schedule_enabled} onChange={(e) => setPromptForm({ ...promptForm, schedule_enabled: e.target.checked })} />
              Schedule after creating
            </label>
          </div>
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input type="checkbox" checked={promptForm.schedule_all_accounts} onChange={(e) => setPromptForm({ ...promptForm, schedule_all_accounts: e.target.checked })} />
            Schedule to matching connected Facebook and Instagram accounts
          </label>
          <div className="flex flex-wrap gap-2">
            {platforms.map((platform) => (
              <label key={platform} className="flex items-center gap-2 rounded-md border border-slate-200 px-3 py-2 text-sm capitalize">
                <input
                  type="checkbox"
                  checked={selected.includes(platform)}
                  onChange={(e) => setSelected(e.target.checked ? [...selected, platform] : selected.filter((item) => item !== platform))}
                />
                {platform}
              </label>
            ))}
          </div>
          <div className="flex flex-wrap gap-2">
            <Button type="submit" disabled={loading || !selected.length}>{loading ? "Creating..." : "Create 10 Posts"}</Button>
            <Button type="button" disabled={loading || !selected.length} onClick={createSingleFromPrompt} className="bg-slate-800 hover:bg-slate-950">
              Create Full Post
            </Button>
          </div>
          <p className="text-xs text-slate-500">No image API is used. The number field is the gap in hours between scheduled posts.</p>
        </form>
      </Card>
      <Card>
        <div className="grid gap-3 md:grid-cols-[1fr_auto_auto]">
          <Select value={contentId} onChange={(e) => setContentId(e.target.value)}>
            {content.map((item) => (
              <option key={item.id ?? item._id} value={item.id ?? item._id}>
                {item.title}
              </option>
            ))}
          </Select>
          <Button disabled={!contentId || loading} onClick={generate}>{loading ? "Generating..." : "Generate Posts"}</Button>
          <Button disabled={!content.length || loading} onClick={generateAll} className="bg-slate-800 hover:bg-slate-950">
            Generate All
          </Button>
        </div>
        {message ? <p className="mt-3 rounded-md bg-brand-50 px-3 py-2 text-sm font-medium text-brand-700">{message}</p> : null}
      </Card>
      <div className="mt-5 grid gap-3">
        {posts.map((post) => (
          <Card key={post.id ?? post._id}>
            <p className="text-sm font-semibold capitalize text-brand-700">{post.platform}</p>
            <p className="mt-2 whitespace-pre-wrap text-slate-800">{post.text}</p>
            <p className="mt-3 text-sm text-slate-500">{post.hashtags.join(" ")}</p>
          </Card>
        ))}
      </div>
    </>
  );
}

export default AIStudioPage;
