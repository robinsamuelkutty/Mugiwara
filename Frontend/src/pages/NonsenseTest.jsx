import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom"; // Import navigate
import AudioRecorder from "../components/AudioRecorder";
import { fetchNonsenseWords } from "../api/audioApi";
import { evaluateLevel, evaluateFull } from "../api/workflowApi"; // Import workflow APIs
import { useAssessment } from "../context/AssessmentContext"; // Import context
import { Sparkles, BrainCircuit, Star, Loader2 } from "lucide-react";

export default function NonsenseTest() {
  const [words, setWords] = useState([]); 
  const [currentIndex, setCurrentIndex] = useState(0); 
  const [loading, setLoading] = useState(true);
  const [completed, setCompleted] = useState(false);
  const [resultsHistory, setResultsHistory] = useState({});
  const [submitting, setSubmitting] = useState(false); // For loading state

  const navigate = useNavigate();
  const { userId, levelResults, saveLevelData } = useAssessment();

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      const data = await fetchNonsenseWords();
      if (data && data.words) {
        setWords(data.words.split(" "));
      }
      setLoading(false);
    };

    loadData();
  }, []);

  // Store detailed results for each word
  const handleAudioResult = (resultData) => {
    setResultsHistory(prev => ({
        ...prev,
        [currentIndex]: resultData
    }));
  };

  const handleNext = () => {
    if (currentIndex < words.length - 1) {
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
        // Aggregate data: Just use the average accuracy for simplicity here,
        // or construct a combined transcript if your backend supports it.
        // For Level 4 (nonsense), we often treat them as a single list.
        
        // Let's create a combined string of target and transcribed text for the report
        const fullTarget = words.join(" ");
        const fullTranscribed = Object.values(resultsHistory)
            .map(r => r.transcribed_text)
            .join(" ");
            
        // 1. Submit Level 4 Data
        await evaluateLevel(
            userId, 
            4, 
            fullTarget, 
            fullTranscribed, 
            [] // Timestamps might be complex to merge, sending empty for now is often okay for simple scoring
        );

        const averageScore = calculateAverage();

        // 2. Save Level 4 to Context
        const currentLevelData = {
            target_text: fullTarget,
            transcribed_text: fullTranscribed,
            accuracy: averageScore
        };
        saveLevelData(4, currentLevelData);

        // 3. Prepare FULL data for final report
        const allData = {
            ...levelResults,
            4: currentLevelData
        };

        console.log("Submitting Full Evaluation...", allData);

        // 4. Trigger Full Evaluation
        const finalReport = await evaluateFull(userId, allData);

        console.log("FINAL REPORT RECEIVED:", finalReport);

        // 5. Navigate to Report Page
        navigate('/report', { state: { report: finalReport } });

    } catch (error) {
        console.error("Submission failed:", error);
        alert("Something went wrong generating the report. Please try again.");
    } finally {
        setSubmitting(false);
    }
  };

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-pink-50 text-pink-600 font-bold text-xl gap-2">
      <BrainCircuit className="animate-pulse" /> Inventing words...
    </div>
  );

  if (completed) {
    const averageScore = calculateAverage();
    
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-pink-50 px-4">
        <div className="bg-white p-10 rounded-3xl shadow-xl text-center max-w-lg border-4 border-pink-100 animate-in fade-in zoom-in duration-500">
          <div className="bg-pink-100 w-24 h-24 rounded-full flex items-center justify-center mx-auto mb-6">
             <Star className="w-12 h-12 text-pink-600 fill-current" />
          </div>
          
          <h1 className="text-4xl font-extrabold text-pink-700 mb-2">Assessment Complete!</h1>
          <p className="text-gray-500 mb-8">You have finished all 4 levels.</p>
          
          <div className="bg-pink-50 rounded-2xl p-6 mb-8 border border-pink-200">
             <p className="text-gray-500 font-bold uppercase text-xs tracking-wider mb-2">Decoding Score</p>
             <div className="flex items-center justify-center gap-2">
                 <Sparkles className="w-8 h-8 text-pink-600" />
                 <span className="text-5xl font-black text-gray-800">{averageScore}%</span>
             </div>
          </div>

          <button 
            onClick={handleFinalSubmit} 
            disabled={submitting}
            className="w-full bg-pink-600 text-white px-8 py-4 rounded-xl font-bold text-lg hover:bg-pink-700 transition-all shadow-lg hover:scale-105 mb-3 flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-wait"
          >
            {submitting ? (
                <>
                    <Loader2 className="w-5 h-5 animate-spin" /> Generating Report...
                </>
            ) : (
                "View Full Report"
            )}
          </button>
          
           <button 
            onClick={() => window.location.href = '/'} 
            disabled={submitting}
            className="text-gray-400 font-bold hover:text-pink-600 text-sm"
          >
            Back to Home
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-50 to-purple-100 flex flex-col items-center py-10 px-4">
      
      {/* Progress Bar */}
      <div className="w-full max-w-md mb-8">
        <div className="flex justify-between text-sm font-bold text-pink-600 mb-2">
          <span>Word {currentIndex + 1} of {words.length}</span>
          <span>{Math.round(((currentIndex) / words.length) * 100)}%</span>
        </div>
        <div className="h-3 bg-white rounded-full overflow-hidden shadow-inner">
          <div 
            className="h-full bg-pink-500 transition-all duration-500 ease-out"
            style={{ width: `${((currentIndex + 1) / words.length) * 100}%` }}
          ></div>
        </div>
      </div>

      <div className="w-full max-w-2xl bg-white rounded-3xl shadow-xl overflow-hidden border-4 border-white">
        <div className="bg-pink-600 p-4 text-center">
          <h1 className="text-2xl font-bold text-white flex items-center justify-center gap-2">
            <Sparkles className="w-6 h-6" /> Magic Words
          </h1>
        </div>

        <div className="p-8">
          <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6 text-sm text-yellow-800">
             <strong>Tip:</strong> These are "Alien Words"! They don't mean anything. Just read them exactly how they sound.
          </div>

          <AudioRecorder 
            targetText={words[currentIndex]} 
            onNext={handleNext} 
            isLast={currentIndex === words.length - 1}
            onResult={handleAudioResult} 
            hideText={false} 
          />
        </div>
      </div>
    </div>
  );
}