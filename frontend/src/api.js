import axios from 'axios';

const API_URL = "http://localhost:8000";

export const login = async (email, password) => {
  return await axios.post(`${API_URL}/login`, { email, password });
};

export const getQuestions = async () => {
  return await axios.get(`${API_URL}/questions`);
};

export const submitAnswers = async (answers) => {
  return await axios.post(`${API_URL}/submit`, { answers });
};

export const signup = async (formData)=>{
  return await axios.post("http://localhost:8000/signup", formData)
}