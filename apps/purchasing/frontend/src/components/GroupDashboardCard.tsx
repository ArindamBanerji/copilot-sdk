import { useEffect, useState } from "react";
import { fetchGroupDashboard, type GroupDashboardResponse } from "../api";

function pct(value?: number) {
  return `${Math.round(Number(value ?? 0) * 100)}%`;
}

function money(value?: number) {
  return `$${Math.round(Number(value ?? 0)).toLocaleString()}`;
}

export default function GroupDashboardCard() {
  const [dashboard, setDashboard] = useState<GroupDashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    fetchGroupDashboard()
      .then((data) => {
        if (mounted) setDashboard(data);
      })
      .catch((caught) => {
        if (mounted) setError(caught instanceof Error ? caught.message : "Group intelligence unavailable");
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  if (loading) return <section className="purchase-card">Loading chain intelligence...</section>;
  if (error) return <section className="purchase-card error-card">{error}</section>;
  if (!dashboard?.locations?.length) return <section className="purchase-card">Add locations to see group intelligence</section>;

  const opportunity = dashboard.transferOpportunities?.[0];

  return (
    <section className="purchase-card" data-testid="group-dashboard-card">
      <div className="panel-header">
        <div>
          <p className="purchase-kicker">Chain Intelligence</p>
          <h2 className="purchase-title">Your Chicago team's experience helps Miami</h2>
        </div>
        <span className="badge">{dashboard.provenance === "demo" ? "Sample data" : "Live"}</span>
      </div>

      <div className="stats-row">
        <div><span>Group accuracy</span><strong>{pct(dashboard.weightedAccuracy)}</strong></div>
        <div><span>Best location</span><strong>{dashboard.bestLocation}</strong></div>
        <div><span>Needs help</span><strong>{dashboard.needsHelpLocation}</strong></div>
        <div><span>Year 1 savings</span><strong>{money(dashboard.economic?.annualProjection)}</strong></div>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Location</th>
              <th>Decisions</th>
              <th>Accuracy</th>
              <th>Food cost</th>
              <th>Learning</th>
            </tr>
          </thead>
          <tbody>
            {dashboard.locations.map((location) => (
              <tr key={location.name}>
                <td>{location.name}</td>
                <td>{location.decisions}</td>
                <td>{pct(location.accuracy)}</td>
                <td>{pct(location.foodCostPct)}</td>
                <td>{location.conservation}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="purchase-grid two">
        <div>
          <h3>Transfer opportunity</h3>
          <p>
            {opportunity
              ? `${opportunity.source} to ${opportunity.target}: estimated ${pct(opportunity.estimatedAccuracy)} day-one accuracy.`
              : "No transfer opportunity right now."}
          </p>
        </div>
        <div>
          <h3>Purchasing power</h3>
          <p>{dashboard.purchasingPower?.callout}</p>
          <p className="trading-muted">$799-1,200/month across 4 locations ($200-300/store)</p>
        </div>
      </div>
    </section>
  );
}
