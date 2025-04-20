import HomeIcon from '@mui/icons-material/Home';
import HistoryIcon from '@mui/icons-material/History';
import SettingsIcon from '@mui/icons-material/Settings';
import HelpIcon from '@mui/icons-material/Help';
import React from 'react';
import './Sidebar.scss';

const Sidebar = ({ onMenuItemClick, activeMenuItem }) => {
  return (
    <aside className="sidebar">
      <nav className="sidebar__nav">
        <ul className="sidebar__menu">
          <li 
            className={`sidebar__menu-item ${activeMenuItem === 'home' ? 'sidebar__menu-item--active' : ''}`}
            onClick={() => onMenuItemClick('home')}
          >
            <span className="sidebar__icon"><HomeIcon /></span>
            <span className="sidebar__text">Trang chủ</span>
          </li>
          <li 
            className={`sidebar__menu-item ${activeMenuItem === 'history' ? 'sidebar__menu-item--active' : ''}`}
            onClick={() => onMenuItemClick('history')}
          >
            <span className="sidebar__icon"><HistoryIcon /></span>
            <span className="sidebar__text">Lịch sử</span>
          </li>
        </ul>
      </nav>
      <div className="sidebar__footer">
        <div className="sidebar__footer-item">
          <span className="sidebar__icon"><SettingsIcon /></span>
          <span className="sidebar__text">Cài đặt</span>
        </div>
        <div className="sidebar__footer-item">
          <span className="sidebar__icon"><HelpIcon /></span>
          <span className="sidebar__text">Hướng dẫn</span>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;