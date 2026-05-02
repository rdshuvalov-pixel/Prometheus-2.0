import type { Metadata } from "next";
import Link from "next/link";
import { createServerSupabase } from "@/lib/supabase/server";
import CandyBackdrop from "./CandyBackdrop";
import "./globals.css";

export const metadata: Metadata = {
  title: "Прометей 2.0",
  description: "Pipeline и вакансии",
  icons: { icon: "/icon.svg", shortcut: "/icon.svg" },
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const supabase = await createServerSupabase();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  return (
    <html lang="ru">
      <body className="relative min-h-screen bg-neutral-50">
        {/* Слой фона: градиент и карамельки над ним, контент выше (иначе -z скрывает SVG под paint body). */}
        <div
          className="fixed inset-0 z-0 bg-gradient-to-br from-[#fff7fa] via-[#fdebf3] to-[#fff5f9]"
          aria-hidden
        />
        <div className="fixed inset-0 z-[1] pointer-events-none overflow-hidden">
          <CandyBackdrop />
        </div>
        <div className="relative z-10">
          <nav className="border-b border-neutral-200 bg-white/90 backdrop-blur-sm px-4 py-3 flex gap-6 text-sm items-center flex-wrap font-medium text-neutral-900 shadow-sm">
            <Link href="/" className="hover:text-candy-700">
              Дашборд
            </Link>
            <Link href="/vacancies" className="hover:text-candy-700">
              Вакансии
            </Link>
            <Link href="/profile" className="hover:text-candy-700">
              Профиль
            </Link>
            <Link href="/cost" className="hover:text-candy-700">
              LLM cost
            </Link>
            <div className="ml-auto flex items-center gap-3 text-neutral-700">
              {user ? (
                <>
                  <span className="truncate max-w-[220px]" title={user.email ?? undefined}>
                    {user.email ?? user.id}
                  </span>
                  <form action="/api/logout" method="post">
                    <button
                      type="submit"
                      className="text-candy-800 hover:text-candy-600 hover:underline bg-transparent border-0 cursor-pointer p-0 text-sm font-medium"
                    >
                      Выйти
                    </button>
                  </form>
                </>
              ) : (
                <Link href="/login" className="hover:text-candy-700 font-medium">
                  Вход
                </Link>
              )}
            </div>
          </nav>
          <main className="max-w-6xl mx-auto p-4">{children}</main>
        </div>
      </body>
    </html>
  );
}
