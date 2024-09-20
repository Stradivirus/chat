import React, { useEffect, useRef } from 'react';

// ChatMessages 컴포넌트: 채팅 메시지를 표시하는 컴포넌트
function ChatMessages({ messages, currentUserId }) {
  // 메시지 목록의 끝을 참조하기 위한 ref
  const messagesEndRef = useRef(null);

  // 메시지 목록의 맨 아래로 스크롤하는 함수
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // messages 배열이 변경될 때마다 스크롤을 아래로 이동
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
        
        // 메시지가 문자열인 경우 JSON 파싱 시도
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
          // 메시지가 객체인 경우 직접 값 할당
          messageContent = message.message;
          sender_id = message.sender_id;
          username = message.username;
        }

        // 시스템 메시지인 경우 Unicode 디코딩
        if (sender_id === 'system' || message.type === 'system') {
          messageContent = decodeUnicode(messageContent);
        }

        // 메시지 내용이 없거나 빈 문자열인 경우 렌더링하지 않음
        if (!messageContent || messageContent.trim() === '' || messageContent === '내용 없음') {
          return null;
        }

        return (
          <div 
            key={index} 
            className={`message ${sender_id === currentUserId ? 'user' : (sender_id === 'system' ? 'system' : 'other')}`}
          >
            {/* 다른 사용자의 메시지인 경우 사용자 이름 표시 */}
            {sender_id !== currentUserId && sender_id !== 'system' && (
              <span className="message-username"><strong>{username || 'Anonymous'}</strong> </span>
            )}
            <span>{messageContent}</span>
          </div>
        );
      })}
      {/* 메시지 목록의 끝을 나타내는 빈 div */}
      <div ref={messagesEndRef} />
    </div>
  );
}

export default ChatMessages;