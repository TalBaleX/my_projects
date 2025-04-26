import { createBrowserRouter } from 'react-router-dom';
import { ErrorPage, HomePage, Hotels, About } from '@pages';
import { HotelDetails } from '@pages/HotelDetails';
import { BookingPage } from '@pages/BookingPage';
import Register from '@components/Register/Register';
import Login from '@components/Login/Login';
import ProfilePage from '@pages/ProfilePage/ProfilePage';

const routerConfig = [
  {
    path: '/',
    errorElement: <ErrorPage />,
    id: 'root',
    children: [
      { index: true, element: <HomePage /> },
      { path: 'about', element: <About /> },
      {
        path: 'hotels',
        children: [
          { index: true, element: <Hotels /> },
          { path: ':id', element: <HotelDetails /> },
        ],
      },
      { path: 'booking/:hotelId', element: <BookingPage /> },
      { path: 'register', element: <Register /> },
      { path: 'login', element: <Login /> },
      { path: 'profile', element: <ProfilePage /> },
    ],
  },
];

export const router = createBrowserRouter(routerConfig);
