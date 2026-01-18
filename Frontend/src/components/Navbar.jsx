import { Link } from "react-router-dom";
import { Brain, Activity, FileText } from "lucide-react";

export default function Navbar() {
  return (
    <nav className="bg-white border-b-2 border-blue-100 px-6 py-4 flex justify-between items-center sticky top-0 z-50 shadow-sm">
      {/* Logo Area */}
      <Link to="/" className="flex items-center gap-2 group">
        <div className="bg-blue-600 p-2 rounded-lg group-hover:bg-blue-700 transition-colors">
          <Brain className="w-6 h-6 text-white" />
        </div>
        <span className="text-xl font-bold text-gray-800 tracking-tight">
          Mugiwara<span className="text-blue-600"> AI</span>
        </span>
      </Link>

      {/* Navigation Links */}
      <div className="hidden md:flex gap-8 font-medium text-gray-600">
        <Link to="/" className="hover:text-blue-600 transition-colors">Home</Link>
        <a href="#features" className="hover:text-blue-600 transition-colors">Features</a>
        <a href="#how-it-works" className="hover:text-blue-600 transition-colors">How it Works</a>
      </div>

      {/* CTA Button */}
      <Link 
        to="/test" 
        className="bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2.5 rounded-full font-semibold transition-all shadow-md hover:shadow-lg flex items-center gap-2"
      >
        <span>Start Screening</span>
        <Activity className="w-4 h-4" />
      </Link>
    </nav>
  );
}