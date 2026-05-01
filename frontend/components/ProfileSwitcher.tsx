"use client";

import { useEffect, useState } from "react";

type P = { id: string; name: string; profession: string; is_default?: boolean };

function cookieProfileId(): string | undefined {
  if (typeof document === "undefined") return undefined;
  const m = document.cookie.match(/(?:^|; )active_profile=([^;]*)/);
  return m?.[1] ? decodeURIComponent(m[1]) : undefined;
}

export function ProfileSwitcher() {
  const [profiles, setProfiles] = useState<P[]>([]);
  const [value, setValue] = useState<string>("");
  useEffect(() => {
    fetch("/api/profiles")
      .then((r) => r.json())
      .then((list: P[]) => {
        setProfiles(list);
        const fromCookie = cookieProfileId();
        const resolved =
          (fromCookie && list.some((p) => p.id === fromCookie) && fromCookie) ||
          list.find((p) => p.is_default)?.id ||
          list[0]?.id ||
          "";
        setValue(resolved);
      })
      .catch(() => setProfiles([]));
  }, []);
  if (profiles.length <= 1) return null;
  return (
    <select
      className="bg-slate-900 border border-slate-700 rounded text-xs px-2 py-1"
      value={value}
      onChange={(e) => {
        setValue(e.target.value);
        document.cookie = `active_profile=${e.target.value}; path=/`;
        window.location.reload();
      }}
    >
      {profiles.map((p) => (
        <option key={p.id} value={p.id}>
          {p.name} · {p.profession}
        </option>
      ))}
    </select>
  );
}
