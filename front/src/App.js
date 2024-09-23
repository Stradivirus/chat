import React, { useState, useEffect, useCallback } from 'react';
import { ThemeProvider, useTheme } from './contexts/ThemeContext';
import ChatPage from './pages/ChatPage';
import AuthModal from './components/AuthModal';
import { useWebSocket } from './hooks/useWebSocket';
import './styles/base.css';
import './styles/components.css';
import './styles/utilities.css';

function AppContent() {
  const [showAuthModal, setShowAuthModal] = useState(true);
  const [authType, setAuthType] = useState('login');
  const { isDarkMode, toggleTheme } = useTheme();
  const [user, setUser] = useState(null);
  const [userCount, setUserCount] = useState(0);

  const {
    socket,
    showSessionExpiredModal,
    setShowSessionExpiredModal,
    chatBanTimeLeft,
    sendMessage
  } = useWebSocket(user);

  useEffect(() => {
    if (socket) {
      const handleMessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'user_count') {
          setUserCount(data.count);
        }
      };

      socket.addEventListener('message', handleMessage);

      return () => {
        socket.removeEventListener('message', handleMessage);
      };
    }
  }, [socket]);

  const handleAuthButton = (type) => {
    setAuthType(type);
    setShowAuthModal(true);
  };

  const handleCloseModal = () => {
    if (user) {
      setShowAuthModal(false);
    }
  };

  const handleLoginSuccess = useCallback((userData) => {
    console.log('Login successful:', userData);
    setUser(userData);
    setShowAuthModal(false);
  }, []);

  const handleLogout = () => {
    setUser(null);
    setUserCount(0);
    setShowAuthModal(true);
    setAuthType('login');
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
        
        </main>
      </div>
      <aside className="side-container">
        <header className="side-header">
          <div className="user-count">현재 접속자 수: {userCount}</div>
          <div className="header-buttons">
            {user ? (
              <>
                <span className="user-nickname">{user.username}님</span>
                <button onClick={handleLogout} className="logout-button">로그아웃</button>
              </>
            ) : (
              <button onClick={() => handleAuthButton('login')} className="login-button">로그인</button>
            )}
            <button onClick={toggleTheme} className="theme-toggle">
              {isDarkMode ? '라이트' : '다크'}
            </button>
          </div>
        </header>
        {user && (
          <ChatPage 
            socket={socket} 
            user={user} 
            chatBanTimeLeft={chatBanTimeLeft}
            sendMessage={sendMessage}
          />
        )}
      </aside>
      {showAuthModal && (
        <div className="modal-backdrop">
          <AuthModal 
            type={authType} 
            onClose={handleCloseModal}
            onLoginSuccess={handleLoginSuccess}
            onSwitchAuthType={(type) => setAuthType(type)}
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