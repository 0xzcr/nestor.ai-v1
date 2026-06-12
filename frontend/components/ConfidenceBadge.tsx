const toneMap = {
  high: "border-emerald-400/25 bg-emerald-400/10 text-emerald-200",
  medium: "border-yellow-400/25 bg-yellow-400/10 text-yellow-200",
  low: "border-orange-400/25 bg-orange-400/10 text-orange-200",
  insufficient: "border-rose-400/25 bg-rose-400/10 text-rose-200"
} as const;

export function ConfidenceBadge({
  label
}: {
  label: keyof typeof toneMap;
}) {
  const textMap = {
    high: "High confidence",
    medium: "Medium confidence",
    low: "Low confidence — treat with caution",
    insufficient: "Could not confirm from sources"
  } as const;

  return (
    <span
      className={`inline-flex items-center rounded-full border px-3 py-1 text-[11px] font-medium uppercase tracking-[0.24em] ${toneMap[label]}`}
    >
      {textMap[label]}
    </span>
  );
}
