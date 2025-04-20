import React, { useState } from 'react';
import './Dashboard.scss';
import Header from '../Header/Header';
import Sidebar from '../Sidebar/Sidebar';
import Chatbot from '../Chatbot/Chatbot';
import Homepage from '../Homepage/Homepage';
import History from '../History/History';

const Dashboard = () => {
  const [activeMenuItem, setActiveMenuItem] = useState('home'); // Default is home
  const [content, setContent] = useState(null);

  const handleMenuItemClick = (menuItem) => {
    setActiveMenuItem(menuItem);
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
    <div className="dashboard">
      <Header />
      <Sidebar onMenuItemClick={handleMenuItemClick} activeMenuItem={activeMenuItem} />
      <main className="dashboard-content">
        {activeMenuItem === 'home' && (
          <Homepage 
            content={content} 
            setContent={setContent}
            handleUploadFile={handleUploadFile}
            handleInputURL={handleInputURL}
            handleUploadVideo={handleUploadVideo}
          />
        )}
        {activeMenuItem === 'history' && (
          <History 
            content={content} 
            setContent={setContent}
          />
        )}
      </main>
      <Chatbot />
    </div>
  );
};

export default Dashboard;