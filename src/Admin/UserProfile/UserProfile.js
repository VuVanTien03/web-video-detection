// UserProfilePage.jsx
import React, { useState } from 'react';
import { Mail, Instagram, Facebook, Search, ChevronRight } from 'lucide-react';
import './UserProfile.scss';

const UserProfile = () => {
  const [currentPage, setCurrentPage] = useState(1);
  
  // Thông tin người dùng
  const userInfo = {
    name: 'Võ Nguyễn Vũ',
    email: 'vonguyenvu_167@hus.edu.vn',
    gender: 'Nam',
    registerDate: '01/01/2025',
    videoCount: 20
  };
  
  // Danh sách video đã tải lên
  const videos = [
    {
      id: 1,
      title: 'JACK - J97 | Thiên Lý Ơi | Official Music Video',
      thumbnail: '/video-thumbnail-1.jpg',
      uploadDate: '02/03/2025',
      violenceLevel: 'Không có'
    },
    {
      id: 2,
      title: 'ERIK - "Dù cho tận thế (vẫn yêu em)" | Official M/V | Valentine 2025',
      thumbnail: '/video-thumbnail-2.jpg',
      uploadDate: '03/03/2025',
      violenceLevel: 'Có'
    },
    {
      id: 3,
      title: 'BIGBANG - HARU HARU(하루하루) M/V',
      thumbnail: '/video-thumbnail-3.jpg',
      uploadDate: '04/03/2025',
      violenceLevel: 'Có'
    }
  ];
  
  return (
    <div className="profile-container">
      {/* Header */}
      <header className="profile-header">
        <button className="menu-button">
          <div className="menu-icon"></div>
        </button>
        
        <h1 className="header-title">Nhận diện bạo lực trong video</h1>
        
        <div className="user-avatar">
          <span>V</span>
        </div>
      </header>
      
      {/* User Profile Section */}
      <div className="profile-section">
        <div className="user-info">
          <div className="info-details">
            <p className="info-item"><strong>Tên người dùng:</strong> {userInfo.name}</p>
            <p className="info-item"><strong>Email:</strong> {userInfo.email}</p>
            <p className="info-item"><strong>Giới tính:</strong> {userInfo.gender}</p>
            <p className="info-item"><strong>Ngày đăng kí:</strong> {userInfo.registerDate}</p>
            <p className="info-item"><strong>Số video đã tải lên:</strong> {userInfo.videoCount}</p>
          </div>
          <div className="user-photo">
            <img src="/user-photo.jpg" alt="User" className="profile-image" />
          </div>
        </div>
      </div>
      
      {/* Video List Section */}
      <div className="video-list-section">
        <div className="video-list-header">
          <h2 className="section-title">Danh sách {userInfo.videoCount} video đã tải lên</h2>
          
          <div className="search-container">
            <input type="text" placeholder="Tìm kiếm" className="search-input" />
            <button className="search-button">
              <Search size={16} />
            </button>
          </div>
        </div>
        
        <div className="video-grid">
          {videos.map(video => (
            <div key={video.id} className="video-card">
              <div className="video-thumbnail">
                <div className="thumbnail-placeholder"></div>
              </div>
              <div className="video-info">
                <h3 className="video-title">{video.title}</h3>
                <p className="video-meta"><strong>Thời gian tải lên:</strong> {video.uploadDate}</p>
                <p className="video-meta"><strong>Mức độ bạo lực:</strong> {video.violenceLevel}</p>
              </div>
            </div>
          ))}
        </div>
        
        {/* Pagination */}
        <div className="pagination">
          <button className={`page-number current`}>1</button>
          <button className="page-number">2</button>
          <button className="page-number">3</button>
          <button className="page-number">4</button>
          <button className="page-number">5</button>
          <button className="next-page">
            <ChevronRight size={16} />
          </button>
        </div>
      </div>
      
      {/* Footer */}
      <footer className="profile-footer">
        <div className="footer-text">
          <p>Dự án này hướng đến việc xây dựng một nền tảng web giúp tự động nhận diện, phân tích các đối tượng trong video và cung cấp báo cáo trực quan cho người dùng.</p>
        </div>
        
        <div className="contact-info">
          <p className="contact-title">Thông tin liên hệ</p>
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

export default UserProfile;