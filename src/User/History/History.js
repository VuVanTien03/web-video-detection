import React, { useState, useEffect } from 'react';
import './History.scss';

const History = ({ content, setContent }) => {
  const [videos, setVideos] = useState([]);
  const [chatMessages, setChatMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');

  useEffect(() => {
    // Gọi API lấy danh sách video
    const fetchVideos = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/v1/videos/', {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
        });
        const data = await res.json();
        setVideos(data);
      } catch (error) {
        console.error('Lỗi khi lấy video lịch sử:', error);
      }
    };

    fetchVideos();
  }, []);

  const handleSendMessage = () => {
    if (newMessage.trim()) {
      setChatMessages((prev) => [...prev, newMessage]);
      setNewMessage('');
    }
  };

  return (
    <div className="history-content">
      {content || (
        <>
          {videos.length > 0 ? (
            videos.map((video) => (
              <div key={video.id} className="main-content__display">
                <video controls width="400" src={video.video_url}></video>
                <h3>{video.title}</h3>
                <p>{video.description}</p>
              </div>
            ))
          ) : (
            <p>Không có video nào trong lịch sử.</p>
          )}

          <div className="chat-area">
            {chatMessages.map((msg, index) => (
              <div key={index} className="chat-area__message">
                {msg}
              </div>
            ))}
            <div className="chat-area__input">
              <input
                type="text"
                placeholder="Nhập tin nhắn..."
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
              />
              <button onClick={handleSendMessage}>Gửi</button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default History;