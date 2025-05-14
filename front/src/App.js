import React, { useState, useEffect, useCallback } from 'react';
import ChatPage from './pages/ChatPage';
import SystemInfoPage from './pages/SystemInfoPage';
import AuthModal from './components/AuthModal';
import { useWebSocket } from './hooks/useWebSocket';
import './styles/base.css';
import './styles/components.css';
import './styles/utilities.css';

function App() {
  const [user, setUser] = useState(null);
  const [userCount, setUserCount] = useState(0);
  const [showInfo, setShowInfo] = useState(false);

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

  const handleLoginSuccess = useCallback((userData) => {
    console.log('Login successful:', userData);
    setUser(userData);
  }, []);

  const handleLogout = () => {
    setUser(null);
    setUserCount(0);
    setShowInfo(false);
    if (socket) {
      socket.close(1000, "Logout");
    }
  };

  const handleSessionExpired = () => {
    setShowSessionExpiredModal(false);
    handleLogout();
  };

  const handleInfoButtonClick = () => {
    setShowInfo(true);
  };

  const handleHomeButtonClick = () => {
    setShowInfo(false);
  };

  const HomeButton = () => (
    <button 
      onClick={handleHomeButtonClick}
      className="home-button button-base"
    >
      홈으로
    </button>
  );

  const MainButtons = () => (
    <div className="main-buttons">
      <p className="description-text">
        "다소니"는<br />
        사랑하는 사람을 뜻하는 순우리말입니다.<br />
        소중한 사람들에게 마음을 전하세요.
      </p>
      <button 
        onClick={handleInfoButtonClick}
        className="info-button button-base"
      >
        시스템 소개
      </button>
    </div>
  );

  return (
    <div className="App">
      <div className="main-section">
        <header className="main-header">
          <h1>다 소 니</h1>
        </header>
        <main className="main-content">
          {showInfo ? (
            <>
              <HomeButton />
              <SystemInfoPage />
            </>
          ) : (
            user && <MainButtons />
          )}
        </main>
      </div>
      <div className="side-container">
        <header className="side-header">
          <span className="user-count">실시간 접속자 수: {userCount}</span>
          {user && (
            <div>
              <span className="user-nickname">{user.username}님</span>
              <button onClick={handleLogout} className="logout-button">Logout</button>
            </div>
          )}
        </header>
        {user ? (
          <ChatPage 
            socket={socket} 
            user={user} 
            chatBanTimeLeft={chatBanTimeLeft}
            sendMessage={sendMessage}
          />
        ) : (
          <div className="login-message">로그인이 필요합니다.</div>
        )}
      </div>
      {!user && (
        <div className="modal-backdrop">
          <AuthModal 
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

export default App;