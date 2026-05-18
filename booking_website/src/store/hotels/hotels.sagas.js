import { call, put, takeLatest } from 'redux-saga/effects';
import {
  FETCH_HOTELS_ACTION,
  FETCH_HOTELS_SUCCESS,
  FETCH_HOTELS_FAILED,
} from './hotels.actions.js';
import { getHotels } from '@api';

export function* fetchHotelsSaga({ payload }) {
  try {
    const data = yield call(getHotels, payload);

    if (!data) {
      throw new Error('No data received from server');
    }

    yield put(FETCH_HOTELS_SUCCESS(data));
  } catch (error) {
    console.error('Error fetching hotels:', error);
    yield put(FETCH_HOTELS_FAILED(error.message));
  }
}

export function* watchFetchHotelsSagas() {
  yield takeLatest(FETCH_HOTELS_ACTION.type, fetchHotelsSaga);
}
