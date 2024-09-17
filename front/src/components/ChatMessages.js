import React, { useEffect, useRef } from 'react';

function ChatMessages({ messages, currentUserId }) {
  // 메시지 목록의 끝을 참조하기 위한 ref
  const messagesEndRef = useRef(null);

  // 메시지 목록의 맨 아래로 스크롤하는 함수
  const scrollToBottom = () => {
    // ref가 존재하면 해당 요소로 부드럽게 스크롤
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // messages 배열이 변경될 때마다 스크롤을 맨 아래로 이동
  useEffect(scrollToBottom, [messages]);

  return (
    <div className="chat-messages">
      {/* 메시지 배열을 순회하며 각 메시지를 렌더링 */}
      {messages.map((message, index) => (
        <div 
          key={index} 
          // 현재 사용자의 메시지인 경우 'user' 클래스를, 아닌 경우 'other' 클래스를 적용
          className={`message ${message.sender === currentUserId ? 'user' : 'other'}`}
        >
          {/* 다른 사용자의 메시지이고 시스템 메시지가 아닌 경우 사용자 이름 표시 */}
          {message.sender !== currentUserId && message.sender !== 'system' && (
            <span className="message-username"><strong>{message.username}</strong>: </span>
          )}
          {/* 시스템 메시지인 경우 특별한 스타일 적용, 아닌 경우 일반 텍스트로 표시 */}
          {message.sender === 'system' ? (
            <span className="system-message">{message.text}</span>
          ) : (
            message.text
          )}
        </div>
      ))}
      {/* 메시지 목록의 끝을 표시하는 빈 div. 스크롤 위치 조정에 사용됨 */}
      <div ref={messagesEndRef} />
    </div>
  );
}

export default ChatMessages;