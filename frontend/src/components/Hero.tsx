import { ArrowRight, Brain, Search, Users, Code, Lightbulb, ClipboardCheck, Wrench, FileCode, Sparkles } from "lucide-react";
import { useState } from "react";

const agents = [
  { 
    id: 1, 
    name: "Survey Agent", 
    angle: 0,
    Icon: Search,
    activities: ["Conducting Surveys...", "Gathering Research Data...", "Analyzing Patterns...", "Literature Review..."]
  },
  { 
    id: 2, 
    name: "Human Feedback", 
    angle: 45,
    Icon: Users,
    activities: ["Expert Consultation...", "Feedback Integration...", "Collaborative Review...", "Knowledge Validation..."]
  },
  { 
    id: 3, 
    name: "Code Review Agent", 
    angle: 90,
    Icon: Code,
    activities: ["Reviewing Code Quality...", "Static Analysis...", "Best Practices Check...", "Security Audit..."]
  },
  { 
    id: 4, 
    name: "Ideas, Innovation Agent", 
    angle: 135,
    Icon: Lightbulb,
    activities: ["Generating Innovations...", "Hypothesis Formation...", "Creative Solutions...", "Novel Approaches..."]
  },
  { 
    id: 5, 
    name: "Assessment Agent", 
    angle: 180,
    Icon: ClipboardCheck,
    activities: ["Evaluating Results...", "Performance Metrics...", "Quality Assessment...", "Impact Analysis..."]
  },
  { 
    id: 6, 
    name: "Method Development Agent", 
    angle: 225,
    Icon: Wrench,
    activities: ["Developing Methods...", "Optimizing Workflows...", "Process Automation...", "Tool Integration..."]
  },
  { 
    id: 7, 
    name: "Coding Agent", 
    angle: 270,
    Icon: FileCode,
    activities: ["Writing Code...", "Implementing Solutions...", "Automated Testing...", "Deployment..."]
  },
  { 
    id: 8, 
    name: "Aider", 
    angle: 315,
    Icon: Sparkles,
    activities: ["Orchestrating Workflows...", "Task Coordination...", "Resource Management...", "System Integration..."]
  },
];

