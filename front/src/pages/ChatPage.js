import React, { useState, useEffect, useCallback } from 'react';
import ChatMessages from '../components/ChatMessages';
import ChatInput from '../components/ChatInput';

function ChatPage({ socket, user }) {
  const [messages, setMessages] = useState([]);

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

  useEffect(() => {
    if (!socket) return;

    const handleMessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type !== 'user_count') {
        setMessages(prev => {
          const isDuplicate = prev.some(msg => msg.timestamp === data.timestamp);
          if (isDuplicate) return prev;

          return [...prev, {
            text: data.message,
            sender: data.sender,
            username: data.username,
            timestamp: data.timestamp
          }];
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
      <ChatInput onSendMessage={handleSendMessage} isLoggedIn={!!user} />
    </div>
  );
}

export default ChatPage;