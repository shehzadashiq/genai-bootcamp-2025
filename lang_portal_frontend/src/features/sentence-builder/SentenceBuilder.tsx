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

interface CategoryResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Category[];
}

interface CategoryWords {
  category_id: string;
  category_name: string;
  words: Word[];
}

// Common auxiliary verbs and sentence endings in Urdu
const auxiliaryVerbs = [
  {
    id: 'aux-1',
    urdu_word: 'ہوں',
    roman_urdu: 'hoon',
    english_translation: 'am',
    category: 'auxiliary'
  },
  {
    id: 'aux-2',
    urdu_word: 'ہے',
    roman_urdu: 'hai',
    english_translation: 'is',
    category: 'auxiliary'
  },
  {
    id: 'aux-3',
    urdu_word: 'ہیں',
    roman_urdu: 'hain',
    english_translation: 'are',
    category: 'auxiliary'
  },
  {
    id: 'aux-4',
    urdu_word: 'تھا',
    roman_urdu: 'tha',
    english_translation: 'was',
    category: 'auxiliary'
  },
  {
    id: 'aux-5',
    urdu_word: 'تھی',
    roman_urdu: 'thi',
    english_translation: 'was (feminine)',
    category: 'auxiliary'
  },
  {
    id: 'aux-6',
    urdu_word: 'تھے',
    roman_urdu: 'thay',
    english_translation: 'were',
    category: 'auxiliary'
  },
  {
    id: 'aux-7',
    urdu_word: '۔',
    roman_urdu: '.',
    english_translation: 'period/full stop',
    category: 'punctuation'
  }
];

// Function to clean verb words by removing the auxiliary ending if present
const cleanVerbWord = (word: Word): Word => {
  // If this is a verb, remove the auxiliary ending (like "ہے" - "hai")
  if (word.category === 'verb' || word.roman_urdu?.includes('hai')) {
    // Common endings to remove
    const endings = [' ہے', ' ہوں', ' ہیں'];
    let cleanedWord = word.urdu_word;
    let cleanedRoman = word.roman_urdu;
    
    // Remove Urdu endings
    for (const ending of endings) {
      if (word.urdu_word.endsWith(ending)) {
        cleanedWord = word.urdu_word.slice(0, -ending.length);
        break;
      }
    }
    
    // Remove Roman Urdu "hai" ending
    if (word.roman_urdu?.includes(' hai')) {
      cleanedRoman = word.roman_urdu.replace(' hai', '');
    }
    
    return {
      ...word,
      urdu_word: cleanedWord,
      roman_urdu: cleanedRoman
    };
  }
  
  return word;
};

// Function to add feminine form to verbs
const addFeminineForm = (word: Word): Word => {
  // Only process verbs
  if (word.category === 'verb' || word.roman_urdu?.includes('karta') || word.roman_urdu?.includes('jata')) {
    // Common masculine endings and their feminine counterparts
    const genderPairs = [
      { masc: 'تا', fem: 'تی' },
      { masc: 'نا', fem: 'نی' },
      { masc: 'را', fem: 'ری' }
    ];
    
    let urduWord = word.urdu_word;
    let romanUrdu = word.roman_urdu || '';
    
    // Check if the word ends with a masculine ending
    for (const pair of genderPairs) {
      if (urduWord.endsWith(pair.masc)) {
        // Replace with both forms
        const basePart = urduWord.slice(0, -pair.masc.length);
        urduWord = `${basePart}${pair.masc}/${pair.fem}`;
        
        // Update Roman Urdu if available
        if (romanUrdu) {
          if (romanUrdu.includes('ta')) {
            romanUrdu = romanUrdu.replace('ta', 'ta/ti');
          } else if (romanUrdu.includes('na')) {
            romanUrdu = romanUrdu.replace('na', 'na/ni');
          } else if (romanUrdu.includes('ra')) {
            romanUrdu = romanUrdu.replace('ra', 'ra/ri');
          }
        }
        
        break;
      }
    }
    
    return {
      ...word,
      urdu_word: urduWord,
      roman_urdu: romanUrdu
    };
  }
  
  return word;
};

