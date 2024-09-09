import React, { useState, useEffect } from 'react';

function ChatInput({ onSendMessage }) {
  const [message, setMessage] = useState('');
  const [isButtonDisabled, setIsButtonDisabled] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim() && message.length <= 30) {
      onSendMessage(message);
      setMessage('');
      setIsButtonDisabled(true);
      setTimeout(() => setIsButtonDisabled(false), 500);
    }
  };

  const handleChange = (e) => {
    const input = e.target.value;
    if (input.length <= 30) {
      setMessage(input);
    }
  };

  return (
    <form className="chat-input" onSubmit={handleSubmit}>
      <input
        type="text"
        value={message}
        onChange={handleChange}
        placeholder="메시지를 입력하세요 (최대 30자)"
        maxLength={30}
      />
      <button type="submit" disabled={isButtonDisabled}>전송</button>
    </form>
  );
}

export default ChatInput;