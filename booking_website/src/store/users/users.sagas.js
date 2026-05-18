import { call, put, takeEvery } from 'redux-saga/effects';
import { registerUser, loginUser } from '@api/users';
import {
  REGISTER_USER_ACTION,
  REGISTER_USER_SUCCESS,
  LOGIN_USER_ACTION,
  LOGIN_USER_SUCCESS,
  LOGIN_USER_FAILED,
  LOGOUT_USER_ACTION,
} from './users.actions';
import { SessionService } from '@services';

function* registerUserSaga(action) {
  try {
    const user = yield call(registerUser, action.payload);

    if (user) {
      yield put({ type: REGISTER_USER_SUCCESS, payload: user });
      window.location.href = '/login';
    }
  } catch (error) {}
}

function* loginUserSaga(action) {
  try {
    const response = yield call(loginUser, action.payload);

    if (response) {
      yield put({ type: LOGIN_USER_SUCCESS, payload: response });
      SessionService.setUser(response);
      yield call([window.history, 'pushState'], {}, '', '/');
      yield call([window.location, 'reload']);
    } else {
      yield put({ type: LOGIN_USER_FAILED, payload: 'Login failed' });
    }
  } catch (error) {
    yield put({ type: LOGIN_USER_FAILED, payload: error.message });
  }
}

function* logoutUserSaga() {
  try {
    SessionService.clearUser();
    yield put({ type: 'users/logoutUser/success' });
  } catch (error) {
    yield put({ type: 'users/logoutUser/failed', payload: error.message });
  }
}

export function* watchUserSagas() {
  yield takeEvery(REGISTER_USER_ACTION, registerUserSaga);
  yield takeEvery(LOGIN_USER_ACTION, loginUserSaga);
  yield takeEvery(LOGOUT_USER_ACTION, logoutUserSaga);
}
