import { useEffect, useState } from "react";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card, SectionTitle } from "../components/ui";
import { api } from "../lib/api";

function AnalyticsPage() {
  const [data, setData] = useState<any>({});
  useEffect(() => {
    api("/analytics").then(setData).catch(console.error);
  }, []);
  const chart = Object.entries(data.platform_comparison ?? {}).map(([platform, metrics]: any) => ({ platform, ...metrics }));
  return (
    <>
      <SectionTitle title="Analytics" subtitle="Clicks, shares, likes, comments, reach, impressions, CTR, and platform comparison." />
      <Card className="h-96">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chart}>
            <XAxis dataKey="platform" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="impressions" fill="#1179e6" radius={[4, 4, 0, 0]} />
            <Bar dataKey="clicks" fill="#0f766e" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Card>
    </>
  );
}

export default AnalyticsPage;
