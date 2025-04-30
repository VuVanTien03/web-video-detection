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
      // Validate đơn giản
      if (!email.includes('@')) {
        throw new Error('Email không hợp lệ');
      }
      if (password.length < 6) {
        throw new Error('Mật khẩu phải có ít nhất 6 ký tự');
      }

      // Tạo form data cho FastAPI OAuth2
      const formData = new FormData();
      formData.append('username', email);
      formData.append('password', password);

      const response = await fetch('http://localhost:8000/api/v1/auth/token', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Đăng nhập thất bại');
      }

      // Lưu token
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('token_type', data.token_type);

      // Lấy thông tin user
      const userData = await fetchUserInfo(data.access_token);

      if (!userData) {
        throw new Error('Không thể lấy thông tin người dùng');
      }

      window.dispatchEvent(new Event('userLoggedIn'));

      // Điều hướng theo role
      if (userData.role === 'user') {
        navigate('/dashboard');
      } else {
        navigate('/admin/home');
      }
    } catch (err) {
      console.error('Lỗi đăng nhập:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchUserInfo = async (token) => {
    try {
      console.log('Đang lấy thông tin người dùng với token:', token);
      const response = await fetch('http://localhost:8000/api/v1/users/me', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        console.error('Response lấy user:', await response.text());
        return null;
      }

      const userData = await response.json();
      console.log('Thông tin người dùng:', userData);

      // Lưu user profile vào localStorage
      localStorage.setItem('user_profile', JSON.stringify(userData));
      return userData;
    } catch (error) {
      console.error('Lỗi lấy thông tin người dùng:', error);
      return null;
    }
  };

  const handleGoogleLogin = () => {
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
