"use client";

import { useEffect, useRef, useState } from "react";

import * as pdfjsLib from "pdfjs-dist";

import { SourceSelection } from "@/components/types";

pdfjsLib.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjsLib.version}/build/pdf.worker.min.mjs`;

export function SourcePanel({ selection }: { selection: SourceSelection | null }) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [pdfStatus, setPdfStatus] = useState("Waiting for a citation.");

  useEffect(() => {
    let cancelled = false;

    const renderPdf = async () => {
      if (!selection?.pdfUrl || !canvasRef.current) {
        setPdfStatus("PDF preview unavailable for this citation.");
        return;
      }
      try {
        const loadingTask = pdfjsLib.getDocument(selection.pdfUrl);
        const pdf = await loadingTask.promise;
        const page = await pdf.getPage(1);
        const viewport = page.getViewport({ scale: 1.2 });
        const canvas = canvasRef.current;
        if (!canvas || cancelled) {
          return;
        }
        const context = canvas.getContext("2d");
        if (!context) {
          return;
        }
        canvas.height = viewport.height;
        canvas.width = viewport.width;
        await page.render({ canvasContext: context, viewport }).promise;
        setPdfStatus("Preview rendered.");
      } catch {
        setPdfStatus("Unable to render this PDF preview.");
      }
    };

    void renderPdf();
    return () => {
      cancelled = true;
    };
  }, [selection]);

  return (
    <aside className="glass animate-float rounded-[30px] p-5">
      <div className="mb-4 flex items-center justify-between gap-4">
        <div>
          <h2 className="font-display text-xl font-semibold text-white">
            Source inspection
          </h2>
          <p className="mt-1 text-sm text-slate-400">
            Review the exact page and highlighted passage before trusting a claim.
          </p>
        </div>
        <div className="rounded-full border border-cyan-300/20 bg-cyan-400/10 px-3 py-1 text-xs uppercase tracking-[0.24em] text-cyan-200">
          PDF.js viewer
        </div>
      </div>

      <div className="rounded-[26px] border border-white/10 bg-[#020612] p-4">
        <div className="mb-3 flex items-center justify-between gap-2 text-xs uppercase tracking-[0.24em] text-slate-500">
          <span>{selection?.source || "Select a citation"}</span>
          <span>{selection?.pageRef || "No page loaded"}</span>
        </div>

        <div className="rounded-[22px] border border-white/10 bg-[linear-gradient(180deg,#081122,#050a14)] p-4">
          <div className="space-y-3 text-sm leading-7 text-slate-300">
            <p>{selection?.quote || "Citation quotes will appear here."}</p>
            <div className="rounded-2xl border border-white/10 bg-black/20 p-3">
              <canvas className="h-auto w-full rounded-xl" ref={canvasRef} />
              <div className="mt-2 text-xs text-slate-500">{pdfStatus}</div>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        {[
          ["Source", selection?.source || "Pending"],
          ["Chunk ID", selection?.chunkId || "Pending"],
          ["Quote Match", selection ? "Ready to inspect" : "Select [1], [2], ..."]
        ].map(([label, value]) => (
          <div
            key={label}
            className="rounded-2xl border border-white/10 bg-black/20 p-3"
          >
            <div className="text-[11px] uppercase tracking-[0.24em] text-slate-500">
              {label}
            </div>
            <div className="mt-2 text-sm font-medium text-white">{value}</div>
          </div>
        ))}
      </div>
    </aside>
  );
}