// Common sentence patterns in Urdu
const commonPatterns = [
  {
    name: "Subject + Verb",
    example: "میں جاتا ہوں۔",
    romanExample: "main jata hoon.",
    englishExample: "I go."
  },
  {
    name: "Subject + Object + Verb",
    example: "میں کھانا کھاتا ہوں۔",
    romanExample: "main khana khata hoon.",
    englishExample: "I eat food."
  },
  {
    name: "Subject + Adjective + Object + Verb",
    example: "میں اچھا کھانا کھاتا ہوں۔",
    romanExample: "main acha khana khata hoon.",
    englishExample: "I eat good food."
  }
];

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
  const [showPatternHelp, setShowPatternHelp] = useState<boolean>(false);
  const [manualValidation, setManualValidation] = useState<boolean>(false);

  // Fetch data from API
  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        console.log('Fetching categories from:', `${API_URL}/api/sentence-builder/categories/`);
        const categoriesResponse = await axios.get<CategoryResponse>(`${API_URL}/api/sentence-builder/categories/`);
        console.log('Categories response:', categoriesResponse.data);
        
        console.log('Fetching words from:', `${API_URL}/api/sentence-builder/words/by_category/`);
        const wordsResponse = await axios.get<CategoryWords[]>(`${API_URL}/api/sentence-builder/words/by_category/`);
        console.log('Words response:', wordsResponse.data);
        
        // Store the results array from categories response
        setCategories(categoriesResponse.data.results);
        
        // Process words by category - the API returns an array of category objects
        const wordsByCat: Record<string, Word[]> = {};
        
        // Check if wordsResponse.data is an array
        if (Array.isArray(wordsResponse.data)) {
          wordsResponse.data.forEach((categoryData) => {
            if (categoryData.category_id && Array.isArray(categoryData.words)) {
              // Clean verb words by removing auxiliary endings and add feminine forms
              const processedWords = categoryData.words.map(word => {
                // If this category is for verbs, clean the words and add feminine forms
                if (categoryData.category_name.toLowerCase().includes('verb')) {
                  const cleanedWord = cleanVerbWord(word);
                  return addFeminineForm(cleanedWord);
                }
                return word;
              });
              
              wordsByCat[categoryData.category_id] = processedWords;
            }
          });
        }
        
        // Add auxiliary verbs to the wordsByCategory
        wordsByCat['auxiliary'] = auxiliaryVerbs;
        
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
      setIsCorrect(response.data.is_valid);
      setManualValidation(false);
    } catch (error) {
      console.error('Error validating sentence:', error);
      setFeedback('Failed to validate sentence. Please try again.');
      setIsCorrect(null);
    }
  };

  // Mark sentence as correct manually (for cases where automatic validation fails)
  const markAsCorrect = () => {
    setIsCorrect(true);
    setManualValidation(true);
    setFeedback('You marked this sentence as correct. Good job!');
  };

  // Reset the sentence
  const resetSentence = () => {
    setSelectedWords([]);
    setFeedback('');
    setIsCorrect(null);
    setManualValidation(false);
    setShowPatternHelp(false);
  };

  if (isLoading) {
    return <div className="p-4">Loading sentence builder...</div>;
  }

  if (error) {
    return <div className="p-4 text-red-500">{error}</div>;
  }

  return (
    <div className="p-4 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Urdu Sentence Builder</h1>
      
      {/* Instructions */}
      <div className="bg-blue-50 p-4 rounded-lg mb-6">
        <h2 className="text-lg font-semibold mb-2">How to Use:</h2>
        <ol className="list-decimal pl-5 space-y-1">
          <li>Select words from each category in the Word Bank below</li>
          <li>Build a grammatically correct Urdu sentence</li>
          <li>Most sentences need a subject, verb, and often an auxiliary verb (like "ہوں", "ہے")</li>
          <li>Click "Check Sentence" to verify if your sentence is correct</li>
          <li>Use "Reset" to start over</li>
        </ol>
        <p className="mt-2 text-sm italic">Example: میں جاتا ہوں۔ (I go.)</p>
        <button 
          className="mt-2 text-blue-600 hover:underline text-sm"
          onClick={() => setShowPatternHelp(!showPatternHelp)}
        >
          {showPatternHelp ? 'Hide Common Patterns' : 'Show Common Patterns'}
        </button>
        
        {showPatternHelp && (
          <div className="mt-3 border-t pt-3">
            <h3 className="font-medium mb-2">Common Sentence Patterns:</h3>
            <ul className="space-y-2">
              {commonPatterns.map((pattern, index) => (
                <li key={index} className="text-sm">
                  <div className="font-medium">{pattern.name}</div>
                  <div dir="rtl" lang="ur" className="text-md">{pattern.example}</div>
                  <div className="text-gray-600">{pattern.romanExample}</div>
                  <div className="text-gray-600 italic">{pattern.englishExample}</div>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
      
      {/* Word Bank */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold mb-4">Word Bank</h2>
        <div className="border rounded-lg p-4">
          {/* Auxiliary Verbs Section - Always show first */}
          <div className="mb-4">
            <h3 className="font-medium mb-2 text-blue-700">Auxiliary Verbs & Endings</h3>
            <div className="flex flex-wrap">
              {auxiliaryVerbs.map(word => (
                <button
                  key={word.id}
                  className="m-1 p-2 border rounded-md bg-blue-50 hover:bg-blue-100"
                  onClick={() => addWord(word)}
                >
                  <div dir="rtl" lang="ur" className="text-lg">{word.urdu_word}</div>
                  <div className="text-xs text-gray-500">{word.roman_urdu}</div>
                </button>
              ))}
            </div>
          </div>
          
          {/* Regular Categories */}
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
        <div className="flex space-x-2">
          {!isCorrect && feedback && !manualValidation && (
            <button
              className="px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600"
              onClick={markAsCorrect}
            >
              Mark as Correct
            </button>
          )}
          <button
            className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
            onClick={validateSentence}
            disabled={selectedWords.length === 0}
          >
            Check Sentence
          </button>
        </div>
      </div>
      
      {/* Feedback */}
      {feedback && (
        <div className={`p-4 rounded-md ${isCorrect ? 'bg-green-100' : 'bg-red-100'}`}>
          <h3 className="font-semibold mb-2">
            {isCorrect ? 'Correct!' : 'Not quite right'}
          </h3>
          <p>{feedback}</p>
          {!isCorrect && !manualValidation && (
            <p className="mt-2 text-sm text-gray-700">
              If you believe your sentence is correct, you can use the "Mark as Correct" button.
            </p>
          )}
        </div>
      )}
    </div>
  );
};

export default SentenceBuilder;
