"use client";

import { useState } from "react";

import { supabase } from "@/lib/supabase";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export function AuthPanel({
  onStatus
}: {
  onStatus: (message: string) => void;
}) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mode, setMode] = useState<"login" | "signup">("login");

  const submit = async () => {
    if (!supabase) {
      onStatus("Configure NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY to enable auth.");
      return;
    }
    if (!email || !password) {
      onStatus("Enter both email and password.");
      return;
    }

    const action =
      mode === "login"
        ? supabase.auth.signInWithPassword({ email, password })
        : supabase.auth.signUp({ email, password });
    const { error } = await action;
    onStatus(error?.message || (mode === "login" ? "Logged in." : "Sign-up email sent or account created."));
  };

  return (
    <section className="glass rounded-[28px] p-5">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <h2 className="font-display text-xl font-semibold text-white">
            Account access
          </h2>
          <p className="mt-1 text-sm text-slate-400">
            Supabase JWT auth is required for every query and upload.
          </p>
        </div>
        <Badge>{mode === "login" ? "Log in" : "Sign up"}</Badge>
      </div>

      <div className="grid gap-3">
        <input
          className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-white outline-none placeholder:text-slate-500"
          onChange={(event) => setEmail(event.target.value)}
          placeholder="Email"
          type="email"
          value={email}
        />
        <input
          className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-white outline-none placeholder:text-slate-500"
          onChange={(event) => setPassword(event.target.value)}
          placeholder="Password"
          type="password"
          value={password}
        />
        <div className="flex flex-wrap gap-3">
          <Button onClick={submit} type="button">
            {mode === "login" ? "Log in" : "Create account"}
          </Button>
          <Button
            onClick={() => setMode((current) => (current === "login" ? "signup" : "login"))}
            type="button"
            variant="secondary"
          >
            Switch to {mode === "login" ? "sign up" : "log in"}
          </Button>
        </div>
      </div>
    </section>
  );
}
