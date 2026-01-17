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
    if (result && result.success && resultsRef.current) {
      setTimeout(() => {
        resultsRef.current.scrollIntoView({
          behavior: "smooth",
          block: "start",
        })
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

  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-gray-100 to-gray-200 p-4">
      <div className="max-w-7xl mx-auto">
        <div className="bg-white shadow-2xl rounded-2xl p-6 md:p-8 space-y-8">

          {/* Header */}
          <div className="text-center">
            <h1 className="text-3xl md:text-4xl font-bold text-gray-800">
              Dysgraphia Handwriting Assessment
            </h1>
            <p className="text-gray-600 mt-2">
              AI-powered handwriting analysis (screening tool)
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

            {/* Inputs */}
            <div className="space-y-6">
              <div>
                <label className="block font-semibold mb-2">Select Age</label>
                <select
                  className="w-full border rounded-lg p-3"
                  value={selectedAge}
                  onChange={(e) => setSelectedAge(e.target.value)}
                >
                  <option value="">-- Select Age --</option>
                  {Array.from({ length: 11 }, (_, i) => i + 5).map((age) => (
                    <option key={age} value={age}>{age}</option>
                  ))}
                </select>
              </div>

              {tasks.length > 0 && (
                <div>
                  <label className="block font-semibold mb-2">
                    Copy the following sentence
                  </label>
                  <select
                    className="w-full border rounded-lg p-3"
                    value={selectedTask}
                    onChange={(e) => setSelectedTask(e.target.value)}
                  >
                    {tasks.map((task, i) => (
                      <option key={i} value={task}>{task}</option>
                    ))}
                  </select>

                  <div className="mt-3 p-4 bg-blue-50 rounded-lg border">
                    {selectedTask}
                  </div>
                </div>
              )}

              <div>
                <label className="block font-semibold mb-2">
                  Upload Handwritten Image
                </label>
                <input type="file" accept="image/*" onChange={handleImageChange} />
                {imagePreview && (
                  <img
                    src={imagePreview}
                    alt="Preview"
                    className="mt-3 max-h-48 border rounded"
                  />
                )}
              </div>

              <button
                onClick={handleSubmit}
                disabled={loading}
                className={`w-full py-3 rounded-lg font-bold text-white ${
                  loading ? "bg-gray-400" : "bg-blue-600 hover:bg-blue-700"
                }`}
              >
                {loading ? "Analyzing..." : "Submit for Evaluation"}
              </button>

              {message && (
                <p className="text-center text-sm text-gray-600">{message}</p>
              )}
            </div>

            {/* Results */}
            <div>
              {result && result.success && (
                <div ref={resultsRef} className="space-y-6">

                  {/* Summary */}
                  <div className="grid grid-cols-3 gap-4">
                    <div className="p-4 bg-gray-50 rounded-lg text-center">
                      <div className="text-sm text-gray-500">Risk Level</div>
                      <div className={`text-xl font-bold ${
                        result.risk_level === "High"
                          ? "text-red-600"
                          : result.risk_level === "Moderate"
                          ? "text-yellow-600"
                          : "text-green-600"
                      }`}>
                        {result.risk_level}
                      </div>
                    </div>

                    <div className="p-4 bg-gray-50 rounded-lg text-center">
                      <div className="text-sm text-gray-500">Risk Score</div>
                      <div className="text-xl font-bold">
                        {result.risk_score.toFixed(2)}
                      </div>
                      <div className="h-2 bg-gray-200 rounded-full mt-2">
                        <div
                          className="h-full bg-blue-500 rounded-full"
                          style={{ width: `${Math.round(result.risk_score * 100)}%` }}
                        />
                      </div>
                    </div>

                    <div className="p-4 bg-gray-50 rounded-lg text-center">
                      <div className="text-sm text-gray-500">Age Group</div>
                      <div className="text-xl font-bold">
                        {result.age_group}
                      </div>
                    </div>
                  </div>

                  {/* CLIP */}
                  <div className="p-4 bg-white border rounded-lg">
                    <h3 className="font-bold mb-2">Visual–Text Alignment (CLIP)</h3>
                    <p><strong>Alignment:</strong> {result.semantic_alignment}</p>
                    <p><strong>CLIP Similarity:</strong> {result.clip_similarity.toFixed(2)}</p>
                  </div>

                  {/* ViT */}
                  {(result.vit_structural_irregularity !== undefined ||
                    result.features_raw?.vit_structural_irregularity !== undefined) && (
                    <div className="p-4 bg-white border rounded-lg">
                      <h3 className="font-bold mb-2">
                        Handwriting Structural Consistency (ViT)
                      </h3>

                      {(() => {
                        const vit =
                          result.vit_structural_irregularity ??
                          result.features_raw?.vit_structural_irregularity

                        let label = "Low Irregularity"
                        let color = "text-green-600"

                        if (vit > 0.6) {
                          label = "High Irregularity"
                          color = "text-red-600"
                        } else if (vit > 0.35) {
                          label = "Moderate Irregularity"
                          color = "text-yellow-600"
                        }

                        return (
                          <>
                            <p>
                              <strong>Pattern:</strong>{" "}
                              <span className={`font-semibold ${color}`}>
                                {label}
                              </span>
                            </p>
                            <p><strong>ViT Score:</strong> {vit.toFixed(2)}</p>
                            <div className="h-2 bg-gray-200 rounded-full mt-2">
                              <div
                                className="h-full bg-purple-500 rounded-full"
                                style={{ width: `${Math.round(vit * 100)}%` }}
                              />
                            </div>
                          </>
                        )
                      })()}
                    </div>
                  )}

                  {/* Disclaimer */}
                  <p className="text-xs text-gray-500 italic">
                    {result.disclaimer}
                  </p>

                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default DysgraphiaAssessment
