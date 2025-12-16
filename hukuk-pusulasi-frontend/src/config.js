// src/config.js
const API_BASE_URL = "https://cathern-imino-alfredo.ngrok-free.dev";

// Tüm API endpoint'leriniz
export const API_ENDPOINTS = {
  HEALTH: `${API_BASE_URL}/health`,
  CHATBOT: `${API_BASE_URL}/chatbot`,
  SESSIONS: `${API_BASE_URL}/sessions`,
  HISTORY: (chatId) => `${API_BASE_URL}/history/${chatId}`,
  DELETE_CHAT: (chatId) => `${API_BASE_URL}/chat/${chatId}`,
  LOGIN: `${API_BASE_URL}/login`,
  REGISTER: `${API_BASE_URL}/register`,
};

export default API_BASE_URL;
