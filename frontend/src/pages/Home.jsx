import Footer from "../components/Footer";
import "../index.css";

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen bg-gradient-to-b from-blue-50 via-white to-blue-100">
      {/* Main Content */}
      <main className="flex-grow flex flex-col items-center justify-center text-center px-6 py-16 md:px-12">
        <div className="w-full max-w-5xl mx-auto flex flex-col items-center">
          {/* Heading */}
          <h1 className="text-5xl md:text-6xl font-extrabold text-blue-900 mb-6 tracking-tight drop-shadow-md">
            Welcome to <span className="text-blue-700">SciFusion</span>
          </h1>

          {/* Subtext */}
          <p className="text-gray-700 text-lg md:text-xl max-w-3xl leading-relaxed mb-8">
            🚀 A next-gen platform for{" "}
            <span className="font-semibold text-blue-800">research automation</span> and{" "}
            <span className="font-semibold text-blue-800">innovative scientific workflows</span>.
          </p>

          {/* Button */}
          <button className="px-8 py-3 bg-blue-600 text-white text-lg font-medium rounded-2xl shadow-lg hover:bg-blue-700 hover:scale-105 transform transition-all duration-300 ease-in-out">
            Get Started
          </button>
        </div>
      </main>

      {/* Footer */}
      <Footer />
    </div>
  );
}
