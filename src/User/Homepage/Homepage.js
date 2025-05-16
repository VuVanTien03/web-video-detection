// Homepage.js
import React, { useState } from 'react';
import './Homepage.scss';

const Homepage = ({ content, setContent }) => {
  const [currentVideoUrl, setCurrentVideoUrl] = useState("sample-video.mp4");
  const [videoTitle, setVideoTitle] = useState("Video có hành vi côn đồ KHÔNG?");
  const [videoDescription, setVideoDescription] = useState("- OST Phim \"Bộ Tư Bốn...\"");
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState("");

  const extractVideoData = (data) => {
    const video = data.video || data;
    return {
      video_url: video.video_url || video.url || video.file_path || "",
      title: video.title || "Không có tiêu đề",
      description: video.description || "",
    };
  };

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
        const token = localStorage.getItem('token');
        if (!token) throw new Error("Không tìm thấy token, vui lòng đăng nhập lại");

        const res = await fetch('http://localhost:8000/api/v1/videos/upload', {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
          body: formData,
        });

        if (!res.ok) {
          const errorText = await res.text();
          throw new Error(`Lỗi HTTP! Trạng thái: ${res.status}, Nội dung: ${errorText}`);
        }

        const data = await res.json();
        const { video_url, title, description } = extractVideoData(data);

        if (!video_url) throw new Error("Không tìm thấy đường dẫn video trong dữ liệu trả về");

        setCurrentVideoUrl(video_url);
        setVideoTitle(title);
        setVideoDescription(description);
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
      if (!/^https?:\/\/.+\..+/.test(url)) throw new Error("URL không hợp lệ");

      const token = localStorage.getItem('token');
      if (!token) throw new Error("Không tìm thấy token, vui lòng đăng nhập lại");

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
      const { video_url, title, description } = extractVideoData(data);

      if (!video_url) throw new Error("Không tìm thấy đường dẫn video trong dữ liệu trả về");

      setCurrentVideoUrl(video_url);
      setVideoTitle(title);
      setVideoDescription(description);
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
      const token = localStorage.getItem('token');
      if (!token) throw new Error("Không tìm thấy token, vui lòng đăng nhập lại");

      const res = await fetch('http://localhost:8000/api/v1/videos/', {
        method: 'GET',
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`Lỗi HTTP! Trạng thái: ${res.status}, Nội dung: ${errorText}`);
      }

      const data = await res.json();
      if (data.length > 0) {
        setContent(
          <div className="video-list">
            {data.map((videoRaw) => {
              const { video_url, title, description } = extractVideoData(videoRaw);
              return (
                <div key={videoRaw.id} className="video-item" onClick={() => {
                  setCurrentVideoUrl(video_url);
                  setVideoTitle(title);
                  setVideoDescription(description);
                  setContent(null);
                }}>
                  <h3>{title}</h3>
                  <div className="video-thumbnail">
                    <video controls src={video_url}></video>
                  </div>
                  <p>{description}</p>
                </div>
              );
            })}
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
      {error && <div className="error-message">{error}</div>}
      <div className="main-content__display">
        {isUploading ? (
          <div className="loading">
            <div className="spinner"></div>
            <p>Đang tải video...</p>
          </div>
        ) : (
          content || (
            <div>
              <div className="video-container">
                <video controls key={currentVideoUrl}>
                  <source src={currentVideoUrl} type="video/mp4" />
                  Trình duyệt của bạn không hỗ trợ video.
                </video>
              </div>
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
