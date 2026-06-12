"use client";

import { useEffect, useState } from "react";

import { AuthPanel } from "@/components/AuthPanel";
import { MessageBubble } from "@/components/MessageBubble";
import { SourcePanel } from "@/components/SourcePanel";
import { QueryPayload, SourceSelection } from "@/components/types";
import { UploadZone } from "@/components/UploadZone";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { supabase } from "@/lib/supabase";

type ChatMessage =
  | {
      role: "user";
      message: string;
    }
  | {
      role: "assistant";
      message?: string;
      directAnswer?: string;
      confidence?: "high" | "medium" | "low" | "insufficient";
      explanation?: QueryPayload["explanation"];
    };

const seedConversation: ChatMessage[] = [
  {
    role: "user",
    message:
      "Explain the brachial plexus in a way that helps me localize an upper trunk lesion."
  }
];

export function ChatInterface() {
  const [messages, setMessages] = useState<ChatMessage[]>(seedConversation);
  const [question, setQuestion] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(
    "PDF only, maximum 20MB, scanned documents are rejected."
  );
  const [authStatus, setAuthStatus] = useState(
    "Log in with Supabase before querying or uploading."
  );
  const [accessToken, setAccessToken] = useState<string>("");
  const [selection, setSelection] = useState<SourceSelection | null>(null);

  useEffect(() => {
    if (!supabase) {
      return;
    }

    void supabase.auth.getSession().then(({ data }) => {
      const token = data.session?.access_token || "";
      setAccessToken(token);
      if (token) {
        setAuthStatus("Authenticated.");
      }
    });

    const {
      data: { subscription }
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setAccessToken(session?.access_token || "");
      setAuthStatus(session?.access_token ? "Authenticated." : "Log in with Supabase before querying or uploading.");
    });

    return () => subscription.unsubscribe();
  }, []);

  const submitQuestion = async () => {
    const trimmed = question.trim();
    if (!trimmed || isLoading) {
      return;
    }
    if (!accessToken) {
      setAuthStatus("Log in before sending anatomy queries.");
      return;
    }

    setIsLoading(true);
    setMessages((current) => [...current, { role: "user", message: trimmed }]);
    setQuestion("");
    const assistantIndex = messages.length + 1;
    setMessages((current) => [
      ...current,
      {
        role: "assistant",
        message: "Searching anatomy sources...",
        confidence: "insufficient",
        explanation: []
      }
    ]);

    try {
      const response = await fetch("/api/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`
        },
        body: JSON.stringify({ query: trimmed, stream: true })
      });
      if (!response.body) {
        throw new Error("Missing response stream.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split("\n\n");
        buffer = events.pop() || "";

        for (const event of events) {
          const line = event
            .split("\n")
            .find((entry) => entry.startsWith("data: "));
          if (!line) {
            continue;
          }

          const payload = JSON.parse(line.slice(6)) as
            | { type: "answer_start" | "done" }
            | { type: "answer_text"; text: string }
            | { type: "citations"; data: QueryPayload }
            | { type: "error"; data: QueryPayload };

          if (payload.type === "answer_text") {
            setMessages((current) =>
              current.map((item, index) =>
                index === assistantIndex
                  ? {
                      role: "assistant" as const,
                      directAnswer: payload.text,
                      confidence: "insufficient",
                      explanation: []
                    }
                  : item
              )
            );
          }

          if (payload.type === "citations") {
            setMessages((current) =>
              current.map((item, index) =>
                index === assistantIndex
                  ? {
                      role: "assistant" as const,
                      message: payload.data.message,
                      directAnswer: payload.data.direct_answer,
                      confidence: payload.data.confidence,
                      explanation: payload.data.explanation
                    }
                  : item
              )
            );
          }

          if (payload.type === "error") {
            setMessages((current) =>
              current.map((item, index) =>
                index === assistantIndex
                  ? {
                      role: "assistant" as const,
                      message: payload.data.message || "The request failed.",
                      confidence: "insufficient",
                      explanation: []
                    }
                  : item
              )
            );
          }
        }
      }
    } catch {
      setMessages((current) =>
        current.map((item, index) =>
          index === assistantIndex
            ? {
                role: "assistant" as const,
                message: "The request failed before citations could be validated.",
                confidence: "insufficient",
                explanation: []
              }
            : item
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  const uploadFile = async (file: File) => {
    if (file.type !== "application/pdf") {
      setUploadStatus("Only PDF uploads are supported.");
      return;
    }
    if (file.size > 20 * 1024 * 1024) {
      setUploadStatus("This file exceeds the 20MB limit.");
      return;
    }
    if (!accessToken) {
      setAuthStatus("Log in before uploading PDFs.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    setUploadStatus(`Uploading ${file.name}...`);

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"}/upload`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${accessToken}`
          },
          body: formData
        }
      );
      const payload = await response.json();
      if (!response.ok) {
        setUploadStatus(payload.detail || "Upload failed.");
        return;
      }
      setUploadStatus(payload.message || `${file.name} processed successfully.`);
    } catch {
      setUploadStatus("Upload failed. Check backend auth and connectivity.");
    }
  };

  return (
    <div className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
      <div className="space-y-6">
        <AuthPanel onStatus={setAuthStatus} />

        <section className="glass rounded-[30px] p-5 sm:p-6">
          <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h2 className="font-display text-2xl font-semibold text-white">
                Anatomy copilot
              </h2>
              <p className="mt-1 text-sm text-slate-400">
                Ask complex anatomy questions and keep every factual claim tied to
                a traceable source chunk.
              </p>
            </div>
            <Badge>Gemini + Gemini Embedding 2 + Qdrant</Badge>
          </div>
          <div className="mb-5 rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-slate-300">
            {authStatus}
          </div>

          <div className="space-y-4">
            {messages.map((item, index) =>
              item.role === "user" ? (
                <MessageBubble
                  key={`${item.role}-${index}`}
                  message={item.message}
                  role="user"
                />
              ) : (
                <MessageBubble
                  key={`${item.role}-${index}`}
                  confidence={item.confidence}
                  directAnswer={item.directAnswer}
                  explanation={item.explanation}
                  message={item.message}
                  onCitationClick={setSelection}
                  role="assistant"
                />
              )
            )}
            {isLoading && messages[messages.length - 1]?.role !== "assistant" ? (
              <div className="rounded-[26px] border border-sky-400/20 bg-sky-500/10 p-4 text-sm text-sky-100">
                Searching anatomy sources...
              </div>
            ) : null}
          </div>

          <div className="mt-5 rounded-[26px] border border-white/10 bg-black/20 p-3">
            <label className="mb-3 block text-xs uppercase tracking-[0.24em] text-slate-500">
              Ask Nestor.ai
            </label>
            <Textarea
              placeholder="Ask a source-grounded anatomy question..."
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
            />
            <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex flex-wrap gap-2 text-xs text-slate-400">
                <span className="rounded-full border border-white/10 px-3 py-1">
                  Query analysis
                </span>
                <span className="rounded-full border border-white/10 px-3 py-1">
                  Claim-level citations
                </span>
                <span className="rounded-full border border-white/10 px-3 py-1">
                  User-upload filters
                </span>
              </div>
              <Button onClick={submitQuestion} type="button">
                Run grounded answer
              </Button>
            </div>
          </div>
        </section>

        <UploadZone onSelect={uploadFile} status={uploadStatus} />
      </div>

      <SourcePanel selection={selection} />
    </div>
  );
}
