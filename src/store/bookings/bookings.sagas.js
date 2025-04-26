import { call, put, takeLatest, all, select } from 'redux-saga/effects';
import { createBooking, getUserBookings, deleteBooking } from '@api/bookings';
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

function* createBookingSaga(action) {
  try {
    const booking = yield call(createBooking, action.payload);
    yield put({ type: CREATE_BOOKING_SUCCESS, payload: booking });
    yield put({
      type: FETCH_USER_BOOKINGS_ACTION,
      payload: action.payload.userId,
    });
  } catch (error) {
    yield put({ type: CREATE_BOOKING_FAILURE, payload: error.message });
  }
}

function* fetchUserBookingsSaga(action) {
  try {
    const bookings = yield call(getUserBookings, action.payload);
    yield put({ type: FETCH_USER_BOOKINGS_SUCCESS, payload: bookings });
  } catch (error) {
    yield put({ type: FETCH_USER_BOOKINGS_FAILURE, payload: error.message });
  }
}

function* deleteBookingSaga(action) {
  try {
    yield call(deleteBooking, action.payload);
    yield put({ type: DELETE_BOOKING_SUCCESS, payload: action.payload });

    const userId = yield select((state) => state.users.currentUser?.id);
    if (userId) {
      yield put({ type: FETCH_USER_BOOKINGS_ACTION, payload: userId });
    }
  } catch (error) {
    yield put({ type: DELETE_BOOKING_FAILURE, payload: error.message });
  }
}

export function* watchBookingSagas() {
  yield all([
    takeLatest(CREATE_BOOKING_ACTION, createBookingSaga),
    takeLatest(FETCH_USER_BOOKINGS_ACTION, fetchUserBookingsSaga),
    takeLatest(DELETE_BOOKING_ACTION, deleteBookingSaga),
  ]);
}
