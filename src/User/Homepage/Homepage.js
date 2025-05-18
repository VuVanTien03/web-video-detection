// Homepage.js
import React, { useState, useEffect } from 'react';
import './Homepage.scss';

const Homepage = ({ content, setContent }) => {
  const [currentVideoUrl, setCurrentVideoUrl] = useState("sample-video.mp4");
  const [videoTitle, setVideoTitle] = useState("Video có hành vi côn đồ KHÔNG?");
  const [videoDescription, setVideoDescription] = useState("- OST Phim \"Bộ Tư Bốn...\"");
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [videoId, setVideoId] = useState(null);
  const [trackedVideoUrl, setTrackedVideoUrl] = useState(null);
  const [detections, setDetections] = useState([]);

  const extractVideoData = (data) => {
    // Checks both nested and direct formats
    const video = data.video || data;
    return {
      video_url: video.video_url || video.url || video.file_path || "",
      title: video.title || "Không có tiêu đề",
      description: video.description || "",
      id: video.id || ""
    };
  };

  // Process video through model with error handling
  const processVideoWithModel = async (videoId) => {
    if (!videoId) return;
    
    try {
      setIsProcessing(true);
      const token = localStorage.getItem('token');
      if (!token) throw new Error("Không tìm thấy token, vui lòng đăng nhập lại");

      // Đợi video được xử lý (poll /processed)
      const waitForProcessing = async (videoId) => {
        const token = localStorage.getItem('token');
        for (let i = 0; i < 30; i++) {
          const res = await fetch(`http://localhost:8000/api/v1/videos/${videoId}/processed`, {
            headers: { Authorization: `Bearer ${token}` },
          });
          if (res.ok) return true;
          if (res.status !== 202) throw new Error("Xử lý video thất bại");
          await new Promise((r) => setTimeout(r, 2000));
        }
        throw new Error("Quá thời gian chờ xử lý video");
      };

      await waitForProcessing(videoId);
      
      // Gọi lại API để lấy video_url sau khi xử lý xong
      const res = await fetch(`http://localhost:8000/api/v1/videos/${videoId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      if (!res.ok) {
        throw new Error(`Lấy thông tin video thất bại: ${res.status}`);
      }
      
      const data = await res.json();
      console.log("Video data after processing:", data);
      
      // Xử lý dữ liệu một cách linh hoạt, đảm bảo trích xuất đúng thông tin video
      const { video_url, title, description } = extractVideoData(data);

      if (video_url) {
        setCurrentVideoUrl(video_url);
        setVideoTitle(title);
        setVideoDescription(description);
      }

      try {
        // Call the track_video API
        const trackRes = await fetch(`http://localhost:8000/api/v1/videos/track_video/${videoId}`, {
          headers: { Authorization: `Bearer ${token}` },
          method: 'GET',
        });
        
        if (!trackRes.ok) {
          console.error(`Lỗi khi gọi track_video: ${trackRes.status}`);
          
          // Nếu lỗi 500, vẫn hiển thị video gốc và thông báo lỗi
          if (trackRes.status === 500) {
            setError("Không thể hiển thị video với phân tích. Hiển thị video gốc.");
            // Không thiết lập trackedVideoUrl để giữ video gốc
            return;
          }
          
          const errorText = await trackRes.text();
          throw new Error(`Lỗi khi hiển thị video với phân tích: ${trackRes.status} - ${errorText}`);
        }
        
        // Nếu thành công, thiết lập URL theo dõi
        setTrackedVideoUrl(`http://localhost:8000/api/v1/videos/track_video/${videoId}`);
        
        // Có thể thử fetch dữ liệu detection nếu cần
        fetchDetectionData(videoId);
        
      } catch (trackError) {
        console.error('Lỗi khi hiển thị video với phân tích:', trackError);
        setError(`Lỗi khi hiển thị video với phân tích: ${trackError.message}. Hiển thị video gốc.`);
        // Không thiết lập trackedVideoUrl để giữ video gốc
      }
      
    } catch (error) {
      console.error('Xử lý video thất bại:', error);
      setError("Xử lý video thất bại: " + error.message);
    } finally {
      setIsProcessing(false);
    }
  };

  // Fetch detection timeline data if needed
  const fetchDetectionData = async (videoId) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) throw new Error("Không tìm thấy token, vui lòng đăng nhập lại");

      const res = await fetch(`http://localhost:8000/api/v1/videos/time_detection/${videoId}`, {
        method: 'GET',
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`Lỗi HTTP! Trạng thái: ${res.status}, Nội dung: ${errorText}`);
      }

      const data = await res.json();
      setDetections(data.detections || []);
    } catch (error) {
      console.error('Lấy dữ liệu phát hiện thất bại:', error);
    }
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
        setTrackedVideoUrl(null); // Reset tracked video
        
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
        const { video_url, title, description, id } = extractVideoData(data);
        
        if (!video_url) throw new Error("Không tìm thấy đường dẫn video trong dữ liệu trả về");

        // Store video details
        setVideoTitle(title);
        setVideoDescription(description);
        setVideoId(data.video?.id || "");
        setContent(null);
        
        // Now process the video through the model
        await processVideoWithModel(data.video?.id || "");
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
      setTrackedVideoUrl(null); // Reset tracked video
      
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
      console.log("Dữ liệu video trả về:", data); // Ghi log để debug
      
      // Trích xuất ID video từ dữ liệu trực tiếp (không cần .video)
      // Đối với API /url, dữ liệu được trả về trực tiếp, không trong trường "video"
      const videoId = data.id || "";
      const title = data.title || "Video từ URL";
      const description = data.description || "Video tải từ đường dẫn";
      const videoUrl = data.video_url || data.url || data.file_path || "";
      
      console.log("Extracted videoId:", videoId);
      console.log("Extracted videoUrl:", videoUrl);
      
      if (!videoId) {
        throw new Error("Không tìm thấy ID video trong dữ liệu trả về");
      }
      
      // Lưu thông tin video
      setVideoId(videoId);
      setVideoTitle(title);
      setVideoDescription(description);
      if (videoUrl) {
        setCurrentVideoUrl(videoUrl);
      }
      setContent(null);
      
      // Xử lý video qua model
      await processVideoWithModel(videoId);
      
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
      setTrackedVideoUrl(null); // Reset tracked video
      
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
                  setVideoId(videoRaw.id);
                  setTrackedVideoUrl(null); // Reset tracked video
                  setContent(null);
                  
                  // Ask if user wants to process with model
                  const shouldProcess = window.confirm("Bạn có muốn xử lý video qua mô hình phát hiện hành vi bạo lực không?");
                  if (shouldProcess) {
                    processVideoWithModel(videoRaw.id);
                  }

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

  const handleAnalyzeVideo = async () => {
    if (!videoId) {
      setError("Vui lòng tải lên hoặc chọn một video trước khi phân tích");
      return;
    }
    
    try {
      await processVideoWithModel(videoId);
    } catch (error) {
      console.error('Phân tích video thất bại:', error);
      setError("Phân tích video thất bại: " + error.message);
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
        {videoId && !trackedVideoUrl && (
          <button className="main-content__button analyze-video" onClick={handleAnalyzeVideo}>
            Phân tích hành vi
          </button>
        )}
      </div>
      <div className="main-content__search">
        <input type="text" placeholder="Search" />
      </div>
      {error && <div className="error-message">{error}</div>}
      <div className="main-content__display">
        {isUploading || isProcessing ? (
          <div className="loading">
            <div className="spinner"></div>
            <p>{isProcessing ? "Đang phân tích video..." : "Đang tải video..."}</p>
          </div>
        ) : (
          content || (
            <div>
              <div className="video-container">
                {trackedVideoUrl ? (
                  // Display the processed video stream with detections
                  <iframe 
                    src={trackedVideoUrl} 
                    width="100%" 
                    height="500" 
                    frameBorder="0"
                    title="Processed Video Stream"
                  ></iframe>
                ) : (
                  // Display regular video
                  <video controls key={currentVideoUrl}>
                    <source src={currentVideoUrl} type="video/mp4" />
                    Trình duyệt của bạn không hỗ trợ video.
                  </video>
                )}
              </div>
              <h3>{videoTitle}</h3>
              <p>{videoDescription}</p>
              {trackedVideoUrl && (
                <div className="detection-info">
                  <p><strong>Đang hiển thị video với phân tích hành vi bạo lực</strong></p>
                  {detections.length > 0 && (
                    <div className="violence-timeline">
                      <h4>Thời điểm phát hiện bạo lực:</h4>
                      <ul>
                        {detections.map((detection, index) => (
                          <li key={index}>
                            Thời điểm: {detection.time_str || detection.timestamp} - 
                            Độ tin cậy: {(detection.confidence * 100).toFixed(2)}%
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        )}
      </div>
    </div>
  );
};

export default Homepage;