import { BrowserRouter, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Home from "./pages/Home";
import ReadingTest from "./pages/ReadingTest";
import RhymeTest from "./pages/RhymeTest";
import RANTest from "./pages/RANTest";
import NonsenseTest from "./pages/NonsenseTest";
import DyscalculiaTest from "./pages/DyscalculiaTest";
import { AssessmentProvider } from "./context/AssessmentContext";
import ReportPage from "./pages/ReportPage";
import DyscalculiaProblemTest from "./pages/DyscalculiaProblemTest";
import WritingTest from "./pages/WritingTest";

function App() {
  return (
    <AssessmentProvider>
    <BrowserRouter>
      <Navbar />
      
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/test" element={<ReadingTest />} />
        <Route path="/rhyme" element={<RhymeTest />} />
        <Route path="/ran" element={<RANTest />} />
        <Route path="/nonsense" element={<NonsenseTest />} />
        <Route path="/dyscalculia" element={<DyscalculiaTest />} />
        <Route path="/dyscalculiaproblem" element={<DyscalculiaProblemTest />} />
        <Route path="/report" element={<ReportPage />} />
        <Route path="/dysgraphia" element={<WritingTest />} />
      </Routes>
    </BrowserRouter>
    </AssessmentProvider>
  );
}

export default App;