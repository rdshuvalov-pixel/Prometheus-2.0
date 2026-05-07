"use client";

import { useEffect, useMemo, useState } from "react";

type Lang = "en" | "ru";

const LS_KEY = "prometei-lang";
const LS_COLLAPSE_KEY = "prometei-desc-collapsed";

const TEXT = {
  en: {
    title: "Prometei — a real job search pipeline service",
    sections: [
      {
        title: "What it does",
        lines: [
          "Prometei automates the most boring and expensive part of job search: collecting vacancies → deduplication → rule-based scoring → preparing outreach materials.",
          "Goal: less noise, more precise matches, and ready-to-send texts — so applying takes minutes, not hours.",
        ],
      },
      {
        title: "The problem it solves",
        lines: [
          "Manual job hunting becomes an endless feed of duplicates, stale listings, and roles that aren’t relevant.",
          "Prometei turns it into a product-grade pipeline: crawl → dedup → score → generate materials.",
        ],
      },
      {
        title: "How it works (step by step)",
        lines: [
          "Collect roles by target titles from tiered sources (career pages + boards).",
          "Deduplicate and store in the database (company + role_title does not multiply).",
          "Score & filter using quality rules (format/location/freshness/relevance).",
          "Generate materials for strong matches (notes + two cover letter variants).",
          "Store results with clear statuses and run history.",
        ],
      },
      {
        title: "What it demonstrates",
        lines: [
          "Product thinking: funnel, quality rules, statuses, predictable outcomes.",
          "Engineering: web UI + API + job queue + worker + database.",
          "Automation: solid data model, dedup, repeatable runs, scheduling and control.",
        ],
      },
    ],
  },
  ru: {
    title: "Prometei — живой сервис для поиска и “упаковки” вакансий",
    sections: [
      {
        title: "Что делает",
        lines: [
          "Prometei автоматизирует самый скучный и дорогой кусок job search: сбор вакансий → дедупликация → скоринг по правилам → подготовка материалов для отклика.",
          "Цель: меньше мусора, больше точных попаданий и готовых текстов, чтобы отклик занимал минуты, а не часы.",
        ],
      },
      {
        title: "Что решает",
        lines: [
          "Ручной мониторинг карьерных страниц и джоббордов превращается в бесконечную ленту повторов, устаревших и нерелевантных вакансий.",
          "Prometei делает это как продуктовый конвейер: crawl → dedup → score → материалы.",
        ],
      },
      {
        title: "Как работает (по шагам)",
        lines: [
          "Сбор вакансий по ролям из Tier-источников (career pages + boards).",
          "Дедупликация и сохранение в базе (та же компания + та же роль не размножается).",
          "Скоринг и отсев по правилам качества (формат/локация/свежесть/релевантность).",
          "Генерация материалов (заметки + 2 варианта cover letter).",
          "Хранение результата: статусы и история запусков.",
        ],
      },
      {
        title: "Что показывает",
        lines: [
          "Product thinking: воронка, правила качества, статусы и предсказуемый результат.",
          "Engineering: web UI + API + очередь + воркер + база данных.",
          "Automation: модель данных, дедуп, повторяемые прогоны, расписание и контроль.",
        ],
      },
    ],
  },
} as const;

function clampAfter(source: string, needle: string): string {
  const i = source.toLowerCase().indexOf(needle.toLowerCase());
  if (i < 0) return source;
  const end = i + needle.length;
  return source.slice(0, end);
}

export default function DescriptionPanel() {
  const [lang, setLang] = useState<Lang>("en");
  const [collapsed, setCollapsed] = useState(true);

  useEffect(() => {
    try {
      const saved = window.localStorage.getItem(LS_KEY);
      if (saved === "ru" || saved === "en") setLang(saved);
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    try {
      window.localStorage.setItem(LS_KEY, lang);
    } catch {
      // ignore
    }
  }, [lang]);

  useEffect(() => {
    try {
      const saved = window.localStorage.getItem(LS_COLLAPSE_KEY);
      if (saved === "0") setCollapsed(false);
      if (saved === "1") setCollapsed(true);
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    try {
      window.localStorage.setItem(LS_COLLAPSE_KEY, collapsed ? "1" : "0");
    } catch {
      // ignore
    }
  }, [collapsed]);

  const t = useMemo(() => TEXT[lang], [lang]);
  const firstLine = t.sections[0]?.lines[0] ?? "";
  const collapsedLine =
    lang === "ru"
      ? clampAfter(firstLine, "сбор вакансий")
      : clampAfter(firstLine, "collecting vacancies");

  return (
    <section className="rounded-2xl border border-neutral-200 bg-white/90 backdrop-blur-sm p-5 shadow-sm">
      <div className="flex items-start gap-3 justify-between flex-wrap">
        <h1 className="text-xl font-semibold text-neutral-900">{t.title}</h1>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setLang("en")}
            className={[
              "px-3 py-1.5 rounded-lg text-xs font-semibold border",
              lang === "en"
                ? "bg-candy-500 text-white border-candy-500"
                : "bg-white/80 text-neutral-700 border-candy-200 hover:border-candy-300",
            ].join(" ")}
          >
            EN
          </button>
          <button
            type="button"
            onClick={() => setLang("ru")}
            className={[
              "px-3 py-1.5 rounded-lg text-xs font-semibold border",
              lang === "ru"
                ? "bg-candy-500 text-white border-candy-500"
                : "bg-white/80 text-neutral-700 border-candy-200 hover:border-candy-300",
            ].join(" ")}
          >
            RU
          </button>
        </div>
      </div>

      <div className="mt-4 grid gap-4">
        {collapsed ? (
          <div className="grid gap-3">
            <div className="text-sm font-semibold text-neutral-900">{t.sections[0]?.title}</div>
            <p className="text-sm text-neutral-800 leading-relaxed">
              {collapsedLine}
              {collapsedLine !== firstLine ? "…" : ""}
            </p>
            <button
              type="button"
              onClick={() => setCollapsed(false)}
              className="self-start text-sm font-semibold text-candy-800 hover:text-candy-600 hover:underline"
            >
              {lang === "ru" ? "Читать полностью" : "Read more"}
            </button>
          </div>
        ) : (
          <>
            {t.sections.map((s) => (
              <div key={s.title} className="grid gap-2">
                <div className="text-sm font-semibold text-neutral-900">{s.title}</div>
                <ul className="list-disc pl-5 text-sm text-neutral-800 grid gap-1">
                  {s.lines.map((x) => (
                    <li key={x}>{x}</li>
                  ))}
                </ul>
              </div>
            ))}
            <button
              type="button"
              onClick={() => setCollapsed(true)}
              className="self-start text-sm font-semibold text-neutral-700 hover:text-neutral-900 hover:underline"
            >
              {lang === "ru" ? "Свернуть" : "Collapse"}
            </button>
          </>
        )}
      </div>
    </section>
  );
}

