import { useState, useRef, useEffect } from 'react';

/**
 * Chat component for the watch party.
 */
function ChatBox({ messages, onSendMessage }) {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputValue.trim()) {
      onSendMessage(inputValue);
      setInputValue('');
    }
  };

  const formatTime = (date) => {
    return new Date(date).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="chat-box">
      <div className="chat-header">
        <h3>Live Chat</h3>
      </div>

      <div className="chat-messages">
        {messages.length === 0 ? (
          <p className="chat-empty">No messages yet. Say hello!</p>
        ) : (
          messages.map((msg, index) => (
            <div
              key={index}
              className={`chat-message ${msg.type === 'system' ? 'system-message' : ''}`}
            >
              {msg.type === 'system' ? (
                <span className="system-text">{msg.message}</span>
              ) : (
                <>
                  <span className="chat-username">{msg.username}</span>
                  <span className="chat-text">{msg.message}</span>
                  <span className="chat-time">{formatTime(msg.timestamp)}</span>
                </>
              )}
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      <form className="chat-input-form" onSubmit={handleSubmit}>
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="Type a message..."
          maxLength={500}
          autoComplete="off"
        />
        <button type="submit" disabled={!inputValue.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}

export default ChatBox;
