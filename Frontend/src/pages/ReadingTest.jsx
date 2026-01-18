import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import AudioRecorder from "../components/AudioRecorder";
import { fetchStory } from "../api/audioApi";
import { useAssessment } from "../context/AssessmentContext"; // 1. Import Context
import { evaluateLevel } from "../api/workflowApi"; // 2. Import Workflow API
import { BookOpen, Star, TrendingUp, ArrowRight, RefreshCcw, Loader2 } from "lucide-react";

export default function ReadingTest() {
  const [sentences, setSentences] = useState([]); 
  const [currentIndex, setCurrentIndex] = useState(0); 
  const [loading, setLoading] = useState(true);
  const [completed, setCompleted] = useState(false);
  const [resultsHistory, setResultsHistory] = useState({});
  const [submitting, setSubmitting] = useState(false); // New state for API loading

  const navigate = useNavigate();
  const { userId, saveLevelData } = useAssessment(); // 3. Get UserID from Context

  useEffect(() => {
    const loadStory = async () => {
      setLoading(true);
      const data = await fetchStory("medium", 8);
      
      if (data && data.story) {
        // 1. Split the story by punctuation (. ! ?)
        const splitText = data.story.match(/[^.!?]+[.!?]+/g) || [data.story];
        
        setSentences(splitText.slice(0, 3).map(s => s.trim().replace(/\.$/, "")));
      } else {
        setSentences(["The quick brown fox jumps over the lazy dog"]); // Removed dot here too
      }
      setLoading(false);
    };

    loadStory();
  }, []);

  // 4. Update: Store the FULL result object, not just the percentage
  const handleAudioResult = (resultData) => {
    setResultsHistory(prev => ({
        ...prev,
        [currentIndex]: resultData 
    }));
  };

  const handleNext = () => {
    if (currentIndex < sentences.length - 1) {
      setCurrentIndex(prev => prev + 1);
    } else {
      setCompleted(true);
    }
  };

  // Update: Calculate average from the full objects
  const calculateAverage = () => {
    const results = Object.values(resultsHistory);
    if (results.length === 0) return 0;
    
    // Access nested stats.accuracy_percent
    const sum = results.reduce((a, b) => a + (b.stats?.accuracy_percent || 0), 0);
    return Math.round(sum / results.length);
  };

  // 5. FINAL SUBMISSION LOGIC
  const handleFinalSubmit = async () => {
    setSubmitting(true);

    try {
        // Strategy: We send the data from the LAST sentence for the "Gatekeeper" check.
        // (In a production app, you might want to join all transcribed_texts together)
        const lastResult = resultsHistory[sentences.length - 1]; 

        // If something went wrong and we have no data, force a fallback
        if (!lastResult) {
            console.error("No result data found.");
            navigate('/rhyme');
            return;
        }

        // A. Call Backend API
        const response = await evaluateLevel(
            userId, 
            1, // Level 1
            lastResult.target_text, 
            lastResult.transcribed_text, 
            lastResult.word_timestamps 
        );

        console.log("Backend Response:", response);

        // B. Save to Context (So we have it for the final report)
        saveLevelData(1, {
            target_text: lastResult.target_text,
            transcribed_text: lastResult.transcribed_text,
            accuracy: response.accuracy || 0
        });

        // C. Decide Navigation
        if (response.status === "RETEST") {
            alert(`⚠️ Retest Suggested: ${response.message}`);
            window.location.reload(); // Reloads page to start Level 1 again
        } else if (response.next_level === 2) {
            navigate('/rhyme');
        } else {
            // Default Fallback
            navigate('/rhyme'); 
        }

    } catch (error) {
        console.error("Submission error:", error);
        // Fallback navigation if API fails
        navigate('/rhyme');
    } finally {
        setSubmitting(false);
    }
  };

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-blue-50 text-blue-600 font-bold text-xl">
      📖 Opening your storybook...
    </div>
  );

  if (completed) {
    const averageScore = calculateAverage();
    const passed = averageScore > 40; 

    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-green-50 px-4">
        <div className="bg-white p-10 rounded-3xl shadow-xl text-center max-w-lg border-4 border-green-100 animate-in fade-in zoom-in duration-500">
          
          <div className="bg-green-100 w-24 h-24 rounded-full flex items-center justify-center mx-auto mb-6">
             <Star className="w-12 h-12 text-green-600 fill-current" />
          </div>
          
          <h1 className="text-4xl font-extrabold text-green-700 mb-2">Great Job!</h1>
          <p className="text-xl text-gray-500 mb-8">You finished the whole story.</p>
          
          <div className="bg-green-50 rounded-2xl p-6 mb-8 border border-green-200">
             <p className="text-gray-500 font-bold uppercase text-xs tracking-wider mb-2">Average Accuracy</p>
             <div className="flex items-center justify-center gap-2">
                 <TrendingUp className="w-8 h-8 text-green-600" />
                 <span className="text-5xl font-black text-gray-800">{averageScore}%</span>
             </div>
          </div>

          <div className="flex flex-col gap-3 w-full">
            {/* CONDITIONAL BUTTON */}
            {passed ? (
              <button 
                onClick={handleFinalSubmit} 
                disabled={submitting}
                className="w-full bg-indigo-600 text-white px-8 py-4 rounded-xl font-bold text-lg hover:bg-indigo-700 transition-all shadow-lg hover:scale-105 flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-wait"
              >
                {submitting ? (
                    <>
                        <Loader2 className="w-5 h-5 animate-spin" /> Analyzing...
                    </>
                ) : (
                    <>
                        Next Assessment <ArrowRight className="w-5 h-5" />
                    </>
                )}
              </button>
            ) : (
               <div className="bg-orange-50 text-orange-600 p-3 rounded-lg text-sm font-medium mb-2">
                  Let's try reading this one more time to improve!
               </div>
            )}

            <button 
              onClick={() => window.location.reload()} 
              disabled={submitting}
              className="w-full bg-white text-green-600 border-2 border-green-100 px-8 py-4 rounded-xl font-bold text-lg hover:bg-green-50 transition-all flex items-center justify-center gap-2"
            >
              <RefreshCcw className="w-5 h-5" /> Read Another Story
            </button>
          </div>

        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex flex-col items-center py-10 px-4">
      
      {/* Progress Bar */}
      <div className="w-full max-w-md mb-8">
        <div className="flex justify-between text-sm font-bold text-indigo-600 mb-2">
          <span>Sentence {currentIndex + 1} of {sentences.length}</span>
          <span>{Math.round(((currentIndex) / sentences.length) * 100)}%</span>
        </div>
        <div className="h-3 bg-white rounded-full overflow-hidden shadow-inner">
          <div 
            className="h-full bg-indigo-500 transition-all duration-500 ease-out"
            style={{ width: `${((currentIndex + 1) / sentences.length) * 100}%` }}
          ></div>
        </div>
      </div>

      <div className="w-full max-w-2xl bg-white rounded-3xl shadow-xl overflow-hidden border-4 border-white">
        <div className="bg-indigo-600 p-4 text-center">
          <h1 className="text-2xl font-bold text-white flex items-center justify-center gap-2">
            <BookOpen className="w-6 h-6" /> Reading Time
          </h1>
        </div>

        <div className="p-8">
          <AudioRecorder 
            targetText={sentences[currentIndex]} 
            onNext={handleNext} 
            isLast={currentIndex === sentences.length - 1}
            onResult={handleAudioResult} 
          />
        </div>
      </div>
    </div>
  );
}