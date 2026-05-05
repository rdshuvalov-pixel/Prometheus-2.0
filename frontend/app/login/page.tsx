"use client";

import { useState } from "react";
import { createClient } from "@/lib/supabase/client";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  async function send() {
    const supabase = createClient();
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: { emailRedirectTo: `${window.location.origin}/auth/callback` },
    });
    setMsg(error ? error.message : "Check your email");
  }
  return (
    <div className="max-w-md space-y-4">
      <h1 className="text-xl font-semibold">Magic link</h1>
      <input
        type="email"
        className="w-full bg-slate-900 border border-slate-700 rounded p-2"
        placeholder="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />
      <button type="button" onClick={send} className="px-4 py-2 bg-blue-600 rounded">
        Send link
      </button>
      {msg && <p className="text-sm">{msg}</p>}
    </div>
  );
}
