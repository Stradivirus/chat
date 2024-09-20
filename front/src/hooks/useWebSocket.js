import { useState, useEffect, useCallback, useRef } from 'react';

// WebSocket 서버 URL
const WS_URL = 'ws://localhost:8000/ws';

// useWebSocket 커스텀 훅: WebSocket 연결 및 관련 기능을 관리
export function useWebSocket(user) {
  // 상태 관리
  const [socket, setSocket] = useState(null);  // WebSocket 인스턴스
  const [userCount, setUserCount] = useState(0);  // 현재 접속 사용자 수
  const [showSessionExpiredModal, setShowSessionExpiredModal] = useState(false);  // 세션 만료 모달 표시 여부
  const [chatBanTimeLeft, setChatBanTimeLeft] = useState(0);  // 채팅 금지 남은 시간

  // ref를 사용한 값 관리
  const reconnectAttempt = useRef(0);  // 재연결 시도 횟수
  const timeoutId = useRef(null);  // 재연결 타이머 ID

  // WebSocket 설정 및 연결 함수
  const setupWebSocket = useCallback(() => {
    if (!user) return;

    const newSocket = new WebSocket(`${WS_URL}/${user.userId}`);

    // WebSocket 연결 성공 시
    newSocket.onopen = () => {
      console.log('WebSocket Connected');
      setSocket(newSocket);
      reconnectAttempt.current = 0;
    };

    // 서버로부터 메시지 수신 시
    newSocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'user_count') {
        setUserCount(data.count);
      } else if (data.type === 'session_expired') {
        setShowSessionExpiredModal(true);
      } else if (data.type === 'chat_banned') {
        setChatBanTimeLeft(data.time_left);
      }
    };

    // WebSocket 연결 종료 시
    newSocket.onclose = (event) => {
      if (event.code !== 1000) {  // 1000은 정상 종료 코드
        console.log('WebSocket Disconnected');
        // 지수 백오프 및 지터를 사용한 재연결 로직
        const timeout = Math.min(1000 * (2 ** reconnectAttempt.current), 30000);
        const jitter = Math.random() * 1000;
        console.log(`Attempting to reconnect in ${timeout + jitter}ms...`);
        
        timeoutId.current = setTimeout(() => {
          reconnectAttempt.current++;
          setupWebSocket();
        }, timeout + jitter);
      }
    };

    // WebSocket 에러 발생 시
    newSocket.onerror = (error) => {
      console.error('WebSocket Error:', error);
    };
  }, [user]);

  // 사용자 정보가 변경될 때 WebSocket 연결 설정
  useEffect(() => {
    if (user) {
      setupWebSocket();
    }
    return () => {
      if (socket) {
        socket.close(1000, "Intentional disconnect");
      }
      if (timeoutId.current) {
        clearTimeout(timeoutId.current);
      }
    };
  }, [user, setupWebSocket]);

  // 채팅 금지 시간 카운트다운
  useEffect(() => {
    if (chatBanTimeLeft > 0) {
      const timer = setInterval(() => {
        setChatBanTimeLeft((prev) => Math.max(0, prev - 1));
      }, 1000);
      return () => clearInterval(timer);
    }
  }, [chatBanTimeLeft]);

  // 메시지 전송 함수
  const sendMessage = useCallback((messageObj) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(messageObj));
    } else {
      console.error('WebSocket is not connected');
    }
  }, [socket]);

  // 훅에서 반환하는 값들
  return {
    socket,
    userCount,
    showSessionExpiredModal,
    setShowSessionExpiredModal,
    chatBanTimeLeft,
    sendMessage
  };
}