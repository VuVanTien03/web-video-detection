import React, { useState } from 'react';
import './Chatbot.scss';

const Chatbot = () => {
  const [isOpen, setIsOpen] = useState(false);
  
  return (
    <div className={`chatbot ${isOpen ? 'chatbot--open' : ''}`}>
      <button 
        className="chatbot__toggle"
        onClick={() => setIsOpen(!isOpen)}
      >
        💬
      </button>
      
      {isOpen && (
        <div className="chatbot__window">
          <div className="chatbot__header">
            <h3>YODO Assistant</h3>
            <button onClick={() => setIsOpen(false)}>✕</button>
          </div>
          <div className="chatbot__messages">
            <div className="chatbot__message chatbot__message--system">
              How can I help you today?
            </div>
            {/* More messages would appear here */}
          </div>
          <div className="chatbot__input-area">
            <input 
              type="text" 
              placeholder="Type your message..." 
              className="chatbot__input"
            />
            <button className="chatbot__send-btn">Send</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Chatbot;