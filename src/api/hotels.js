import { get } from './httpClient.js';

export async function getHotels(signal) {
  try {
    return await get('/hotels', signal);
  } catch (error) {
    console.error('Error in getHotels:', error);
    throw error;
  }
}
