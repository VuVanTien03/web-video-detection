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

      const response = await fetch('http://localhost:8000/auth/login', {
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
      
      // Redirect sau khi đăng nhập thành công
      navigate('/dashboard');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
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