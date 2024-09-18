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
        let messageContent, sender_id, username;
        
        if (typeof message === 'string') {
          try {
            const parsedMessage = JSON.parse(message);
            messageContent = parsedMessage.message;
            sender_id = parsedMessage.sender_id;
            username = parsedMessage.username;
          } catch (e) {
            console.error("Failed to parse message:", e);
            return null;
          }
        } else {
          messageContent = message.message;
          sender_id = message.sender_id;
          username = message.username;
        }

        // System message 처리
        if (sender_id === 'system' || message.type === 'system') {
          messageContent = decodeUnicode(messageContent);
        }

        if (!messageContent || messageContent.trim() === '' || messageContent === '내용 없음') {
          return null;
        }

        return (
          <div 
            key={index} 
            className={`message ${sender_id === currentUserId ? 'user' : (sender_id === 'system' ? 'system' : 'other')}`}
          >
            {sender_id !== currentUserId && sender_id !== 'system' && (
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