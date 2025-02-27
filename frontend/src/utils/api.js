import axios from 'axios';

const API_URL = '/api/v1';

const api = {
  get: async (endpoint) => {
    try {
      const response = await axios.get(`${API_URL}${endpoint}`, {
        credentials: 'omit',
        headers: {
          'Cache-Control': 'no-cache, no-store'
        }
      });
      return response.data;
    } catch (error) {
      console.error(`API GET Error: ${endpoint}`, error);
      throw error.response?.data || error.message;
    }
  },
  
  post: async (endpoint, data) => {
    try {
      const response = await axios.post(`${API_URL}${endpoint}`, data, {
        credentials: 'omit',
        headers: {
          'Cache-Control': 'no-cache, no-store'
        }
      });
      return response.data;
    } catch (error) {
      console.error(`API POST Error: ${endpoint}`, error);
      throw error.response?.data || error.message;
    }
  }
};

export default api;