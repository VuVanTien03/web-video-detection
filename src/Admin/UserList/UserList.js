// UserListPage.jsx
import React, { useState } from 'react';
import { Mail, Instagram, Facebook, Search, Plus } from 'lucide-react';
import './UserList.scss';

const UserList = () => {
  const [users, setUsers] = useState([
    {
      id: '001',
      name: 'Nguyễn Văn A',
      registerDate: '01/01/2025',
      videoCount: 20
    }
  ]);

  const handleDeleteUser = (userId) => {
    setUsers(users.filter(user => user.id !== userId));
  };

  return (
    <div className="user-list-container">
      {/* Header */}
      <header className="main-header">
        <button className="menu-button">
          <div className="menu-icon"></div>
        </button>
        
        <h1 className="header-title">Nhận diện bạo lực trong video</h1>
        
        <div className="user-avatar">
          <span>V</span>
        </div>
      </header>
      
      {/* Main Content */}
      <main className="content-area">
        <div className="user-list-header">
          <h2 className="section-title">Danh sách người dùng</h2>
          
          <div className="search-container">
            <input type="text" placeholder="Tìm kiếm" className="search-input" />
            <button className="search-button">
              <Search size={16} />
            </button>
          </div>
        </div>
        
        <div className="table-container">
          <div className="table-header">
            <label className="table-name">
              <input type="checkbox" className="table-checkbox" />
              <span>Table 1</span>
            </label>
          </div>
          
          <table className="user-table">
            <thead>
              <tr>
                <th className="id-column">ID</th>
                <th className="name-column">Tên người dùng</th>
                <th className="date-column">Ngày đăng kí</th>
                <th className="video-column">Số video đã tải lên</th>
                <th className="action-column">Quản lý</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id}>
                  <td>{user.id}</td>
                  <td>{user.name}</td>
                  <td>{user.registerDate}</td>
                  <td>{user.videoCount}</td>
                  <td>
                    <button 
                      className="delete-button"
                      onClick={() => handleDeleteUser(user.id)}
                    >
                      Xóa user
                    </button>
                  </td>
                </tr>
              ))}
              {/* Empty rows for layout */}
              {[...Array(5)].map((_, index) => (
                <tr key={`empty-${index}`} className="empty-row">
                  <td></td>
                  <td></td>
                  <td></td>
                  <td></td>
                  <td></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        <div className="action-buttons">
          {/* <button className="add-button">
            <Plus size={16} />
            <span>Fra...</span>
          </button> */}
          
          {/* <button className="delete-user-button">
            Xóa user
          </button> */}
        </div>
      </main>
      
      {/* Footer */}
      <footer className="main-footer">
        <div className="footer-text">
          <p>Dự án này hướng đến việc xây dựng một nền tảng web giúp tự động nhận diện, phân tích các đối tượng trong video và cung cấp báo cáo trực quan cho người dùng</p>
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

export default UserList;