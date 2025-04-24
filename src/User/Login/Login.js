import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Login.scss';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // FormData sử dụng cho OAuth2PasswordRequestForm trong FastAPI
      const formData = new FormData();
      formData.append('username', email); // FastAPI sử dụng 'username' cho đăng nhập
      formData.append('password', password);

      const response = await fetch('http://localhost:8000/api/v1/auth/token', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Đăng nhập thất bại');
      }

      // Lưu token vào localStorage
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('token_type', data.token_type);
      
      // Lấy thông tin người dùng sau khi đăng nhập
      const userData = await fetchUserInfo(data.access_token);
      
      // Gửi một event thông báo rằng người dùng đã đăng nhập
      window.dispatchEvent(new Event('userLoggedIn'));
      
      // Redirect sau khi đăng nhập thành công - thay đổi thành Dashboard
      
      // if (userData.role == 'user') {
      //   navigate('/dashboard'); // Route dành cho admin
      // } else {
        navigate('/Dashboard'); // Route dành cho user
      // }
    } catch (err) {
      console.error('Lỗi đăng nhập:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Hàm lấy thông tin người dùng
  const fetchUserInfo = async (token) => {
    try {
      console.log('Đang lấy thông tin người dùng với token:', token);
      const response = await fetch('http://localhost:8000/api/v1/users/me', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Không thể lấy thông tin người dùng');
      }

      const userData = await response.json();
      console.log('Đã lấy được thông tin người dùng:', userData);
      
      // Lưu thông tin người dùng vào localStorage với key 'user_profile'
      localStorage.setItem('user_profile', JSON.stringify(userData));
      return userData;
    } catch (error) {
      console.error('Lỗi khi lấy thông tin người dùng:', error);
      return null;
    }
  };

  const handleGoogleLogin = () => {
    // Xử lý đăng nhập bằng Google (nếu có)
    alert('Chức năng đăng nhập bằng Google chưa được triển khai');
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h2>Welcome Back</h2>
        {error && <div className="error-message">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Email</label>
            <input 
              type="email" 
              placeholder="john.doe@email.com" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input 
              type="password" 
              placeholder="********" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button type="submit" disabled={loading}>
            {loading ? 'Đang đăng nhập...' : 'Log in'}
          </button>
          <button 
            type="button" 
            className="google-btn" 
            onClick={handleGoogleLogin}
            disabled={loading}
          >
            <img src="https://www.google.com/favicon.ico" alt="Google" /> Log in with Google
          </button>
          <p className="forgot-password">Forgot password?</p>
          <p className="signup-link">Don't have an account? <a href="/signup">Sign up</a></p>
        </form>
      </div>
    </div>
  );
};

export default Login;