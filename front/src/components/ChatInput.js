import React, { useState, useEffect } from 'react';

function ChatInput({ onSendMessage, isLoggedIn, chatBanTimeLeft }) {
  const [message, setMessage] = useState('');
  const [isButtonDisabled, setIsButtonDisabled] = useState(false);

  useEffect(() => {
    if (chatBanTimeLeft > 0) {
      setIsButtonDisabled(true);
    } else {
      setIsButtonDisabled(false);
    }
  }, [chatBanTimeLeft]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim() && message.length <= 30 && isLoggedIn && chatBanTimeLeft === 0) {
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
        placeholder={isLoggedIn ? (chatBanTimeLeft > 0 ? `채팅 금지: ${chatBanTimeLeft}초 남음` : "메시지를 입력하세요 (최대 30자)") : ""}
        maxLength={30}
        disabled={!isLoggedIn || chatBanTimeLeft > 0}
        className={chatBanTimeLeft > 0 ? "chat-banned" : ""}
      />
      <button type="submit" disabled={isButtonDisabled || !isLoggedIn || chatBanTimeLeft > 0}>
        {isLoggedIn ? (chatBanTimeLeft > 0 ? `${chatBanTimeLeft}초` : "전송") : "로그인 해주세요"}
      </button>
    </form>
  );
}

export default ChatInput;