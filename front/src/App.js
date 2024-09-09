import React, { useState, useEffect, useCallback } from 'react';
import { ThemeProvider, useTheme } from './contexts/ThemeContext';
import ChatPage from './pages/ChatPage';
import AuthModal from './components/AuthModal';
import './styles/base.css';
import './styles/components.css';
import './styles/utilities.css';

// WebSocket 연결 URL (환경에 따라 변경 필요)
const WS_URL = 'ws://localhost:8000/ws';

function AppContent() {
  const [userCount, setUserCount] = useState(0);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authType, setAuthType] = useState(null);
  const { isDarkMode, toggleTheme } = useTheme();
  const [socket, setSocket] = useState(null);
  const [clientId, setClientId] = useState(null);

  const setupWebSocket = useCallback(() => {
    const newClientId = Math.random().toString(36).substr(2, 9);
    setClientId(newClientId);
    const newSocket = new WebSocket(`${WS_URL}/${newClientId}`);

    newSocket.onopen = () => {
      console.log('WebSocket Connected');
      setSocket(newSocket);
    };

    newSocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      // 여기서 메시지 처리 로직을 구현할 수 있습니다.
      // 예: 사용자 수 업데이트
      if (data.type === 'user_count') {
        setUserCount(data.count);
      }
    };

    newSocket.onclose = () => {
      console.log('WebSocket Disconnected');
      setTimeout(() => {
        console.log('Attempting to reconnect...');
        setupWebSocket();
      }, 5000);  // 5초 후 재연결 시도
    };

    newSocket.onerror = (error) => {
      console.error('WebSocket Error:', error);
    };
  }, []);

  useEffect(() => {
    setupWebSocket();
    return () => {
      if (socket) {
        socket.close();
      }
    };
  }, [setupWebSocket]);

  const handleAuthButton = (type) => {
    setAuthType(type);
    setShowAuthModal(true);
  };

  const handleCloseModal = () => {
    setShowAuthModal(false);
    setAuthType(null);
  };

  return (
    <div className={`App ${isDarkMode ? 'dark-mode' : 'light-mode'}`}>
      <div className="main-section">
        <header className="main-header">
          <h1>채팅 애플리케이션</h1>
        </header>
        <main className="main-content">
          {/* 여기에 메인 콘텐츠가 들어갑니다 */}
        </main>
      </div>
      <aside className="side-container">
        <header className="side-header">
          <div className="user-count">현재 접속자 수: {userCount}</div>
          <div className="header-buttons">
            <button onClick={toggleTheme} className="theme-toggle">
              {isDarkMode ? '라이트' : '다크'}
            </button>
            <button onClick={() => handleAuthButton('login')}>로그인</button>
            <button onClick={() => handleAuthButton('register')}>회원가입</button>
          </div>
        </header>
        <ChatPage socket={socket} clientId={clientId} />
      </aside>
      {showAuthModal && (
        <div className="modal-backdrop">
          <AuthModal type={authType} onClose={handleCloseModal} />
        </div>
      )}
    </div>
  );
}

function App() {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
}

export default App;