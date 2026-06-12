import { ChatInterface } from "@/components/ChatInterface";

export default function HomePage() {
  return (
    <main className="relative overflow-hidden">
      <div className="hero-ring left-[-12rem] top-[-10rem] h-[26rem] w-[26rem]" />
      <div className="hero-ring right-[-8rem] top-[4rem] h-[18rem] w-[18rem]" />

      <section className="mx-auto flex min-h-screen w-full max-w-7xl flex-col px-4 pb-10 pt-6 sm:px-6 lg:px-8">
        <header className="glass animate-glow relative mb-6 overflow-hidden rounded-[28px] p-6 sm:p-8">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(56,189,248,0.18),transparent_22%),linear-gradient(135deg,transparent,rgba(37,99,235,0.1))]" />

          <div className="relative flex flex-col gap-8 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs uppercase tracking-[0.28em] text-sky-200">
                <span className="h-2 w-2 rounded-full bg-sky-400 shadow-[0_0_14px_rgba(56,189,248,0.8)]" />
                Nestor.ai Anatomy RAG
              </div>
              <h1 className="font-display text-4xl font-semibold leading-none sm:text-6xl">
                <span className="text-white">Clinical anatomy answers,</span>{" "}
                <span className="text-gradient">grounded down to the passage.</span>
              </h1>
              <p className="mt-5 max-w-2xl text-sm leading-7 text-slate-300 sm:text-base">
                A high-trust workspace for medical students. Ask anatomy questions,
                upload your own PDFs, and inspect every citation with a black-glass
                interface built to feel precise, premium, and fast.
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-3 lg:min-w-[360px]">
              {[
                ["0 Hallucinations", "Every answer must resolve to a source chunk."],
                ["3 Source Lanes", "Trusted references, uploads, and citations stay separated."],
                ["Live Confidence", "See answer reliability before you trust it."]
              ].map(([title, copy]) => (
                <div
                  key={title}
                  className="rounded-2xl border border-white/10 bg-black/20 p-4 backdrop-blur-sm"
                >
                  <div className="text-sm font-semibold text-white">{title}</div>
                  <div className="mt-1 text-xs leading-6 text-slate-400">{copy}</div>
                </div>
              ))}
            </div>
          </div>
        </header>

        <ChatInterface />

        <div className="mt-6 rounded-[22px] border border-amber-300/15 bg-amber-400/10 px-4 py-3 text-sm text-amber-100">
          For educational use only. Not clinical advice.
        </div>
      </section>
    </main>
  );
}
