import React, { useState } from 'react';
import './styles/App.css';
import { ChatWrapper } from '../components/chat-wrapper';

function App() {
  return (
    <div className="App">
      <h1>TERRAIN Chatbot</h1>
      <ChatWrapper chatType="simple-text" content={simpleContent} />
    </div>
  );
}

export default App;
