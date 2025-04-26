import { useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { LOGOUT_USER_ACTION } from '@store/users/users.actions';

const Logout = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();

  useEffect(() => {
    dispatch({ type: LOGOUT_USER_ACTION });
    navigate('/login');
  }, [dispatch, navigate]);

  return null;
};

export default Logout;
