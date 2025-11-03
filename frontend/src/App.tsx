import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { LiveTestPage } from './pages/LiveTestPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Make the live test page the new homepage */}
        <Route path="/" element={<LiveTestPage />} />

        {/* You can add other routes here later */}
        {/* <Route path="/login" element={...} /> */}
      </Routes>
    </BrowserRouter>
  );
}

export default App;