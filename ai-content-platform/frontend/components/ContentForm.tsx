"use client";

import { useState } from "react";
import {
  ContentResponse,
  ContentType,
  Length,
  Platform,
  Tone,
  generateContent,
  pollGeneration,
  refineContent,
  resolveImageUrl,
} from "@/lib/api";

const CONTENT_TYPES: { value: ContentType; label: string }[] = [
  { value: "blog_post", label: "Blog post" },
  { value: "article", label: "Article" },
  { value: "social_post", label: "Social post" },
  { value: "caption", label: "Caption" },
  { value: "marketing_copy", label: "Marketing copy" },
  { value: "ad_copy", label: "Ad copy" },
  { value: "newsletter", label: "Newsletter" },
  { value: "script", label: "Script" },
  { value: "summary", label: "Summary" },
  { value: "headline", label: "Headline" },
];

const PLATFORMS: { value: Platform; label: string }[] = [
  { value: "blog", label: "Blog" },
  { value: "twitter", label: "X / Twitter" },
  { value: "linkedin", label: "LinkedIn" },
  { value: "instagram", label: "Instagram" },
  { value: "facebook", label: "Facebook" },
  { value: "youtube", label: "YouTube" },
  { value: "tiktok", label: "TikTok" },
  { value: "newsletter", label: "Newsletter" },
  { value: "marketing", label: "Marketing" },
  { value: "news_portal", label: "News portal" },
];

const TONES: Tone[] = [
  "professional",
  "casual",
  "witty",
  "formal",
  "persuasive",
  "informative",
  "inspirational",
  "friendly",
];

const LENGTHS: Length[] = ["short", "medium", "long"];

function platformLabel(p: string): string {
  return PLATFORMS.find((x) => x.value === p)?.label ?? p;
}

function typeLabel(t: string): string {
  return CONTENT_TYPES.find((x) => x.value === t)?.label ?? t;
}

