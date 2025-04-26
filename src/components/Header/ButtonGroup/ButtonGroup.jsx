import { NavLink } from '@ui';
import { ButtonGroup as ButtonGroupMUI } from '@mui/material';
import { useSelector } from 'react-redux';

export function ButtonGroup() {
  const currentUser = useSelector((state) => {
    return state.users?.currentUser;
  });

  return (
    <ButtonGroupMUI
      component="nav"
      sx={{
        '& a': {
          textDecoration: 'none',
          flex: '0 0 auto',
          padding: '6px 16px',
          border: 'none',
          borderRadius: '0',
          backgroundColor: 'primary.main',
          color: '#fff',
          '&:hover': {
            backgroundColor: 'primary.dark',
            color: '#fff',
          },
          '&:first-of-type': {
            borderTopLeftRadius: '4px',
            borderBottomLeftRadius: '4px',
          },
          '&:last-of-type': {
            borderTopRightRadius: '4px',
            borderBottomRightRadius: '4px',
          },
        },
        display: 'flex',
        gap: '8px',
      }}
    >
      <NavLink to="/hotels" variant="contained">
        Hotels
      </NavLink>
      <NavLink to="/about" variant="contained">
        About
      </NavLink>
      {currentUser ? (
        <>
          <NavLink to="/profile" variant="contained">
            {currentUser.name}
          </NavLink>
          <NavLink to="/logout" variant="contained">
            Logout
          </NavLink>
        </>
      ) : (
        <>
          <NavLink to="/register" variant="contained">
            Register
          </NavLink>
          <NavLink to="/login" variant="contained">
            Login
          </NavLink>
        </>
      )}
    </ButtonGroupMUI>
  );
}
