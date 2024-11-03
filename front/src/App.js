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
  const [showExam, setShowExam] = useState(false);
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
    setShowExam(false);
    setShowInfo(false);
    if (socket) {
      socket.close(1000, "Logout");
    }
  };

  const handleSessionExpired = () => {
    setShowSessionExpiredModal(false);
    handleLogout();
  };

  const handleExamButtonClick = () => {
    setShowExam(true);
    setShowInfo(false);
  };

  const handleInfoButtonClick = () => {
    setShowInfo(true);
    setShowExam(false);
  };

  const handleHomeButtonClick = () => {
    setShowExam(false);
    setShowInfo(false);
  };

  const HomeButton = () => (
    <button 
      onClick={handleHomeButtonClick}
      style={{
        position: 'absolute',
        left: '20px',
        top: '20px',
        padding: '8px 16px',
        backgroundColor: '#4a90e2',
        color: 'white',
        border: 'none',
        borderRadius: '4px',
        cursor: 'pointer',
        zIndex: 1000
      }}
    >
      홈으로
    </button>
  );

  const MainButtons = () => (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      gap: '20px',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100%'
    }}>
      <button 
        onClick={handleExamButtonClick}
        style={{
          padding: '15px 30px',
          fontSize: '18px',
          backgroundColor: '#4a90e2',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer'
        }}
      >
        시험 보러가기
      </button>
      <button 
        onClick={handleInfoButtonClick}
        style={{
          padding: '15px 30px',
          fontSize: '18px',
          backgroundColor: '#28a745',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer'
        }}
      >
        시스템 소개
      </button>
    </div>
  );

  return (
    <div className="App">
      <div className="main-section">
        <header className="main-header">
          <h1>채팅 애플리케이션</h1>
        </header>
        <main className="main-content">
          {showInfo ? (
            <>
              <HomeButton />
              <SystemInfoPage />
            </>
          ) : showExam ? (
            <>
              <HomeButton />
              <iframe 
                src="http://localhost:8001"
                style={{
                  width: '100%',
                  height: '100%',
                  border: 'none',
                  overflow: 'hidden'
                }}
                title="Docker Service"
                sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-modals allow-downloads"
                referrerPolicy="origin"
              />
            </>
          ) : (
            user && <MainButtons />
          )}
        </main>
      </div>
      <div className="side-container">
        <header className="side-header">
          <span className="user-count">현재 접속자 수: {userCount}</span>
          {user && (
            <div>
              <span className="user-nickname">{user.username}님</span>
              <button onClick={handleLogout} className="logout-button">로그아웃</button>
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