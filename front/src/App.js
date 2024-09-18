import React, { useState, useEffect, useCallback } from 'react';
import { ThemeProvider, useTheme } from './contexts/ThemeContext';
import ChatPage from './pages/ChatPage';
import AuthModal from './components/AuthModal';
import { useWebSocket } from './hooks/useWebSocket';
import './styles/base.css';
import './styles/components.css';
import './styles/utilities.css';

// AppContent 컴포넌트: 애플리케이션의 주요 내용을 담당
function AppContent() {
  // 상태 관리
  const [showAuthModal, setShowAuthModal] = useState(false);  // 인증 모달 표시 여부
  const [authType, setAuthType] = useState(null);  // 인증 타입 (로그인/회원가입)
  const { isDarkMode, toggleTheme } = useTheme();  // 테마 관련 상태 및 함수
  const [user, setUser] = useState(null);  // 현재 로그인한 사용자 정보

  // useWebSocket 훅 사용
  const {
    socket,
    userCount,
    showSessionExpiredModal,
    setShowSessionExpiredModal,
    chatBanTimeLeft,
    sendMessage
  } = useWebSocket(user);

  // 인증 버튼 클릭 핸들러
  const handleAuthButton = (type) => {
    setAuthType(type);
    setShowAuthModal(true);
  };

  // 모달 닫기 핸들러
  const handleCloseModal = () => {
    setShowAuthModal(false);
    setAuthType(null);
  };

  // 로그인 성공 핸들러
  const handleLoginSuccess = useCallback((userData) => {
    console.log('Login successful:', userData);
    setUser(userData);
    handleCloseModal();
  }, []);

  // 로그아웃 핸들러
  const handleLogout = () => {
    setUser(null);
    if (socket) {
      socket.close(1000, "Logout");
    }
  };

  // 세션 만료 핸들러
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

// App 컴포넌트: ThemeProvider로 AppContent를 감싸 테마 기능 제공
function App() {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
}

export default App;