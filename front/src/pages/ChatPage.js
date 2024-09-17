import React, { useState, useEffect, useCallback } from 'react';
import ChatMessages from '../components/ChatMessages';
import ChatInput from '../components/ChatInput';

function ChatPage({ socket, user, chatBanTimeLeft }) {
  // 채팅 메시지를 저장하는 상태
  const [messages, setMessages] = useState([]);

  // 메시지 전송 핸들러 함수
  const handleSendMessage = useCallback((messageText) => {
    if (socket && socket.readyState === WebSocket.OPEN && user) {
      const messageObj = {
        message: messageText,
        sender: user.userId,
        username: user.username,
        timestamp: Date.now()
      };
      socket.send(JSON.stringify(messageObj));
    } else {
      console.error('WebSocket is not connected or user is not logged in');
    }
  }, [socket, user]);

  // 소켓 메시지 수신 처리를 위한 useEffect
  useEffect(() => {
    if (!socket) return;

    const handleMessage = (event) => {
      const data = JSON.parse(event.data);
            
      if (data.type !== 'user_count' && data.type !== 'chat_banned') {
        setMessages(prev => {
          // 중복 메시지 체크
          const isDuplicate = prev.some(msg => msg.timestamp === data.timestamp);
          // '내용 없음' 메시지 체크
          const isEmptyContent = !data.message || data.message.trim() === '' || data.message === '내용 없음';
          
          // 중복이거나 내용이 없는 메시지는 무시
          if (isDuplicate || isEmptyContent) return prev;

          // 새 메시지 추가
          return [...prev, data];
        });
      }
    };

    socket.addEventListener('message', handleMessage);

    return () => {
      socket.removeEventListener('message', handleMessage);
    };
  }, [socket]);

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