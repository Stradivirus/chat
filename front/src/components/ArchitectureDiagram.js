import React from 'react';
import architectureImage from '../assets/architecture-diagram.png'; // 이미지 파일 import

const ArchitectureDiagram = () => {
  return (
    <div className="architecture-diagram" style={{
      maxWidth: '1000px',
      margin: '0 auto',
      padding: '20px'
    }}>
      <img 
        src={architectureImage} 
        alt="시스템 아키텍처 다이어그램"
        style={{
          width: '100%',
          height: 'auto',
          borderRadius: '8px',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
        }}
      />
    </div>
  );
};

export default ArchitectureDiagram;