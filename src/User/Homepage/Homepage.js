import React from 'react';
import './Homepage.scss';

const Homepage = ({ content, setContent, handleUploadFile, handleInputURL, handleUploadVideo }) => {
  return (
    <div className="homepage">
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
            <p>MV CHỊNG TÂN CÔN ĐỔ KHÔNG?</p>
            <p>- Orange | OST Phim "Bộ Tư Bốn..."</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Homepage;