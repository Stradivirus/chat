import React, { useState, useEffect } from 'react';

function ChatInput({ onSendMessage, isLoggedIn, chatBanTimeLeft }) {
  // 메시지 입력 상태 관리
  const [message, setMessage] = useState('');
  // 전송 버튼 비활성화 상태 관리
  const [isButtonDisabled, setIsButtonDisabled] = useState(false);

  // chatBanTimeLeft가 변경될 때마다 실행되는 효과
  useEffect(() => {
    // 채팅 금지 시간이 남아있으면 버튼 비활성화
    if (chatBanTimeLeft > 0) {
      setIsButtonDisabled(true);
    } else {
      setIsButtonDisabled(false);
    }
  }, [chatBanTimeLeft]);

  // 폼 제출 핸들러
  const handleSubmit = (e) => {
    e.preventDefault();
    // 메시지가 있고, 30자 이하이며, 로그인 상태이고, 채팅 금지 상태가 아닐 때만 전송
    if (message.trim() && message.length <= 30 && isLoggedIn && chatBanTimeLeft === 0) {
      onSendMessage(message);
      setMessage(''); // 메시지 입력창 초기화
      setIsButtonDisabled(true); // 버튼 일시적 비활성화
      // 0.5초 후 버튼 다시 활성화 (연속 전송 방지)
      setTimeout(() => setIsButtonDisabled(false), 500);
    }
  };

  // 입력 변경 핸들러
  const handleChange = (e) => {
    const input = e.target.value;
    // 30자 이하일 때만 입력 허용
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
        // 로그인 상태와 채팅 금지 상태에 따라 다른 플레이스홀더 표시
        placeholder={isLoggedIn ? (chatBanTimeLeft > 0 ? `채팅 금지: ${chatBanTimeLeft}초 남음` : "메시지를 입력하세요 (최대 30자)") : ""}
        maxLength={30}
        // 로그인 상태가 아니거나 채팅 금지 상태일 때 입력 비활성화
        disabled={!isLoggedIn || chatBanTimeLeft > 0}
        // 채팅 금지 상태일 때 추가 스타일 적용
        className={chatBanTimeLeft > 0 ? "chat-banned" : ""}
      />
      <button 
        type="submit" 
        // 버튼 비활성화 조건: 버튼 비활성화 상태이거나 로그인하지 않았거나 채팅 금지 상태일 때
        disabled={isButtonDisabled || !isLoggedIn || chatBanTimeLeft > 0}
      >
        {/* 로그인 상태와 채팅 금지 상태에 따라 다른 버튼 텍스트 표시 */}
        {isLoggedIn ? (chatBanTimeLeft > 0 ? `${chatBanTimeLeft}초` : "전송") : "로그인 해주세요"}
      </button>
    </form>
  );
}

export default ChatInput;