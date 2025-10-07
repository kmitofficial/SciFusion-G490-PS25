import Navbar from "@/components/Navbar";
import Hero from "@/components/Hero";
import About from "@/components/About";
import Features from "@/components/Features";

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main>
        <Hero />
        <About />
        <Features />
      </main>
      <footer className="border-t border-border py-8 sm:py-12 bg-card">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-primary rounded-lg flex items-center justify-center shadow-glow-primary">
                <span className="text-lg font-bold font-heading">SF</span>
              </div>
              <span className="text-lg font-bold font-heading bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
                SciFusion
              </span>
            </div>
            <p className="text-sm text-muted-foreground text-center sm:text-left">
              © 2025 SciFusion. Revolutionizing scientific research with AI.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Index;