const Hero = () => {
  const [hoveredAgent, setHoveredAgent] = useState<number | null>(null);

  return (
    <section className="relative min-h-screen flex flex-col items-center justify-start pt-20 overflow-hidden bg-slate-950">
      {/* Animated Grid Background */}
      <div className="absolute inset-0 z-0 opacity-20">
        <div className="absolute inset-0" style={{
          backgroundImage: `
            linear-gradient(to right, rgb(71, 85, 105) 1px, transparent 1px),
            linear-gradient(to bottom, rgb(71, 85, 105) 1px, transparent 1px)
          `,
          backgroundSize: '50px 50px'
        }}></div>
      </div>

      {/* Content */}
      <div className="container relative z-10 px-4 sm:px-6 lg:px-8 py-12 sm:py-16 w-full">
        <div className="grid lg:grid-cols-2 gap-8 lg:gap-12 items-start max-w-7xl mx-auto">
          {/* Left Side - Content */}
          <div className="space-y-4 sm:space-y-6">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-500/10 border border-blue-500/20 backdrop-blur-sm">
              <Sparkles className="w-4 h-4 text-blue-400" />
              <span className="text-xs sm:text-sm font-medium text-blue-400">AI-Powered Scientific Discovery</span>
            </div>

            {/* Headline */}
            <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold leading-tight">
              <span className="bg-gradient-to-r from-blue-400 via-purple-400 to-blue-400 bg-clip-text text-transparent">
                SciFusion
              </span>
              <br />
              <span className="text-white">
                AI-Driven Innovation in Scientific Research
              </span>
            </h1>

            {/* Description */}
            <p className="text-sm sm:text-base text-slate-300 leading-relaxed">
              An autonomous, multi-agent assistant that generates ideas, tests hypotheses, and evolves discoveries faster than ever. 
              Bridging AI intelligence with expert feedback for scalable, breakthrough research.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-3 pt-2">
              <button className="px-6 sm:px-8 py-4 sm:py-5 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white rounded-lg font-semibold text-sm sm:text-base transition-all flex items-center justify-center gap-2 group">
                Get Started
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </button>
              <button className="px-6 sm:px-8 py-4 sm:py-5 border border-blue-500/30 hover:bg-blue-500/10 text-white rounded-lg font-semibold text-sm sm:text-base transition-all">
                Learn More
              </button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-3 pt-4">
              <div className="text-center p-3 rounded-lg bg-slate-800/50 backdrop-blur-sm border border-slate-700">
                <div className="text-xl sm:text-2xl font-bold text-blue-400">10x</div>
                <div className="text-xs text-slate-400 mt-1">Faster Research</div>
              </div>
              <div className="text-center p-3 rounded-lg bg-slate-800/50 backdrop-blur-sm border border-slate-700">
                <div className="text-xl sm:text-2xl font-bold text-purple-400">24/7</div>
                <div className="text-xs text-slate-400 mt-1">Autonomous Work</div>
              </div>
              <div className="text-center p-3 rounded-lg bg-slate-800/50 backdrop-blur-sm border border-slate-700">
                <div className="text-xl sm:text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">∞</div>
                <div className="text-xs text-slate-400 mt-1">Scalable Discovery</div>
              </div>
            </div>
          </div>

          {/* Right Side - Agent Network */}
          <div className="relative h-[400px] lg:h-[500px] mt-4 lg:mt-8">
            <div className="absolute inset-0 p-6">
              
              {/* Title */}
              <div className="absolute -top-16 left-1/2 -translate-x-1/2 text-center z-10">
                <h3 className="text-lg font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-blue-400 bg-clip-text text-transparent">
                  Multi-Agent Architecture
                </h3>
                <p className="text-sm text-slate-400 mt-1">Hover to explore agents</p>
              </div>

              {/* Concentric Circles Background */}
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
                <div className="w-[180px] h-[180px] rounded-full border border-blue-500/10"></div>
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[240px] h-[240px] rounded-full border border-blue-500/5"></div>
              </div>

              {/* Center Hub - Brain Icon */}
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-20">
                <div className="relative">
                  {/* Outer glow ring */}
                  <div className="absolute inset-0 w-20 h-20 rounded-full bg-gradient-to-br from-blue-500/30 to-purple-500/30 blur-xl animate-pulse"></div>
                  
                  {/* Main circle */}
                  <div className="relative w-20 h-20 rounded-full bg-gradient-to-br from-blue-500 via-purple-500 to-blue-500 flex items-center justify-center shadow-2xl border-4 border-blue-500/30">
                    <Brain className="w-10 h-10 text-white" strokeWidth={1.5} />
                  </div>
                </div>
              </div>

              {/* Agent Nodes */}
              {agents.map((agent) => {
                const radius = 120;
                const angleRad = (agent.angle * Math.PI) / 180;
                const x = 50 + (radius / 3) * Math.cos(angleRad);
                const y = 50 + (radius / 3) * Math.sin(angleRad);
                const isHovered = hoveredAgent === agent.id;

                return (
                  <div key={agent.id}>
                    {/* Connection Line to Center */}
                    <svg className="absolute inset-0 w-full h-full pointer-events-none z-0">
                      <defs>
                        <linearGradient id={`gradient-${agent.id}`} x1="0%" y1="0%" x2="100%" y2="100%">
                          <stop offset="0%" stopColor="rgb(59, 130, 246)" stopOpacity="0.6" />
                          <stop offset="100%" stopColor="rgb(168, 85, 247)" stopOpacity="0.3" />
                        </linearGradient>
                      </defs>
                      <line
                        x1="50%"
                        y1="50%"
                        x2={`${x}%`}
                        y2={`${y}%`}
                        stroke={`url(#gradient-${agent.id})`}
                        strokeWidth={isHovered ? "2" : "1.5"}
                        className="transition-all duration-300"
                        style={{ 
                          filter: isHovered ? 'drop-shadow(0 0 4px rgb(59, 130, 246))' : 'none'
                        }}
                      />
                    </svg>

                    {/* Agent Node */}
                    <div
                      className="absolute group cursor-pointer transition-all duration-300 z-10"
                      style={{
                        left: `${x}%`,
                        top: `${y}%`,
                        transform: `translate(-50%, -50%) ${isHovered ? 'scale(1.15)' : 'scale(1)'}`,
                      }}
                      onMouseEnter={() => setHoveredAgent(agent.id)}
                      onMouseLeave={() => setHoveredAgent(null)}
                    >
                      <div className="relative">
                        {/* Glow Effect */}
                        <div className={`absolute inset-0 bg-gradient-to-br from-blue-500/40 to-purple-500/40 rounded-full blur-lg transition-opacity duration-300 ${isHovered ? 'opacity-100' : 'opacity-0'}`}></div>
                        
                        {/* Node Circle */}
                        <div className={`relative w-14 h-14 rounded-full bg-gradient-to-br from-slate-800 to-slate-900 border-2 flex items-center justify-center transition-all duration-300 ${
                          isHovered 
                            ? 'border-blue-500 shadow-lg shadow-blue-500/50' 
                            : 'border-blue-500/40'
                        }`}>
                          <agent.Icon className={`w-6 h-6 transition-colors duration-300 ${
                            isHovered ? 'text-blue-400' : 'text-blue-500/60'
                          }`} />
                        </div>

                        {/* Label - Always visible */}
                        <div className="absolute top-full mt-2 left-1/2 -translate-x-1/2 whitespace-nowrap">
                          <span className="text-[10px] font-medium text-slate-400">{agent.name}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}

              {/* Floating Activity Panel - Only on hover */}
              {hoveredAgent !== null && (
                <div className="absolute top-16 right-4 w-60 bg-slate-900/95 backdrop-blur-md border border-blue-500/30 rounded-xl p-3 shadow-2xl shadow-blue-500/20 z-30">
                  <div className="flex items-center gap-2 mb-2">
                    {agents.find(a => a.id === hoveredAgent)?.Icon && (
                      <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center">
                        {(() => {
                          const Agent = agents.find(a => a.id === hoveredAgent);
                          return Agent ? <Agent.Icon className="w-4 h-4 text-blue-400" /> : null;
                        })()}
                      </div>
                    )}
                    <h4 className="font-semibold text-xs text-white">
                      {agents.find(a => a.id === hoveredAgent)?.name}
                    </h4>
                  </div>
                  <div className="space-y-1.5">
                    {agents.find(a => a.id === hoveredAgent)?.activities.map((activity, idx) => (
                      <div key={idx} className="flex items-start gap-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-blue-400 mt-1.5 flex-shrink-0 animate-pulse" style={{ animationDelay: `${idx * 0.15}s` }}></div>
                        <span className="text-xs text-slate-300 leading-relaxed">{activity}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Gradient Orbs */}
      <div className="absolute top-1/4 left-1/4 w-64 sm:w-96 h-64 sm:h-96 bg-blue-500/20 rounded-full blur-3xl opacity-20 animate-pulse"></div>
      <div className="absolute bottom-1/4 right-1/4 w-64 sm:w-96 h-64 sm:h-96 bg-purple-500/20 rounded-full blur-3xl opacity-20 animate-pulse" style={{ animationDelay: "1s" }}></div>
    </section>
  );
};

export default Hero;