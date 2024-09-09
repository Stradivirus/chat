import React, { useState, useEffect, useCallback } from 'react';
import ChatMessages from '../components/ChatMessages';
import ChatInput from '../components/ChatInput';

function ChatPage({ socket, clientId }) {
  const [messages, setMessages] = useState([]);

  const handleSendMessage = useCallback((messageText) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      const messageObj = {
        message: messageText,
        sender: clientId,
        timestamp: Date.now()
      };
      socket.send(JSON.stringify(messageObj));
      
    } else {
      console.error('WebSocket is not connected');
    }
  }, [socket, clientId]);

  useEffect(() => {
    if (!socket) return;

    const handleMessage = (event) => {
      const data = JSON.parse(event.data);
      
      // 메시지 중복 방지 및 자신의 메시지 구분
      setMessages(prev => {
        // 이미 존재하는 메시지인지 확인 (timestamp로 비교)
        const isDuplicate = prev.some(msg => msg.timestamp === data.timestamp);
        if (isDuplicate) return prev;

        return [...prev, {
          text: data.message || data.text,
          sender: data.sender === clientId ? 'user' : 'other',
          timestamp: data.timestamp
        }];
      });
    };

    socket.addEventListener('message', handleMessage);

    return () => {
      socket.removeEventListener('message', handleMessage);
    };
  }, [socket, clientId]);

  return (
    <div className="chat-page">
      <ChatMessages messages={messages} />
      <ChatInput onSendMessage={handleSendMessage} />
    </div>
  );
}

export default ChatPage;