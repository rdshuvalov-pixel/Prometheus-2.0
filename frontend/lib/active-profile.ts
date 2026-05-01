import { cookies } from "next/headers";

/** Cookie из ProfileSwitcher; если нет — страницы берут дефолтный профиль в БД. */
export async function getActiveProfileId(): Promise<string | null> {
  const store = await cookies();
  return store.get("active_profile")?.value ?? null;
}
