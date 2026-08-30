import { useEffect, useState } from "react";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { api } from "../lib/api";
import { Card, SectionTitle } from "../components/ui";

function DashboardPage() {
  const [data, setData] = useState<any>();
  useEffect(() => {
    api("/dashboard").then(setData).catch(console.error);
  }, []);
  const counts = data?.counts ?? {};
  const cards = [
    ["Websites", counts.websites ?? 0],
    ["Scheduled", counts.scheduled ?? 0],
    ["Published", counts.published ?? 0],
    ["Failed", counts.failed ?? 0],
    ["Drafts", counts.drafts ?? 0],
    ["Accounts", counts.connected_accounts ?? 0]
  ];
  const chart = Object.entries(data?.analytics ?? {}).map(([name, value]) => ({ name, value }));
  return (
    <>
      <SectionTitle title="Dashboard" subtitle="Automation health, publishing pipeline, AI credits, and content performance." />
      <div className="grid gap-4 md:grid-cols-3">
        {cards.map(([label, value]) => (
          <Card key={label}>
            <p className="text-sm text-slate-500">{label}</p>
            <p className="mt-2 text-3xl font-bold text-slate-950">{value}</p>
          </Card>
        ))}
      </div>
      <Card className="mt-5 h-80">
        <h3 className="mb-4 font-semibold text-slate-950">Analytics Snapshot</h3>
        <ResponsiveContainer width="100%" height="85%">
          <BarChart data={chart}>
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="value" fill="#1179e6" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Card>
    </>
  );
}

export default DashboardPage;
