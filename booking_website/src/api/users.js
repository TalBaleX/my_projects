import { post, get } from './httpClient';

export const registerUser = async (userData) => {
  try {
    const existingUsers = await get('/users');
    const userExists = existingUsers.some(
      (user) => user.name === userData.name
    );

    if (userExists) {
      alert('This username already exists!');
      window.location.reload();
      return null;
    }

    const response = await post('/users', userData);
    return response;
  } catch (error) {
    alert('Registration failed!');
    window.location.reload();
    return null;
  }
};

export const loginUser = async (credentials) => {
  try {
    const users = await get('/users');
    const user = users.find(
      (u) => u.name === credentials.name && u.password === credentials.password
    );

    if (!user) {
      alert('Username or password is incorrect!');
      window.location.reload();
      return null;
    }

    return user;
  } catch (error) {
    alert('Login failed!');
    window.location.reload();
    return null;
  }
};
