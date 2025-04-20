import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { RiUploadCloudFill } from "react-icons/ri";
import './LadingPage.scss';

const LadingPage = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file && (file.type === 'video/mp4' || file.type === 'video/webm' || file.type === 'video/ogg')) {
      setSelectedFile(file);
      console.log('Tệp đã chọn:', file.name);
    } else {
      alert('Vui lòng chọn một tệp video hợp lệ (mp4, webm, hoặc ogg).');
      setSelectedFile(null);
    }
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setIsDragOver(false);
    const file = event.dataTransfer.files[0];
    if (file && (file.type === 'video/mp4' || file.type === 'video/webm' || file.type === 'video/ogg')) {
      setSelectedFile(file);
      console.log('Tệp được kéo thả:', file.name);
    } else {
      alert('Vui lòng kéo thả một tệp video hợp lệ (mp4, webm, hoặc ogg).');
      setSelectedFile(null);
    }
  };

  const handleDragOver = (event) => {
    event.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (event) => {
    event.preventDefault();
    setIsDragOver(false);
  };

  return (
    <div className="homepage-container">
      <header className="header">
        <div className="logo">YODO</div>
        <Link to="/login" className="login-btn">Đăng nhập</Link>
      </header>
      <main className="main-content1">
        <h1 className="moving-text">Video Detection AI</h1>
        <div className="upload-section">
          <div
            className={`upload-area ${isDragOver ? 'dragover' : ''}`}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onClick={() => document.getElementById('file-input').click()}
          >
            <input
              type="file"
              id="file-input"
              accept="video/mp4,video/webm,video/ogg"
              onChange={handleFileChange}
              style={{ display: 'none' }}
            />
            <span className="upload-icon moving-cloud"> <RiUploadCloudFill /></span>
            <p>
              Tải tệp lên<br />(Hỗ trợ video)
              {selectedFile && <span> (Đã chọn: {selectedFile.name})</span>}
            </p>
          </div>
          <p className="or-text">Hoặc</p>
          <div className="url-input">
            <input type="text" placeholder="Dán một URL (youtube...)" />
            <button className="import-btn">Nhập từ URL</button>
          </div>
          {selectedFile && (
            <button className="upload-btn">
              Tải lên video
            </button>
          )}
        </div>
      </main>
    </div>
  );
};

export default LadingPage;
