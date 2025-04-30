import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './Header.scss';

const Header = () => {
  const [showUserInfo, setShowUserInfo] = useState(false);
  const [userInfo, setUserInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  // Lấy thông tin người dùng khi component được tạo ra hoặc khi có đăng nhập mới
  useEffect(() => {
    // Kiểm tra nếu đã có thông tin trong localStorage
    const checkStoredUserData = () => {
      // Thử lấy từ cả hai key có thể có: user_profile và userData
      const storedUserData = localStorage.getItem('user_profile') || localStorage.getItem('userData');
      if (storedUserData) {
        console.log('Đã tìm thấy thông tin người dùng trong localStorage:', JSON.parse(storedUserData));
        setUserInfo(JSON.parse(storedUserData));
      } else if (localStorage.getItem('token')) {
        // Nếu có token nhưng không có userData, gọi API để lấy thông tin
        fetchUserInfo();
      }
    };

    checkStoredUserData();

    // Lắng nghe sự kiện khi người dùng đăng nhập
    const handleUserLoggedIn = () => {
      checkStoredUserData();
    };

    window.addEventListener('userLoggedIn', handleUserLoggedIn);
    window.addEventListener('storage', handleUserLoggedIn); // Lắng nghe thay đổi trong localStorage

    return () => {
      window.removeEventListener('userLoggedIn', handleUserLoggedIn);
      window.removeEventListener('storage', handleUserLoggedIn);
    };
  }, []);

  const fetchUserInfo = async () => {
    const token = localStorage.getItem('token');
    if (!token) return;

    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/users/me', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Không thể lấy thông tin người dùng');
      }

      const data = await response.json();
      console.log('Thông tin người dùng từ API:', data);
      setUserInfo(data);
      // Lưu thông tin vào localStorage để lần sau không cần gọi API
      localStorage.setItem('user_profile', JSON.stringify(data));
    } catch (error) {
      console.error('Lỗi khi lấy thông tin người dùng:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUserClick = () => {
    if (!userInfo && localStorage.getItem('token')) {
      fetchUserInfo();
    }
    setShowUserInfo(!showUserInfo);
  };

  const handleLogout = () => {
    // Xóa token và thông tin người dùng
    localStorage.removeItem('token');
    localStorage.removeItem('token_type');
    localStorage.removeItem('user_profile');
    localStorage.removeItem('userData');
    setUserInfo(null);
    setShowUserInfo(false);
    
    // Chuyển về trang đăng nhập
    navigate('/login');
  };

  // Lấy tên hiển thị từ full_name hoặc username
  const getDisplayName = () => {
    if (!userInfo) return null;
    return userInfo.full_name || userInfo.username || 'Người dùng';
  };

  // Lấy chữ cái đầu tiên để hiển thị avatar
  const getInitial = () => {
    const displayName = getDisplayName();
    return displayName ? displayName.charAt(0).toUpperCase() : '?';
  };

  return (
    <header className="header">
      <div className="header__logo">
        <span className="header__logo-icon">🎬</span>
        <span className="header__logo-text">YODO</span>
      </div>
      <div className="header__actions">
        <div className="header__user">
          <button className="header__user-btn" onClick={handleUserClick}>
            {userInfo ? (
              <div className="header__user-avatar-btn">
                {getInitial()}
              </div>
            ) : (
              '👤'
            )}
          </button>
          
          {showUserInfo && (
            <div className="header__user-info">
              {loading ? (
                <p>Đang tải thông tin...</p>
              ) : userInfo ? (
                <>
                  <div className="header__user-avatar">
                    {userInfo.avatar ? (
                      <img src={userInfo.avatar} alt={getDisplayName()} />
                    ) : (
                      <div className="header__default-avatar">
                        {getInitial()}
                      </div>
                    )}
                  </div>
                  <div className="header__user-details">
                    <h3>{getDisplayName()}</h3>
                    <p>{userInfo.email}</p>
                    {userInfo.role && <p className="header__user-role">{userInfo.role}</p>}
                  </div>
                  <div className="header__user-actions">
                    <button>Thông tin tài khoản</button>
                    <button>Cài đặt</button>
                    <button className="header__logout-btn" onClick={handleLogout}>Đăng xuất</button>
                  </div>
                </>
              ) : (
                <div className="header__user-not-logged-in">
                  <p>Bạn chưa đăng nhập</p>
                  <button onClick={() => navigate('/login')}>Đăng nhập</button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;