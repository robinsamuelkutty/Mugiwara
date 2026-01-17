import { useEffect, useState, useRef } from "react"
import axios from "axios"
import DysgraphiaText from "../data/DysgraphiaText.json"

const DysgraphiaAssessment = () => {
  const [selectedAge, setSelectedAge] = useState("")
  const [tasks, setTasks] = useState([])
  const [selectedTask, setSelectedTask] = useState("")
  const [imageFile, setImageFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState("")
  const [result, setResult] = useState(null)
  const [imagePreview, setImagePreview] = useState(null)
  const resultsRef = useRef(null)

  useEffect(() => {
    if (!selectedAge) {
      setTasks([])
      setSelectedTask("")
      return
    }

    const key = `age_${selectedAge}`
    if (DysgraphiaText[key]) {
      setTasks(DysgraphiaText[key].tasks)
      setSelectedTask(DysgraphiaText[key].tasks[0])
    }
  }, [selectedAge])

  useEffect(() => {
    if (result?.success && resultsRef.current) {
      setTimeout(() => {
        resultsRef.current.scrollIntoView({ behavior: "smooth" })
      }, 100)
    }
  }, [result])

  const handleImageChange = (e) => {
    const file = e.target.files[0]
    setImageFile(file)

    if (file) {
      const reader = new FileReader()
      reader.onloadend = () => setImagePreview(reader.result)
      reader.readAsDataURL(file)
    } else {
      setImagePreview(null)
    }
  }

  const handleSubmit = async () => {
    if (!selectedAge || !selectedTask || !imageFile) {
      setMessage("Please select age, text, and upload an image.")
      return
    }

    try {
      setLoading(true)
      setMessage("")
      setResult(null)

      const formData = new FormData()
      formData.append("age", Number(selectedAge))
      formData.append("expected_sentence", selectedTask)
      formData.append("file", imageFile)

      const response = await axios.post(
        "http://127.0.0.1:8000/screen",
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      )

      setResult(response.data)
      setMessage("Evaluation completed successfully.")
    } catch (error) {
      console.error(error)
      setMessage("Failed to submit for evaluation.")
    } finally {
      setLoading(false)
    }
  }

  const severityColor = (severity) => {
    if (severity === "High") return "text-red-600"
    if (severity === "Moderate") return "text-yellow-600"
    return "text-green-600"
  }

  const severityBg = (severity) => {
    if (severity === "High") return "bg-red-50 border-red-200"
    if (severity === "Moderate") return "bg-yellow-50 border-yellow-200"
    return "bg-green-50 border-green-200"
  }

  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-blue-50 via-white to-indigo-50 p-4 animate-gradient">
      <div className="max-w-7xl mx-auto">
        {/* Animated Background Elements */}
        <div className="fixed inset-0 pointer-events-none">
          <div className="absolute top-10 left-10 w-72 h-72 bg-purple-300 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse"></div>
          <div className="absolute top-20 right-20 w-72 h-72 bg-yellow-300 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse delay-1000"></div>
          <div className="absolute -bottom-8 left-20 w-72 h-72 bg-pink-300 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse delay-500"></div>
        </div>

        <div className="relative bg-white/90 backdrop-blur-sm shadow-2xl rounded-3xl p-6 md:p-8 space-y-8 transform transition-all duration-300 hover:shadow-3xl">
          
          {/* Header with Animation */}
          <div className="text-center space-y-4">
            <div className="inline-block">
              <h1 className="text-4xl md:text-5xl font-bold text-gray-800 mb-2 animate-fade-in-down">
                Dysgraphia Handwriting Assessment
              </h1>
              <div className="h-1 w-24 bg-gradient-to-r from-blue-500 to-purple-600 mx-auto rounded-full animate-expand"></div>
            </div>
            <p className="text-gray-600 mt-2 text-lg animate-fade-in-up delay-100">
              AI-powered handwriting screening tool for early detection
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            
            {/* Input Panel */}
            <div className="space-y-6">
              {/* Age Selection Card */}
              <div className="bg-gradient-to-br from-blue-50 to-white p-6 rounded-2xl border border-blue-100 shadow-sm hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
                <label className="block font-bold text-gray-700 mb-3 text-lg flex items-center gap-2">
                  <span className="bg-blue-100 p-2 rounded-lg">
                    <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </span>
                  Select Age Group
                </label>
                <select
                  className="w-full border-2 border-gray-200 rounded-xl p-4 text-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-200 focus:ring-opacity-50 transition-all duration-200 hover:border-blue-300"
                  value={selectedAge}
                  onChange={(e) => setSelectedAge(e.target.value)}
                >
                  <option value="">-- Select Age --</option>
                  {Array.from({ length: 11 }, (_, i) => i + 5).map((age) => (
                    <option key={age} value={age} className="py-2">{age} years old</option>
                  ))}
                </select>
              </div>

              {/* Task Selection Card */}
              {tasks.length > 0 && (
                <div className="bg-gradient-to-br from-green-50 to-white p-6 rounded-2xl border border-green-100 shadow-sm hover:shadow-lg transition-all duration-300 hover:-translate-y-1 animate-slide-up">
                  <label className="block font-bold text-gray-700 mb-3 text-lg flex items-center gap-2">
                    <span className="bg-green-100 p-2 rounded-lg">
                      <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </span>
                    Copy the following sentence
                  </label>
                  <select
                    className="w-full border-2 border-gray-200 rounded-xl p-4 text-lg mb-4 focus:border-green-500 focus:ring-2 focus:ring-green-200 focus:ring-opacity-50 transition-all duration-200 hover:border-green-300"
                    value={selectedTask}
                    onChange={(e) => setSelectedTask(e.target.value)}
                  >
                    {tasks.map((task, i) => (
                      <option key={i} value={task}>{task}</option>
                    ))}
                  </select>

                  <div className="mt-3 p-5 bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl border-2 border-green-200 shadow-inner transform transition-transform duration-200 hover:scale-[1.02]">
                    <div className="text-lg font-semibold text-gray-800 leading-relaxed animate-pulse-slow">
                      {selectedTask}
                    </div>
                  </div>
                </div>
              )}

              {/* Image Upload Card */}
              <div className="bg-gradient-to-br from-purple-50 to-white p-6 rounded-2xl border border-purple-100 shadow-sm hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
                <label className="block font-bold text-gray-700 mb-3 text-lg flex items-center gap-2">
                  <span className="bg-purple-100 p-2 rounded-lg">
                    <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </span>
                  Upload Handwritten Image
                </label>
                
                <div className="mb-4">
                  <label className="relative cursor-pointer group">
                    <div className="border-2 border-dashed border-gray-300 rounded-2xl p-8 text-center transition-all duration-300 group-hover:border-purple-400 group-hover:bg-purple-50 group-hover:scale-[1.02]">
                      <svg className="w-12 h-12 text-gray-400 mx-auto mb-4 group-hover:text-purple-500 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                      </svg>
                      <p className="text-gray-600 group-hover:text-purple-700 transition-colors">
                        Click to upload or drag and drop
                      </p>
                      <p className="text-sm text-gray-500 mt-2">
                        PNG, JPG, GIF up to 10MB
                      </p>
                    </div>
                    <input 
                      type="file" 
                      accept="image/*" 
                      onChange={handleImageChange} 
                      className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    />
                  </label>
                </div>

                {imagePreview && (
                  <div className="mt-4 transform transition-all duration-500 animate-scale-in">
                    <div className="text-sm font-medium text-gray-700 mb-2">Preview:</div>
                    <div className="relative group">
                      <img
                        src={imagePreview}
                        alt="Preview"
                        className="w-full h-48 object-contain border-4 border-white rounded-xl shadow-lg transform transition-transform duration-300 group-hover:scale-[1.03]"
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-xl"></div>
                    </div>
                  </div>
                )}
              </div>

              {/* Submit Button */}
              <div className="sticky bottom-0 pt-4 bg-gradient-to-t from-white via-white to-transparent">
                <button
                  onClick={handleSubmit}
                  disabled={loading}
                  className={`w-full py-4 rounded-xl font-bold text-white text-lg shadow-lg transform transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] ${
                    loading 
                      ? "bg-gradient-to-r from-gray-400 to-gray-500 cursor-not-allowed" 
                      : "bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 hover:shadow-2xl"
                  }`}
                >
                  {loading ? (
                    <div className="flex items-center justify-center gap-3">
                      <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      <span>Analyzing Handwriting...</span>
                    </div>
                  ) : (
                    <div className="flex items-center justify-center gap-3">
                      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                      </svg>
                      <span>Submit for Evaluation</span>
                    </div>
                  )}
                </button>
                
                {message && (
                  <div className={`mt-4 p-4 rounded-xl text-center animate-fade-in ${
                    message.includes("successfully") 
                      ? "bg-green-50 text-green-700 border border-green-200" 
                      : "bg-red-50 text-red-700 border border-red-200"
                  }`}>
                    {message}
                  </div>
                )}
              </div>
            </div>

            {/* Results Panel */}
            <div>
              {result?.success ? (
                <div ref={resultsRef} className="space-y-6 animate-fade-in-left">
                  
                  {/* Risk Summary Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="p-6 bg-gradient-to-br from-red-50 to-white rounded-2xl border border-red-100 shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1 transform">
                      <div className="text-sm text-red-600 font-medium mb-2">Risk Level</div>
                      <div className="text-3xl font-bold text-red-700 animate-pulse-slow">
                        {result.risk_level}
                      </div>
                      <div className="mt-3 h-2 bg-red-100 rounded-full overflow-hidden">
                        <div 
                          className={`h-full rounded-full transition-all duration-1000 ease-out ${
                            result.risk_level === "High" 
                              ? "bg-red-500 w-full" 
                              : result.risk_level === "Moderate"
                              ? "bg-yellow-500 w-2/3"
                              : "bg-green-500 w-1/3"
                          }`}
                        ></div>
                      </div>
                    </div>

                    <div className="p-6 bg-gradient-to-br from-blue-50 to-white rounded-2xl border border-blue-100 shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1 transform">
                      <div className="text-sm text-blue-600 font-medium mb-2">Risk Score</div>
                      <div className="text-3xl font-bold text-blue-700">
                        {result.risk_score.toFixed(2)}
                      </div>
                      <div className="mt-3 text-sm text-gray-600">Out of 100</div>
                    </div>

                    <div className="p-6 bg-gradient-to-br from-green-50 to-white rounded-2xl border border-green-100 shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1 transform">
                      <div className="text-sm text-green-600 font-medium mb-2">Age Group</div>
                      <div className="text-3xl font-bold text-green-700">
                        {result.age_group}
                      </div>
                      <div className="mt-3 text-sm text-gray-600">Years</div>
                    </div>
                  </div>

                  {/* Explanation Card */}
                  <div className="bg-white border-2 border-gray-100 rounded-2xl shadow-lg overflow-hidden hover:shadow-xl transition-all duration-300">
                    <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-5">
                      <h3 className="font-bold text-xl text-white flex items-center gap-2">
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        Detailed Analysis & Explanation
                      </h3>
                    </div>
                    
                    <div className="p-6 space-y-6">
                      {/* Contributing Factors */}
                      <div>
                        <h4 className="font-bold text-lg text-gray-800 mb-4 flex items-center gap-2">
                          <span className="bg-blue-100 p-2 rounded-lg">
                            <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                          </span>
                          Contributing Factors
                        </h4>
                        <div className="space-y-3">
                          {result.explanation.contributing_factors.map((factor, i) => (
                            <div 
                              key={i}
                              className={`p-4 rounded-xl border-2 transform transition-all duration-300 hover:scale-[1.02] ${severityBg(factor.severity)} animate-slide-up`}
                              style={{ animationDelay: `${i * 100}ms` }}
                            >
                              <div className="flex justify-between items-center mb-2">
                                <span className="font-bold text-gray-800">
                                  {factor.feature}
                                </span>
                                <span className={`px-3 py-1 rounded-full font-bold text-sm ${severityColor(factor.severity)} bg-white`}>
                                  {factor.severity}
                                </span>
                              </div>
                              <p className="text-gray-600 text-sm leading-relaxed">
                                {factor.description}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Recommendations */}
                      <div>
                        <h4 className="font-bold text-lg text-gray-800 mb-4 flex items-center gap-2">
                          <span className="bg-green-100 p-2 rounded-lg">
                            <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                            </svg>
                          </span>
                          Recommendations
                        </h4>
                        <div className="bg-gradient-to-r from-green-50 to-emerald-50 p-4 rounded-xl border border-green-200">
                          <ul className="space-y-3">
                            {result.explanation.recommendations.map((rec, i) => (
                              <li key={i} className="flex items-start gap-3 p-3 bg-white rounded-lg border hover:shadow-md transition-all duration-200">
                                <span className="bg-green-100 text-green-800 rounded-full p-1 mt-1">
                                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                                  </svg>
                                </span>
                                <span className="text-gray-700">{rec}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>

                      {/* Strengths */}
                      <div>
                        <h4 className="font-bold text-lg text-gray-800 mb-4 flex items-center gap-2">
                          <span className="bg-yellow-100 p-2 rounded-lg">
                            <svg className="w-5 h-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                            </svg>
                          </span>
                          Strengths
                        </h4>
                        {result.explanation.strengths.length === 0 ? (
                          <div className="p-4 bg-gray-50 rounded-xl border text-center">
                            <p className="text-gray-500">No specific strengths identified.</p>
                          </div>
                        ) : (
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            {result.explanation.strengths.map((s, i) => (
                              <div 
                                key={i}
                                className="p-4 bg-gradient-to-r from-yellow-50 to-amber-50 rounded-xl border border-yellow-200 transform transition-all duration-300 hover:scale-[1.02]"
                              >
                                <div className="flex items-center gap-3">
                                  <span className="bg-yellow-100 text-yellow-800 rounded-lg p-2">
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                                    </svg>
                                  </span>
                                  <span className="text-gray-700">{s}</span>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* CLIP Analysis Card */}
                  <div className="bg-gradient-to-br from-purple-50 to-pink-50 p-6 rounded-2xl border border-purple-100 shadow-lg hover:shadow-xl transition-all duration-300">
                    <h3 className="font-bold text-xl text-gray-800 mb-4 flex items-center gap-2">
                      <span className="bg-purple-100 p-2 rounded-lg">
                        <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 10l-2 1m0 0l-2-1m2 1v2.5M20 7l-2 1m2-1l-2-1m2 1v2.5M14 4l-2-1-2 1M4 7l2-1M4 7l2 1M4 7v2.5M12 21l-2-1m2 1l2-1m-2 1v-2.5M6 18l-2-1v-2.5M18 18l2-1v-2.5" />
                        </svg>
                      </span>
                      Visual–Text Alignment (CLIP Analysis)
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="p-4 bg-white rounded-xl border shadow-sm">
                        <div className="text-sm text-purple-600 font-medium">Semantic Alignment</div>
                        <div className="text-2xl font-bold text-gray-800 mt-2">{result.semantic_alignment}</div>
                      </div>
                      <div className="p-4 bg-white rounded-xl border shadow-sm">
                        <div className="text-sm text-purple-600 font-medium">CLIP Similarity Score</div>
                        <div className="text-2xl font-bold text-gray-800 mt-2">
                          {result.clip_similarity.toFixed(2)}
                          <span className="text-sm text-gray-500 ml-2">/ 1.0</span>
                        </div>
                        <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-gradient-to-r from-purple-400 to-pink-500 rounded-full transition-all duration-1000"
                            style={{ width: `${result.clip_similarity * 100}%` }}
                          ></div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* File Info Card */}
                  <div className="p-5 bg-gray-50 rounded-2xl border border-gray-200 shadow-sm">
                    <div className="flex items-center gap-3">
                      <div className="bg-gray-100 p-3 rounded-xl">
                        <svg className="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                        </svg>
                      </div>
                      <div>
                        <div className="text-sm text-gray-500">Uploaded File</div>
                        <div className="font-medium text-gray-800 truncate">{result.filename}</div>
                      </div>
                    </div>
                  </div>

                  {/* Disclaimer */}
                  <div className="p-4 bg-gradient-to-r from-gray-50 to-gray-100 rounded-xl border border-gray-200">
                    <p className="text-xs text-gray-600 italic leading-relaxed">
                      {result.disclaimer}
                    </p>
                  </div>
                </div>
              ) : (
                /* Empty State for Results Panel */
                <div className="h-full flex flex-col items-center justify-center p-12 text-center border-2 border-dashed border-gray-200 rounded-2xl bg-gradient-to-br from-gray-50 to-white animate-pulse-slow">
                  <div className="w-24 h-24 bg-gradient-to-r from-blue-100 to-purple-100 rounded-full flex items-center justify-center mb-6">
                    <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-semibold text-gray-700 mb-2">
                    Awaiting Analysis Results
                  </h3>
                  <p className="text-gray-500 max-w-md">
                    Submit a handwriting sample to see detailed analysis, risk assessment, and personalized recommendations.
                  </p>
                  <div className="mt-8 flex space-x-4">
                    <div className="w-3 h-3 bg-blue-400 rounded-full animate-bounce"></div>
                    <div className="w-3 h-3 bg-purple-400 rounded-full animate-bounce delay-75"></div>
                    <div className="w-3 h-3 bg-pink-400 rounded-full animate-bounce delay-150"></div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Add custom animations to Tailwind */}
      <style jsx>{`
        @keyframes gradient {
          0% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
          100% { background-position: 0% 50%; }
        }
        
        @keyframes fadeInDown {
          from {
            opacity: 0;
            transform: translateY(-20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        @keyframes fadeInLeft {
          from {
            opacity: 0;
            transform: translateX(20px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }
        
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        
        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        @keyframes scaleIn {
          from {
            opacity: 0;
            transform: scale(0.95);
          }
          to {
            opacity: 1;
            transform: scale(1);
          }
        }
        
        @keyframes expand {
          from { width: 0; }
          to { width: 6rem; }
        }
        
        .animate-gradient {
          background-size: 200% 200%;
          animation: gradient 15s ease infinite;
        }
        
        .animate-fade-in-down {
          animation: fadeInDown 0.6s ease-out;
        }
        
        .animate-fade-in-up {
          animation: fadeInUp 0.6s ease-out;
        }
        
        .animate-fade-in-left {
          animation: fadeInLeft 0.6s ease-out;
        }
        
        .animate-fade-in {
          animation: fadeIn 0.3s ease-out;
        }
        
        .animate-slide-up {
          animation: slideUp 0.4s ease-out;
        }
        
        .animate-scale-in {
          animation: scaleIn 0.3s ease-out;
        }
        
        .animate-expand {
          animation: expand 0.8s ease-out;
        }
        
        .animate-pulse-slow {
          animation: pulse 3s ease-in-out infinite;
        }
      `}</style>
    </div>
  )
}

export default DysgraphiaAssessment