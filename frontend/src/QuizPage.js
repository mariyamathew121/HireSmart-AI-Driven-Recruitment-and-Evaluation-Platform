import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import "./QuizPage.css";

function QuizPage() {
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [loading, setLoading] = useState(true);
  const videoRef = useRef(null);
  const socketRef = useRef(null);
  const navigate = useNavigate();

  const ALERT_THRESHOLD = 7; // Number of alerts before disqualification
  let alertCount = 0;

  useEffect(() => {
    async function fetchQuestions() {
      const url = "https://aptitude-api.vercel.app/Random";
      const fetchedQuestions = [];

      try {
        for (let i = 1; i <= 5; i++) { // Fetch 5 questions
          const response = await fetch(url);
          if (!response.ok) throw new Error(`Error fetching question ${i}`);

          const questionData = await response.json();
          questionData.id = i;
          fetchedQuestions.push(questionData);
        }
        setQuestions(fetchedQuestions);
      } catch (error) {
        console.error("Failed to fetch questions:", error);
        toast.error("An error occurred while loading questions. Please try again.");
      } finally {
        setLoading(false);
      }
    }
    fetchQuestions();
  }, []);

  useEffect(() => {
    // Establish WebSocket connection
    socketRef.current = new WebSocket("ws://127.0.0.1:8000/ws");
    socketRef.current.binaryType = "arraybuffer";

    socketRef.current.onmessage = (event) => {
      const message = event.data;
      console.log("[WebSocket] Received:", message);

      if (message.startsWith("Alert:")) {
        alertCount++;
        toast.error(message, {
          autoClose: 8000,
          style: { fontSize: "20px", padding: "20px", width: "400px", textAlign: "center" },
        });

        if (alertCount >= ALERT_THRESHOLD) {
          socketRef.current.close();
          navigate("/disqualified");
        }
      }
    };

    socketRef.current.onclose = () => console.log("[WebSocket] Connection closed");

    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  });

  useEffect(() => {
    navigator.mediaDevices.getUserMedia({ video: true })
      .then((stream) => {
        if (videoRef.current) videoRef.current.srcObject = stream;

        const video = videoRef.current;
        const canvas = document.createElement("canvas");
        const ctx = canvas.getContext("2d");
        let lastFrameTime = 0;
        const frameInterval = 100; // Send frames every 100ms (10 fps)

        const sendFrame = () => {
          const now = Date.now();
          if (now - lastFrameTime >= frameInterval && video?.readyState === 4) {
            lastFrameTime = now;
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

            canvas.toBlob((blob) => {
              if (socketRef.current.readyState === WebSocket.OPEN && blob) {
                blob.arrayBuffer().then((buffer) => {
                  socketRef.current.send(buffer);
                });
              }
            }, "image/jpeg");
          }
          requestAnimationFrame(sendFrame);
        };

        sendFrame();
      })
      .catch((err) => {
        console.error("Camera access error:", err);
        toast.error("Camera access is required for the exam.");
      });
  }, []);

  const handleAnswerChange = (questionId, answer) => {
    setAnswers((prev) => ({ ...prev, [questionId]: answer }));
  };

  const handleSubmit = async () => {
  let score = 0;
  questions.forEach((q) => {
    if (answers[q.id] === q.answer) score++;
  });

  // Assuming you have the user's id stored in localStorage (or from your global state)
  const user_id = localStorage.getItem("user_id"); // or however you store it

  if (!user_id) {
    console.error("No user_id available. Score cannot be submitted.");
    return;
  }

  try {
    const response = await fetch("http://127.0.0.1:8000/submit", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ user_id, score }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Error submitting score");
    }

    const data = await response.json();
    console.log("Score submitted successfully:", data);
  } catch (error) {
    console.error("Failed to submit score:", error);
  }

  navigate("/results", { state: { score } });
};


  return (
    <div className="quiz-container">
      {/* Video Preview Container */}
      <div className="video-container">
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          style={{ width: "300px", height: "250px", border: "2px solid #333", borderRadius: "5px" }}
        />
      </div>
      
      <h1 className="quiz-title">Quiz</h1>

      {/* Show loading indicator while fetching questions */}
      {loading ? (
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p className="loading-text">Loading Questions...</p>
        </div>
      ) : (
        questions.map((q) => (
          <div key={q.id} className="question-card">
            <h3 className="question-text">{q.question}</h3>
            <div className="options-container">
              {q.options.map((option) => (
                <label key={option} className="option-label">
                  <input
                    type="radio"
                    name={q.id}
                    value={option}
                    checked={answers[q.id] === option}
                    onChange={() => handleAnswerChange(q.id, option)}
                  />
                  {option}
                </label>
              ))}
            </div>
          </div>
        ))
      )}

      {!loading && (
        <button className="submit-button" onClick={handleSubmit}>
          Submit Quiz
        </button>
      )}

      {/* Toast Notification Container */}
      <ToastContainer
        position="top-right"
        toastStyle={{ fontSize: "20px", padding: "20px", width: "400px", textAlign: "center" }}
      />
    </div>
  );
}

export default QuizPage;
