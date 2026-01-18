import { createContext, useContext, useState, useEffect } from "react";
import { v4 as uuidv4 } from 'uuid';

const AssessmentContext = createContext();

export function AssessmentProvider({ children }) {
  // 1. Generate a unique ID for this child's session
  const [userId, setUserId] = useState("");
  
  // 2. Store results from each level
  // Format: { 1: {target: "...", transcribed: "..."}, 2: {...} }
  const [levelResults, setLevelResults] = useState({});

  useEffect(() => {
    // Check if we already have an ID, if not create one
    let id = localStorage.getItem("dyslexia_user_id");
    if (!id) {
        id = uuidv4();
        localStorage.setItem("dyslexia_user_id", id);
    }
    setUserId(id);
  }, []);

  const saveLevelData = (level, data) => {
    setLevelResults(prev => ({
      ...prev,
      [level]: data
    }));
  };

  return (
    <AssessmentContext.Provider value={{ userId, levelResults, saveLevelData }}>
      {children}
    </AssessmentContext.Provider>
  );
}

export const useAssessment = () => useContext(AssessmentContext);