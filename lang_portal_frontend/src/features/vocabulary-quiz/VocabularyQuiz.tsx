import React, { useReducer, useEffect, useRef } from 'react';
import axios from 'axios';
import { studySessionsApi, vocabularyQuizApi } from '@/services/api';

interface WordResponse {
  id: number;
  urdu: string;
  urdlish: string;
  english: string;
}

interface QuizWord {
  word: WordResponse;
  options: string[];
}

interface VocabularyQuizProps {
  sessionId: string;
}

interface QuizState {
  words: QuizWord[];
  currentWordIndex: number;
  showAnswer: boolean;
  loading: boolean;
  error: string | null;
  quizSessionId: number | null;
  isQuizComplete: boolean;
  selectedOption: string | null;
  currentWord: QuizWord | null;
  submitting: boolean;
  score: {
    totalWords: number;
    correctCount: number;
    accuracy: number;
  } | null;
}

type QuizAction =
  | { type: 'START_LOADING' }
  | { type: 'SET_WORDS'; payload: QuizWord[] }
  | { type: 'SET_ERROR'; payload: string }
  | { type: 'SET_SESSION_ID'; payload: number }
  | { type: 'START_SUBMIT' }
  | { type: 'SHOW_ANSWER'; payload: string }
  | { type: 'NEXT_WORD' }
  | { type: 'COMPLETE_QUIZ' }
  | { type: 'SET_SCORE'; payload: { total_words: number; correct_count: number; accuracy: number } }
  | { type: 'RESET' };

const initialState: QuizState = {
  words: [],
  currentWordIndex: 0,
  showAnswer: false,
  loading: false,
  error: null,
  quizSessionId: null,
  isQuizComplete: false,
  selectedOption: null,
  currentWord: null,
  submitting: false,
  score: null,
};

function quizReducer(state: QuizState, action: QuizAction): QuizState {
  console.log('Reducing action:', { type: action.type, payload: action, state });

  switch (action.type) {
    case 'START_LOADING':
      return { ...initialState, loading: true };
    case 'SET_WORDS':
      const words = action.payload;
      console.log('Setting words:', { 
        words,
        firstWord: words[0],
        firstWordUrdu: words[0]?.word?.urdu,
        firstWordEnglish: words[0]?.word?.english,
        firstWordOptions: words[0]?.options,
        wordCount: words.length,
        allWords: words.map(w => ({
          id: w.word.id,
          urdu: w.word.urdu,
          english: w.word.english,
          options: w.options
        }))
      });

      return {
        ...state,
        words,
        loading: false,
        currentWord: words[0],
        currentWordIndex: 0
      };
    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
        loading: false,
        submitting: false,
      };
    case 'SET_SESSION_ID':
      return {
        ...state,
        quizSessionId: action.payload,
      };
    case 'START_SUBMIT':
      return {
        ...state,
        submitting: true,
      };
    case 'SHOW_ANSWER':
      return {
        ...state,
        showAnswer: true,
        selectedOption: action.payload,
        submitting: false,
      };
    case 'NEXT_WORD':
      const nextIndex = state.currentWordIndex + 1;
      if (nextIndex >= state.words.length) {
        return {
          ...state,
          isQuizComplete: true
        };
      }
      
      // Get the next word
      const nextWord = state.words[nextIndex];
      console.log('Moving to next word:', {
        nextIndex,
        nextWord,
        nextWordId: nextWord?.word?.id,
        nextWordUrdu: nextWord?.word?.urdu,
        nextWordEnglish: nextWord?.word?.english,
        nextWordOptions: nextWord?.options,
        totalWords: state.words.length,
        allCurrentWords: state.words.map(w => ({
          id: w.word.id,
          urdu: w.word.urdu,
          english: w.word.english,
          options: w.options
        }))
      });

      // Create a new state with the next word
      return {
        ...state,
        currentWordIndex: nextIndex,
        currentWord: nextWord,
        showAnswer: false,
        selectedOption: null,
      };
    case 'COMPLETE_QUIZ':
      return {
        ...state,
        isQuizComplete: true,
      };
    case 'SET_SCORE':
      return {
        ...state,
        score: {
          totalWords: action.payload.total_words,
          correctCount: action.payload.correct_count,
          accuracy: action.payload.accuracy
        }
      };
    case 'RESET':
      return initialState;
    default:
      return state;
  }
}

