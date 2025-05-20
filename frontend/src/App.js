import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import IntroPage from './IntroPage'; // Import the IntroPage
import LoginPage from './LoginPage';
import Signup from './SignupPage';
import QuizPage from './QuizPage';
import './App.css';
import ResultsPage from './ResultPage';
import DisqualifiedPage from './DisqualifiedPage';


function App() {
  const [loggedIn, setLoggedIn] = useState(false);
  return (
    <Router>
      <div className="app-container">
        <Routes>
          {/* IntroPage as the default initial route */}
          <Route path="/" element={<IntroPage />} />
          {/* LoginPage route */}
          <Route
            path="/login"
            element={<LoginPage onLogin={() => setLoggedIn(true)} />}
          />
          {/* SignupPage route */}
          <Route path="/signup" element={<Signup />} />
          
          {/* QuizPage for authenticated users */}
          <Route path="/quiz" element={loggedIn ? <QuizPage /> : <LoginPage onLogin={() => setLoggedIn(true)} />} />
          
          <Route path="/results" element={<ResultsPage />} />
          <Route path="/disqualified" element={<DisqualifiedPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
