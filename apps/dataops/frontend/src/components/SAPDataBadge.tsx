interface SAPDataBadgeProps {
  po_count?: number;
  poCount?: number;
  variant_text?: string;
  variantText?: string;
}

export function SAPDataBadge({
  po_count,
  poCount,
  variant_text,
  variantText,
}: SAPDataBadgeProps) {
  const count = poCount ?? po_count;
  const variant = variantText ?? variant_text;

  return (
    <span className="inline-flex items-center rounded-md border border-purple-300/40 bg-purple-500/10 px-2.5 py-1 text-xs font-semibold text-purple-100">
      SAP S/4HANA
      {typeof count === "number" ? ` · ${count} POs` : ""}
      {variant ? ` · ${variant}` : ""}
    </span>
  );
}
