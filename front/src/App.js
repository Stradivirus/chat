import React, { useState, useEffect, useCallback } from 'react';
import { ThemeProvider, useTheme } from './contexts/ThemeContext';
import ChatPage from './pages/ChatPage';
import AuthModal from './components/AuthModal';
import './styles/base.css';
import './styles/components.css';
import './styles/utilities.css';

// WebSocket 서버 URL
const WS_URL = 'ws://218.156.126.186:8000/ws';

function AppContent() {
  // 상태 관리
  const [userCount, setUserCount] = useState(0);  // 현재 접속자 수
  const [showAuthModal, setShowAuthModal] = useState(false);  // 인증 모달 표시 여부
  const [authType, setAuthType] = useState(null);  // 인증 타입 (로그인/회원가입)
  const { isDarkMode, toggleTheme } = useTheme();  // 테마 관련 상태와 함수
  const [socket, setSocket] = useState(null);  // WebSocket 연결 객체
  const [user, setUser] = useState(null);  // 현재 로그인한 사용자 정보
  const [showSessionExpiredModal, setShowSessionExpiredModal] = useState(false);  // 세션 만료 모달 표시 여부
  const [chatBanTimeLeft, setChatBanTimeLeft] = useState(0);  // 채팅 금지 남은 시간

  // WebSocket 연결 설정 함수
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

  // 사용자 로그인 상태 변경 시 WebSocket 연결 설정
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

  // 채팅 금지 타이머 관리
  useEffect(() => {
    if (chatBanTimeLeft > 0) {
      const timer = setInterval(() => {
        setChatBanTimeLeft((prev) => Math.max(0, prev - 1));
      }, 1000);
      return () => clearInterval(timer);
    }
  }, [chatBanTimeLeft]);

  // 인증 모달 표시 함수
  const handleAuthButton = (type) => {
    setAuthType(type);
    setShowAuthModal(true);
  };

  // 인증 모달 닫기 함수
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

// 최상위 App 컴포넌트
function App() {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
}

export default App;