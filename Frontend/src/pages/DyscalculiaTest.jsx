import { useState, useEffect } from "react";
import { fetchDyscalculiaNumbers, uploadHandwritingImage } from "../api/dyscalculiaApi"; 
import { Calculator, Camera, CheckCircle, ArrowRight, Loader2, AlertTriangle } from "lucide-react";
import { Link } from "react-router-dom";

export default function DyscalculiaTest() {
  const [numbers, setNumbers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [step, setStep] = useState(1); // 1=Write, 2=Upload, 3=Result
  const [selectedImage, setSelectedImage] = useState(null);
  const [imageFile, setImageFile] = useState(null);
  
  // Stores the parsed result: { label: string, reason: string, isRisk: boolean }
  const [result, setResult] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const data = await fetchDyscalculiaNumbers(6);
        setNumbers(data || [2, 5, 8, 3, 9, 6]);
      } catch (e) {
        setNumbers([2, 5, 8, 3, 9, 6]);
      }
      setLoading(false);
    };
    loadData();
  }, []);

  const handleImageUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedImage(URL.createObjectURL(file));
      setImageFile(file);
    }
  };

  const handleAnalysis = async () => {
    if (!imageFile) return;
    
    setAnalyzing(true);
    try {
        const response = await uploadHandwritingImage(imageFile);
        console.log("Analysis Result:", response);

        const rawResult = response.result || "";
        const lines = rawResult.split('\n');
        
        const label = lines[0] ? lines[0].trim() : "UNKNOWN";
        const reason = lines.length > 1 ? lines.slice(1).join(" ").trim() : "No details provided.";
        const isRisk = label.includes("LIKELY_DYSCALCULIA") && !label.includes("UNLIKELY");

        setResult({
            label: label.replace("_", " "), 
            reason: reason,
            isRisk: isRisk
        });

        setStep(3); 
    } catch (error) {
        console.error(error);
        alert("Error analyzing image. Please try again.");
    } finally {
        setAnalyzing(false);
    }
  };

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-teal-50 text-teal-600 font-bold text-xl gap-2">
      <Calculator className="animate-bounce" /> Connecting to Teammate...
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-50 to-emerald-100 flex flex-col items-center py-10 px-4">
      
      {/* Header */}
      <div className="w-full max-w-2xl text-center mb-8">
        <h1 className="text-3xl font-extrabold text-teal-700 flex items-center justify-center gap-2">
          <Calculator className="w-8 h-8" /> Number Writing
        </h1>
        <p className="text-gray-600 mt-2">
          {step === 1 && "Write these numbers down on a piece of paper."}
          {step === 2 && "Take a photo of your paper."}
          {step === 3 && "Screening Analysis Complete."}
        </p>
      </div>

      <div className="w-full max-w-2xl bg-white rounded-3xl shadow-xl overflow-hidden border-4 border-white p-8">
        
        {/* --- STEP 1: SHOW NUMBERS --- */}
        {step === 1 && (
          <div className="animate-in fade-in slide-in-from-right duration-500">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-6 mb-8">
              {numbers.map((num, index) => (
                <div key={index} className="bg-teal-50 border-2 border-teal-100 rounded-2xl p-6 flex items-center justify-center">
                  <span className="text-4xl font-black text-gray-800 tracking-widest">{num}</span>
                </div>
              ))}
            </div>

            <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-8 text-yellow-800 text-sm">
              <strong>Instructions:</strong> Take a pen and paper. Write these numbers exactly as you see them.
            </div>

            <button 
              onClick={() => setStep(2)}
              className="w-full bg-teal-600 text-white px-8 py-4 rounded-xl font-bold text-lg hover:bg-teal-700 transition-all shadow-lg flex items-center justify-center gap-2"
            >
              I'm Done Writing <ArrowRight className="w-5 h-5" />
            </button>
          </div>
        )}

        {/* --- STEP 2: UPLOAD PHOTO --- */}
        {step === 2 && (
          <div className="animate-in fade-in slide-in-from-right duration-500 text-center">
            
            {!selectedImage ? (
              <div className="border-4 border-dashed border-gray-200 rounded-3xl p-10 mb-6 hover:bg-gray-50 transition-colors group relative cursor-pointer">
                <input 
                  type="file" 
                  accept="image/*" 
                  capture="environment"
                  onChange={handleImageUpload}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
                <div className="flex flex-col items-center text-gray-400 group-hover:text-teal-600">
                  <Camera className="w-16 h-16 mb-4" />
                  <span className="font-bold text-lg">Tap to Take Photo</span>
                </div>
              </div>
            ) : (
              <div className="mb-8">
                <img src={selectedImage} alt="Uploaded" className="w-full h-64 object-cover rounded-2xl border-4 border-teal-100 shadow-md mb-4" />
                <button onClick={() => setSelectedImage(null)} className="text-sm text-red-500 underline mb-2">Retake Photo</button>
              </div>
            )}

            <div className="flex gap-4">
               <button 
                 onClick={() => setStep(1)}
                 disabled={analyzing}
                 className="flex-1 bg-gray-100 text-gray-600 font-bold py-3 rounded-xl hover:bg-gray-200 disabled:opacity-50"
               >
                 Back
               </button>
               
               {selectedImage && (
                 <button 
                   onClick={handleAnalysis}
                   disabled={analyzing}
                   className="flex-1 bg-teal-600 text-white font-bold py-3 rounded-xl hover:bg-teal-700 shadow-lg flex items-center justify-center gap-2 disabled:opacity-70"
                 >
                   {analyzing ? (
                     <><Loader2 className="w-5 h-5 animate-spin" /> Analyzing...</>
                   ) : (
                     "Analyze Handwriting"
                   )}
                 </button>
               )}
            </div>
          </div>
        )}

        {/* --- STEP 3: RESULTS (UPDATED WITH NEXT BUTTON) --- */}
        {step === 3 && result && (
           <div className="animate-in zoom-in duration-500">
              <div className={`p-6 rounded-2xl mb-6 text-center ${
                  result.isRisk ? "bg-orange-50 text-orange-800" : "bg-green-50 text-green-800"
              }`}>
                  {result.isRisk ? (
                      <AlertTriangle className="w-12 h-12 mx-auto mb-2 text-orange-500" />
                  ) : (
                      <CheckCircle className="w-12 h-12 mx-auto mb-2 text-green-500" />
                  )}
                  
                  <h2 className="text-2xl font-black uppercase tracking-wide">
                      {result.label}
                  </h2>
              </div>

              <div className="bg-gray-50 rounded-xl p-6 mb-6 text-left border border-gray-100">
                  <h3 className="font-bold text-gray-700 mb-2 text-lg">Analysis Summary:</h3>
                  <p className="text-gray-600 text-md leading-relaxed">
                      {result.reason}
                  </p>
              </div>
              
              <div className="bg-blue-50 p-4 rounded-xl mb-6 text-sm text-blue-700">
                  <strong>Note:</strong> This is an AI-powered screening tool, not a medical diagnosis. Please consult a specialist for confirmation.
              </div>

              {/* NEXT STEP BUTTONS */}
              <div className="flex flex-col gap-3">
                <Link 
                  to="/dyscalculiaproblem" 
                  className="w-full bg-teal-600 text-white px-6 py-4 rounded-xl font-bold text-lg hover:bg-teal-700 shadow-lg flex items-center justify-center gap-2 transition-all transform hover:scale-[1.02]"
                >
                   Next Assessment <ArrowRight className="w-6 h-6" />
                </Link>

                <div className="text-center mt-2">
                  <Link to="/" className="text-gray-400 font-bold hover:text-teal-600 text-sm">
                    Back to Home
                  </Link>
                </div>
              </div>

           </div>
        )}

      </div>
    </div>
  );
}