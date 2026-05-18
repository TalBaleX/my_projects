import { all } from 'redux-saga/effects';
import { watchFetchHotelsSagas } from './hotels';
import { watchBookingSagas } from './bookings/bookings.sagas';
import { watchUserSagas } from './users/users.sagas';

export function* rootSaga() {
  yield all([watchFetchHotelsSagas(), watchBookingSagas(), watchUserSagas()]);
}
