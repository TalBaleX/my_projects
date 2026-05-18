import { createBrowserRouter, Navigate } from 'react-router-dom';
import { Hotels } from '@pages/Hotels';
import { HotelDetails } from '@pages/HotelDetails';
import { BookingPage } from '@pages/BookingPage';
import { LoginPage } from '@pages/LoginPage';
import { ProfilePage } from '@pages/ProfilePage/ProfilePage';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Navigate to="/hotels" replace />,
  },
  {
    path: '/hotels',
    element: <Hotels />,
  },
  {
    path: '/hotel-details/:id',
    element: <HotelDetails />,
  },
  {
    path: '/booking/:hotelId',
    element: <BookingPage />,
  },
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/profile',
    element: <ProfilePage />,
  },
]);
