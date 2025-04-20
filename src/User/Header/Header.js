import React from 'react';
import './Header.scss';

const Header = () => {
  return (
    <header className="header">
      <div className="header__logo">
        <span className="header__logo-icon">🎬</span>
        <span className="header__logo-text">YODO</span>
      </div>
      <div className="header__actions">
        <button className="header__settings-btn">⚙️</button>
      </div>
    </header>
  );
};

export default Header;