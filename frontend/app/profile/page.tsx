import dynamic from "next/dynamic";
import { CreateProfileButton } from "@/components/CreateProfileButton";
import { getActiveProfileId } from "@/lib/active-profile";
import { createServerSupabase } from "@/lib/supabase/server";

const Editor = dynamic(() => import("./profile-editor"), { ssr: false });

export default async function ProfilePage() {
  const supabase = await createServerSupabase();
  const { data: profiles } = await supabase.from("candidate_profiles").select("*").order("created_at");
  const activeId = await getActiveProfileId();
  const profile =
    (activeId ? profiles?.find((p: { id: string }) => p.id === activeId) : null) ||
    profiles?.find((p: { is_default?: boolean }) => p.is_default) ||
    profiles?.[0];

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Профиль кандидата</h1>
      <CreateProfileButton />
      {!profile && (
        <p className="text-slate-400">
          Нет записи в candidate_profiles. Запустите seed_profile и проверьте RLS.
        </p>
      )}
      {profile && <Editor profile={profile} />}
    </div>
  );
}
