const labels: Record<string, string> = {
  protein: "PR",
  produce: "PD",
  dairy: "DY",
  dry_goods: "DG",
  beverages: "BV",
};

interface CategoryEmojiProps {
  category?: string;
}

export default function CategoryEmoji({ category }: CategoryEmojiProps) {
  const key = category ?? "item";
  return <span className="purchase-pill">{labels[key] ?? key.slice(0, 2).toUpperCase()}</span>;
}
