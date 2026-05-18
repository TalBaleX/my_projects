import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Typography,
  TextField,
  Button,
  Box,
  Alert,
} from '@mui/material';
import { LOGIN_USER_ACTION } from '@store/users/users.actions';

const Login = () => {
  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const error = useSelector((state) => state.users.error);
  const currentUser = useSelector((state) => state.users.currentUser);
  const loading = useSelector((state) => state.users.loading);

  useEffect(() => {
    if (currentUser) {
      navigate('/');
    }
  }, [currentUser, navigate]);

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!name || !password) {
      return;
    }

    dispatch({
      type: LOGIN_USER_ACTION,
      payload: { name, password },
    });
  };

  return (
    <Container maxWidth="sm">
      <Typography variant="h4" align="center" gutterBottom>
        Login
      </Typography>
      <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2 }}>
        <TextField
          label="Username"
          variant="outlined"
          fullWidth
          margin="normal"
          required
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <TextField
          label="Password"
          variant="outlined"
          fullWidth
          margin="normal"
          required
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
          <Button
            variant="contained"
            color="primary"
            type="submit"
            disabled={loading}
          >
            {loading ? 'Logging in...' : 'Login'}
          </Button>
          <Button variant="outlined" onClick={() => navigate('/')}>
            Back to Home
          </Button>
        </Box>
        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}
        <Box sx={{ mt: 2, textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            Don't have an account?{' '}
            <Button color="primary" onClick={() => navigate('/register')}>
              Register here
            </Button>
          </Typography>
        </Box>
      </Box>
    </Container>
  );
};

export default Login;
