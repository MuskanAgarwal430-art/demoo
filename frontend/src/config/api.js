const BASE_URL = process.env.REACT_APP_API_URL || "/api/v1";

export const API = {
  // Auth
  LOGIN: `${BASE_URL}/auth/login/`,
  LOGOUT: `${BASE_URL}/auth/logout/`,
  REFRESH: `${BASE_URL}/auth/refresh/`,
  VERIFY_TOKEN: `${BASE_URL}/auth/verify-token/`,
  ME: `${BASE_URL}/users/me/`,

  // Companies
  COMPANIES: `${BASE_URL}/companies/`,
  COMPANY: (code) => `${BASE_URL}/companies/${code}/`,

  // Per-company
  EMPLOYEES: (code) => `${BASE_URL}/${code}/employees/`,
  EMPLOYEE: (code, empCode) => `${BASE_URL}/${code}/employees/${empCode}/`,

  FACE_CAPTURE: (code) => `${BASE_URL}/${code}/faces/capture/`,
  FACE_LIST: (code) => `${BASE_URL}/${code}/faces/`,
  FACE_DELETE: (code) => `${BASE_URL}/${code}/faces/delete/`,
  FACE_DELETE_ALL: (code) => `${BASE_URL}/${code}/faces/delete-all/`,
  FACE_APPROVE: (code) => `${BASE_URL}/${code}/faces/approve/`,
  FACE_TRAIN: (code) => `${BASE_URL}/${code}/faces/train/`,
  FACE_TRAIN_ALL: (code) => `${BASE_URL}/${code}/faces/train-all/`,
  FACE_TRAINING_STATUS: (code) => `${BASE_URL}/${code}/faces/training-status/`,

  KIOSK_RECOGNIZE: (code) => `${BASE_URL}/${code}/kiosk/recognize/`,
  KIOSK_CONFIG: (code) => `${BASE_URL}/${code}/kiosk/config/`,

  ATTENDANCE: (code) => `${BASE_URL}/${code}/attendance/`,
  ATTENDANCE_SUMMARY: (code) => `${BASE_URL}/${code}/attendance/summary/`,
  ATTENDANCE_EXPORT: (code) => `${BASE_URL}/${code}/attendance/export/`,
};

export default BASE_URL;
