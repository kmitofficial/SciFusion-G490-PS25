import { Brain, Zap, Users, BarChart, Microscope, RefreshCw } from "lucide-react";

const features = [
  {
    icon: Brain,
    title: "AI-Powered Hypothesis Generation",
    description: "Specialized agents collaboratively generate novel, data-driven research hypotheses using advanced machine learning algorithms.",
  },
  {
    icon: Microscope,
    title: "Autonomous Experiment Design",
    description: "Automated methodology development and feasibility assessment, preparing robust experimental frameworks for practical implementation.",
  },
  {
    icon: Zap,
    title: "Rapid Execution & Optimization",
    description: "Execute simulations and experiments at unprecedented speeds with continuous optimization through adaptive learning algorithms.",
  },
  {
    icon: RefreshCw,
    title: "Closed-Loop Learning",
    description: "Integrate human expert feedback seamlessly to iteratively refine results and improve research outcomes continuously.",
  },
  {
    icon: Users,
    title: "Multi-Agent Collaboration",
    description: "Survey, Code Review, Idea Innovation, Assessment, Coder, and Debugger agents work in harmony to drive discovery.",
  },
  {
    icon: BarChart,
    title: "Scalable Research Pipeline",
    description: "Reduce time and cost significantly while scaling research efforts across multiple domains and disciplines effortlessly.",
  },
];

const Features = () => {
  return (
    <section id="features" className="py-16 sm:py-24 lg:py-32 bg-background">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="max-w-3xl mx-auto text-center mb-12 sm:mb-16 space-y-4">
          <div className="inline-block px-4 py-1.5 rounded-full bg-secondary/10 border border-secondary/20">
            <span className="text-sm font-medium text-secondary">Key Features</span>
          </div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold font-heading">
            Powered by{" "}
            <span className="bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              Advanced AI Technology
            </span>
          </h2>
          <p className="text-base sm:text-lg text-muted-foreground max-w-2xl mx-auto">
            SciFusion combines cutting-edge AI agents with proven scientific methodologies to revolutionize the research process.
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <div
                key={index}
                className="group relative p-6 sm:p-8 rounded-2xl bg-card border border-border hover:border-primary/50 transition-all duration-300 animate-fade-in"
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                {/* Hover Glow Effect */}
                <div className="absolute inset-0 rounded-2xl bg-gradient-primary opacity-0 group-hover:opacity-5 transition-opacity duration-300"></div>
                
                {/* Icon */}
                <div className="relative mb-4 sm:mb-6">
                  <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-xl bg-gradient-primary flex items-center justify-center shadow-glow-primary group-hover:scale-110 transition-transform duration-300">
                    <Icon className="w-6 h-6 sm:w-7 sm:h-7 text-primary-foreground" />
                  </div>
                </div>

                {/* Content */}
                <div className="relative space-y-2 sm:space-y-3">
                  <h3 className="text-lg sm:text-xl font-bold font-heading text-foreground group-hover:text-primary transition-colors">
                    {feature.title}
                  </h3>
                  <p className="text-sm sm:text-base text-muted-foreground leading-relaxed">
                    {feature.description}
                  </p>
                </div>

                {/* Bottom Accent Line */}
                <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-primary rounded-b-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              </div>
            );
          })}
        </div>

        {/* Bottom CTA */}
        <div className="mt-12 sm:mt-16 text-center">
          <p className="text-sm sm:text-base text-muted-foreground mb-4">
            Ready to accelerate your research?
          </p>
          <a
            href="#about"
            className="inline-flex items-center gap-2 text-primary hover:text-secondary transition-colors font-medium"
          >
            Learn more about our technology
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </a>
        </div>
      </div>
    </section>
  );
};

export default Features;
