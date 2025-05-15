import React, { useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import { RiUploadCloudFill } from "react-icons/ri";
import './LadingPage.scss';

const LadingPage = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [videoUrl, setVideoUrl] = useState('');
  const fileInputRef = useRef(null);

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file && ['video/mp4', 'video/webm', 'video/ogg'].includes(file.type)) {
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
    if (file && ['video/mp4', 'video/webm', 'video/ogg'].includes(file.type)) {
      setSelectedFile(file);
      console.log('Tệp được kéo thả:', file.name);
    } else {
      alert('Vui lòng kéo thả một tệp video hợp lệ.');
      setSelectedFile(null);
    }
  };

  const handleUrlImport = () => {
    if (!videoUrl.trim()) {
      alert('Vui lòng nhập URL video hợp lệ.');
      return;
    }
    console.log('URL nhập vào:', videoUrl);
    // Bạn có thể gọi API hoặc chuyển URL này sang backend xử lý tại đây.
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
            onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
            onDragLeave={(e) => { e.preventDefault(); setIsDragOver(false); }}
            onClick={() => fileInputRef.current.click()}
          >
            <input
              type="file"
              ref={fileInputRef}
              accept="video/mp4,video/webm,video/ogg"
              onChange={handleFileChange}
              style={{ display: 'none' }}
            />
            <span className="upload-icon moving-cloud"><RiUploadCloudFill /></span>
            <p>
              Tải tệp lên<br />(Hỗ trợ video)
              {selectedFile && <span> (Đã chọn: {selectedFile.name})</span>}
            </p>
          </div>

          <p className="or-text">Hoặc</p>
          <div className="url-input">
            <input
              type="text"
              placeholder="Dán một URL (youtube...)"
              value={videoUrl}
              onChange={(e) => setVideoUrl(e.target.value)}
            />
            <button className="import-btn" onClick={handleUrlImport}>Nhập từ URL</button>
          </div>

          {(selectedFile || videoUrl.trim()) && (
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
