import React, { useEffect, useRef } from 'react';

function ChatMessages({ messages, currentUserId }) {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  return (
    <div className="chat-messages">
      {messages.map((message, index) => {
                
        const messageContent = message.message || message.text;
        // 메시지 내용이 없거나 '내용 없음'인 경우 렌더링하지 않음
        if (!messageContent || messageContent.trim() === '' || messageContent === '내용 없음') {
          return null;
        }

        const sender = message.sender || 'unknown';
        const username = message.username || 'Anonymous';

        return (
          <div 
            key={index} 
            className={`message ${sender === currentUserId ? 'user' : 'other'}`}
          >
            {sender !== currentUserId && (
              <span className="message-username"><strong>{username}</strong> </span>
            )}
            <span>{messageContent}</span>
          </div>
        );
      })}
      <div ref={messagesEndRef} />
    </div>
  );
}

export default ChatMessages;