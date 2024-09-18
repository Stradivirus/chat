import React, { useEffect, useRef } from 'react';

// ChatMessages 컴포넌트: 채팅 메시지를 표시하는 컴포넌트
function ChatMessages({ messages, currentUserId }) {
  // messagesEndRef: 메시지 목록의 끝을 참조하기 위한 ref
  const messagesEndRef = useRef(null);

  // scrollToBottom: 메시지 목록의 맨 아래로 스크롤하는 함수
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // useEffect: messages 배열이 변경될 때마다 스크롤을 아래로 이동
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
            {/* 다른 사용자의 메시지인 경우 사용자 이름 표시 */}
            {sender !== currentUserId && (
              <span className="message-username"><strong>{username || 'Anonymous'}</strong> </span>
            )}
            <span>{messageContent}</span>
          </div>
        );
      })}
      {/* 메시지 목록의 끝을 참조하는 빈 div */}
      <div ref={messagesEndRef} />
    </div>
  );
}

export default ChatMessages;