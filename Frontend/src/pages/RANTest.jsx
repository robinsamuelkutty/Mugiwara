import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import AudioRecorder from "../components/AudioRecorder";
import { fetchRANGrid } from "../api/audioApi";
import { useAssessment } from "../context/AssessmentContext"; // 1. Import Context
import { evaluateLevel } from "../api/workflowApi"; // 2. Import Workflow API
import { Grid, Zap, Loader2 } from "lucide-react";

export default function RANTest() {
  const [grid, setGrid] = useState([]);
  const [targetText, setTargetText] = useState(""); 
  const [loading, setLoading] = useState(true);
  const [completed, setCompleted] = useState(false);
  const [score, setScore] = useState(0);
  
  // Store the full result data so we can send it to backend
  const [fullResult, setFullResult] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const navigate = useNavigate();
  const { userId, saveLevelData } = useAssessment(); // 3. Get UserID

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      const data = await fetchRANGrid();
      if (data) {
        setGrid(data.grid); 
        setTargetText(data.target_text); 
      }
      setLoading(false);
    };
    loadData();
  }, []);

  const handleAudioResult = (resultData) => {
    setScore(resultData.stats.accuracy_percent);
    setFullResult(resultData); // Save data for submission
    setCompleted(true);
  };

  // --- FINAL SUBMISSION LOGIC ---
  const handleFinalSubmit = async () => {
    setSubmitting(true);
    try {
        if (!fullResult) {
            navigate('/nonsense');
            return;
        }

        // A. Call Backend
        const response = await evaluateLevel(
            userId, 
            3, // Level 3
            fullResult.target_text, 
            fullResult.transcribed_text, 
            fullResult.word_timestamps
        );

        // B. Save to Context
        saveLevelData(3, {
            target_text: fullResult.target_text,
            transcribed_text: fullResult.transcribed_text,
            accuracy: score
        });

        // C. Decide Navigation
        // (Usually RAN doesn't have a RETEST logic, but we keep it just in case)
        if (response.status === "RETEST") {
            alert(`⚠️ Retest Suggested: ${response.message}`);
            window.location.reload(); 
        } else {
            navigate('/nonsense'); // Move to Level 4
        }

    } catch (error) {
        console.error("Submission error:", error);
        navigate('/nonsense');
    } finally {
        setSubmitting(false);
    }
  };

  const getColorClass = (colorName) => {
    switch (colorName) {
      case "red": return "bg-red-500 border-red-700";
      case "blue": return "bg-blue-500 border-blue-700";
      case "green": return "bg-green-500 border-green-700";
      case "yellow": return "bg-yellow-400 border-yellow-600";
      case "black": return "bg-gray-800 border-black";
      default: return "bg-gray-200";
    }
  };

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-orange-50 text-orange-600 font-bold text-xl gap-2">
      <Grid className="animate-spin" /> Painting circles...
    </div>
  );

  if (completed) {
    const passed = score > 40;
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-orange-50 px-4">
        <div className="bg-white p-10 rounded-3xl shadow-xl text-center max-w-lg border-4 border-orange-100 animate-in fade-in zoom-in duration-500">
          <h1 className="text-4xl font-extrabold text-orange-600 mb-2">Speed Run Done!</h1>
          
          <div className="bg-orange-50 rounded-2xl p-6 mb-8 mt-6 border border-orange-200">
             <p className="text-gray-500 font-bold uppercase text-xs tracking-wider mb-2">Color Naming Accuracy</p>
             <div className="flex items-center justify-center gap-2">
                 <Zap className="w-8 h-8 text-orange-500" />
                 <span className="text-5xl font-black text-gray-800">{score}%</span>
             </div>
          </div>

          <div className="flex flex-col gap-3 w-full">
            {passed ? (
              <button 
                onClick={handleFinalSubmit} 
                disabled={submitting}
                className="w-full bg-orange-600 text-white px-8 py-4 rounded-xl font-bold text-lg hover:bg-orange-700 transition-all shadow-lg hover:scale-105 flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-wait"
              >
                {submitting ? (
                    <>
                        <Loader2 className="w-5 h-5 animate-spin" /> Analyzing...
                    </>
                ) : (
                    "Next Level: Magic Words"
                )}
              </button>
            ) : (
               <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm font-medium mb-2">
                  Try saying the colors a bit slower/clearer.
               </div>
            )}
             
             <button 
                onClick={() => window.location.reload()} 
                disabled={submitting}
                className="text-gray-500 font-bold hover:text-orange-600 transition-colors mt-2"
            >
                Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-yellow-100 flex flex-col items-center py-6 px-4">
      
      {/* Header */}
      <div className="text-center mb-6">
        <h1 className="text-3xl font-extrabold text-orange-600 flex items-center justify-center gap-2">
           <Zap className="w-8 h-8" /> Color Speed Run
        </h1>
        <p className="text-gray-600 font-medium mt-2">
           Say the colors from <b>Left to Right</b> as fast as you can!
        </p>
      </div>

      {/* THE GRID */}
      <div className="bg-white p-6 rounded-3xl shadow-lg mb-8 border-4 border-orange-200">
        <div className="grid grid-cols-5 gap-4 md:gap-6">
            {grid.map((row, rIndex) => (
                row.map((color, cIndex) => (
                    <div 
                        key={`${rIndex}-${cIndex}`}
                        className={`w-12 h-12 md:w-16 md:h-16 rounded-full shadow-inner border-b-4 ${getColorClass(color)} transition-transform hover:scale-110`}
                    ></div>
                ))
            ))}
        </div>
      </div>

      <div className="w-full max-w-lg">
         <AudioRecorder 
            targetText={targetText} 
            hideText={true}  
            onNext={() => setCompleted(true)} 
            isLast={true}
            onResult={handleAudioResult} 
         />
      </div>

    </div>
  );
}