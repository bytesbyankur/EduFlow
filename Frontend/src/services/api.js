const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';
// Fallback root URL if proxy or direct routing is used
const ROOT_URL = import.meta.env.VITE_ROOT_URL || 'http://127.0.0.1:8000';

async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
  try {
    const res = await fetch(url, options);
    if (!res.ok) {
      let errData = {};
      try {
        errData = await res.json();
      } catch {
        errData = { detail: `HTTP error! Status: ${res.status}` };
      }
      throw new Error(errData.detail || errData.message || `Request failed with status ${res.status}`);
    }
    const contentType = res.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return await res.json();
    }
    return res;
  } catch (error) {
    console.error(`API Error on [${options.method || 'GET'}] ${url}:`, error);
    throw error;
  }
}

export const api = {
  // Authentication
  async login(userId, password, role) {
    return await request('/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, password, role }),
    });
  },

  // Teacher & Dashboard operations
  async getDashboardData() {
    return await request('/get-dashboard-data');
  },

  async getClassRoster(className) {
    return await request(`/get-class-roster?class_name=${encodeURIComponent(className)}`);
  },

  async getAllStudents() {
    return await request('/students');
  },

  async deleteStudent(studentIdOrName) {
    return await request('/delete-student', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        student_id: studentIdOrName,
        name: studentIdOrName,
        id: studentIdOrName
      }),
    });
  },

  async getCourses() {
    return await request('/courses');
  },

  async markAttendance(className, imageBlob) {
    const formData = new FormData();
    formData.append('class_name', className);
    formData.append('file', imageBlob, 'scan.jpg');

    return await request('/mark-attendance', {
      method: 'POST',
      body: formData,
    });
  },

  async registerStudent(name, className, imageBlob) {
    const formData = new FormData();
    formData.append('name', name);
    formData.append('class_name', className);
    formData.append('file', imageBlob, `${name.replace(/\s+/g, '_')}.jpg`);

    return await request('/register-student', {
      method: 'POST',
      body: formData,
    });
  },

  async compareFaces(imageBlob1, imageBlob2) {
    const formData = new FormData();
    formData.append('image1', imageBlob1, 'img1.jpg');
    formData.append('image2', imageBlob2, 'img2.jpg');

    return await request('/compare-faces', {
      method: 'POST',
      body: formData,
    });
  },

  async getModelInfo() {
    return await request('/model-info');
  },

  async exportCsv() {
    const url = `${API_BASE_URL}/export-csv`;
    window.open(url, '_blank');
  },

  async resetDatabase() {
    return await request('/reset-db', {
      method: 'POST',
    });
  },

  // Student specific operations
  async getStudentStats(studentName) {
    return await request(`/student/stats/${encodeURIComponent(studentName)}`);
  },

  async getStudentHistory(studentName) {
    return await request(`/student/history/${encodeURIComponent(studentName)}`);
  },

  async checkHealth() {
    return await request('/health');
  },
};

export default api;
