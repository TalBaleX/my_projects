import { post, get, del } from './httpClient.js';

export async function createBooking(bookingData) {
  return await post('/bookings', bookingData);
}

export async function getUserBookings(userId) {
  const bookings = await get('/bookings');
  return bookings.filter((booking) => booking.userId === userId);
}

export async function deleteBooking(bookingId) {
  return await del(`/bookings/${bookingId}`);
}
