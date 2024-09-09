import React, { useState } from 'react';
import axios from 'axios';
import '../styles/AuthModal.css';

// axios 인스턴스 생성
const api = axios.create({
  baseURL: 'http://localhost:8000',
  withCredentials: true // CORS 관련 설정
});

function AuthModal({ type, onClose, onLoginSuccess }) {
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [nickname, setNickname] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errors, setErrors] = useState({});

  const validateForm = () => {
    const newErrors = {};
    
    if (type === 'register') {
      if (!email || !/\S+@\S+\.\S+/.test(email)) {
        newErrors.email = '유효한 이메일 주소를 입력해주세요.';
      }
      if (!nickname || nickname.length < 2) {
        newErrors.nickname = '닉네임은 2자 이상이어야 합니다.';
      }
      if (password !== confirmPassword) {
        newErrors.confirmPassword = '비밀번호가 일치하지 않습니다.';
      }
    }

    if (!username || username.length < 4) {
      newErrors.username = '아이디는 4자 이상이어야 합니다.';
    }
    if (!password || password.length < 8) {
      newErrors.password = '비밀번호는 8자 이상이어야 합니다.';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (validateForm()) {
      try {
        let response;
        if (type === 'login') {
          response = await api.post('/login', { username, password });
        } else {
          response = await api.post('/register', { email, username, nickname, password });
        }
        console.log('Response:', response.data);
        if (type === 'login') {
          // 로그인 성공 시 처리
          onLoginSuccess(response.data);
        } else {
          // 회원가입 성공 시 처리
          console.log('Registration successful');
        }
        onClose();
      } catch (error) {
        console.error('Error:', error.response ? error.response.data : error.message);
        setErrors({ api: error.response ? error.response.data.detail : '서버 오류가 발생했습니다.' });
      }
    }
  };

  return (
    <div className="auth-modal">
      <h2>{type === 'login' ? '로그인' : '회원가입'}</h2>
      <form onSubmit={handleSubmit}>
        {type === 'login' && (
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
        <button type="submit">{type === 'login' ? '로그인' : '회원가입'}</button>
      </form>
      <button onClick={onClose} className="close-button">&times;</button>
    </div>
  );
}

export default AuthModal;