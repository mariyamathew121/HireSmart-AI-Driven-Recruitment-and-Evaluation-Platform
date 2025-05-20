import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import './ResultPage.css'

function ResultsPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { score } = location.state || { score: 0 };

  return (
    <div className="results-container">
      <h1>Your Results</h1>
      <p className="score-text">You scored: {score}</p>
      <button className="retry-button" onClick={() => navigate('/quiz')}>
        Retry Quiz
      </button>
    </div>
  );
}

export default ResultsPage;