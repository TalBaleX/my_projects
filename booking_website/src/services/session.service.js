export class SessionService {
  static setUser(user) {
    sessionStorage.setItem('user', JSON.stringify(user));
  }

  static getUser() {
    const user = sessionStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  }

  static clearUser() {
    sessionStorage.removeItem('user');
  }
}
