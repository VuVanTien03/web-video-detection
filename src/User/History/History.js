import React, { useState, useEffect } from 'react';
import './History.scss';

const History = ({ content, setContent }) => {
  const [videos, setVideos] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    // Gọi API lấy danh sách video đã xem
    const fetchVideos = async () => {
      try {
        setIsLoading(true);
        setError("");
        
        const token = localStorage.getItem('token');
        if (!token) {
          throw new Error("Không tìm thấy token, vui lòng đăng nhập lại");
        }
        
        const res = await fetch('http://localhost:8000/api/v1/videos/', {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        
        if (!res.ok) {
          throw new Error(`Lỗi HTTP! Trạng thái: ${res.status}`);
        }
        
        const data = await res.json();
        setVideos(data);
      } catch (error) {
        console.error('Lỗi khi lấy danh sách video lịch sử:', error);
        setError("Không thể tải danh sách video: " + error.message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchVideos();
  }, []);

  // Xử lý khi người dùng chọn một video để xem
  const handleSelectVideo = (video) => {
    // Chuyển hướng đến trang chính với video đã chọn
    console.log("Đã chọn video:", video.title);
    
    // Ở đây bạn có thể thực hiện chuyển hướng hoặc gọi một hàm callback
    // để thông báo cho component cha biết video đã được chọn
    if (typeof setContent === 'function') {
      // Giả sử setContent có thể được sử dụng để thay đổi nội dung trên trang chính
      setContent(null);
      
      // Lưu video đã chọn vào localStorage hoặc state global
      localStorage.setItem('selectedVideo', JSON.stringify(video));
      
      // Chuyển hướng đến trang chính (ví dụ)
      window.location.href = '/';
    }
  };

  return (
    <div className="history-page">
      <div className="history-header">
        <h1>Lịch sử xem video</h1>
      </div>
      
      {error && <div className="error-message">{error}</div>}
      
      {isLoading ? (
        <div className="loading">
          <div className="spinner"></div>
          <p>Đang tải danh sách video...</p>
        </div>
      ) : videos.length > 0 ? (
        <div className="history-grid">
          {videos.map((video) => (
            <div 
              key={video.id} 
              className="video-card"
              onClick={() => handleSelectVideo(video)}
            >
              <div className="video-thumbnail">
                <video src={video.video_url || video.url || video.file_path}></video>
                <div className="play-overlay">
                  <div className="play-icon"></div>
                </div>
              </div>
              <div className="video-info">
                <h3 className="video-title">{video.title}</h3>
                <p className="video-description">{video.description}</p>
                <div className="video-meta">
                  <span className="video-date">
                    {video.created_at ? new Date(video.created_at).toLocaleDateString() : 'Không có ngày'}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="empty-history">
          <div className="empty-icon">📺</div>
          <h2>Chưa có video nào trong lịch sử</h2>
          <p>Các video bạn đã xem sẽ xuất hiện tại đây</p>
        </div>
      )}
    </div>
  );
};

export default History;