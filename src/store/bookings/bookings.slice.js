import { createSlice } from '@reduxjs/toolkit';
import {
  CREATE_BOOKING_ACTION,
  CREATE_BOOKING_SUCCESS,
  CREATE_BOOKING_FAILURE,
  FETCH_USER_BOOKINGS_ACTION,
  FETCH_USER_BOOKINGS_SUCCESS,
  FETCH_USER_BOOKINGS_FAILURE,
  DELETE_BOOKING_ACTION,
  DELETE_BOOKING_SUCCESS,
  DELETE_BOOKING_FAILURE,
} from './bookings.actions';

const initialState = {
  userBookings: [],
  loading: false,
  error: null,
};

const bookingsSlice = createSlice({
  name: 'bookings',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(CREATE_BOOKING_ACTION, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(CREATE_BOOKING_SUCCESS, (state, action) => {
        state.loading = false;
        state.userBookings.push(action.payload);
      })
      .addCase(CREATE_BOOKING_FAILURE, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      .addCase(FETCH_USER_BOOKINGS_ACTION, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(FETCH_USER_BOOKINGS_SUCCESS, (state, action) => {
        state.loading = false;
        state.userBookings = action.payload;
      })
      .addCase(FETCH_USER_BOOKINGS_FAILURE, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      .addCase(DELETE_BOOKING_ACTION, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(DELETE_BOOKING_SUCCESS, (state, action) => {
        state.loading = false;
        state.userBookings = state.userBookings.filter(
          (booking) => booking.id !== action.payload
        );
        state.error = null;
      })
      .addCase(DELETE_BOOKING_FAILURE, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  },
});

export const bookingsReducer = bookingsSlice.reducer;
