import React, { useEffect, useRef } from 'react';

function ChatMessages({ messages, currentUserId }) {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  // Unicode 문자열을 디코딩하는 함수
  const decodeUnicode = (str) => {
    return str.replace(/\\u[\dA-F]{4}/gi, (match) => {
      return String.fromCharCode(parseInt(match.replace(/\\u/g, ''), 16));
    });
  };

  return (
    <div className="chat-messages">
      {messages.map((message, index) => {
        let messageContent, sender, username;
        
        if (typeof message === 'string') {
          try {
            const parsedMessage = JSON.parse(message);
            messageContent = parsedMessage.message;
            sender = parsedMessage.sender;
            username = parsedMessage.username;
          } catch (e) {
            console.error("Failed to parse message:", e);
            return null;
          }
        } else {
          messageContent = message.message || message.text;
          sender = message.sender;
          username = message.username;
        }

        // System message 처리
        if (sender === 'system' || message.type === 'system') {
          messageContent = decodeUnicode(messageContent);
        }

        if (!messageContent || messageContent.trim() === '' || messageContent === '내용 없음') {
          return null;
        }

        return (
          <div 
            key={index} 
            className={`message ${sender === currentUserId ? 'user' : (sender === 'system' ? 'system' : 'other')}`}
          >
            {sender !== currentUserId && sender !== 'system' && (
              <span className="message-username"><strong>{username || 'Anonymous'}</strong> </span>
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