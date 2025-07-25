// TODO: Add voice input using Web Speech API for seller bot
// See: https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API/Using_the_Web_Speech_API
// You can add a microphone button and use window.SpeechRecognition

import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import './SellerBotPopup.css';

const SELLER_IMG = 'https://img.freepik.com/photos-premium/femme-souriante-profitant-journee-ensoleillee_1257736-11056.jpg'; // Placeholder seller image

export default function SellerBotPopup({ show, onClose }) {
  const [messages, setMessages] = useState([
    { from: 'bot', text: 'Asleeema! I\'m **Amira**, your CLOESS style assistant. How can I help you discover beautiful **Tunisian fashion** today? 🌟\n\nYou can ask me:\n• **Product availability** and stock\n• **Price ranges** and categories\n• **Traditional artisanat** information' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const chatEndRef = useRef(null);

  useEffect(() => {
    if (show && chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, show]);

  const sendMessage = async () => {
    if (!input.trim()) return;
    const userMsg = { from: 'user', text: input };
    setMessages((msgs) => [...msgs, userMsg]);
    setInput('');
    setLoading(true);
    setIsTyping(true);
    
    try {
      const requestBody = { 
        message: userMsg.text,
        session_id: sessionId 
      };
      
      const res = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });
      const data = await res.json();
      
      // Update session ID if provided by server
      if (data.session_id && !sessionId) {
        setSessionId(data.session_id);
      }
      
      // Simulate typing delay for more natural feel
      setTimeout(() => {
        setMessages((msgs) => [...msgs, { from: 'bot', text: data.response }]);
        setIsTyping(false);
      }, 1000);
    } catch (e) {
      setTimeout(() => {
        setMessages((msgs) => [...msgs, { from: 'bot', text: 'Sorry, I could not connect to the server. Please try again later! 😊' }]);
        setIsTyping(false);
      }, 1000);
    }
    setLoading(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') sendMessage();
  };

  const toggleMinimize = () => {
    setIsMinimized(!isMinimized);
  };

  if (!show) return null;

  return (
    <div className={`sellerbot-popup ${isMinimized ? 'minimized' : ''}`}>
      {/* Character Section */}
      <div className="sellerbot-character">
        <div className="character-container">
          <img src={SELLER_IMG} alt="Amira - Style Assistant" className="character-img" />
          {!isMinimized && (
            <div className="character-greeting">
              <div className="greeting-bubble">
                <span>Asleeema!</span>
              </div>
            </div>
          )}
        </div>
      </div>
      
      {/* Glassmorphism Chat Window */}
      <div className="chat-window">
        <div className="chat-header">
          <div className="header-content">
            <div className="assistant-info">
              <span className="assistant-name">Amira</span>
              <span className="assistant-title">Tunisian Style Assistant</span>
            </div>
            <div className="header-controls">
              <button className="minimize-btn" onClick={toggleMinimize} title={isMinimized ? "Expand" : "Minimize"}>
                {isMinimized ? (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                    <path d="M7 14l5-5 5 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                ) : (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                    <path d="M7 10l5 5 5-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                )}
              </button>
              <button className="close-btn" onClick={onClose} title="Close">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                  <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
        
        {!isMinimized && (
          <>
            <div className="chat-messages">
              {messages.map((msg, i) => (
                <div key={i} className={`message ${msg.from}`}>
                  <div className="message-content">
                    <ReactMarkdown 
                      components={{
                        // Customize rendering for different elements
                        p: ({node, ...props}) => <span {...props} />, // Render paragraphs as spans to avoid extra spacing
                        strong: ({node, ...props}) => <strong style={{fontWeight: '600', color: 'inherit'}} {...props} />,
                        em: ({node, ...props}) => <em style={{fontStyle: 'italic'}} {...props} />,
                        ul: ({node, ...props}) => <ul style={{margin: '0.5rem 0', paddingLeft: '1.2rem'}} {...props} />,
                        ol: ({node, ...props}) => <ol style={{margin: '0.5rem 0', paddingLeft: '1.2rem'}} {...props} />,
                        li: ({node, ...props}) => <li style={{marginBottom: '0.25rem'}} {...props} />,
                        br: () => <br />
                      }}
                    >
                      {msg.text}
                    </ReactMarkdown>
                  </div>
                </div>
              ))}
              {isTyping && (
                <div className="message bot typing">
                  <div className="message-content">
                    <div className="typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>
            
            <div className="chat-input">
              <div className="input-container">
                <input
                  type="text"
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask about Tunisian styles, sizes..."
                  disabled={loading}
                  className="message-input"
                />
                <button 
                  onClick={sendMessage} 
                  disabled={loading || !input.trim()}
                  className="send-button"
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                    <path d="m5 12 7-7 7 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" transform="rotate(90 12 12)"/>
                  </svg>
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
} 