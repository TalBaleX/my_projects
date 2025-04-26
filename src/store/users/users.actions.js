import { createAction } from '@reduxjs/toolkit';

export const REGISTER_USER_ACTION = 'users/registerUser';
export const REGISTER_USER_SUCCESS = 'users/registerUser/success';
export const REGISTER_USER_FAILED = 'users/registerUser/failed';

export const LOGIN_USER_ACTION = 'users/loginUser';
export const LOGIN_USER_SUCCESS = 'users/loginUser/success';
export const LOGIN_USER_FAILED = 'users/loginUser/failed';
export const LOGIN_USER_TIMEOUT = 'users/loginUser/timeout';

export const LOGOUT_USER_ACTION = 'users/logoutUser';
export const LOGOUT_USER_SUCCESS = 'users/logoutUser/success';
export const LOGOUT_USER_FAILED = 'users/logoutUser/failed';
