"use client";

import { ChangeEvent, useRef } from "react";

import { Button } from "@/components/ui/button";

export function UploadZone({
  onSelect,
  status
}: {
  onSelect: (file: File) => void;
  status: string;
}) {
  const inputRef = useRef<HTMLInputElement | null>(null);

  const onChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    onSelect(file);
    event.target.value = "";
  };

  return (
    <section className="glass rounded-[28px] p-5">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <h2 className="font-display text-xl font-semibold text-white">
            Upload anatomy references
          </h2>
          <p className="mt-1 text-sm text-slate-400">
            Drag in PDF textbooks, lecture notes, or lab packets to route them
            into the private user collection.
          </p>
        </div>
        <div className="rounded-full border border-sky-400/20 bg-sky-400/10 px-3 py-1 text-xs uppercase tracking-[0.24em] text-sky-200">
          Private by user_id
        </div>
      </div>

      <div className="relative rounded-[24px] border border-dashed border-sky-300/25 bg-gradient-to-br from-sky-500/10 via-transparent to-cyan-400/10 p-6">
        <div className="flex flex-col items-start gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="text-sm font-medium text-white">Drop PDFs here</div>
            <div className="mt-1 text-sm leading-6 text-slate-400">
              Chunk, embed, and trace each passage back to its page reference.
            </div>
            <div className="mt-2 text-xs text-slate-500">{status}</div>
          </div>

          <input
            accept="application/pdf"
            className="hidden"
            onChange={onChange}
            ref={inputRef}
            type="file"
          />
          <Button
            onClick={() => inputRef.current?.click()}
            type="button"
            variant="secondary"
          >
            Select files
          </Button>
        </div>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        {[
          ["Gray's Anatomy Notes.pdf", "42 pages indexed", "Ready"],
          ["Thorax Revision Pack.pdf", "18 pages indexed", "Syncing"]
        ].map(([name, state, status]) => (
          <div
            key={name}
            className="rounded-2xl border border-white/10 bg-black/20 p-4"
          >
            <div className="flex items-center justify-between gap-3">
              <div className="text-sm font-medium text-white">{name}</div>
              <span className="rounded-full border border-white/10 px-2 py-1 text-[11px] uppercase tracking-[0.22em] text-slate-300">
                {status}
              </span>
            </div>
            <div className="mt-2 text-sm text-slate-400">{state}</div>
          </div>
        ))}
      </div>
    </section>
  );
}
