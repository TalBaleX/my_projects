import axios from 'axios';

const axiosConf = (signal) =>
  axios.create({
    baseURL: import.meta.env.VITE_API_URL,
    headers: {
      'Content-Type': 'application/json',
    },
    timeout: 2000,
    ...(signal ? { signal } : {}),
  });

const genericRequest = async ({ requestType, url, data, signal }) => {
  try {
    const httpClient = axiosConf(signal);
    const response = await httpClient[requestType](url, data);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.code === 'ERR_CANCELED') {
        return null;
      }
      throw new Error(error.message);
    }
    throw error;
  }
};

export async function post(url, data, signal) {
  return genericRequest({ requestType: 'post', url, signal, data });
}

export async function get(url, signal) {
  return genericRequest({ requestType: 'get', url, signal });
}

export async function del(url, signal) {
  return genericRequest({ requestType: 'delete', url, signal });
}
