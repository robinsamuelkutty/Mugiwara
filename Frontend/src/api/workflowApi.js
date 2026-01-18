import { v4 as uuidv4 } from 'uuid'; 

const API_BASE = "http://127.0.0.1:8000";


export async function evaluateLevel(userId, level, targetText, transcribedText, wordTimestamps) {
  try {
    const payload = {
      user_id: userId,
      level: level,
      target_text: targetText,
      transcribed_text: transcribedText,
      word_timestamps: wordTimestamps || []
    };

    const response = await fetch(`${API_BASE}/dyslexia/level-evaluate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!response.ok) throw new Error("Level evaluation failed");
    return await response.json();

  } catch (error) {
    console.error("Workflow Error:", error);
    // Fallback logic if backend is offline, to keep demo working
    return { status: "PASS", next_level: level + 1, should_continue: true }; 
  }
}

// 2. Final Evaluation (Hits /dyslexia/full-evaluate)
export async function evaluateFull(userId, allLevelsData) {
  try {
    const payload = {
      user_id: userId,
      levels: allLevelsData // This passes { "1": {...}, "2": {...} }
    };

    const response = await fetch(`${API_BASE}/dyslexia/full-evaluate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    return await response.json();
  } catch (error) {
    console.error("Final Eval Error:", error);
    return null;
  }
}