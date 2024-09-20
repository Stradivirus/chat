import React, { useState, useEffect, useCallback } from 'react';
import { ThemeProvider, useTheme } from './contexts/ThemeContext';
import ChatPage from './pages/ChatPage';
import AuthModal from './components/AuthModal';
import { useWebSocket } from './hooks/useWebSocket';
import './styles/base.css';
import './styles/components.css';
import './styles/utilities.css';

function AppContent() {
  // 상태 관리
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authType, setAuthType] = useState(null);
  const { isDarkMode, toggleTheme } = useTheme();
  const [user, setUser] = useState(null);
  const [userCount, setUserCount] = useState(0);

  // 웹소켓 커스텀 훅 사용
  const {
    socket,
    showSessionExpiredModal,
    setShowSessionExpiredModal,
    chatBanTimeLeft,
    sendMessage
  } = useWebSocket(user);

  // 웹소켓 메시지 처리
  useEffect(() => {
    if (socket) {
      const handleMessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'user_count') {
          setUserCount(data.count);
        }
        // 다른 메시지 처리...
      };

      socket.addEventListener('message', handleMessage);

      return () => {
        socket.removeEventListener('message', handleMessage);
      };
    }
  }, [socket]);

  // 인증 모달 표시 함수
  const handleAuthButton = (type) => {
    setAuthType(type);
    setShowAuthModal(true);
  };

  // 모달 닫기 함수
  const handleCloseModal = () => {
    setShowAuthModal(false);
    setAuthType(null);
  };

  // 로그인 성공 처리 함수
  const handleLoginSuccess = useCallback((userData) => {
    console.log('Login successful:', userData);
    setUser(userData);
    handleCloseModal();
  }, []);

  // 로그아웃 처리 함수
  const handleLogout = () => {
    setUser(null);
    setUserCount(0);
    if (socket) {
      socket.close(1000, "Logout");
    }
  };

  // 세션 만료 처리 함수
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
                <span className="user-nickname">{user.username}님</span>
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
          sendMessage={sendMessage}
        />
      </aside>
      {/* 인증 모달 */}
      {showAuthModal && (
        <div className="modal-backdrop">
          <AuthModal 
            type={authType} 
            onClose={handleCloseModal}
            onLoginSuccess={handleLoginSuccess}
          />
        </div>
      )}
      {/* 세션 만료 모달 */}
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