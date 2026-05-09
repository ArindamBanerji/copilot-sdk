interface AEManagedBadgeProps {
  managed?: boolean;
  count?: number;
}

export default function AEManagedBadge({ managed, count }: AEManagedBadgeProps) {
  if (!managed) {
    return <span className="purchase-pill">Manual</span>;
  }

  return <span className="purchase-pill ae-pill">AE managed{count ? ` x${count}` : ""}</span>;
}
