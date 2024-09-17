import React, { useState, useEffect, useCallback } from 'react';
import { ThemeProvider, useTheme } from './contexts/ThemeContext';
import ChatPage from './pages/ChatPage';
import AuthModal from './components/AuthModal';
import './styles/base.css';
import './styles/components.css';
import './styles/utilities.css';

const WS_URL = 'ws://218.156.126.186:8000/ws';

function AppContent() {
  const [userCount, setUserCount] = useState(0);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authType, setAuthType] = useState(null);
  const { isDarkMode, toggleTheme } = useTheme();
  const [socket, setSocket] = useState(null);
  const [user, setUser] = useState(null);
  const [showSessionExpiredModal, setShowSessionExpiredModal] = useState(false);
  const [chatBanTimeLeft, setChatBanTimeLeft] = useState(0);

  const setupWebSocket = useCallback(() => {
    if (!user) return;

    const newSocket = new WebSocket(`${WS_URL}/${user.userId}`);

    newSocket.onopen = () => {
      console.log('WebSocket Connected');
      setSocket(newSocket);
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
        setTimeout(() => {
          console.log('Attempting to reconnect...');
          setupWebSocket();
        }, 5000);
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

  const handleAuthButton = (type) => {
    setAuthType(type);
    setShowAuthModal(true);
  };

  const handleCloseModal = () => {
    setShowAuthModal(false);
    setAuthType(null);
  };

  const handleLoginSuccess = useCallback((userData) => {
    console.log('Login successful:', userData);
    setUser(userData);
    handleCloseModal();
  }, []);

  const handleLogout = () => {
    setUser(null);
    if (socket) {
      socket.close(1000, "Logout");
    }
  };

  const handleSessionExpired = () => {
    setShowSessionExpiredModal(false);
    handleLogout();
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
            {user ? (
              <>
                <span className="user-nickname">{user.username}님 환영합니다</span>
                <button onClick={handleLogout} className="logout-button">로그아웃</button>
              </>
            ) : (
              <>
                <button onClick={() => handleAuthButton('login')}>로그인</button>
                <button onClick={() => handleAuthButton('register')}>회원가입</button>
              </>
            )}
            <button onClick={toggleTheme} className="theme-toggle">
              {isDarkMode ? '라이트' : '다크'}
            </button>
          </div>
        </header>
        <ChatPage 
          socket={socket} 
          user={user} 
          chatBanTimeLeft={chatBanTimeLeft} 
        />
      </aside>
      {showAuthModal && (
        <div className="modal-backdrop">
          <AuthModal 
            type={authType} 
            onClose={handleCloseModal}
            onLoginSuccess={handleLoginSuccess}
          />
        </div>
      )}
      {showSessionExpiredModal && (
        <div className="modal-backdrop">
          <div className="session-expired-modal">
            <p>다른 기기에서 로그인되어 로그아웃 되었습니다.</p>
            <button onClick={handleSessionExpired}>확인</button>
          </div>
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