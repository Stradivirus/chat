import React, { useState } from 'react';

function ChatInput({ onSendMessage, isLoggedIn }) {
  const [message, setMessage] = useState('');
  const [isButtonDisabled, setIsButtonDisabled] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim() && message.length <= 30 && isLoggedIn) {
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
        placeholder={isLoggedIn ? "메시지를 입력하세요 (최대 30자)" : "로그인 해주세요"}
        maxLength={30}
        disabled={!isLoggedIn}
      />
      <button type="submit" disabled={isButtonDisabled || !isLoggedIn}>
        {isLoggedIn ? "전송" : "로그인 해주세요"}
      </button>
    </form>
  );
}

export default ChatInput;