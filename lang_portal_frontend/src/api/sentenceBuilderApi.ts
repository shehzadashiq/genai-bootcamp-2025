import axios from 'axios';

// Explicitly set the API URL to the backend port
const API_URL = 'http://localhost:8080';

export const sentenceBuilderApi = {
  // Get all word categories
  getCategories: async () => {
    console.log('Calling API:', `${API_URL}/api/sentence-builder/categories/`);
    return axios.get(`${API_URL}/api/sentence-builder/categories/`);
  },
  
  // Get words grouped by category
  getWordsByCategory: async () => {
    console.log('Calling API:', `${API_URL}/api/sentence-builder/words/by_category/`);
    return axios.get(`${API_URL}/api/sentence-builder/words/by_category/`);
  },
  
  // Validate a sentence
  validateSentence: async (sentence: string, userId?: string) => {
    console.log('Calling API:', `${API_URL}/api/sentence-builder/validate_sentence/`);
    return axios.post(`${API_URL}/api/sentence-builder/validate_sentence/`, {
      sentence,
      user_id: userId
    });
  },
  
  // Get user's previous sentences
  getUserSentences: async (userId: string) => {
    console.log('Calling API:', `${API_URL}/api/sentence-builder/get_user_sentences/`);
    return axios.get(`${API_URL}/api/sentence-builder/get_user_sentences/`, {
      params: { user_id: userId }
    });
  }
};
