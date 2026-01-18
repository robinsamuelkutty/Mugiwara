const API_BASE = "http://127.0.0.1:8000";

export async function fetchDyscalculiaNumbers(count = 6) {
  try {
    const response = await fetch(`${API_BASE}/dyscalculia/number_generator?n=${count}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });

    if (!response.ok) throw new Error("Failed to fetch numbers");

    const textData = await response.json(); 
    if (typeof textData === 'string') {
        return textData.split(" ").filter(n => n.trim().length > 0);
    }
    return ["123", "456", "789", "101", "202", "303"];
  } catch (error) {
    console.error("Dyscalculia API Error:", error);
    return ["123", "456", "789", "101", "202", "303"];
  }
}

// ✅ FIX: Explicitly exporting this function
export async function uploadHandwritingImage(imageFile) {
  const formData = new FormData();
  // The backend expects the file key to be 'image' (matches 'image: UploadFile' in FastAPI)
  formData.append("image", imageFile);

  try {
    // UPDATED: Changed endpoint from 'problem_detector' to 'number_detector'
    const response = await fetch(`${API_BASE}/dyscalculia/number_detector`, {
      method: "POST",
      body: formData,
      // Do NOT set Content-Type header for FormData, browser does it automatically
    });

    if (!response.ok) {
        const err = await response.text();
        throw new Error("Analysis failed: " + err);
    }

    const data = await response.json();
    return data; // Returns { filename: "...", result: "LIKELY/UNLIKELY..." }
  } catch (error) {
    console.error("Upload Error:", error);
    throw error;
  }
}
export async function uploadProblemImage(imageFile) {
  const formData = new FormData();
  formData.append("image", imageFile);

  try {
    // Points to the NEW endpoint
    const response = await fetch(`${API_BASE}/dyscalculia/problem_detector`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
        const err = await response.text();
        throw new Error("Analysis failed: " + err);
    }

    const data = await response.json();
    return data; // Returns the full JSON object (digits, analysis, risk, etc.)
  } catch (error) {
    console.error("Upload Error:", error);
    throw error;
  }
}