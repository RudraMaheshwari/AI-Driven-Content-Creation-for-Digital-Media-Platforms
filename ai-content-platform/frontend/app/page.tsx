import ContentForm from "@/components/ContentForm";

export default function HomePage() {
  return (
    <div className="space-y-10">
      <section className="space-y-4">
        <span className="eyebrow">Issue 01 · The studio</span>
        <h1 className="font-serif text-5xl leading-[1.05] tracking-tight">
          Sketch a brief.<br />
          <span className="text-accent-600">We&apos;ll draft, refine, and illustrate it.</span>
        </h1>
        <p className="max-w-2xl text-base text-ink-700 leading-relaxed">
          A single prompt becomes a polished piece of content for your chosen
          platform — written by Gemini, scored and rewritten by an evaluator,
          tailored to your audience, and paired with a generated illustration.
        </p>
      </section>
      <ContentForm />
    </div>
  );
}
