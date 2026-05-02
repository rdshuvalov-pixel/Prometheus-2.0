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
      <body className="min-h-screen">
        <CandyBackdrop />
        <nav className="border-b border-candy-200 bg-white/70 backdrop-blur-sm px-4 py-3 flex gap-6 text-sm items-center flex-wrap text-candy-700">
          <Link href="/" className="hover:text-candy-600">
            Дашборд
          </Link>
          <Link href="/vacancies" className="hover:text-candy-600">
            Вакансии
          </Link>
          <Link href="/profile" className="hover:text-candy-600">
            Профиль
          </Link>
          <Link href="/cost" className="hover:text-candy-600">
            LLM cost
          </Link>
          <div className="ml-auto flex items-center gap-3">
            {user ? (
              <>
                <span className="text-candy-600 truncate max-w-[220px]" title={user.email ?? undefined}>
                  {user.email ?? user.id}
                </span>
                <form action="/api/logout" method="post">
                  <button
                    type="submit"
                    className="text-candy-600 hover:text-candy-500 hover:underline bg-transparent border-0 cursor-pointer p-0 text-sm"
                  >
                    Выйти
                  </button>
                </form>
              </>
            ) : (
              <Link href="/login" className="hover:text-candy-600">
                Вход
              </Link>
            )}
          </div>
        </nav>
        <main className="max-w-6xl mx-auto p-4">{children}</main>
      </body>
    </html>
  );
}
