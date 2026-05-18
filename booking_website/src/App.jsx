import { RouterProvider, createBrowserRouter } from 'react-router-dom';
import {
  CircularProgress,
  createTheme,
  responsiveFontSizes,
  ThemeProvider,
} from '@mui/material';
import { useSelector, useDispatch } from 'react-redux';
import { selectTheme } from '@store';
import { useMemo, useEffect } from 'react';
import { getDesignTokens, SessionService } from '@services';
import CssBaseline from '@mui/material/CssBaseline';
import {
  HomePage,
  About,
  Hotels,
  HotelDetails,
  ErrorPage,
  ProfilePage,
} from '@pages';
import Register from '@components/Register/Register';
import Login from '@components/Login/Login';
import Logout from '@components/Logout/Logout';
import { LOGIN_USER_SUCCESS } from '@store/users/users.actions';
import { BookingPage } from '@pages/BookingPage/BookingPage';

export function App() {
  const dispatch = useDispatch();
  const mode = useSelector(selectTheme);
  const theme = useMemo(() => createTheme(getDesignTokens(mode)), [mode]);

  useEffect(() => {
    const user = SessionService.getUser();
    if (user) {
      dispatch({ type: LOGIN_USER_SUCCESS, payload: user });
    }
  }, [dispatch]);

  const router = createBrowserRouter([
    {
      path: '/',
      errorElement: <ErrorPage />,
      children: [
        { index: true, element: <HomePage /> },
        { path: 'about', element: <About /> },
        { path: 'hotels', element: <Hotels /> },
        { path: 'hotel-details/:id', element: <HotelDetails /> },
        { path: 'booking/:hotelId', element: <BookingPage /> },
        { path: 'register', element: <Register /> },
        { path: 'login', element: <Login /> },
        { path: 'logout', element: <Logout /> },
        { path: 'profile', element: <ProfilePage /> },
      ],
    },
  ]);

  return (
    <ThemeProvider theme={responsiveFontSizes(theme)}>
      <CssBaseline />
      <RouterProvider router={router} fallbackElement={<CircularProgress />} />
    </ThemeProvider>
  );
}
