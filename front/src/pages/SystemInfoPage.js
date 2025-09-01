// src/pages/SystemInfoPage.js
import React from 'react';
import ArchitectureDiagram from '../components/ArchitectureDiagram';
import './SystemInfoPage.css';

const SystemInfoPage = () => {
  return (
    <div className="system-info">
      <h2 style={{ color: '#333', marginBottom: '2rem' }}>시스템 아키텍쳐</h2>
      
      <div className="content-grid">
        {/* 왼쪽: 시스템 구성 */}
        <div>
          {/* GitHub 링크 섹션 */}
          <div className="github-links">
            <div className="link-container">
              <a href="https://github.com/Stradivirus/chat" target="_blank" rel="noopener noreferrer">
                Chat 깃
              </a>
            </div>
          </div>
          
          {/* 아키텍처 다이어그램 */}
          <div className="architecture-diagram-container">
            <ArchitectureDiagram />
          </div>
          
          <h2 style={{ color: '#333', marginBottom: '1.5rem' }}>시스템 구성</h2>
          
          <div className="system-section">
            <h3>1. 채팅 시스템 (chat-network)</h3>
            <div className="component-description">
              <h4>프론트엔드 (React)</h4>
              <ul>
                <li>실시간 채팅 UI 제공</li>
                <li>채팅창 관리 및 스팸 방지 기능</li>
                <li>WebSocket을 통한 실시간 통신</li>
              </ul>

              <h4>백엔드 (FastAPI)</h4>
              <ul>
                <li>사용자 인증 및 세션 관리</li>
                <li>WebSocket 연결 관리</li>
                <li>실시간 메시지 처리</li>
                <li>사용자 인증 처리</li>
              </ul>

              <h4>데이터 저장소</h4>
              <ul>
                <li>Redis: 실시간 채팅 데이터 캐싱</li>
                <li>Redis에서 Postgresql로 자동 동기화</li>
                <li>PostgreSQL: 사용자 정보 및 채팅 이력 저장</li>
              </ul>
            </div>
          </div>

          <div className="system-section">
            <h3>2. 데이터 흐름</h3>
            <div className="component-description">
              <ul>
                <li>채팅 데이터: FastAPI → Redis → PostgreSQL</li>
                <li>로그인 정보: FastAPI → PostgreSQL</li>
              </ul>
            </div>
          </div>
        </div>

        {/* 오른쪽: 향후 추가 기능 */}
        <div>
          <h2 style={{ color: '#333', marginBottom: '1.5rem' }}>향후 추가하고 싶은 기능</h2>
          
          <div className="system-section">
            <h3>MSA 구조 완성</h3>
            <div className="component-description">
              <h4>API Gateway 구축</h4>
              <ul>
                <li>중앙 집중식 라우팅 처리</li>
                <li>인증/인가 통합 관리</li>
                <li>로드 밸런싱 구현</li>
              </ul>

              <h4>서비스 디스커버리</h4>
              <ul>
                <li>동적 서비스 등록/발견</li>
                <li>상태 모니터링</li>
                <li>자동 장애 복구</li>
              </ul>

              <h4>서비스 간 통신</h4>
              <ul>
                <li>Event Bus 구현</li>
                <li>비동기 통신 구조</li>
                <li>Circuit Breaker 패턴 적용</li>
              </ul>
            </div>
          </div>

          <div className="system-section">
            <h3>Kafka 관련 기능</h3>
            <div className="component-description">
              <h4>JWT 토큰 관리</h4>
              <ul>
                <li>토큰 발급: 30분 만료</li>
                <li>만료 5분 전 자동 갱신</li>
                <li>15분 무활동 시 토큰 무효화</li>
              </ul>

              <h4>유저 접속 정보 관리</h4>
              <ul>
                <li>로그인/로그아웃 이벤트 기록</li>
                <li>사용자 활동 추적</li>
                <li>IP 주소, 디바이스 정보 저장</li>
                <li>15분 무활동 자동 로그아웃</li>
              </ul>

              <h4>데이터 백업 및 동기화</h4>
              <ul>
                <li>Kafka에 저장된 접속 정보 백업</li>
                <li>실시간/영구 저장소 동기화</li>
              </ul>
            </div>
          </div>

          <div className="system-section">
            <h3>시스템 모니터링</h3>
            <div className="component-description">
              <h4>성능 모니터링</h4>
              <ul>
                <li>Prometheus + Grafana 메트릭 수집/시각화</li>
                <li>ELK 스택 통합 로깅</li>
                <li>실시간 서비스 상태 모니터링</li>
                <li>임계치 기반 알림 시스템</li>
              </ul>
            </div>
          </div>

          <div className="system-section">
            <h3>어드민 페이지</h3>
            <div className="component-description">
              <ul>
                <li>사용자 관리 대시보드</li>
                <li>채팅 로그 조회 및 관리</li>
                <li>시스템 설정 관리</li>
              </ul>
            </div>
          </div>

          <div className="system-section">
            <h3>CI/CD 및 인프라 개선</h3>
            <div className="component-description">
              <h4>자동화 파이프라인</h4>
              <ul>
                <li>Argo CD를 통한 CD 자동화</li>
                <li>테스트 자동화 연동</li>
              </ul>

              <h4>쿠버네티스 마이그레이션</h4>
              <ul>
                <li>도커 컴포즈에서 k8s 전환</li>
                <li>서비스 매니페스트 작성</li>
                <li>컨테이너 자원 관리 최적화</li>
                <li>무중단 배포 전략 구현</li>
                <li>스케일링 자동화</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemInfoPage;