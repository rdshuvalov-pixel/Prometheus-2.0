"use client";

export function CreateProfileButton() {
  async function createProfile() {
    const name = typeof window !== "undefined" ? window.prompt("Имя профиля", "Второй профиль") : null;
    if (!name?.trim()) return;
    const r = await fetch("/api/profiles", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: name.trim(),
        profession: "Senior Product Manager",
        search_keywords: ["product", "b2b"],
      }),
    });
    if (!r.ok) {
      alert(await r.text());
      return;
    }
    const j = await r.json();
    if (j.id) {
      document.cookie = `active_profile=${j.id}; path=/`;
    }
    window.location.reload();
  }

  return (
    <button type="button" onClick={createProfile} className="text-sm px-3 py-1 border border-slate-600 rounded">
      Создать профиль
    </button>
  );
}
