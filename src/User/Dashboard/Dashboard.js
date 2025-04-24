import React, { useState } from 'react';
import './Dashboard.scss';
import Header from '../Header/Header';
import Sidebar from '../Sidebar/Sidebar';
import Chatbot from '../Chatbot/Chatbot';
import Homepage from '../Homepage/Homepage';
import History from '../History/History';

const Dashboard = () => {
  const [activeMenuItem, setActiveMenuItem] = useState('home');
  
  // State riêng cho trang chủ
  const [homeContent, setHomeContent] = useState(null);
  // State riêng cho trang lịch sử
  const [historyContent, setHistoryContent] = useState(null);

  const handleMenuItemClick = (menuItem) => {
    setActiveMenuItem(menuItem);
  };

  return (
    <div className="dashboard">
      <Header />
      <Sidebar onMenuItemClick={handleMenuItemClick} activeMenuItem={activeMenuItem} />
      <main className="dashboard-content">
        {activeMenuItem === 'home' && (
          <Homepage
            content={homeContent}
            setContent={setHomeContent}
          />
        )}
        {activeMenuItem === 'history' && (
          <History
            content={historyContent}
            setContent={setHistoryContent}
          />
        )}
      </main>
      <Chatbot />
    </div>
  );
};

export default Dashboard;