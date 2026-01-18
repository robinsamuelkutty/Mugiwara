import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import AudioRecorder from "../components/AudioRecorder";
import { fetchRhymes } from "../api/audioApi";
import { useAssessment } from "../context/AssessmentContext"; // 1. Import Context
import { evaluateLevel } from "../api/workflowApi"; // 2. Import Workflow API
import { Music, Star, TrendingUp, RefreshCw, ArrowRight, Loader2 } from "lucide-react";

export default function RhymeTest() {
  const [rhymePairs, setRhymePairs] = useState([]); 
  const [currentIndex, setCurrentIndex] = useState(0); 
  const [loading, setLoading] = useState(true);
  const [completed, setCompleted] = useState(false);
  const [resultsHistory, setResultsHistory] = useState({});
  const [submitting, setSubmitting] = useState(false); // Loading state

  const navigate = useNavigate();
  const { userId, saveLevelData } = useAssessment(); // 3. Get UserID

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      const data = await fetchRhymes("easy");
      setRhymePairs(data.slice(0, 3));
      setLoading(false);
    };

    loadData();
  }, []);

  // Store FULL result object for each pair
  const handleAudioResult = (resultData) => {
    setResultsHistory(prev => ({
        ...prev,
        [currentIndex]: resultData
    }));
  };

  const handleNext = () => {
    if (currentIndex < rhymePairs.length - 1) {
      setCurrentIndex(prev => prev + 1);
    } else {
      setCompleted(true);
    }
  };

  const calculateAverage = () => {
    const results = Object.values(resultsHistory);
    if (results.length === 0) return 0;
    const sum = results.reduce((a, b) => a + (b.stats?.accuracy_percent || 0), 0);
    return Math.round(sum / results.length);
  };

  // --- FINAL SUBMISSION LOGIC ---
  const handleFinalSubmit = async () => {
    setSubmitting(true);
    try {
        // Strategy: Send the LAST pair to the backend to check the "Level 2" logic.
        // In a full app, you might want to join all pairs into one big string.
        const lastResult = resultsHistory[rhymePairs.length - 1]; 

        if (!lastResult) {
            navigate('/ran');
            return;
        }

        // A. Call Backend
        const response = await evaluateLevel(
            userId, 
            2, // Level 2
            lastResult.target_text, 
            lastResult.transcribed_text, 
            lastResult.word_timestamps
        );

        console.log("Backend Response (L2):", response);

        // B. Save to Context (Average accuracy of all pairs)
        const averageAcc = calculateAverage();
        saveLevelData(2, {
            target_text: lastResult.target_text, // Simplified: saving last one
            transcribed_text: lastResult.transcribed_text,
            accuracy: averageAcc
        });

        // C. Decide Navigation
        if (response.status === "RETEST") {
            alert(`⚠️ Retest Suggested: ${response.message}`);
            window.location.reload(); 
        } else if (response.next_level === 3) {
            navigate('/ran');
        } else {
            navigate('/ran'); 
        }

    } catch (error) {
        console.error("Submission error:", error);
        navigate('/ran');
    } finally {
        setSubmitting(false);
    }
  };

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-purple-50 text-purple-600 font-bold text-xl gap-2">
      <RefreshCw className="animate-spin" /> Loading Rhymes...
    </div>
  );

  if (completed) {
    const averageScore = calculateAverage();
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-purple-50 px-4">
        <div className="bg-white p-10 rounded-3xl shadow-xl text-center max-w-lg border-4 border-purple-100 animate-in fade-in zoom-in duration-500">
          <div className="bg-purple-100 w-24 h-24 rounded-full flex items-center justify-center mx-auto mb-6">
             <Star className="w-12 h-12 text-purple-600 fill-current" />
          </div>
          <h1 className="text-4xl font-extrabold text-purple-700 mb-2">Rhyme Time Done!</h1>
          
          <div className="bg-purple-50 rounded-2xl p-6 mb-8 border border-purple-200 mt-6">
             <p className="text-gray-500 font-bold uppercase text-xs tracking-wider mb-2">Rhyming Accuracy</p>
             <div className="flex items-center justify-center gap-2">
                 <TrendingUp className="w-8 h-8 text-purple-600" />
                 <span className="text-5xl font-black text-gray-800">{averageScore}%</span>
             </div>
          </div>

          <div className="flex gap-4 justify-center">
            <button 
                onClick={() => window.location.href = '/'} 
                disabled={submitting}
                className="text-gray-500 font-bold hover:text-purple-600 transition-colors"
            >
                Back Home
            </button>
            
            <button 
                onClick={handleFinalSubmit} 
                disabled={submitting}
                className="bg-purple-600 text-white px-6 py-3 rounded-full font-bold hover:bg-purple-700 transition-all shadow-lg flex items-center gap-2 disabled:opacity-70 disabled:cursor-wait"
            >
                {submitting ? (
                    <>
                        <Loader2 className="w-5 h-5 animate-spin" /> Analyzing...
                    </>
                ) : (
                    <>
                        Next Level <ArrowRight className="w-5 h-5" />
                    </>
                )}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-100 flex flex-col items-center py-10 px-4">
      
      {/* Progress Bar */}
      <div className="w-full max-w-md mb-8">
        <div className="flex justify-between text-sm font-bold text-purple-600 mb-2">
          <span>Pair {currentIndex + 1} of {rhymePairs.length}</span>
          <span>{Math.round(((currentIndex) / rhymePairs.length) * 100)}%</span>
        </div>
        <div className="h-3 bg-white rounded-full overflow-hidden shadow-inner">
          <div 
            className="h-full bg-purple-500 transition-all duration-500 ease-out"
            style={{ width: `${((currentIndex + 1) / rhymePairs.length) * 100}%` }}
          ></div>
        </div>
      </div>

      <div className="w-full max-w-2xl bg-white rounded-3xl shadow-xl overflow-hidden border-4 border-white">
        <div className="bg-purple-600 p-4 text-center">
          <h1 className="text-2xl font-bold text-white flex items-center justify-center gap-2">
            <Music className="w-6 h-6" /> Rhyme Time
          </h1>
        </div>

        <div className="p-8">
          <p className="text-center text-gray-500 mb-6 font-medium">
             Read these two words together!
          </p>

          <AudioRecorder 
            targetText={rhymePairs[currentIndex]} 
            onNext={handleNext} 
            isLast={currentIndex === rhymePairs.length - 1}
            onResult={handleAudioResult} 
          />
        </div>
      </div>
    </div>
  );
}