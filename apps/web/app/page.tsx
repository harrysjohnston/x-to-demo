import { AuthSection } from "@/components/AuthSection";

export default function HomePage() {
  return (
    <main className="min-h-screen gradient-mesh">
      {/* Asymmetric layout - content offset to the left with generous right margin */}
      <div className="min-h-screen flex items-center px-6 py-16 lg:px-16">
        <div className="w-full max-w-6xl lg:ml-[4%]">
          {/* Decorative element */}
          <div className="animate-fade-up mb-8">
            <div className="inline-flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-muted-foreground">
              <span className="w-8 h-px bg-primary/60" />
              <span>X-to-demo pipeline</span>
            </div>
          </div>

          {/* Main heading */}
          <h1 className="animate-fade-up stagger-1 text-4xl md:text-5xl lg:text-6xl font-display font-semibold tracking-tight leading-[1.06] mb-6 max-w-4xl">
            Turn <span className="text-primary">input X</span> into a runnable demo code spec
          </h1>

          <p className="animate-fade-up stagger-2 text-lg text-muted-foreground max-w-3xl mb-12 leading-relaxed">
            Upload or paste brainstorming input, run the multi-stage pipeline, and produce a saved
            code spec aligned to the master plan and sub-plans.
          </p>

          {/* Auth section with staggered animation */}
          <div className="animate-fade-up stagger-3">
            <AuthSection />
          </div>
        </div>
      </div>

      {/* Decorative corner accent */}
      <div className="fixed bottom-0 right-0 w-64 h-64 pointer-events-none opacity-30">
        <div className="absolute bottom-8 right-8 w-px h-32 bg-gradient-to-t from-primary/50 to-transparent" />
        <div className="absolute bottom-8 right-8 w-32 h-px bg-gradient-to-l from-primary/50 to-transparent" />
      </div>
    </main>
  );
}
