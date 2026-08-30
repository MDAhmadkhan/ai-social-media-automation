import { useEffect, useState } from "react";

import { Card, SectionTitle } from "../components/ui";
import { api } from "../lib/api";

function LogsPage() {
  const [items, setItems] = useState<any[]>([]);
  useEffect(() => {
    api<any[]>("/logs").then(setItems).catch(console.error);
  }, []);
  return (
    <>
      <SectionTitle title="Audit Logs" subtitle="Security and operational history for sensitive actions." />
      <div className="grid gap-3">
        {items.map((item) => (
          <Card key={item.id ?? item._id}>
            <p className="font-semibold text-slate-950">{item.action}</p>
            <p className="text-sm text-slate-600">{item.entity} · {new Date(item.created_at).toLocaleString()}</p>
          </Card>
        ))}
      </div>
    </>
  );
}

export default LogsPage;
