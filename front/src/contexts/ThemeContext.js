import React, { createContext, useState, useContext, useEffect } from 'react';

// 테마 컨텍스트 생성
const ThemeContext = createContext();

// ThemeProvider 컴포넌트 정의
export const ThemeProvider = ({ children }) => {
  // 다크 모드 상태를 관리하는 state
  const [isDarkMode, setIsDarkMode] = useState(false);

  // 컴포넌트 마운트 시 로컬 스토리지에서 저장된 테마 불러오기
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
      setIsDarkMode(true);
    }
  }, []); // 빈 배열을 넣어 마운트 시에만 실행

  // 테마 토글 함수
  const toggleTheme = () => {
    setIsDarkMode(!isDarkMode); // 현재 상태의 반대로 설정
    localStorage.setItem('theme', !isDarkMode ? 'dark' : 'light'); // 로컬 스토리지에 테마 저장
  };

  // ThemeContext.Provider를 사용하여 자식 컴포넌트에게 테마 상태와 토글 함수 제공
  return (
    <ThemeContext.Provider value={{ isDarkMode, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

// 커스텀 훅: 다른 컴포넌트에서 테마 상태와 토글 함수를 쉽게 사용할 수 있게 함
export const useTheme = () => useContext(ThemeContext);