export default function ContentForm() {
  const [prompt, setPrompt] = useState("");
  const [contentType, setContentType] = useState<ContentType>("blog_post");
  const [platform, setPlatform] = useState<Platform>("blog");
  const [tone, setTone] = useState<Tone>("professional");
  const [length, setLength] = useState<Length>("medium");
  const [audience, setAudience] = useState("");
  const [refineLoop, setRefineLoop] = useState(true);
  const [personalize, setPersonalize] = useState(true);
  const [generateImage, setGenerateImage] = useState(true);

  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<ContentResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [feedback, setFeedback] = useState("");
  const [refining, setRefining] = useState(false);

  async function handleGenerate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!prompt.trim()) return;
    setSubmitting(true);
    setResult(null);
    try {
      const pending = await generateContent({
        prompt,
        content_type: contentType,
        platform,
        tone,
        length,
        audience: audience || undefined,
        refine_loop: refineLoop,
        personalize,
        generate_image: generateImage,
      });
      setResult(pending);
      const final = await pollGeneration(pending.id, {
        intervalMs: 1000,
        onTick: (g) => setResult(g),
      });
      setResult(final);
      if (final.status === "failed") {
        setError(final.error || "generation failed");
      }
    } catch (e: any) {
      setError(e.message || "generation failed");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleRefine() {
    if (!result?.final_output || !feedback.trim()) return;
    setRefining(true);
    setError(null);
    try {
      const r = await refineContent({
        content: result.final_output,
        feedback,
        refined_prompt: result.refined_prompt || undefined,
      });
      setResult({ ...result, final_output: r.revised_content });
      setFeedback("");
    } catch (e: any) {
      setError(e.message || "refine failed");
    } finally {
      setRefining(false);
    }
  }

  const imageUrl = resolveImageUrl(result?.image_url);
  const completed = result?.status === "completed";
  const textReady = !!result?.final_output;
  const imageRendering =
    submitting &&
    textReady &&
    !imageUrl &&
    generateImage &&
    result?.status !== "failed";

  return (
    <div className="grid gap-8 lg:grid-cols-[minmax(0,360px)_minmax(0,1fr)]">
      {/* Left rail — brief */}
      <form onSubmit={handleGenerate} className="deck h-fit space-y-5 p-6">
        <div className="space-y-1">
          <span className="eyebrow">The brief</span>
          <h2 className="font-serif text-xl">Tell us what to write</h2>
        </div>

        <div>
          <label className="label">Prompt</label>
          <textarea
            className="textarea"
            placeholder="A friendly Instagram post announcing our new espresso bar opening Saturday in Udaipur, with the launch discount."
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            required
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">Type</label>
            <select
              className="select"
              value={contentType}
              onChange={(e) => setContentType(e.target.value as ContentType)}
            >
              {CONTENT_TYPES.map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Platform</label>
            <select
              className="select"
              value={platform}
              onChange={(e) => setPlatform(e.target.value as Platform)}
            >
              {PLATFORMS.map((p) => (
                <option key={p.value} value={p.value}>{p.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Tone</label>
            <select
              className="select"
              value={tone}
              onChange={(e) => setTone(e.target.value as Tone)}
            >
              {TONES.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Length</label>
            <select
              className="select"
              value={length}
              onChange={(e) => setLength(e.target.value as Length)}
            >
              {LENGTHS.map((l) => (
                <option key={l} value={l}>{l}</option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="label">Audience (optional)</label>
          <input
            className="input"
            placeholder="e.g. early-career marketers in India"
            value={audience}
            onChange={(e) => setAudience(e.target.value)}
          />
        </div>

        <div className="space-y-2 text-sm text-ink-700">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={refineLoop}
              onChange={(e) => setRefineLoop(e.target.checked)}
              className="h-4 w-4 accent-ink-900"
            />
            Run quality + rewrite refinement loop
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={personalize}
              onChange={(e) => setPersonalize(e.target.checked)}
              className="h-4 w-4 accent-ink-900"
            />
            Personalize for the audience
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={generateImage}
              onChange={(e) => setGenerateImage(e.target.checked)}
              className="h-4 w-4 accent-ink-900"
            />
            Generate an accompanying image
          </label>
        </div>

        <button
          type="submit"
          className="btn-primary w-full"
          disabled={submitting || !prompt.trim()}
        >
          {submitting ? "Composing…" : "Compose piece"}
        </button>

        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-800">
            {error}
          </div>
        )}
      </form>

      {/* Right — composed piece */}
      <div className="space-y-6">
        <article className="deck overflow-hidden">
          {/* Hero image */}
          <div className="relative w-full bg-paper-100">
            {imageUrl ? (
              <div className="flex w-full justify-center bg-paper-100 py-4">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={imageUrl}
                  alt={result?.image_prompt || "Generated illustration"}
                  className="max-h-[640px] w-auto max-w-full object-contain"
                />
              </div>
            ) : imageRendering ? (
              <div className="flex aspect-[4/5] max-h-[520px] w-full items-center justify-center bg-paper-100 sm:aspect-[16/9]">
                <div className="flex flex-col items-center gap-3 text-sm text-ink-500">
                  <span className="relative inline-flex h-10 w-10">
                    <span className="absolute inset-0 animate-ping rounded-full bg-accent-400 opacity-40" />
                    <span className="relative grid h-10 w-10 place-items-center rounded-full bg-accent-500 text-white text-xs font-semibold">
                      ✦
                    </span>
                  </span>
                  <span className="font-serif italic">Rendering illustration…</span>
                  <span className="text-[11px] uppercase tracking-[0.18em] text-ink-300">
                    typically 10–20s
                  </span>
                </div>
              </div>
            ) : (
              <div className="flex aspect-[16/9] w-full items-center justify-center text-sm text-ink-300">
                {submitting
                  ? "Drafting…"
                  : generateImage
                  ? "An illustration will appear here"
                  : "Image generation is off for this piece"}
              </div>
            )}
          </div>

          <div className="space-y-5 p-8">
            {/* Eyebrow row */}
            <div className="flex flex-wrap items-center gap-2 text-[11px]">
              {result ? (
                <>
                  <span className="eyebrow">{platformLabel(result.platform)}</span>
                  <span className="text-ink-300">·</span>
                  <span className="tag">{typeLabel(result.content_type)}</span>
                  <span className="tag">{result.tone}</span>
                  <span className="tag">{result.length}</span>
                  {result.quality_score !== null && (
                    <span className="tag-accent">
                      quality {result.quality_score?.toFixed(2)}
                    </span>
                  )}
                  {result.refinement_iterations > 0 && (
                    <span className="tag">{result.refinement_iterations} rewrite</span>
                  )}
                  {imageRendering && (
                    <span className="tag-accent animate-pulse">image rendering…</span>
                  )}
                  <span className="ml-auto text-ink-500">
                    {result.duration_ms ? `${(result.duration_ms / 1000).toFixed(1)}s` : ""}
                  </span>
                </>
              ) : (
                <>
                  <span className="eyebrow">{platformLabel(platform)}</span>
                  <span className="text-ink-300">·</span>
                  <span className="tag">{typeLabel(contentType)}</span>
                  <span className="tag">{tone}</span>
                </>
              )}
            </div>

            <div className="divider" />

            {/* Body */}
            {!result && !submitting && (
              <p className="text-base text-ink-500 italic">
                Fill in the brief on the left and press <span className="font-semibold text-ink-700">Compose piece</span>.
                Your finished article and illustration will appear here.
              </p>
            )}
            {submitting && !textReady && (
              <p className="text-base text-ink-500 italic animate-pulse">
                Composing — safety check, brief, draft, evaluation, rewrite, personalization…
              </p>
            )}
            {textReady && (
              <div className="article-body">{result!.final_output}</div>
            )}
          </div>
        </article>

        {result?.refined_prompt && completed && (
          <div className="grid gap-4 lg:grid-cols-2">
            <div className="deck-flat p-5">
              <span className="eyebrow">Refined brief</span>
              <p className="mt-2 text-sm leading-relaxed text-ink-700">
                {result.refined_prompt}
              </p>
            </div>
            {result.image_prompt && (
              <div className="deck-flat p-5">
                <span className="eyebrow">Image prompt</span>
                <p className="mt-2 text-sm leading-relaxed text-ink-700">
                  {result.image_prompt}
                </p>
              </div>
            )}
            {result.quality_notes && (
              <div className="deck-flat p-5 lg:col-span-2">
                <span className="eyebrow">Editor&apos;s note</span>
                <p className="mt-2 text-sm leading-relaxed text-ink-700">
                  {result.quality_notes}
                </p>
              </div>
            )}
          </div>
        )}

        {result?.final_output && (
          <div className="deck p-5">
            <span className="eyebrow">Ask for a revision</span>
            <div className="mt-3 flex flex-col gap-2 sm:flex-row">
              <input
                className="input"
                placeholder="e.g. make it shorter and add a clear CTA"
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
              />
              <button
                type="button"
                className="btn-accent shrink-0"
                disabled={refining || !feedback.trim()}
                onClick={handleRefine}
              >
                {refining ? "Revising…" : "Revise"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
