import React from 'react';
import './styles/input-bar.css';

function InputBar({ value, onChange, onSend }){
  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      onSend && onSend();
    }
  };
  return (
    <div className="chat-input-bar">
      <input
        type="text"
        placeholder="Type a message..."
        value={value}
        onChange={onChange}
        onKeyDown={handleKeyDown}
      />
      <button onClick={onSend} aria-label="Send message">↑</button>
    </div>
  );
};

export { InputBar };