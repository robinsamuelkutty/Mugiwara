export async function fetchStory(difficulty = "medium", age = 8) {
  // Build the URL with query parameters
  const params = new URLSearchParams({
    difficulty: difficulty,
    age: age,
    // You can add theme/gender here if you want
  });

  try {
    const response = await fetch(`http://127.0.0.1:8000/dyslexia/story?${params}`);
    if (!response.ok) throw new Error("Failed to fetch story");
    
    const data = await response.json();
    return data; // Assuming backend returns { "story": "Once upon a time..." } or just the string
  } catch (error) {
    console.error("Story Fetch Error:", error);
    return null;
  }
}

export async function sendAudio(audioBlob, targetText) {
  const formData = new FormData();
  
  // 1. Append your data
  formData.append("audio_file", audioBlob, "recording.webm");
  formData.append("target_text", targetText);

  // ---------------------------------------------------------
  // 🔍 DEBUGGING SECTION: This is how you inspect FormData
  // ---------------------------------------------------------
  console.log("--- 📦 Preparing to Send Data ---");
  
  // Check the text field
  console.log("📝 Target Text:", formData.get("target_text"));
  
  // Check the file details specifically
  const file = formData.get("audio_file");
  console.log("🎤 Audio File Details:", {
    name: file.name,
    size: file.size + " bytes",
    type: file.type
  });

  // (Optional) Loop through everything to be sure
  for (let [key, value] of formData.entries()) {
    console.log(`${key}:`, value);
  }
  console.log("-----------------------------------");
  // ---------------------------------------------------------

  const response = await fetch("http://127.0.0.1:8000/analyze-audio", {
    method: "POST",
    body: formData
    // Note: Do NOT set "Content-Type": "application/json" manually here. 
    // The browser sets the correct "multipart/form-data" boundary automatically.
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error("❌ Backend Error:", errorText); // See the exact error from Python
    throw new Error("Backend error");
  }

  const data = await response.json();
  console.log("✅ Backend Response:", data); // See what Python sent back
  return data;
}
export async function compareAudio(transcriptionData) {
  try {
    const response = await fetch("http://127.0.0.1:8000/dyslexia/compare", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(transcriptionData),
    });

    if (!response.ok) throw new Error("Comparison failed");

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Comparison Error:", error);
    return null;
  }
}

export async function fetchRhymes(level = "easy") {
  try {
    const response = await fetch(`http://127.0.0.1:8000/dyslexia/rhymes?level=${level}`);
    if (!response.ok) throw new Error("Failed to fetch rhymes");
    
    const data = await response.json();
    return data.rhymes; // Returns ["cat hat", "sun run", ...]
  } catch (error) {
    console.error("Rhyme Fetch Error:", error);
    return ["cat hat", "sun run"]; // Fallback
  }
}

export async function fetchRANGrid() {
  try {
    const response = await fetch("http://127.0.0.1:8000/dyslexia/ran");
    if (!response.ok) throw new Error("Failed to fetch RAN grid");
    return await response.json();
  } catch (error) {
    console.error("RAN Fetch Error:", error);
    return null;
  }
}

export async function fetchNonsenseWords() {
  try {
    const response = await fetch("http://127.0.0.1:8000/dyslexia/nonsense");
    if (!response.ok) throw new Error("Failed to fetch nonsense words");
    return await response.json();
  } catch (error) {
    console.error("Nonsense Fetch Error:", error);
    return { words: "zog pleet brimpf dresp thazz" }; // Fallback
  }
}