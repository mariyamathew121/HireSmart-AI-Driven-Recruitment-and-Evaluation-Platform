import React from 'react';
import { useNavigate } from 'react-router-dom';
import './IntroPage.css';

const IntroPage = () => {
  const navigate = useNavigate();

  return (
    <div className="intro-container">
      <h1>Welcome to HireSmart</h1>
      <p>Log in or sign up to get started</p>
      <div className="button-group">
        <button className="intro-login-button" onClick={() => navigate('/login')}>
          Log in
        </button>
        <button className="intro-signup-button" onClick={() => navigate('/signup')}>
          Sign up
        </button>
      </div>
    </div>
  );
};

export default IntroPage;
