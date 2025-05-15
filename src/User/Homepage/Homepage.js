// Homepage.js
import React, { useState, useEffect } from 'react';
import './Homepage.scss';

const Homepage = ({ content, setContent }) => {
  const [currentVideoUrl, setCurrentVideoUrl] = useState("sample-video.mp4");
  const [videoTitle, setVideoTitle] = useState("Video có hành vi côn đồ KHÔNG?");
  const [videoDescription, setVideoDescription] = useState("- OST Phim \"Bộ Tư Bốn...\"");
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState("");

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
        setError("");
        console.log("Đang tải file lên:", file.name, "Kích thước:", file.size);
        
        // Kiểm tra token trước khi gửi request
        const token = localStorage.getItem('token');
        if (!token) {
          throw new Error("Không tìm thấy token, vui lòng đăng nhập lại");
        }
        console.log("Token tìm thấy:", token.substring(0, 10) + "...");
        
        const res = await fetch('http://localhost:8000/api/v1/videos/upload', {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
          },
          body: formData,
        });

        console.log("Phản hồi từ server:", res.status);
        
        if (!res.ok) {
          const errorText = await res.text();
          console.error("Nội dung lỗi:", errorText);
          throw new Error(`Lỗi HTTP! Trạng thái: ${res.status}, Nội dung: ${errorText}`);
        }

        const data = await res.json();
        console.log("Dữ liệu nhận được:", data);
        
        // Ưu tiên sử dụng file_path, nếu không có thì dùng video_url hoặc url
        const videoSource = data.video.file_path || data.video.video_url || data.video.url;
        console.log("Đường dẫn video:", videoSource);
        
        if (!videoSource) {
          throw new Error("Không tìm thấy đường dẫn video trong dữ liệu trả về");
        }
        
        setCurrentVideoUrl(videoSource);
        setVideoTitle(data.video.title);
        setVideoDescription(data.video.description || "");
        setContent(null);
      } catch (error) {
        console.error('Upload thất bại:', error);
        setError("Tải lên thất bại: " + error.message);
      } finally {
        setIsUploading(false);
      }
    };
    fileInput.click();
  };

  const handleInputURL = async () => {
    const url = prompt('Nhập URL video (có thể là YouTube):');
    if (!url) return;
  
    try {
      setIsUploading(true);
      setError("");
      console.log("Đang tải video từ URL:", url);
  
      // Kiểm tra định dạng URL cơ bản
      if (!/^https?:\/\/.+\..+/.test(url)) {
        throw new Error("URL không hợp lệ");
      }
  
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error("Không tìm thấy token, vui lòng đăng nhập lại");
      }
  
      const requestData = {
        url,
        title: 'Video từ URL',
        description: 'Video tải từ đường dẫn',
        tags: ['url', 'video'],
        status: 'public',
      };
  
      const res = await fetch('http://localhost:8000/api/v1/videos/url', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(requestData),
      });
  
      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`Lỗi HTTP! Trạng thái: ${res.status}, Nội dung: ${errorText}`);
      }
  
      const data = await res.json();
  
      const videoSource = data.video.url || data.video.video_url || data.video.file_path;
      if (!videoSource) {
        throw new Error("Không tìm thấy đường dẫn video trong dữ liệu trả về");
      }
  
      setCurrentVideoUrl(videoSource);
      setVideoTitle(data.video.title || "Video từ URL");
      setVideoDescription(data.video.description || "");
      setContent(null);
    } catch (error) {
      console.error('Tải từ URL thất bại:', error);
      setError("Tải từ URL thất bại: " + error.message);
    } finally {
      setIsUploading(false);
    }
  };
  

  const handleUploadVideo = async () => {
          try {
      setIsUploading(true);
      setError("");
      console.log("Đang lấy danh sách video...");
      
      // Kiểm tra token trước khi gửi request
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error("Không tìm thấy token, vui lòng đăng nhập lại");
      }
      
      const res = await fetch('http://localhost:8000/api/v1/videos/', {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      console.log("Phản hồi từ server:", res.status);
      
      if (!res.ok) {
        const errorText = await res.text();
        console.error("Nội dung lỗi:", errorText);
        throw new Error(`Lỗi HTTP! Trạng thái: ${res.status}, Nội dung: ${errorText}`);
      }

      const data = await res.json();
      if (data.length > 0) {
        setContent(
          <div className="video-list">
            {data.map((video) => (
              <div 
                key={video.id} 
                className="video-item" 
                onClick={() => {
                  // Ưu tiên sử dụng file_path, nếu không có thì dùng url hoặc video_url
                  const videoSource = video.file_path || video.url || video.video_url;
                  setCurrentVideoUrl(videoSource);
                  setVideoTitle(video.title);
                  setVideoDescription(video.description || "");
                  setContent(null);
                }}
              >
                <h3>{video.title}</h3>
                <video width="200" src={video.file_path || video.url || video.video_url}></video>
                <p>{video.description || ""}</p>
              </div>
            ))}
          </div>
        );
      } else {
        setContent(<p>Không có video nào.</p>);
      }
    } catch (error) {
      console.error('Lấy danh sách video thất bại:', error);
      setError("Lấy danh sách video thất bại: " + error.message);
    } finally {
      setIsUploading(false);
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
      {error && (
        <div className="error-message">
          {error}
        </div>
      )}
      <div className="main-content__display">
        {isUploading ? (
          <div className="loading">
            <div className="spinner"></div>
            <p>Đang tải video...</p>
          </div>
        ) : (
          content || (
            <div>
              <video controls width="400" key={currentVideoUrl}>
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