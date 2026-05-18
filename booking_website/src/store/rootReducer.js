import { combineReducers } from '@reduxjs/toolkit';
import { hotelsReducer } from './hotels';
import { appReducer } from './app';
import { usersReducer } from './users';
import { bookingsReducer } from './bookings';

export const rootReducer = combineReducers({
  hotels: hotelsReducer,
  app: appReducer,
  users: usersReducer,
  bookings: bookingsReducer,
});
