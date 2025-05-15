// 개발 환경: 로컬에서 실행 시 localhost 사용
// 프로덕션: Docker 내부에서 web 서비스명 사용
const BASE_URL = process.env.REACT_APP_API_URL || 'http://web:8000';

export const URLS = {
  API_BASE_URL: BASE_URL,
  WS_URL: `ws://${window.location.host}/ws`,
  LOGIN: `${BASE_URL}/api/login`,
  REGISTER: `${BASE_URL}/api/register`,
  CHECK_DUPLICATE: `${BASE_URL}/api/check_duplicate`,
};

export default URLS;
