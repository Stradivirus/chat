import React, { useState } from 'react';
import ChatMessages from '../components/ChatMessages';
import ChatInput from '../components/ChatInput';

function ChatPage() {
  const [messages, setMessages] = useState([]);

  const handleSendMessage = (message) => {
    setMessages([...messages, { text: message, sender: 'user' }]);
    // 여기에서 서버로 메시지를 보내는 로직을 추가할 수 있습니다.
    
    // 예시: 다른 사용자의 메시지를 테스트
    setTimeout(() => {
      setMessages(prev => [...prev, { text: "다른 사용자의 응답입니다.", sender: 'other' }]);
    }, 1000);
  };

  return (
    <div className="chat-page">
      <div className="chat-messages">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.sender}`}>
            {msg.text}
          </div>
        ))}
      </div>
      <ChatInput onSendMessage={handleSendMessage} />
    </div>
  );
}

export default ChatPage;