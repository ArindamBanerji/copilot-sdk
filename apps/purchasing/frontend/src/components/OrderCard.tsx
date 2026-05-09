import CategoryEmoji from "./CategoryEmoji";
import type { JoinedOrder } from "../types";

function displayDate(value?: string) {
  if (!value) {
    return "Date unavailable";
  }
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString();
}

function currency(value?: number) {
  return Number.isFinite(value) ? `$${Number(value).toFixed(0)}` : "n/a";
}

interface OrderCardProps {
  order: JoinedOrder;
  onClick?: () => void;
}

export default function OrderCard({ order, onClick }: OrderCardProps) {
  const metadata = order.metadata ?? order.decision?.metadata;
  const item = order.item;
  const name = metadata?.displayName ?? item?.displayName ?? metadata?.itemName ?? metadata?.item ?? order.decision?.item ?? "Order";
  const category = metadata?.category ?? item?.category ?? order.decision?.category;
  const action = metadata?.action ?? order.decision?.actualAction ?? order.decision?.action ?? "Completed";
  const reward = Number(metadata?.reward ?? order.decision?.reward);

  return (
    <button className="order-card" type="button" onClick={onClick}>
      <div className="order-card-top">
        <CategoryEmoji category={category} />
        <span className="purchase-muted">{displayDate(metadata?.createdAt ?? order.decision?.timestamp)}</span>
      </div>
      <h3>{name}</h3>
      <p>{String(action).replace(/_/g, " ")}</p>
      <div className="order-card-bottom">
        <span>{currency(metadata?.totalCost)}</span>
        <strong>{Number.isFinite(reward) ? `${reward > 0 ? "+" : ""}${reward.toFixed(2)}` : "reward n/a"}</strong>
      </div>
    </button>
  );
}
