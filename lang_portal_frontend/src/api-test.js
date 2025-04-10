// Simple script to test API connectivity
import { sentenceBuilderApi } from './api/sentenceBuilderApi';

async function testApiConnection() {
  console.log('Testing API connection...');
  try {
    // Log the API URL being used
    console.log('API URL:', import.meta.env.VITE_API_URL || 'http://localhost:8080');
    
    // Test categories endpoint
    const categoriesResponse = await sentenceBuilderApi.getCategories();
    console.log('Categories response:', categoriesResponse);
    
    // Test words by category endpoint
    const wordsResponse = await sentenceBuilderApi.getWordsByCategory();
    console.log('Words by category response:', wordsResponse);
    
    console.log('API connection test completed successfully!');
  } catch (error) {
    console.error('API connection test failed:', error);
    console.error('Error details:', error.response || error.request || error.message);
  }
}

// Run the test
testApiConnection();

export default testApiConnection;
