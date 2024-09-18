import React, { useState, useEffect, useCallback } from 'react';
import ChatMessages from '../components/ChatMessages';
import ChatInput from '../components/ChatInput';

function ChatPage({ socket, user, chatBanTimeLeft, sendMessage }) {
  const [messages, setMessages] = useState([]);

  const handleSendMessage = useCallback((messageText) => {
    if (user) {
      const messageObj = {
        message: messageText,
        sender: user.userId,
        username: user.username,
        timestamp: Date.now()
      };
      sendMessage(messageObj);
    } else {
      console.error('User is not logged in');
    }
  }, [user, sendMessage]);

  useEffect(() => {
    if (!socket) return;

    const handleMessage = (event) => {
      const data = JSON.parse(event.data);
            
      if (data.type !== 'user_count' && data.type !== 'chat_banned') {
        setMessages(prev => {
          const isDuplicate = prev.some(msg => 
            msg.timestamp === data.timestamp && msg.sender === data.sender
          );
          const isEmptyContent = !data.message || data.message.trim() === '' || data.message === '내용 없음';
          
          if (isDuplicate || isEmptyContent) return prev;

          // 퇴장 메시지 필터링 제거
          return [...prev, data];
        });
      }
    };

    socket.addEventListener('message', handleMessage);

    return () => {
      socket.removeEventListener('message', handleMessage);
    };
  }, [socket]);

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