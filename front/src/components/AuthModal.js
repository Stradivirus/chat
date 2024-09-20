import React, { useState } from 'react';
import axios from 'axios';
import '../styles/AuthModal.css';

// axios 인스턴스 생성
// baseURL을 설정하여 모든 요청의 기본 URL을 지정
// withCredentials를 true로 설정하여 쿠키를 포함한 크로스 도메인 요청을 가능하게 함
const api = axios.create({
  baseURL: 'http://localhost:8000/',
  withCredentials: true // CORS 관련 설정
});

// AuthModal 컴포넌트 정의
// type: 'login' 또는 'register'를 받아 모달의 유형을 결정
// onClose: 모달을 닫는 함수
// onLoginSuccess: 로그인 성공 시 호출될 콜백 함수
function AuthModal({ type, onClose, onLoginSuccess }) {
  // 상태 관리를 위한 useState 훅 사용
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [nickname, setNickname] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errors, setErrors] = useState({}); // 폼 유효성 검사 오류를 저장
  const [isLoading, setIsLoading] = useState(false); // 로딩 상태 관리

  // 폼 유효성 검사 함수
  const validateForm = () => {
    const newErrors = {};
    
    // 회원가입 시 추가 검증
    if (type === 'register') {
      // 이메일 형식 검사
      if (!email || !/\S+@\S+\.\S+/.test(email)) {
        newErrors.email = '유효한 이메일 주소를 입력해주세요.';
      }
      // 닉네임 길이 검사
      if (!nickname || nickname.length < 2) {
        newErrors.nickname = '닉네임은 2자 이상이어야 합니다.';
      }
      // 비밀번호 일치 여부 검사
      if (password !== confirmPassword) {
        newErrors.confirmPassword = '비밀번호가 일치하지 않습니다.';
      }
    }

    // 공통 검증
    if (!username || username.length < 4) {
      newErrors.username = '아이디는 4자 이상이어야 합니다.';
    }
    if (!password || password.length < 8) {
      newErrors.password = '비밀번호는 8자 이상이어야 합니다.';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0; // 오류가 없으면 true 반환
  };

  // 폼 제출 핸들러
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (validateForm()) {
      setIsLoading(true);
      try {
        let response;
        if (type === 'login') {
          // 로그인 요청
          response = await api.post('/login', { username, password });
          console.log('Login response:', response.data);
          if (response.data && response.data.user_id) {
            // 로그인 성공 시 0.5초 후 onLoginSuccess 콜백 실행
            setTimeout(() => {
              if (typeof onLoginSuccess === 'function') {
                onLoginSuccess({
                  userId: response.data.user_id,
                  username: username
                });
              } else {
                console.error('onLoginSuccess is not a function');
              }
              setIsLoading(false);
              onClose();
            }, 500);
          } else {
            throw new Error('Invalid server response');
          }
        } else {
          // 회원가입 요청
          response = await api.post('/register', { email, username, nickname, password });
          console.log('Registration successful:', response.data);
          if (response.data && response.data.user_id) {
            // 회원가입 후 자동 로그인
            if (typeof onLoginSuccess === 'function') {
              onLoginSuccess({
                userId: response.data.user_id,
                username: username
              });
            } else {
              console.error('onLoginSuccess is not a function');
            }
          }
          setIsLoading(false);
          onClose();
        }
      } catch (error) {
        // 에러 처리
        console.error('Error:', error.response ? error.response.data : error.message);
        setErrors({ api: error.response ? error.response.data.detail : '서버 오류가 발생했습니다.' });
        setIsLoading(false);
      }
    }
  };

  // 컴포넌트 렌더링
  return (
    <div className="auth-modal">
      <h2>{type === 'login' ? '로그인' : '회원가입'}</h2>
      <form onSubmit={handleSubmit}>
        {type === 'login' && (
          // 로그인 폼 필드
          <>
            <input
              type="text"
              placeholder="아이디"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
            {errors.username && <p className="error">{errors.username}</p>}
            <input
              type="password"
              placeholder="비밀번호"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            {errors.password && <p className="error">{errors.password}</p>}
          </>
        )}
        {type === 'register' && (
          // 회원가입 폼 필드
          <>
            <input
              type="email"
              placeholder="이메일"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            {errors.email && <p className="error">{errors.email}</p>}
            <input
              type="text"
              placeholder="아이디"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
            {errors.username && <p className="error">{errors.username}</p>}
            <input
              type="text"
              placeholder="닉네임"
              value={nickname}
              onChange={(e) => setNickname(e.target.value)}
              required
            />
            {errors.nickname && <p className="error">{errors.nickname}</p>}
            <input
              type="password"
              placeholder="비밀번호"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            {errors.password && <p className="error">{errors.password}</p>}
            <input
              type="password"
              placeholder="비밀번호 확인"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />
            {errors.confirmPassword && <p className="error">{errors.confirmPassword}</p>}
          </>
        )}
        {errors.api && <p className="error">{errors.api}</p>}
        <button type="submit" disabled={isLoading}>
          {isLoading ? '처리 중...' : (type === 'login' ? '로그인' : '회원가입')}
        </button>
      </form>
      <button onClick={onClose} className="close-button">&times;</button>
    </div>
  );
}

export default AuthModal;