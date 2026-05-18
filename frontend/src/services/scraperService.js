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

  listAirlines: async () => {
    const response = await client.get('/airlines/list');
    return response.data;
  },

  getAirlineConfig: async (airlineName) => {
    const response = await client.get(`/airlines/config/${encodeURIComponent(airlineName)}`);
    return response.data;
  },

  startMultiAirlineScrape: async (formData) => {
    const response = await client.post('/start-multi-airline-scrape', formData);
    return response.data;
  },

  getTaskFlights: async (taskId) => {
    const response = await client.get(`/flights/history/${taskId}`);
    return response.data;
  },

  getFlightStats: async (origin, destination) => {
    const response = await client.get(
      `/flights/stats/${encodeURIComponent(origin)}/${encodeURIComponent(destination)}`
    );
    return response.data;
  },
};

export default client;
