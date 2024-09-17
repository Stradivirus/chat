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
        let messageContent, sender, username;
        
        // 메시지가 문자열인 경우 JSON으로 파싱
        if (typeof message === 'string') {
          try {
            const parsedMessage = JSON.parse(message);
            messageContent = parsedMessage.message;
            sender = parsedMessage.sender;
            username = parsedMessage.username;
          } catch (e) {
            console.error("Failed to parse message:", e);
            return null; // 파싱 실패 시 이 메시지는 렌더링하지 않음
          }
        } else {
          // 이미 객체인 경우 직접 사용
          messageContent = message.message || message.text;
          sender = message.sender;
          username = message.username;
        }

        // 메시지 내용이 없거나 '내용 없음'인 경우 렌더링하지 않음
        if (!messageContent || messageContent.trim() === '' || messageContent === '내용 없음') {
          return null;
        }

        return (
          <div 
            key={index} 
            className={`message ${sender === currentUserId ? 'user' : 'other'}`}
          >
            {sender !== currentUserId && (
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