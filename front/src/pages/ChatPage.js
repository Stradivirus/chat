import React, { useState, useEffect, useCallback } from 'react';
import ChatMessages from '../components/ChatMessages';
import ChatInput from '../components/ChatInput';

function ChatPage({ socket, user, chatBanTimeLeft }) {
  // 채팅 메시지를 저장하는 상태
  const [messages, setMessages] = useState([]);

  // 메시지 전송 핸들러 함수
  // useCallback을 사용하여 불필요한 재생성 방지
  const handleSendMessage = useCallback((messageText) => {
    // 소켓이 연결되어 있고 사용자가 로그인한 상태인지 확인
    if (socket && socket.readyState === WebSocket.OPEN && user) {
      // 메시지 객체 생성
      const messageObj = {
        message: messageText,
        sender: user.userId,
        username: user.username,
        timestamp: Date.now()
      };
      // 소켓을 통해 메시지 전송
      socket.send(JSON.stringify(messageObj));
    } else {
      console.error('WebSocket is not connected or user is not logged in');
    }
  }, [socket, user]); // socket과 user가 변경될 때만 함수 재생성

  // 소켓 메시지 수신 처리를 위한 useEffect
  useEffect(() => {
    if (!socket) return; // 소켓이 없으면 아무것도 하지 않음

    // 메시지 수신 핸들러 함수
    const handleMessage = (event) => {
      const data = JSON.parse(event.data);
      
      // 사용자 수 업데이트나 채팅 금지 메시지가 아닌 경우에만 처리
      if (data.type !== 'user_count' && data.type !== 'chat_banned') {
        setMessages(prev => {
          // 중복 메시지 체크
          const isDuplicate = prev.some(msg => msg.timestamp === data.timestamp);
          if (isDuplicate) return prev;

          // 새 메시지 추가
          return [...prev, {
            text: data.message,
            sender: data.sender,
            username: data.username,
            timestamp: data.timestamp
          }];
        });
      }
    };

    // 소켓에 메시지 이벤트 리스너 추가
    socket.addEventListener('message', handleMessage);

    // 컴포넌트 언마운트 시 이벤트 리스너 제거
    return () => {
      socket.removeEventListener('message', handleMessage);
    };
  }, [socket]); // socket이 변경될 때만 효과 재실행

  return (
    <div className="chat-page">
      {/* 채팅 메시지 표시 컴포넌트 */}
      <ChatMessages messages={messages} currentUserId={user?.userId} />
      {/* 채팅 입력 컴포넌트 */}
      <ChatInput 
        onSendMessage={handleSendMessage} 
        isLoggedIn={!!user} // 사용자 로그인 여부
        chatBanTimeLeft={chatBanTimeLeft} // 채팅 금지 남은 시간
      />
    </div>
  );
}

export default ChatPage;