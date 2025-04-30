// Homepage.js
import React, { useState } from 'react';
import './Homepage.scss';

const Homepage = ({ content, setContent }) => {
  const [currentVideoUrl, setCurrentVideoUrl] = useState("sample-video.mp4");
  const [videoTitle, setVideoTitle] = useState("Video có hành vi côn đồ KHÔNG?");
  const [videoDescription, setVideoDescription] = useState("- OST Phim \"Bộ Tư Bốn...\"");
  const [isUploading, setIsUploading] = useState(false);

  const handleUploadFile = async () => {
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = 'video/*';
    fileInput.onchange = async (event) => {
      const file = event.target.files[0];
      if (!file) return;

      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', 'Tiêu đề video');
      formData.append('description', 'Mô tả video');
      formData.append('tags', JSON.stringify(['tag1', 'tag2']));
      formData.append('status', 'public');

      try {
        setIsUploading(true);
        const res = await fetch('http://localhost:8000/api/v1/videos/upload', {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
          body: formData,
        });

        const data = await res.json();
        setCurrentVideoUrl(data.video.video_url);
        setVideoTitle(data.video.title);
        setVideoDescription(data.video.description);
      } catch (error) {
        console.error('Upload thất bại:', error);
      } finally {
        setIsUploading(false);
      }
    };
    fileInput.click();
  };

  const handleInputURL = async () => {
    const url = prompt('Nhập URL video:');
    if (!url) return;

    try {
      setIsUploading(true);
      const res = await fetch('http://localhost:8000/api/v1/videos/url', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          url,
          title: 'Video từ URL',
          description: 'Video tải từ đường dẫn',
          tags: ['url', 'video'],
          status: 'public',
        }),
      });

      const data = await res.json();
      setCurrentVideoUrl(data.video.video_url);
      setVideoTitle(data.video.title);
      setVideoDescription(data.video.description);
    } catch (error) {
      console.error('Tải từ URL thất bại:', error);
    } finally {
      setIsUploading(false);
    }
  };

  const handleUploadVideo = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/v1/videos/', {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });

      const data = await res.json();
      if (data.length > 0) {
        setContent(
          <div className="video-list">
            {data.map((video) => (
              <div 
                key={video.id} 
                className="video-item" 
                onClick={() => {
                  setCurrentVideoUrl(video.video_url);
                  setVideoTitle(video.title);
                  setVideoDescription(video.description);
                  setContent(null);
                }}
              >
                <h3>{video.title}</h3>
                <video width="200" src={video.video_url}></video>
                <p>{video.description}</p>
              </div>
            ))}
          </div>
        );
      } else {
        setContent(<p>Không có video nào.</p>);
      }
    } catch (error) {
      console.error('Lấy danh sách video thất bại:', error);
    }
  };

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
        {isUploading ? (
          <div className="loading">
            <div className="spinner"></div>
            <p>Đang tải video...</p>
          </div>
        ) : (
          content || (
            <div>
              <video controls width="400">
                <source src={currentVideoUrl} type="video/mp4" />
                Trình duyệt của bạn không hỗ trợ video.
              </video>
              <h3>{videoTitle}</h3>
              <p>{videoDescription}</p>
            </div>
          )
        )}
      </div>
    </div>
  );
};

export default Homepage;
