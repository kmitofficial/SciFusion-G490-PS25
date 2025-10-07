import aboutIllustration from "@/assets/about-illustration.jpg";

const About = () => {
  return (
    <section id="about" className="py-16 sm:py-24 lg:py-32 bg-gradient-to-b from-background to-background/50">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid lg:grid-cols-12 gap-8 lg:gap-12 items-center">
          {/* Image Column - 8 cols on large screens */}
          <div className="lg:col-span-6 order-2 lg:order-1">
            <div className="relative group">
              <div className="absolute -inset-1 bg-gradient-primary rounded-2xl blur opacity-25 group-hover:opacity-40 transition duration-1000"></div>
              <div className="relative rounded-2xl overflow-hidden border border-border">
                <img
                  src={aboutIllustration}
                  alt="AI Multi-Agent System Illustration"
                  className="w-full h-auto object-cover"
                />
              </div>
            </div>
          </div>

          {/* Content Column - 4 cols on large screens */}
          <div className="lg:col-span-6 order-1 lg:order-2 space-y-6">
            <div className="space-y-4">
              <div className="inline-block px-4 py-1.5 rounded-full bg-primary/10 border border-primary/20">
                <span className="text-sm font-medium text-primary">About SciFusion</span>
              </div>
              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold font-heading leading-tight">
                Revolutionizing
                <span className="block bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
                  Scientific Discovery
                </span>
              </h2>
            </div>

            <div className="space-y-4 text-muted-foreground leading-relaxed">
              <p className="text-base sm:text-lg">
                SciFusion leverages <strong className="text-foreground">NovelSeek's multi-agent framework</strong> to create an autonomous AI assistant that transforms the research process.
              </p>
              
              <div className="space-y-3 pl-4 border-l-2 border-primary/30">
                <div>
                  <h3 className="text-foreground font-semibold mb-1">🤖 Autonomous AI Agents</h3>
                  <p className="text-sm sm:text-base">
                    Specialized agents collaborate to generate novel hypotheses, design experiments, and optimize results continuously.
                  </p>
                </div>
                
                <div>
                  <h3 className="text-foreground font-semibold mb-1">🔄 Closed-Loop Learning</h3>
                  <p className="text-sm sm:text-base">
                    Our system integrates human expert feedback to iteratively refine and improve research outcomes.
                  </p>
                </div>
                
                <div>
                  <h3 className="text-foreground font-semibold mb-1">⚡ Accelerated Innovation</h3>
                  <p className="text-sm sm:text-base">
                    Significantly reduce time, cost, and manual effort while empowering researchers to focus on insights.
                  </p>
                </div>
              </div>

              <p className="text-base sm:text-lg pt-2">
                By automating repetitive and data-intensive phases, SciFusion enables researchers to dedicate their expertise to 
                <strong className="text-foreground"> critical thinking, analysis, and interpretation</strong>.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default About;
