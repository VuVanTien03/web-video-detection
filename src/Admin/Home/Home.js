// VideoAnalyticsDashboard.jsx
import React from 'react';
import { Mail, Instagram, Facebook } from 'lucide-react';
import './Home.scss';

const Home = () => {
  // Sample data for charts
  const newUserData = [2, 4, 1, 2, 2, 5, 1];
  const videoUploadData = [5, 3, 2, 3, 2, 4, 6];
  
  return (
    <div className="dashboard-container">
      {/* Header */}
      <header className="dashboard-header">
        <button className="menu-button">
          <div className="menu-icon"></div>
        </button>
        
        <div className="search-bar">
          <input type="text" placeholder="Tìm kiếm người dùng, video..." />
          <button className="search-button">
            <span className="search-icon">⌕</span>
          </button>
        </div>
        
        <div className="user-avatar">
          <span>V</span>
        </div>
      </header>
      
      {/* Stats Cards */}
      <div className="stats-container">
        <div className="stat-card">
          <p className="stat-title">Tổng số người dùng:</p>
          <p className="stat-value">100</p>
        </div>
        
        <div className="stat-card">
          <p className="stat-title">Số người dùng mới:</p>
          <p className="stat-value">10</p>
        </div>
        
        <div className="stat-card">
          <p className="stat-title">Số video đã tải lên:</p>
          <p className="stat-value">1000</p>
        </div>
      </div>
      
      {/* Charts Section */}
      <div className="charts-container">
        <div className="chart-section">
          <h3 className="chart-title">Thống kê số người dùng mới theo ngày</h3>
          <div className="bar-chart">
            {newUserData.map((value, index) => (
              <div key={index} className="bar-container">
                <div 
                  className="bar" 
                  style={{ height: `${value * 20}%` }}
                ></div>
                <div className="bar-label">{index + 1}</div>
              </div>
            ))}
          </div>
        </div>
        
        <div className="chart-section">
          <h3 className="chart-title">Thống kê số video tải lên theo ngày</h3>
          <div className="area-chart">
            <svg viewBox="0 0 300 150" preserveAspectRatio="none">
              <path 
                d={`M0,${150 - videoUploadData[0] * 15} 
                   L${300/6},${150 - videoUploadData[1] * 15} 
                   L${300/6*2},${150 - videoUploadData[2] * 15} 
                   L${300/6*3},${150 - videoUploadData[3] * 15}
                   L${300/6*4},${150 - videoUploadData[4] * 15}
                   L${300/6*5},${150 - videoUploadData[5] * 15}
                   L${300},${150 - videoUploadData[6] * 15}
                   L${300},150 L0,150 Z`}
                className="area-path"
              />
            </svg>
          </div>
        </div>
      </div>
      
      {/* Footer */}
      <footer className="dashboard-footer">
        <div className="footer-text">
          <p>Dự án này hướng đến việc xây dựng một nền tảng web giúp tự động nhận diện, phân tích các đối tượng trong videos và cung cấp báo cáo trực quan cho người dùng</p>
        </div>
        
        <div className="footer-links">
          <p className="footer-title">Thông tin liên hệ</p>
          <div className="social-links">
            <a href="#" className="social-link">
              <Mail size={18} />
            </a>
            <a href="#" className="social-link">
              <Instagram size={18} />
            </a>
            <a href="#" className="social-link">
              <Facebook size={18} />
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Home;