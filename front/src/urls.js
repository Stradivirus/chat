// src/urls.js
// 로컬로 바로 실행할 경우
//const BASE_URL = 'http://34.64.160.67:8000';
//const BASE_URL = 'http://localhost:8000';
//export const URLS = {
//  API_BASE_URL: BASE_URL,
//  WS_URL: `ws${BASE_URL.slice(4)}/ws`,
//  LOGIN: `${BASE_URL}/login`,
//  REGISTER: `${BASE_URL}/register`,
//  CHECK_DUPLICATE: `${BASE_URL}/check_duplicate`,
//};

//export default URLS;

// front/src/urls.js

const BASE_URL = '';  // 또는 const BASE_URL = '/api';
export const URLS = {
  API_BASE_URL: '/api',
  WS_URL: '/ws',
  LOGIN: '/api/login',
  REGISTER: '/api/register',
  CHECK_DUPLICATE: '/api/check_duplicate',
};

export default URLS;