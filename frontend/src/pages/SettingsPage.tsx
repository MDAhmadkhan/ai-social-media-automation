import { useEffect, useState } from "react";

import { Button, Card, Input, SectionTitle, Select } from "../components/ui";
import { api, uploadApi } from "../lib/api";

function SettingsPage() {
  const [settings, setSettings] = useState<any>({});
  const [message, setMessage] = useState("");
  useEffect(() => {
    api("/settings/brand").then((data) => setSettings(data ?? {})).catch(console.error);
  }, []);
  async function save() {
    setSettings(await api("/settings/brand", { method: "PATCH", body: JSON.stringify(settings) }));
    setMessage("Settings saved.");
  }
  async function uploadLogo(file?: File) {
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    setSettings(await uploadApi("/settings/brand/logo", formData));
    setMessage("Logo uploaded. New generated posts will use this logo.");
  }
  return (
    <>
      <SectionTitle title="Settings" subtitle="Brand voice, language, tone, emoji level, hashtag count, CTA, schedule, and timezone." />
      <Card className="grid gap-3">
        <div className="grid gap-3 md:grid-cols-[220px_1fr] md:items-center">
          <div className="flex h-28 w-full items-center justify-center rounded-md border border-slate-200 bg-white p-3">
            {settings.logo_url ? (
              <img src={settings.logo_url} alt="Brand logo" className="max-h-20 max-w-full object-contain" />
            ) : (
              <span className="text-sm text-slate-500">No logo uploaded</span>
            )}
          </div>
          <div className="grid gap-2">
            <label className="text-sm font-semibold text-slate-700">Brand logo for generated banners</label>
            <Input type="file" accept="image/png,image/jpeg,image/webp" onChange={(e) => uploadLogo(e.target.files?.[0])} />
            <p className="text-sm text-slate-500">Upload a transparent PNG logo for best professional results. New AI Studio posts will use this logo.</p>
          </div>
        </div>
        <Input placeholder="Brand voice" value={settings.brand_voice ?? ""} onChange={(e) => setSettings({ ...settings, brand_voice: e.target.value })} />
        <div className="grid gap-3 md:grid-cols-3">
          <Select value={settings.language ?? "English"} onChange={(e) => setSettings({ ...settings, language: e.target.value })}>
            {["English", "Hindi", "Arabic", "Spanish", "French", "German"].map((item) => <option key={item}>{item}</option>)}
          </Select>
          <Select value={settings.tone ?? "professional"} onChange={(e) => setSettings({ ...settings, tone: e.target.value })}>
            {["professional", "friendly", "witty", "educational", "persuasive"].map((item) => <option key={item}>{item}</option>)}
          </Select>
          <Input type="number" min={0} max={20} value={settings.hashtag_count ?? 6} onChange={(e) => setSettings({ ...settings, hashtag_count: Number(e.target.value) })} />
        </div>
        <Input placeholder="Default CTA" value={settings.default_cta ?? ""} onChange={(e) => setSettings({ ...settings, default_cta: e.target.value })} />
        <Input placeholder="Timezone" value={settings.timezone ?? ""} onChange={(e) => setSettings({ ...settings, timezone: e.target.value })} />
        <Button onClick={save}>Save Settings</Button>
        {message && <div className="rounded-md bg-blue-50 p-3 text-blue-700">{message}</div>}
      </Card>
    </>
  );
}

export default SettingsPage;
