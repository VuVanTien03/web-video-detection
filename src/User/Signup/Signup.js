import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Signup.scss';

const Signup = () => {
  const [username, setUsername] = useState('');
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
      const response = await fetch('http://localhost:8000/api/v1/auth/signup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username,
          email,
          password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Đăng ký thất bại');
      }

      // Đăng ký thành công, chuyển hướng đến trang đăng nhập
      navigate('/login');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignup = () => {
    // Xử lý đăng ký bằng Google (nếu có)
    alert('Chức năng đăng ký bằng Google chưa được triển khai');
  };

  return (
    <div className="signup-container">
      <div className="signup-card">
        <h2>Create Account</h2>
        {error && <div className="error-message">{error}</div>}
        <button 
          type="button" 
          className="google-btn" 
          onClick={handleGoogleSignup}
          disabled={loading}
        >
          <img src="https://www.google.com/favicon.ico" alt="Google" /> Sign up with Google
        </button>
        <div className="separator">or</div>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Username</label>
            <input 
              type="text" 
              placeholder="john" 
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
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
            {loading ? 'Đang tạo tài khoản...' : 'Create Account'}
          </button>
          <p className="login-link">Already have an account? <a href="/login">Log in</a></p>
        </form>
      </div>
    </div>
  );
};

export default Signup;