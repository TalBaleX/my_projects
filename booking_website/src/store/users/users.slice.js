import { createSlice } from '@reduxjs/toolkit';
import { SessionService } from '@services';

const initialState = {
  users: [],
  currentUser: SessionService.getUser(),
  loading: false,
  error: null,
};

export const usersSlice = createSlice({
  name: 'users',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase('users/loginUser', (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase('users/loginUser/success', (state, action) => {
        state.loading = false;
        state.currentUser = action.payload;
        state.error = null;
      })
      .addCase('users/loginUser/failed', (state, action) => {
        state.loading = false;
        state.error = action.payload;
        state.currentUser = null;
      })
      .addCase('users/logoutUser', (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase('users/logoutUser/success', (state) => {
        state.loading = false;
        state.currentUser = null;
        state.error = null;
      })
      .addCase('users/logoutUser/failed', (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  },
});

export default usersSlice.reducer;
