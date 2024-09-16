import React from 'react';

function ChatMessages({ messages, currentUserId }) {
  return (
    <div className="chat-messages">
      {messages.map((message, index) => (
        <div key={index} className={`message ${message.sender === currentUserId ? 'user' : 'other'}`}>
          {message.sender !== currentUserId && message.sender !== 'system' && (
            <span className="message-username"><strong>{message.username}</strong>: </span>
          )}
          {message.sender === 'system' ? (
            <span className="system-message">{message.text}</span>
          ) : (
            message.text
          )}
        </div>
      ))}
    </div>
  );
}

export default ChatMessages;