export const VocabularyQuiz: React.FC<VocabularyQuizProps> = ({ sessionId }) => {
  const [state, dispatch] = useReducer(quizReducer, initialState);
  const loadingRef = useRef<{ sessionId: string | null; loading: boolean }>({ sessionId: null, loading: false });
  const isMounted = useRef(true);

  const loadQuiz = React.useCallback(async () => {
    // Skip if no session ID or already loading this session
    if (!sessionId || loadingRef.current.loading || loadingRef.current.sessionId === sessionId) {
      return;
    }

    try {
      loadingRef.current = { sessionId, loading: true };
      dispatch({ type: 'START_LOADING' });

      // Use the existing study session
      dispatch({ type: 'SET_SESSION_ID', payload: parseInt(sessionId, 10) });

      // Get the quiz words
      const response = await vocabularyQuizApi.getWords(parseInt(sessionId, 10));

      if (!isMounted.current) return;

      console.log('Received quiz words:', response);

      const words = response.data;
      if (!Array.isArray(words)) {
        throw new Error('Invalid response format from quiz API');
      }

      if (words.length === 0) {
        throw new Error('Quiz returned empty word list');
      }

      // Create a deep copy of the words array to prevent reference issues
      const wordsCopy = words.map(word => ({
        word: { ...word.word },
        options: [...word.options]
      }));

      dispatch({ type: 'SET_WORDS', payload: wordsCopy });
    } catch (err) {
      if (!isMounted.current) return;

      if (axios.isAxiosError(err)) {
        const errorMessage = err.response?.data?.error || err.message;
        console.error('VocabularyQuiz error:', {
          message: err.message,
          response: err.response?.data,
          status: err.response?.status,
          url: err.config?.url,
          method: err.config?.method,
          data: err.config?.data,
        });
        dispatch({ type: 'SET_ERROR', payload: `Failed to load quiz words: ${errorMessage}` });
      } else if (err instanceof Error) {
        console.error('VocabularyQuiz error:', err);
        dispatch({ type: 'SET_ERROR', payload: `Failed to load quiz words: ${err.message}` });
      } else {
        console.error('VocabularyQuiz unknown error:', err);
        dispatch({ type: 'SET_ERROR', payload: 'An unknown error occurred while loading quiz words' });
      }
    } finally {
      if (isMounted.current) {
        loadingRef.current = { sessionId: null, loading: false };
      }
    }
  }, [sessionId]);

  useEffect(() => {
    if (!sessionId) return;

    isMounted.current = true;
    if (loadingRef.current.sessionId !== sessionId) {
      dispatch({ type: 'RESET' });
      loadQuiz();
    }

    return () => {
      isMounted.current = false;
    };
  }, [sessionId, loadQuiz]);

  const handleAnswer = async (selectedOption: string) => {
    if (!state.currentWord?.word || !state.quizSessionId) return;

    dispatch({ type: 'START_SUBMIT' });

    const isCorrect = selectedOption === state.currentWord.word.english;
    try {
      await vocabularyQuizApi.submitAnswer({
        word_id: state.currentWord.word.id,
        session_id: state.quizSessionId,
        answer: selectedOption,
        correct: isCorrect,
      });
      
      dispatch({ type: 'SHOW_ANSWER', payload: selectedOption });
    } catch (err) {
      console.error('Failed to submit answer:', err);
      dispatch({ type: 'SET_ERROR', payload: 'Failed to submit answer' });
    }
  };

  const handleNextWord = async () => {
    console.log('handleNextWord:', {
      currentWordIndex: state.currentWordIndex,
      totalWords: state.words.length,
      isLastWord: state.currentWordIndex >= state.words.length - 1,
      currentWord: state.currentWord,
      nextWord: state.currentWordIndex < state.words.length - 1 ? state.words[state.currentWordIndex + 1] : null,
    });

    if (state.currentWordIndex < state.words.length - 1) {
      dispatch({ type: 'NEXT_WORD' });
    } else {
      try {
        // Get the final score
        const score = await vocabularyQuizApi.getScore(state.quizSessionId!);
        console.log('Got quiz score:', score);
        dispatch({ type: 'SET_SCORE', payload: score });
        dispatch({ type: 'COMPLETE_QUIZ' });
      } catch (err) {
        console.error('Failed to get quiz score:', err);
        dispatch({ type: 'SET_ERROR', payload: 'Failed to get quiz score' });
        dispatch({ type: 'COMPLETE_QUIZ' });
      }
    }
  };

  console.log('Rendering quiz:', {
    currentWordIndex: state.currentWordIndex,
    totalWords: state.words.length,
    showAnswer: state.showAnswer,
    isQuizComplete: state.isQuizComplete,
    currentWord: state.currentWord,
    score: state.score,
  });

  if (state.loading) {
    return <div>Loading quiz...</div>;
  }

  if (state.error) {
    return <div className="text-red-500">{state.error}</div>;
  }

  if (!state.currentWord && !state.isQuizComplete) {
    return <div>No words available</div>;
  }

  if (state.isQuizComplete) {
    return (
      <div className="space-y-4">
        <h2 className="text-2xl font-bold">Quiz Complete!</h2>
        {state.score ? (
          <div className="space-y-2">
            <p>Total Words: {state.score.totalWords}</p>
            <p>Correct Answers: {state.score.correctCount}</p>
            <p>Accuracy: {(state.score.accuracy * 100).toFixed(1)}%</p>
          </div>
        ) : (
          <p>Loading score...</p>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="urdu-text text-3xl mb-6 font-bold">{state.currentWord.word.urdu}</div>
      <div className="space-y-2">
        {state.currentWord.options.map((option) => (
          <button
            key={option}
            onClick={() => handleAnswer(option)}
            disabled={state.showAnswer || state.submitting}
            className={`w-full p-2 text-left border rounded ${
              state.showAnswer
                ? option === state.currentWord?.word.english
                  ? 'bg-green-100 border-green-500'
                  : option === state.selectedOption
                  ? 'bg-red-100 border-red-500'
                  : 'bg-gray-100'
                : state.submitting
                ? 'bg-gray-100 cursor-not-allowed'
                : 'hover:bg-gray-100'
            }`}
          >
            {option}
          </button>
        ))}
      </div>
      {state.showAnswer && (
        <button
          onClick={handleNextWord}
          className="w-full p-2 mt-4 text-white bg-blue-500 rounded hover:bg-blue-600"
        >
          Next Word
        </button>
      )}
      <div className="text-sm text-gray-500">
        Word {state.currentWordIndex + 1} of {state.words.length}
      </div>
    </div>
  );
};
