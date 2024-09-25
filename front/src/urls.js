// src/urls.js

//const BASE_URL = 'http://218.156.126.186:8000';
const BASE_URL = 'http://localhost:8000';
export const URLS = {
  API_BASE_URL: BASE_URL,
  WS_URL: `ws${BASE_URL.slice(4)}/ws`,
  LOGIN: `${BASE_URL}/login`,
  REGISTER: `${BASE_URL}/register`,
  CHECK_DUPLICATE: `${BASE_URL}/check_duplicate`,
};

export default URLS;