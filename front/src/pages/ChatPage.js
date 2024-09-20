import React, { useState, useEffect, useCallback } from 'react';
import ChatMessages from '../components/ChatMessages';
import ChatInput from '../components/ChatInput';

function ChatPage({ socket, user, chatBanTimeLeft, sendMessage }) {
  // 채팅 메시지를 저장하는 상태
  const [messages, setMessages] = useState([]);

  // 메시지 전송 핸들러
  const handleSendMessage = useCallback((messageText) => {
    if (user) {
      const messageObj = {
        message: messageText,
        sender_id: user.userId,
        username: user.username,
        timestamp: Date.now()
      };
      sendMessage(messageObj);
    } else {
      console.error('User is not logged in');
    }
  }, [user, sendMessage]);

  // 웹소켓 메시지 수신 처리
  useEffect(() => {
    if (!socket) return;

    const handleMessage = (event) => {
      const data = JSON.parse(event.data);
            
      // 사용자 수 업데이트와 채팅 금지 메시지는 무시
      if (data.type !== 'user_count' && data.type !== 'chat_banned') {
        setMessages(prev => {
          // 중복 메시지 및 빈 메시지 필터링
          const isDuplicate = prev.some(msg => 
            msg.timestamp === data.timestamp && msg.sender_id === data.sender_id
          );
          const isEmptyContent = !data.message || data.message.trim() === '' || data.message === '내용 없음';
          
          if (isDuplicate || isEmptyContent) return prev;

          return [...prev, data];
        });
      }
    };

    socket.addEventListener('message', handleMessage);

    // 컴포넌트 언마운트 시 이벤트 리스너 제거
    return () => {
      socket.removeEventListener('message', handleMessage);
    };
  }, [socket]);

  // 사용자 변경 시 메시지 초기화
  useEffect(() => {
    setMessages([]);
  }, [user]);

  return (
    <div className="chat-page">
      <ChatMessages messages={messages} currentUserId={user?.userId} />
      <ChatInput 
        onSendMessage={handleSendMessage} 
        isLoggedIn={!!user}
        chatBanTimeLeft={chatBanTimeLeft}
      />
    </div>
  );
}

export default ChatPage;