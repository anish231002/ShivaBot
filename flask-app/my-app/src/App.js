import React, { useRef, useState, useEffect } from "react";
import "./App.css"; // Copy your CSS from index.html <style> to App.css

function App() {
  const [messages, setMessages] = useState([
    {
      text: "Jay Maharashtra! I am Chhatrapati Shivaji Maharaj. How may I be of service to you today?",
      type: "received",
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);
  const [input, setInput] = useState("");
  const [ttsPlaying, setTtsPlaying] = useState(false);
  const [theme, setTheme] = useState("light");
  const chatEndRef = useRef(null);

  useEffect(() => {
    if (chatEndRef.current) chatEndRef.current.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    document.body.setAttribute("data-theme", theme);
  }, [theme]);

  const sendMessage = async (msg) => {
    if (!msg.trim()) return;
    const time = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    setMessages((msgs) => [...msgs, { text: msg, type: "sent", time }]);
    setInput("");
    try {
      const res = await fetch("http://127.0.0.1:5000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg }),
      });
      const data = await res.json();

      if (!data.response) {
        console.error("No response received from server");
        return;
      }

      // Set the response message first
      setMessages((msgs) => [
        ...msgs,
        {
          text: data.response,
          type: "received",
          time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);

      // Play audio from audio_url if available
      if (data.audio_url) {
        const audio = new Audio(`http://127.0.0.1:5000${data.audio_url}`);
        audio.play().catch((err) => console.error("Audio play error:", err));
      } else {
        // Fallback to TTS if no audio_url
        setTimeout(async () => {
          await playTTS(data.response);
        }, 100);
      }
    } catch {
      setMessages((msgs) => [
        ...msgs,
        {
          text: "Sorry, could not connect to the server.",
          type: "received",
          time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      sendMessage(input);
    }
  };

  const handleMic = () => {
    if (!("webkitSpeechRecognition" in window)) {
      alert("Speech Recognition not supported!");
      return;
    }
    setMessages((msgs) => [
      ...msgs,
      {
        text: "[ Maharaj is listening... ]",
        type: "info",
        time: "",
      },
    ]);
    const recognition = new window.webkitSpeechRecognition();
    recognition.lang = "en-IN";
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setInput(transcript);
      sendMessage(transcript);
    };
    recognition.start();
  };

  // Function to play TTS and manage mic button state
  const playTTS = async (text) => {
    let audioElement = null;
    try {
      setTtsPlaying(true);
      console.log("Requesting TTS for:", text);
      
      const res = await fetch("http://127.0.0.1:5000/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      
      if (!res.ok) {
        const errorData = await res.json();
        console.error("TTS Error:", errorData);
        setTtsPlaying(false);
        return;
      }

      const blob = await res.blob();
      if (blob.size === 0) {
        console.error("Received empty audio blob");
        setTtsPlaying(false);
        return;
      }

      console.log("Received audio blob of size:", blob.size);
      const url = URL.createObjectURL(blob);
      
      // Create and configure audio element
      audioElement = new Audio();
      
      // Set up event listeners
      audioElement.onended = () => {
        console.log("Audio playback completed");
        setTtsPlaying(false);
        URL.revokeObjectURL(url);
      };
      
      audioElement.onerror = (e) => {
        console.error("Audio playback error:", e);
        setTtsPlaying(false);
        URL.revokeObjectURL(url);
      };

      // Load and play the audio
      audioElement.src = url;
      await audioElement.play();
      console.log("Audio playback started");
    } catch (error) {
      console.error("TTS/playTTS error:", error);
      setTtsPlaying(false);
    }
  };

  const getMsgClass = (type) => {
    if (type === "sent") return "message sent";
    if (type === "received") return "message received";
    if (type === "info") return "message info";
    return "message";
  };

  return (
    <div className="container">
      <header className="header">
        <div className="header-left">
          <div className="avatar-header">
            <img
              src="/front_angle.jpg"
              alt="Profile"
              style={{ width: "100%", height: "100%", borderRadius: "50%" }}
            />
          </div>
          <h1>AI VideoBot</h1>
          <span className="status-dot online"></span>
          <p>Talk with Chartrapati Shivaji Maharaj</p>    
          <span className="status-dot in-progress"></span>   
        </div>
        <div className="header-right">
          <span className="status-dot connected"></span>
          <p>Connected</p>
          <button
            style={{
              marginTop: "10px",
              padding: "6px 16px",
              borderRadius: "20px",
              border: "none",
              background: "var(--accent-color)",
              color: "#fff",
              cursor: "pointer"
            }}
            onClick={() => setTheme(theme === "light" ? "dark" : "light")}
          >
            {theme === "light" ? "🌙 Dark" : "☀️ Light"}
          </button>
        </div>
      </header>
      <main className="main-content">
        <div className="video-section">
          <div className="user-video-preview">
            <span className="material-icons">person</span>
            <p>You</p>
          </div>
          <div className="main-video-area">
            <div
              className="main-video-placeholder"
              style={{
                width: "400px",
                height: "300px",
                overflow: "hidden",
                display: "flex",
                justifyContent: "center",
                alignItems: "center",   
                borderRadius: "50%",
                background: "/front_angle.jpg",
              }}
            >
              <img
                src="/front_angle.jpg"
                alt="Shivaji Maharaj"
                style={{
                  width: "100%",
                  height: "100%",
                  objectFit: "cover",
                  borderRadius: "50%"
                }}
              />
            </div>
            <p> </p>           
            <button className="ai-powered-avatar-btn">AI-Powered Avatar</button>
          </div>
          <div className="controls"></div>
        </div>
        <div className="chat-section">
          <div className="chat-header">
            <span className="material-icons">chat</span>
            <h2>Chat</h2>
          </div>
          <div className="chat-messages">
            {messages.map((msg, idx) => (
              <div className={getMsgClass(msg.type)} key={idx}>
                <div className="avatar-chat">
                    <img
                      src={msg.type === "sent" ? "/guardian_logo.png" : "/front_angle.jpg"}
                      alt={msg.type === "sent" ? "User Profile" : "Shivaji Maharaj"}
                      style={{ width: "100%", height: "100%", borderRadius: "50%" }}
                    />
                </div>
                <p>{msg.text}</p>
                {msg.time && <span>{msg.time}</span>}
              </div>
            ))}
            <div ref={chatEndRef}></div>
          </div>
          <div className="chat-input">
            <input
              type="text"
              lang="mr"
              placeholder="Type your message..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
            />
            <button onClick={handleMic} title="Speak" disabled={ttsPlaying}>
              <span className="material-icons">mic</span>
            </button>
            <button onClick={() => sendMessage(input)} title="Send" disabled={ttsPlaying}>
              <span className="material-icons">send</span>
            </button>
          </div>
        </div>
      </main>
      {/* Optional: style info messages */}
      <style>{`
        .message.info p {
          font-style: italic;
          color: #888;
          background: none;
          text-align: center;
        }
      `}</style>
      {/* Audio plays automatically in the background */}
    </div>
  );
}

export default App;
