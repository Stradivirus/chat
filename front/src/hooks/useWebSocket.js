import { useState, useEffect, useCallback, useRef } from 'react';
import { URLS } from '../urls';

export function useWebSocket(user) {
  const [socket, setSocket] = useState(null);
  const [userCount, setUserCount] = useState(0);
  const [showSessionExpiredModal, setShowSessionExpiredModal] = useState(false);
  const [chatBanTimeLeft, setChatBanTimeLeft] = useState(0);

  const reconnectAttempt = useRef(0);
  const timeoutId = useRef(null);

  const setupWebSocket = useCallback(() => {
    if (!user) return;

    const newSocket = new WebSocket(`${URLS.WS_URL}/${user.userId}`);

    newSocket.onopen = () => {
      console.log('WebSocket Connected');
      setSocket(newSocket);
      reconnectAttempt.current = 0;
    };

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

    newSocket.onclose = (event) => {
      if (event.code !== 1000) {
        console.log('WebSocket Disconnected');
        const timeout = Math.min(1000 * (2 ** reconnectAttempt.current), 30000);
        const jitter = Math.random() * 1000;
        console.log(`Attempting to reconnect in ${timeout + jitter}ms...`);
        
        timeoutId.current = setTimeout(() => {
          reconnectAttempt.current++;
          setupWebSocket();
        }, timeout + jitter);
      }
    };

    newSocket.onerror = (error) => {
      console.error('WebSocket Error:', error);
    };
  }, [user]);

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

  useEffect(() => {
    if (chatBanTimeLeft > 0) {
      const timer = setInterval(() => {
        setChatBanTimeLeft((prev) => Math.max(0, prev - 1));
      }, 1000);
      return () => clearInterval(timer);
    }
  }, [chatBanTimeLeft]);

  const sendMessage = useCallback((messageObj) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(messageObj));
    } else {
      console.error('WebSocket is not connected');
    }
  }, [socket]);

  return {
    socket,
    userCount,
    showSessionExpiredModal,
    setShowSessionExpiredModal,
    chatBanTimeLeft,
    sendMessage
  };
}