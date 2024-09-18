import React, { useState, useEffect, useCallback } from 'react';
import ChatMessages from '../components/ChatMessages';
import ChatInput from '../components/ChatInput';

// ChatPage 컴포넌트: 채팅 페이지의 전체 구조를 담당
function ChatPage({ socket, user, chatBanTimeLeft, sendMessage }) {
  // 메시지 목록을 관리하는 상태
  const [messages, setMessages] = useState([]);

  // 메시지 전송 핸들러
  const handleSendMessage = useCallback((messageText) => {
    if (user) {
      // 메시지 객체 생성
      const messageObj = {
        message: messageText,
        sender: user.userId,
        username: user.username,
        timestamp: Date.now()
      };
      // 메시지 전송
      sendMessage(messageObj);
    } else {
      console.error('User is not logged in');
    }
  }, [user, sendMessage]);

  // WebSocket 메시지 수신 처리
  useEffect(() => {
    if (!socket) return;

    const handleMessage = (event) => {
      const data = JSON.parse(event.data);
            
      // 사용자 수 업데이트나 채팅 금지 메시지가 아닌 경우에만 처리
      if (data.type !== 'user_count' && data.type !== 'chat_banned') {
        setMessages(prev => {
          // 중복 메시지 체크
          const isDuplicate = prev.some(msg => msg.timestamp === data.timestamp);
          // 빈 메시지 체크
          const isEmptyContent = !data.message || data.message.trim() === '' || data.message === '내용 없음';
          
          // 중복이거나 빈 메시지면 이전 상태 그대로 반환
          if (isDuplicate || isEmptyContent) return prev;

          // 새 메시지를 기존 메시지 목록에 추가
          return [...prev, data];
        });
      }
    };

    // WebSocket 메시지 이벤트 리스너 등록
    socket.addEventListener('message', handleMessage);

    // 컴포넌트 언마운트 시 이벤트 리스너 제거
    return () => {
      socket.removeEventListener('message', handleMessage);
    };
  }, [socket]);

  return (
    <div className="chat-page">
      {/* 채팅 메시지 표시 컴포넌트 */}
      <ChatMessages messages={messages} currentUserId={user?.userId} />
      {/* 채팅 입력 컴포넌트 */}
      <ChatInput 
        onSendMessage={handleSendMessage} 
        isLoggedIn={!!user}
        chatBanTimeLeft={chatBanTimeLeft}
      />
    </div>
  );
}

export default ChatPage;