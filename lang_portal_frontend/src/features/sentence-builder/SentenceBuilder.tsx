import React, { useState, useEffect } from 'react';
import axios from 'axios';

// Hardcoded API URL to ensure it uses port 8080
const API_URL = 'http://localhost:8080';

// Define types
interface Word {
  id: string;
  urdu_word: string;
  roman_urdu: string;
  english_translation: string;
  category: string;
}

interface Category {
  id: string;
  name: string;
}

interface ApiResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

interface SentenceBuilderProps {
  sessionId: string;
}

const SentenceBuilder: React.FC<SentenceBuilderProps> = ({ sessionId }) => {
  const [categories, setCategories] = useState<Category[]>([]);
  const [wordsByCategory, setWordsByCategory] = useState<Record<string, Word[]>>({});
  const [selectedWords, setSelectedWords] = useState<Word[]>([]);
  const [feedback, setFeedback] = useState<string>('');
  const [isCorrect, setIsCorrect] = useState<boolean | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch data from API
  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        console.log('Fetching categories from:', `${API_URL}/api/sentence-builder/categories/`);
        const categoriesResponse = await axios.get<ApiResponse<Category>>(`${API_URL}/api/sentence-builder/categories/`);
        console.log('Categories response:', categoriesResponse.data);
        
        console.log('Fetching words from:', `${API_URL}/api/sentence-builder/words/by_category/`);
        const wordsResponse = await axios.get(`${API_URL}/api/sentence-builder/words/by_category/`);
        console.log('Words response:', wordsResponse.data);
        
        // Store the results array, not the whole response object
        setCategories(categoriesResponse.data.results);
        
        // Process words by category - the API returns an array of category objects
        const wordsByCat: Record<string, Word[]> = {};
        
        // Check if wordsResponse.data is an array
        if (Array.isArray(wordsResponse.data)) {
          wordsResponse.data.forEach((categoryData) => {
            if (categoryData.category_id && Array.isArray(categoryData.words)) {
              wordsByCat[categoryData.category_id] = categoryData.words;
            }
          });
        }
        
        setWordsByCategory(wordsByCat);
      } catch (error) {
        console.error('Error fetching data:', error);
        setError('Failed to load data. Please try again later.');
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchData();
  }, []);

  // Add a word to the sentence
  const addWord = (word: Word) => {
    setSelectedWords([...selectedWords, word]);
  };

  // Remove a word from the sentence
  const removeWord = (index: number) => {
    const newWords = [...selectedWords];
    newWords.splice(index, 1);
    setSelectedWords(newWords);
  };

  // Validate the sentence
  const validateSentence = async () => {
    if (selectedWords.length === 0) {
      setFeedback('Please select words to form a sentence first.');
      setIsCorrect(null);
      return;
    }
    
    const sentence = selectedWords.map(word => word.urdu_word).join(' ');
    
    try {
      console.log('Validating sentence:', `${API_URL}/api/sentence-builder/validate_sentence/`);
      const response = await axios.post(`${API_URL}/api/sentence-builder/validate_sentence/`, {
        sentence,
        user_id: sessionId
      });
      
      console.log('Validation response:', response.data);
      setFeedback(response.data.feedback);
      setIsCorrect(response.data.is_correct);
    } catch (error) {
      console.error('Error validating sentence:', error);
      setFeedback('Failed to validate sentence. Please try again.');
      setIsCorrect(null);
    }
  };

  // Reset the sentence
  const resetSentence = () => {
    setSelectedWords([]);
    setFeedback('');
    setIsCorrect(null);
  };

  if (isLoading) {
    return <div className="p-4">Loading sentence builder...</div>;
  }

  if (error) {
    return <div className="p-4 text-red-500">{error}</div>;
  }

  return (
    <div className="p-4 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Urdu Sentence Builder</h1>
      
      {/* Word Bank */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold mb-4">Word Bank</h2>
        <div className="border rounded-lg p-4">
          {categories.map(category => (
            <div key={category.id} className="mb-4">
              <h3 className="font-medium mb-2">{category.name}</h3>
              <div className="flex flex-wrap">
                {wordsByCategory[category.id] && wordsByCategory[category.id].map(word => (
                  <button
                    key={word.id}
                    className="m-1 p-2 border rounded-md hover:bg-gray-100"
                    onClick={() => addWord(word)}
                  >
                    <div dir="rtl" lang="ur" className="text-lg">{word.urdu_word}</div>
                    <div className="text-xs text-gray-500">{word.roman_urdu}</div>
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Sentence Workspace */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold mb-4">Your Sentence</h2>
        <div className="border rounded-lg p-4 min-h-[200px]">
          {selectedWords.length === 0 ? (
            <div className="text-center text-gray-500 py-10">
              Select words from the word bank to build your sentence
            </div>
          ) : (
            <div className="flex flex-wrap justify-end" dir="rtl">
              {selectedWords.map((word, index) => (
                <div key={`${word.id}-${index}`} className="inline-block m-1">
                  <div className="relative border rounded-md p-3">
                    <button
                      className="absolute top-1 right-1 text-gray-500 hover:text-gray-700"
                      onClick={() => removeWord(index)}
                    >
                      ×
                    </button>
                    <div dir="rtl" lang="ur" className="text-lg">{word.urdu_word}</div>
                    <div className="text-xs text-gray-500">{word.roman_urdu}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
      
      {/* Actions */}
      <div className="flex justify-between mb-6">
        <button
          className="px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600"
          onClick={resetSentence}
        >
          Reset
        </button>
        <button
          className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
          onClick={validateSentence}
          disabled={selectedWords.length === 0}
        >
          Check Sentence
        </button>
      </div>
      
      {/* Feedback */}
      {feedback && (
        <div className={`p-4 rounded-md ${isCorrect ? 'bg-green-100' : 'bg-red-100'}`}>
          <h3 className="font-semibold mb-2">
            {isCorrect ? 'Correct!' : 'Not quite right'}
          </h3>
          <p>{feedback}</p>
        </div>
      )}
    </div>
  );
};

export default SentenceBuilder;
