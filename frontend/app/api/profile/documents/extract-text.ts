import pdfParse from "pdf-parse";
import mammoth from "mammoth";

export type ExtractResult = { text: string; mimeType: string };

function toUtf8(buf: ArrayBuffer): string {
  return Buffer.from(buf).toString("utf8");
}

export async function extractText(fileName: string, mimeType: string, bytes: ArrayBuffer): Promise<ExtractResult> {
  const mt = (mimeType || "").toLowerCase();
  const name = (fileName || "").toLowerCase();

  const isPdf = mt === "application/pdf" || name.endsWith(".pdf");
  if (isPdf) {
    const parsed = await pdfParse(Buffer.from(bytes));
    return { text: (parsed.text || "").trim(), mimeType: "application/pdf" };
  }

  const isDocx =
    mt === "application/vnd.openxmlformats-officedocument.wordprocessingml.document" || name.endsWith(".docx");
  if (isDocx) {
    const out = await mammoth.extractRawText({ buffer: Buffer.from(bytes) });
    return { text: (out.value || "").trim(), mimeType: "application/vnd.openxmlformats-officedocument.wordprocessingml.document" };
  }

  const isText =
    mt.startsWith("text/") ||
    name.endsWith(".txt") ||
    name.endsWith(".md") ||
    name.endsWith(".markdown");
  if (isText) {
    return { text: toUtf8(bytes).trim(), mimeType: mt || "text/plain" };
  }

  throw new Error("unsupported_file_type");
}

