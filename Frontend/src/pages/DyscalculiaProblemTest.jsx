import { useState } from "react";
import { uploadProblemImage } from "../api/dyscalculiaApi"; 
import { Camera, CheckCircle, ArrowRight, Loader2, AlertTriangle, FileSearch, RefreshCw } from "lucide-react";
import { Link } from "react-router-dom";

export default function DyscalculiaProblemTest() {
  const [step, setStep] = useState(1); // 1=Upload, 2=Result
  const [selectedImage, setSelectedImage] = useState(null);
  const [imageFile, setImageFile] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState(null);

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
        const response = await uploadProblemImage(imageFile);
        console.log("Full API Response:", response);
        
        // The API returns { result: { ...data } }, so we access response.result
        setResult(response.result); 
        setStep(2); 
    } catch (error) {
        console.error(error);
        alert("Error analyzing image. Please try again.");
    } finally {
        setAnalyzing(false);
    }
  };

  // Helper to determine color based on Risk Level
  const getRiskColor = (level) => {
    switch (level?.toUpperCase()) {
      case "HIGH": return "bg-red-50 text-red-800 border-red-200";
      case "MEDIUM": return "bg-orange-50 text-orange-800 border-orange-200";
      default: return "bg-green-50 text-green-800 border-green-200";
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-purple-100 flex flex-col items-center py-10 px-4">
      
      {/* Header */}
      <div className="w-full max-w-3xl text-center mb-8">
        <h1 className="text-3xl font-extrabold text-indigo-800 flex items-center justify-center gap-2">
          <FileSearch className="w-8 h-8" /> Problem Detector
        </h1>
        <p className="text-gray-600 mt-2">
          Upload a picture of a math problem or handwritten numbers for detailed analysis.
        </p>
      </div>

      <div className="w-full max-w-3xl bg-white rounded-3xl shadow-xl overflow-hidden border-4 border-white p-6 md:p-8">
        
        {/* --- STEP 1: UPLOAD & PREVIEW --- */}
        {step === 1 && (
          <div className="animate-in fade-in slide-in-from-bottom duration-500">
            
            <div className="text-center mb-6">
              {!selectedImage ? (
                <div className="border-4 border-dashed border-indigo-200 rounded-3xl p-12 hover:bg-indigo-50 transition-colors group relative cursor-pointer">
                  <input 
                    type="file" 
                    accept="image/*" 
                    onChange={handleImageUpload}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  />
                  <div className="flex flex-col items-center text-gray-400 group-hover:text-indigo-600">
                    <Camera className="w-16 h-16 mb-4" />
                    <span className="font-bold text-lg">Tap to Upload Problem</span>
                    <span className="text-sm mt-2">Supports clear handwriting</span>
                  </div>
                </div>
              ) : (
                <div className="relative">
                  <img src={selectedImage} alt="Uploaded" className="w-full h-64 object-contain bg-gray-900 rounded-2xl shadow-md mb-6" />
                  <button 
                    onClick={() => { setSelectedImage(null); setImageFile(null); }}
                    className="absolute top-2 right-2 bg-white/90 p-2 rounded-full text-red-500 shadow-sm hover:bg-white"
                  >
                    <RefreshCw className="w-5 h-5" />
                  </button>
                </div>
              )}
            </div>

            {selectedImage && (
              <button 
                onClick={handleAnalysis}
                disabled={analyzing}
                className="w-full bg-indigo-600 text-white font-bold py-4 rounded-xl hover:bg-indigo-700 shadow-lg flex items-center justify-center gap-2 disabled:opacity-70 text-lg transition-all"
              >
                {analyzing ? (
                  <><Loader2 className="w-6 h-6 animate-spin" /> Analyzing Details...</>
                ) : (
                  <>Run Detailed Analysis <ArrowRight className="w-6 h-6" /></>
                )}
              </button>
            )}
          </div>
        )}

        {/* --- STEP 2: DETAILED RESULTS --- */}
        {step === 2 && result && (
           <div className="animate-in zoom-in duration-500 space-y-6">
              
              {/* 1. Risk Assessment Card */}
              <div className={`p-6 rounded-2xl border-2 text-center ${getRiskColor(result.screening_risk?.risk_level)}`}>
                  <div className="flex justify-center mb-3">
                    {result.screening_risk?.risk_level === "HIGH" ? (
                        <AlertTriangle className="w-12 h-12" />
                    ) : (
                        <CheckCircle className="w-12 h-12" />
                    )}
                  </div>
                  <h2 className="text-2xl font-black uppercase tracking-wide">
                      {result.screening_risk?.risk_level} RISK DETECTED
                  </h2>
                  <p className="font-medium mt-2 text-lg px-4">
                      {result.screening_risk?.reason}
                  </p>
              </div>

              {/* 2. Detected Content */}
              <div className="bg-gray-50 p-4 rounded-xl border border-gray-200 flex justify-between items-center">
                 <div>
                    <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider">Complete Sequence</h3>
                    <p className="text-xl font-mono font-bold text-gray-800">{result.complete_number}</p>
                 </div>
                 <div className="text-right">
                    <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider">Digits Found</h3>
                    <div className="flex gap-1 justify-end mt-1">
                        {result.digits?.map((d, i) => (
                            <span key={i} className="bg-white px-2 py-1 rounded shadow-sm font-mono text-sm border">{d}</span>
                        ))}
                    </div>
                 </div>
              </div>

              {/* 3. Detailed Observations */}
              <div className="space-y-2">
                 <h3 className="font-bold text-gray-700 ml-1">Key Observations:</h3>
                 <ul className="bg-white rounded-xl border border-indigo-100 divide-y divide-indigo-50">
                    {result.observations?.map((obs, i) => (
                        <li key={i} className="p-3 text-gray-600 text-sm flex gap-3">
                            <span className="text-indigo-400 font-bold">•</span>
                            {obs}
                        </li>
                    ))}
                 </ul>
              </div>

              {/* 4. Digit-by-Digit Breakdown (Table) */}
              {result.digit_analysis && result.digit_analysis.length > 0 && (
                  <div>
                    <h3 className="font-bold text-gray-700 ml-1 mb-2">Digit Breakdown:</h3>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm text-left text-gray-500 border rounded-lg overflow-hidden">
                            <thead className="text-xs text-gray-700 uppercase bg-gray-100">
                                <tr>
                                    <th className="px-4 py-3">Digit</th>
                                    <th className="px-4 py-3">Issues</th>
                                    <th className="px-4 py-3">Notes</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                                {result.digit_analysis.map((item, i) => (
                                    <tr key={i} className="bg-white hover:bg-gray-50">
                                        <td className="px-4 py-3 font-bold text-indigo-900 text-lg">{item.digit}</td>
                                        <td className="px-4 py-3">
                                            {item.issues?.map((issue, idx) => (
                                                <span 
                                                    key={idx} 
                                                    className={`inline-block px-2 py-0.5 rounded-full text-xs mr-1 mb-1 font-medium
                                                        ${issue === 'none' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}
                                                    `}
                                                >
                                                    {issue}
                                                </span>
                                            ))}
                                        </td>
                                        <td className="px-4 py-3 text-gray-600">{item.notes}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                  </div>
              )}

              <div className="text-center pt-4">
                <button 
                    onClick={() => { setStep(1); setResult(null); }}
                    className="text-indigo-600 font-bold hover:text-indigo-800 underline mr-4"
                >
                    Analyze Another
                </button>
                <Link to="/" className="text-gray-500 font-bold hover:underline">Back to Home</Link>
              </div>

           </div>
        )}

      </div>
    </div>
  );
}