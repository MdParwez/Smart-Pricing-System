import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const scraperService = {
  startScrape: async (formData) => {
    const response = await client.post('/start-scrape', formData);
    return response.data;
  },

  scheduleScrape: async (formData) => {
    const response = await client.post('/schedule-scrape', formData);
    return response.data;
  },

  getScrapingStatus: async (taskId) => {
    const response = await client.get(`/scraping-status/${taskId}`);
    return response.data;
  },

  downloadExcel: async (fileName) => {
    const response = await client.get(`/download/${fileName}`, {
      responseType: 'blob',
    });
    return response.data;
  },

  getScrapingHistory: async () => {
    const response = await client.get('/scraping-history');
    return response.data;
  },
};

export default client;
