"use client";

import { ConfidenceBadge } from "@/components/ConfidenceBadge";
import { ExplanationItem, SourceSelection } from "@/components/types";

export function MessageBubble({
  role,
  directAnswer,
  confidence,
  explanation,
  message,
  onCitationClick
}: {
  role: "user" | "assistant";
  directAnswer?: string;
  confidence?: "high" | "medium" | "low" | "insufficient";
  explanation?: ExplanationItem[];
  message?: string;
  onCitationClick?: (selection: SourceSelection) => void;
}) {
  const isUser = role === "user";

  return (
    <article
      className={`rounded-[26px] border p-5 shadow-[0_20px_55px_rgba(2,6,23,0.34)] ${
        isUser
          ? "ml-auto max-w-2xl border-sky-400/20 bg-sky-500/10"
          : "glass max-w-3xl"
      }`}
    >
      <div className="mb-3 flex items-center justify-between gap-4">
        <div className="text-xs uppercase tracking-[0.3em] text-slate-400">
          {isUser ? "Student query" : "Nestor response"}
        </div>
        {confidence ? <ConfidenceBadge label={confidence} /> : null}
      </div>

      <p className="text-sm leading-7 text-slate-100">{directAnswer || message}</p>

      {explanation?.length ? (
        <div className="mt-4 grid gap-3 border-t border-white/10 pt-4">
          {explanation.map((item, index) => (
            <div
              key={`${item.chunk_id}-${index}`}
              className="rounded-2xl border border-white/10 bg-black/20 p-3"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="text-sm leading-6 text-slate-300">
                  {item.claim}
                  <button
                    className="ml-2 rounded-full border border-sky-400/20 bg-sky-400/10 px-2 py-0.5 text-[11px] uppercase tracking-[0.18em] text-sky-200"
                    onClick={() =>
                      onCitationClick?.({
                        source: "Retrieved source",
                        pageRef: item.chunk_id,
                        quote: item.quote,
                        chunkId: item.chunk_id
                      })
                    }
                    type="button"
                  >
                    [{index + 1}]
                  </button>
                </div>
              </div>
              <div className="mt-2 text-xs leading-6 text-slate-500">
                {item.chunk_id}
              </div>
            </div>
          ))}
        </div>
      ) : null}
    </article>
  );
}
