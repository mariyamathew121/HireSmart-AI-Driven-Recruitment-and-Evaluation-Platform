import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login } from './api';
import './LoginPage.css';

function LoginPage({ onLogin }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate(); // Hook for navigation

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const response = await login(email, password);
      if (response.data) {
      // Store user_id in localStorage for global access
      localStorage.setItem("user_id", response.data.user_id);
      onLogin();
      navigate('/quiz');
      }
    } catch (error) {
      let errorMessage = 'Login failed! ';
      if (error.response) {
        errorMessage += error.response.data?.message || 'Please check your credentials.';
      } else if (error.request) {
        errorMessage = 'Cannot connect to server. Please check if the server is running.';
      } else {
        errorMessage += 'Please try again later.';
      }
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-container">
      <form className="login-form" onSubmit={handleSubmit}>
        <h2>Login</h2>
        {error && <div className="error-message">{error}</div>}
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          disabled={isLoading}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          disabled={isLoading}
        />
        <button type="submit" disabled={isLoading} className="login-button">
          {isLoading ? 'Logging in...' : 'Login'}
        </button>
        <button
          type="button"
          className="signup-redirect"
          onClick={() => navigate('/signup')}
        >
          <span className="signup-text">Don't have an account? </span>
          <span className="signup-link">Sign up</span>
        </button>
      </form>
    </div>
  );
}

export default LoginPage;
