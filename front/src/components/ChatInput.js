import React, { useState, useEffect, useRef } from 'react';

function ChatInput({ onSendMessage, isLoggedIn }) {
  const [message, setMessage] = useState('');
  const [isButtonDisabled, setIsButtonDisabled] = useState(false);
  const [isChatBanned, setIsChatBanned] = useState(false);
  const [banTimeLeft, setBanTimeLeft] = useState(0);
  const lastMessages = useRef([]);
  const banTimerRef = useRef(null);

  useEffect(() => {
    return () => {
      if (banTimerRef.current) {
        clearInterval(banTimerRef.current);
      }
    };
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim() && message.length <= 30 && isLoggedIn && !isChatBanned) {
      onSendMessage(message);
      lastMessages.current.push(message);
      if (lastMessages.current.length > 3) {
        lastMessages.current.shift();
      }
      if (lastMessages.current.length === 3 && 
          lastMessages.current.every(msg => msg === lastMessages.current[0])) {
        setIsChatBanned(true);
        setBanTimeLeft(20);
        banTimerRef.current = setInterval(() => {
          setBanTimeLeft(prev => {
            if (prev <= 1) {
              clearInterval(banTimerRef.current);
              setIsChatBanned(false);
              return 0;
            }
            return prev - 1;
          });
        }, 1000);
      }
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
        placeholder={isLoggedIn ? (isChatBanned ? `채팅 금지: ${banTimeLeft}초 남음` : "메시지를 입력하세요 (최대 30자)") : "로그인 해주세요"}
        maxLength={30}
        disabled={!isLoggedIn || isChatBanned}
        className={isChatBanned ? "chat-banned" : ""}
      />
      <button type="submit" disabled={isButtonDisabled || !isLoggedIn || isChatBanned}>
        {isLoggedIn ? (isChatBanned ? `${banTimeLeft}초` : "전송") : "로그인 해주세요"}
      </button>
    </form>
  );
}

export default ChatInput;