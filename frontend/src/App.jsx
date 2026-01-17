import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import WritingTest from './pages/WritingTest'

function App() {
  return (
   <BrowserRouter>
   <div>
   <Routes>
    <Route path="/" element={<WritingTest />} />
   </Routes>
   </div>
   </BrowserRouter>
  )
}

export default App
