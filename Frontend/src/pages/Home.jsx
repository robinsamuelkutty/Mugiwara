import { Link } from "react-router-dom";
import {
  BookOpen,
  PenTool,
  Calculator,
  ArrowRight,
  Activity,
  Brain,
} from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      {/* --- HERO SECTION --- */}
      <header className="px-6 pt-16 pb-24 text-center max-w-5xl mx-auto">
        <div className="inline-block px-4 py-1.5 bg-indigo-100 text-indigo-700 rounded-full text-sm font-semibold mb-6 animate-fade-in">
          🚀 AI-Powered Learning Differences Detection
        </div>
        <h1 className="text-5xl md:text-7xl font-extrabold text-gray-900 mb-6 leading-tight">
          Unlocking Potential through <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-purple-600">
            Smart Screening
          </span>
        </h1>
        <p className="text-xl text-gray-600 mb-10 max-w-2xl mx-auto leading-relaxed">
          A gamified AI platform designed to detect early signs of learning
          differences through interactive challenges.
        </p>

        <div className="flex justify-center">
          <Link
            to="/test"
            className="flex items-center gap-2 bg-indigo-600 text-white px-8 py-4 rounded-xl text-lg font-bold hover:bg-indigo-700 transition-all shadow-xl hover:scale-105"
          >
            Start Assessment <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </header>

      {/* --- MODULES GRID --- */}
      <section id="modules" className="py-20 bg-white relative overflow-hidden">
        {/* Decorative Background Blob */}
        <div className="absolute top-0 left-0 w-full h-full bg-[radial-gradient(circle_at_top_right,_var(--tw-gradient-stops))] from-blue-50 via-transparent to-transparent opacity-50"></div>

        <div className="max-w-6xl mx-auto px-6 relative z-10">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900">
              Our Assessment Modules
            </h2>
            <p className="text-gray-500 mt-3 text-lg">
              Select a module to begin the screening process
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {/* 📘 MODULE 1: DYSLEXIA (Active) */}
            <div className="group relative bg-white rounded-3xl p-8 shadow-lg border-2 border-indigo-100 hover:border-indigo-500 transition-all hover:-translate-y-2">
              <div className="absolute top-0 right-0 bg-indigo-600 text-white text-xs font-bold px-3 py-1 rounded-bl-xl rounded-tr-2xl uppercase tracking-wider">
                Live
              </div>
              <div className="w-16 h-16 bg-indigo-50 rounded-2xl flex items-center justify-center mb-6 group-hover:bg-indigo-600 transition-colors duration-300">
                <BookOpen className="w-8 h-8 text-indigo-600 group-hover:text-white" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-3">
                Dyslexia
              </h3>
              <p className="text-gray-500 mb-8 leading-relaxed">
                Evaluates reading fluency, phonological awareness (rhyming), and
                decoding skills using speech analysis.
              </p>
              <Link
                to="/test"
                className="w-full block text-center bg-indigo-600 text-white font-bold py-3 rounded-xl hover:bg-indigo-700 transition-colors shadow-md"
              >
                Start Screening
              </Link>
            </div>

            {/* ✏️ MODULE 2: DYSGRAPHIA (Placeholder) */}
            <div className="group bg-white rounded-3xl p-8 shadow-lg border-2 border-gray-100 hover:border-purple-400 transition-all hover:-translate-y-2">
              <div className="w-16 h-16 bg-purple-50 rounded-2xl flex items-center justify-center mb-6 group-hover:bg-purple-600 transition-colors duration-300">
                <PenTool className="w-8 h-8 text-purple-600 group-hover:text-white" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-3">
                Dysgraphia
              </h3>
              <p className="text-gray-500 mb-8 leading-relaxed">
                Analyzes handwriting samples for letter reversals, spacing
                issues, and fine motor control challenges.
              </p>
              <Link
                to="/dysgraphia"
                className="w-full block text-center bg-teal-600 text-white font-bold py-3 rounded-xl hover:bg-teal-700 transition-colors shadow-md"
              >
                Start Screening
              </Link>
            </div>

            {/* 🧮 MODULE 3: DYSCALCULIA (Placeholder) */}
            <div className="group bg-white rounded-3xl p-8 shadow-lg border-2 border-gray-100 hover:border-teal-400 transition-all hover:-translate-y-2">
              <div className="w-16 h-16 bg-teal-50 rounded-2xl flex items-center justify-center mb-6 group-hover:bg-teal-600 transition-colors duration-300">
                <Calculator className="w-8 h-8 text-teal-600 group-hover:text-white" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-3">
                Dyscalculia
              </h3>
              <p className="text-gray-500 mb-8 leading-relaxed">
                Tests number sense, arithmetic patterns, and spatial reasoning
                using gamified math challenges.
              </p>
              <Link
                to="/dyscalculia"
                className="w-full block text-center bg-teal-600 text-white font-bold py-3 rounded-xl hover:bg-teal-700 transition-colors shadow-md"
              >
                Start Screening
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* --- TECH STACK / HOW IT WORKS --- */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-5xl mx-auto px-6">
          <div className="flex items-center gap-3 justify-center mb-12">
            <Brain className="w-8 h-8 text-gray-400" />
            <h2 className="text-3xl font-bold text-gray-900 text-center">
              Powered by Advanced AI
            </h2>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm flex items-start gap-4">
              <div className="bg-blue-100 p-3 rounded-lg">
                <Activity className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <h4 className="font-bold text-gray-900">
                  Speech-to-Text Analysis
                </h4>
                <p className="text-sm text-gray-500 mt-1">
                  Using OpenAI Whisper to transcribe reading patterns with
                  millisecond precision.
                </p>
              </div>
            </div>
            <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm flex items-start gap-4">
              <div className="bg-green-100 p-3 rounded-lg">
                <Activity className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <h4 className="font-bold text-gray-900">Phonetic Comparison</h4>
                <p className="text-sm text-gray-500 mt-1">
                  Levenshtein distance algorithms identify subtle
                  mispronunciations and substitutions.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-8 text-center">
        <p>© 2026 NeuroDiversify AI. Built for the Hackathon.</p>
      </footer>
    </div>
  );
}
