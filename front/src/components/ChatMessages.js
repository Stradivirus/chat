import React from 'react';

function ChatMessages({ messages }) {
  return (
    <div className="chat-messages">
      {messages.map((message, index) => (
        <div key={index} className={`message ${message.sender === 'user' ? 'user' : 'other'}`}>
          {message.text}
        </div>
      ))}
    </div>
  );
}

export default ChatMessages;