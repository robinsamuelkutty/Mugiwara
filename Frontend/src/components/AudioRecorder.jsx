import { useState, useRef, useEffect } from "react";
import { Mic, Square, RefreshCcw, ArrowRight, AlertCircle, CheckCircle } from "lucide-react"; 
import { sendAudio, compareAudio } from "../api/audioApi";

export default function AudioRecorder({ targetText, onNext, isLast, onResult, hideText }) {
  const [recording, setRecording] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState(null);
  const [stats, setStats] = useState({ accuracy: 0, errorCount: 0 });

  useEffect(() => {
    setResult(null);
    setStats({ accuracy: 0, errorCount: 0 });
  }, [targetText]);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm" });

      audioChunksRef.current = [];
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorder.start();
      setRecording(true);
      setResult(null); 
    } catch (err) {
      console.error("Error accessing microphone:", err);
      alert("Microphone access denied!");
    }
  };

  const stopRecording = async () => {
    mediaRecorderRef.current.stop();
    setRecording(false);
    setProcessing(true); 

    mediaRecorderRef.current.onstop = async () => {
      const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
      
      try {
        // 1. Get Raw Transcription (Has punctuation like "Red,")
        const transcription = await sendAudio(audioBlob, targetText);
        
        // --- 🧹 CLEANING STATION 🧹 ---
        
        // A. Remove punctuation from the text string
        const cleanTranscribedText = transcription.transcribed_text
          .replace(/[.,\/#!$%\^&\*;:{}=\-_`~()]/g, "") // Delete commas/periods
          .replace(/\s{2,}/g, " ") // Fix double spaces
          .trim()
          .toLowerCase();

        // B. Remove punctuation from the timestamp objects
        const cleanTimestamps = transcription.word_timestamps.map(ts => ({
           ...ts,
           word: ts.word.replace(/[.,\/#!$%\^&\*;:{}=\-_`~()]/g, "").trim().toLowerCase()
        }));

        // C. Clean target text (just in case)
        const cleanTargetText = targetText.toLowerCase();

        // 2. Send CLEAN data to be compared
        const comparePayload = {
           target_text: cleanTargetText,
           transcribed_text: cleanTranscribedText,
           word_timestamps: cleanTimestamps
        };

        const analysis = await compareAudio(comparePayload);
        
        // 3. Calculate Score
        if (analysis && analysis.word_status) {
            const totalWords = analysis.word_status.length;
            
            // Count "correct" words
            const correctCount = analysis.word_status.filter(w => w.label === "correct").length;
            const errorCount = totalWords - correctCount;
            
            // Calculate accuracy
            const accuracy = totalWords > 0 
                ? Math.round((correctCount / totalWords) * 100) 
                : 0;
            
            const calculatedStats = { accuracy, errorCount };
            setStats(calculatedStats);
            setResult(analysis);

            if (onResult) {
                onResult({ ...analysis, stats: { accuracy_percent: accuracy } });
            }
        }

      } catch (error) {
        console.error("Process failed", error);
      } finally {
        setProcessing(false);
      }
    };
  };

  return (
    <div className="flex flex-col items-center w-full max-w-lg mx-auto">
      
      {/* Hide Sentence Card if hideText is true */}
      {!hideText && (
        <div className="bg-indigo-50 border-2 border-indigo-100 rounded-2xl p-8 mb-8 w-full text-center shadow-sm relative overflow-hidden">
          <p className="text-2xl md:text-3xl font-bold text-gray-800 leading-snug tracking-wide">
            "{targetText}"
          </p>
        </div>
      )}

      {/* Controls */}
      <div className="relative mb-6">
        {recording && <div className="absolute inset-0 rounded-full bg-red-400 animate-ping opacity-75"></div>}

        {!recording ? (
          <button
            onClick={startRecording}
            disabled={processing}
            className={`relative z-10 flex items-center justify-center w-24 h-24 rounded-full shadow-xl transition-all border-4 border-white ${
              processing ? "bg-gray-300" : "bg-gradient-to-r from-blue-500 to-indigo-600 hover:scale-105"
            }`}
          >
            {processing ? <RefreshCcw className="w-10 h-10 text-white animate-spin" /> : <Mic className="w-10 h-10 text-white" />}
          </button>
        ) : (
          <button onClick={stopRecording} className="relative z-10 flex items-center justify-center w-24 h-24 bg-red-500 rounded-full shadow-xl hover:scale-105 border-4 border-white">
            <Square className="w-10 h-10 text-white fill-current" />
          </button>
        )}
      </div>
      
      <p className="text-gray-400 font-medium mb-8 h-6">
        {recording ? "Listening..." : processing ? "Analyzing..." : "Tap mic to read"}
      </p>

      {/* Results */}
      {result && result.word_status && (
        <div className="w-full bg-white rounded-2xl border-2 border-gray-100 shadow-lg overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-500">
          
          <div className="bg-gray-50 px-6 py-4 border-b border-gray-100 flex justify-between items-center">
            <div className="flex items-center gap-3">
              {stats.accuracy > 80 ? (
                <div className="bg-green-100 p-2 rounded-full"><CheckCircle className="w-6 h-6 text-green-600" /></div>
              ) : (
                <div className="bg-orange-100 p-2 rounded-full"><AlertCircle className="w-6 h-6 text-orange-600" /></div>
              )}
              <div>
                <h3 className="font-bold text-gray-800 text-lg">{stats.accuracy}% Accuracy</h3>
                <p className="text-xs text-gray-500">
                   {stats.errorCount} issues found
                </p>
              </div>
            </div>

            <button onClick={onNext} className="bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2 rounded-full text-sm font-bold flex items-center gap-2 transition-all shadow-md">
              {isLast ? "Finish" : "Next"} <ArrowRight className="w-4 h-4" />
            </button>
          </div>

          <div className="p-6">
            <div className="flex flex-wrap gap-2 justify-center leading-relaxed">
              {result.word_status.map((item, index) => {
                let colorClass = "text-gray-800";
                
                if (item.label === "correct") colorClass = "text-green-600 font-bold";
                if (item.label === "error") colorClass = "text-red-500 font-bold line-through decoration-2";
                if (item.label === "mispronunciation") colorClass = "text-orange-500 font-bold border-b-2 border-orange-300";

                return (
                  <div key={index} className="flex flex-col items-center group relative">
                    <span className={`px-2 py-1 rounded-lg text-lg transition-colors ${colorClass}`}>
                      {item.target_word}
                    </span>
                    {item.label !== "correct" && (
                      <span className="text-xs text-red-400 mt-1 font-medium">
                        "{item.spoken_word}"
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}