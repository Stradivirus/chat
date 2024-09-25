import React, { useState, useEffect } from 'react';
import axios from 'axios';
import '../styles/AuthModal.css';
import { URLS } from '../urls';

const api = axios.create({
  baseURL: URLS.API_BASE_URL,
  withCredentials: true
});

function AuthModal({ onLoginSuccess }) {
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [nickname, setNickname] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errors, setErrors] = useState({});
  const [duplicates, setDuplicates] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [isLoginMode, setIsLoginMode] = useState(true);

  const validateForm = () => {
    const newErrors = {};
    
    if (!isLoginMode) {
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

  const checkDuplicate = async (field) => {
    if (!isLoginMode && (field === 'email' || field === 'username' || field === 'nickname')) {
      const value = field === 'email' ? email : field === 'username' ? username : nickname;
      
      // 빈 값 체크
      if (!value.trim()) {
        setDuplicates(prev => ({ ...prev, [field]: null }));
        return;
      }

      try {
        const response = await api.post(URLS.CHECK_DUPLICATE, { [field]: value });
        if (response.data.isDuplicate) {
          setDuplicates(prev => ({ ...prev, [field]: `이 ${field === 'email' ? '이메일' : field === 'username' ? '아이디' : '닉네임'}은 이미 사용 중입니다.` }));
        } else {
          setDuplicates(prev => ({ ...prev, [field]: null }));
        }
      } catch (error) {
        console.error('Error checking duplicate:', error);
        // 422 에러 (Unprocessable Entity)를 특별히 처리
        if (error.response && error.response.status === 422) {
          setDuplicates(prev => ({ ...prev, [field]: null }));
        } else {
          setErrors(prev => ({ ...prev, api: '서버 오류가 발생했습니다. 나중에 다시 시도해주세요.' }));
        }
      }
    }
  };

  const handleBlur = (field) => {
    if (!isLoginMode) {
      checkDuplicate(field);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (validateForm() && !Object.values(duplicates).some(Boolean)) {
      setIsLoading(true);
      // 2초 대기
      await new Promise(resolve => setTimeout(resolve, 2000));
      try {
        let response;
        if (isLoginMode) {
          response = await api.post(URLS.LOGIN, { username, password });
          if (response.data && response.data.user_id) {
            onLoginSuccess({
              userId: response.data.user_id,
              username: username
            });
          } else {
            throw new Error('Invalid server response');
          }
        } else {
          response = await api.post(URLS.REGISTER, { email, username, nickname, password });
          if (response.data && response.data.user_id) {
            onLoginSuccess({
              userId: response.data.user_id,
              username: username
            });
          }
        }
        setIsLoading(false);
      } catch (error) {
        console.error('Error:', error.response ? error.response.data : error.message);
        setErrors({ api: error.response ? error.response.data.detail : '서버 오류가 발생했습니다.' });
        setIsLoading(false);
      }
    }
  };

  const toggleMode = () => {
    setIsLoginMode(!isLoginMode);
    setErrors({});
    setDuplicates({});
    setEmail('');
    setUsername('');
    setNickname('');
    setPassword('');
    setConfirmPassword('');
  };

  return (
    <div className="auth-modal">
      <h2>{isLoginMode ? '로그인' : '회원가입'}</h2>
      <form onSubmit={handleSubmit}>
        {!isLoginMode && (
          <>
            <input
              type="email"
              placeholder="이메일"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onBlur={() => handleBlur('email')}
              required
            />
            {errors.email && <p className="error">{errors.email}</p>}
            {duplicates.email && <p className="duplicate-error">{duplicates.email}</p>}
          </>
        )}
        <input
          type="text"
          placeholder="아이디"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          onBlur={() => handleBlur('username')}
          required
        />
        {errors.username && <p className="error">{errors.username}</p>}
        {duplicates.username && <p className="duplicate-error">{duplicates.username}</p>}
        {!isLoginMode && (
          <>
            <input
              type="text"
              placeholder="닉네임"
              value={nickname}
              onChange={(e) => setNickname(e.target.value)}
              onBlur={() => handleBlur('nickname')}
              required
            />
            {errors.nickname && <p className="error">{errors.nickname}</p>}
            {duplicates.nickname && <p className="duplicate-error">{duplicates.nickname}</p>}
          </>
        )}
        <input
          type="password"
          placeholder="비밀번호"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        {errors.password && <p className="error">{errors.password}</p>}
        {!isLoginMode && (
          <>
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
        <button type="submit" disabled={isLoading || Object.values(duplicates).some(Boolean)}>
          {isLoading ? '처리 중...' : (isLoginMode ? '로그인' : '회원가입')}
        </button>
      </form>
      <button onClick={toggleMode} className="switch-auth-type">
        {isLoginMode ? '회원가입' : '로그인'}
      </button>
    </div>
  );
}

export default AuthModal;