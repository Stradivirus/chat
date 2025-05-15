// src/urls.js
// 로컬로 바로 실행할 경우
const BASE_URL = 'http://web:8000';
//const BASE_URL = 'http://localhost:8000';

export const URLS = {
  API_BASE_URL: BASE_URL,
  WS_URL: `ws://${window.location.host}/ws`,
  LOGIN: `${BASE_URL}/api/login`,
  REGISTER: `${BASE_URL}/api/register`,
  CHECK_DUPLICATE: `${BASE_URL}/api/check_duplicate`,
};

export default URLS;