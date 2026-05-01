import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Прометей 2.0",
  description: "Pipeline и вакансии",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body className="min-h-screen">
        <nav className="border-b border-slate-800 px-4 py-3 flex gap-6 text-sm">
          <Link href="/">Дашборд</Link>
          <Link href="/timeline">Timeline</Link>
          <Link href="/vacancies">Вакансии</Link>
          <Link href="/profile">Профиль</Link>
          <Link href="/cost">LLM cost</Link>
          <Link href="/login" className="ml-auto">
            Вход
          </Link>
        </nav>
        <main className="max-w-6xl mx-auto p-4">{children}</main>
      </body>
    </html>
  );
}
