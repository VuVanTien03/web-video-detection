import React, { useState } from 'react';
import Sidebar from '../Sidebar/Sidebar';
import './History.scss';

const History = () => {
  const [activeMenuItem, setActiveMenuItem] = useState('home');
  const [content, setContent] = useState(null);
  const [chatMessages, setChatMessages] = useState([
    'Thấy video này rồi?',
    'Gửi bạn link video này?',
    '0:01/2:01',
  ]);

  const handleMenuItemClick = (path) => {
    setActiveMenuItem(path);
    if (path === 'history') {
      setContent(
        <div className="history-content">
          <div className="main-content__display">
            <video controls>
              <source src="sample-video.mp4" type="video/mp4" />
              Your browser does not support the video tag.
            </video>
            <p>MV CHỈNG TÂN CÔN ĐỔ KHÔNG?</p>
            <p>- Orange | OST Phim "Bộ Tư Bốn..."</p>
          </div>
          <div className="chat-area">
            {chatMessages.map((msg, index) => (
              <div key={index} className="chat-area__message">
                {msg}
              </div>
            ))}
            <div className="chat-area__input">
              <input type="text" placeholder="Nhập tin nhắn..." />
              <button>Gửi</button>
            </div>
          </div>
        </div>
      );
    } else {
      setContent(null); // Reset content khi quay lại Trang chủ
    }
  };

  const handleUploadFile = () => {
    alert('Tải file lên chưa được triển khai!');
  };

  const handleInputURL = () => {
    const url = prompt('Nhập URL:');
    if (url) setContent(<p>Đang tải nội dung từ URL: {url}</p>);
  };

  const handleUploadVideo = () => {
    alert('Tải video chưa được triển khai!');
  };

  return (
    <div className="layout">
      <Sidebar onMenuItemClick={handleMenuItemClick} activeMenuItem={activeMenuItem} />
      <div className="main">
        <header className="header">
          <span className="header__logo">YODO</span>
          <span className="header__user">👤</span>
        </header>
        <main className="main-content">
          {activeMenuItem === 'home' && (
            <>
              <div className="main-content__actions">
                <button className="main-content__button upload-file" onClick={handleUploadFile}>
                  Tải file lên
                </button>
                <button className="main-content__button input-url" onClick={handleInputURL}>
                  Nhập URL
                </button>
                <button className="main-content__button upload-video" onClick={handleUploadVideo}>
                  Tải video
                </button>
              </div>
              <div className="main-content__search">
                <input type="text" placeholder="Search" />
              </div>
              <div className="main-content__display">
                {content || (
                  <div>
                    <video controls>
                      <source src="sample-video.mp4" type="video/mp4" />
                      Your browser does not support the video tag.
                    </video>
                    <p>MV CHỈNG TÂN CÔN ĐỔ KHÔNG?</p>
                    <p>- Orange | OST Phim "Bộ Tư Bốn..."</p>
                  </div>
                )}
              </div>
            </>
          )}
          {activeMenuItem === 'history' && content}
        </main>
      </div>
    </div>
  );
};

export default History;