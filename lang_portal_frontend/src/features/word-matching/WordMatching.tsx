import { useReducer, useEffect, useRef } from 'react';
import { wordMatchingApi } from '@/services/api';
import type { WordMatchingGame } from './types';

interface GameState {
  game: WordMatchingGame | null;
  loading: boolean;
  error: string | null;
  currentQuestionIndex: number;
  showAnswer: boolean;
  submitting: boolean;
  selectedAnswer: string | null;
  options: string[];
}

type GameAction =
  | { type: 'START_LOADING' }
  | { type: 'SET_GAME'; payload: WordMatchingGame }
  | { type: 'SET_ERROR'; payload: string }
  | { type: 'SET_OPTIONS'; payload: string[] }
  | { type: 'START_SUBMIT' }
  | { type: 'SHOW_ANSWER'; payload: string }
  | { type: 'NEXT_QUESTION' }
  | { type: 'COMPLETE_GAME' };

const initialState: GameState = {
  game: null,
  loading: false,
  error: null,
  currentQuestionIndex: 0,
  showAnswer: false,
  submitting: false,
  selectedAnswer: null,
  options: [],
};

function gameReducer(state: GameState, action: GameAction): GameState {
  switch (action.type) {
    case 'START_LOADING':
      return { ...initialState, loading: true };
    case 'SET_GAME':
      return {
        ...state,
        game: action.payload,
        loading: false,
      };
    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
        loading: false,
        submitting: false,
      };
    case 'SET_OPTIONS':
      return {
        ...state,
        options: action.payload,
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
        selectedAnswer: action.payload,
        submitting: false,
      };
    case 'NEXT_QUESTION':
      return {
        ...state,
        currentQuestionIndex: state.currentQuestionIndex + 1,
        showAnswer: false,
        selectedAnswer: null,
        options: [],
      };
    case 'COMPLETE_GAME':
      return {
        ...state,
        loading: false,
        submitting: false,
      };
    default:
      return state;
  }
}

export default function WordMatching() {
  const [state, dispatch] = useReducer(gameReducer, initialState);
  const startTimeRef = useRef<number>(0);
  const isMounted = useRef(true);

  const currentQuestion = state.game?.questions[state.currentQuestionIndex];

  useEffect(() => {
    isMounted.current = true;
    startGame();
    return () => {
      isMounted.current = false;
    };
  }, []);

  useEffect(() => {
    if (currentQuestion && !state.showAnswer) {
      loadOptions();
      startTimeRef.current = Date.now();
    }
  }, [currentQuestion, state.showAnswer]);

  const startGame = async () => {
    dispatch({ type: 'START_LOADING' });
    try {
      const game = await wordMatchingApi.startGame('user123', 10); // TODO: Get real user
      dispatch({ type: 'SET_GAME', payload: game });
    } catch (error) {
      console.error('Failed to start game:', error);
      dispatch({ type: 'SET_ERROR', payload: 'Failed to start game' });
    }
  };

  const loadOptions = async () => {
    if (!state.game || !currentQuestion) return;
    try {
      const options = await wordMatchingApi.getOptions(state.game.id, currentQuestion.id);
      if (isMounted.current) {
        dispatch({ type: 'SET_OPTIONS', payload: options });
      }
    } catch (error) {
      console.error('Failed to load options:', error);
      dispatch({ type: 'SET_ERROR', payload: 'Failed to load options' });
    }
  };

  const handleAnswer = async (selectedOption: string) => {
    if (!state.game || !currentQuestion) return;

    dispatch({ type: 'START_SUBMIT' });
    const responseTime = Math.round((Date.now() - startTimeRef.current) / 1000);

    try {
      const updatedGame = await wordMatchingApi.submitAnswer(
        state.game.id,
        currentQuestion.id,
        selectedOption,
        responseTime
      );
      dispatch({ type: 'SET_GAME', payload: updatedGame });
      dispatch({ type: 'SHOW_ANSWER', payload: selectedOption });
    } catch (error) {
      console.error('Failed to submit answer:', error);
      dispatch({ type: 'SET_ERROR', payload: 'Failed to submit answer' });
    }
  };

  const handleNextQuestion = () => {
    if (state.currentQuestionIndex < (state.game?.questions.length || 0) - 1) {
      dispatch({ type: 'NEXT_QUESTION' });
    } else {
      dispatch({ type: 'COMPLETE_GAME' });
    }
  };

  if (state.loading) {
    return <div>Loading game...</div>;
  }

  if (state.error) {
    return <div className="text-red-500">{state.error}</div>;
  }

  if (!state.game || !currentQuestion) {
    return <div>No game available</div>;
  }

  if (state.game.completed) {
    return (
      <div className="space-y-4 max-w-2xl mx-auto px-4">
        <h2 className="text-2xl font-bold text-center">Game Complete!</h2>
        <div className="space-y-2">
          <p className="text-center">Score: {state.game.score}</p>
          <p className="text-center">Correct Answers: {state.game.correct_answers}</p>
          <p className="text-center">
            Accuracy:{' '}
            {((state.game.correct_answers / state.game.total_questions) * 100).toFixed(1)}%
          </p>
          <button
            onClick={startGame}
            className="w-full p-3 text-white bg-blue-500 rounded-lg hover:bg-blue-600"
          >
            Play Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4 max-w-2xl mx-auto px-4">
      <div className="urdu-text text-3xl mb-6 font-bold text-center">{currentQuestion.word_urdu}</div>
      <div className="space-y-2">
        {state.options.map((option) => (
          <button
            key={option}
            onClick={() => handleAnswer(option)}
            disabled={state.showAnswer || state.submitting}
            className={`w-full p-3 text-center border rounded-lg ${
              state.showAnswer
                ? option === currentQuestion.word_english
                  ? 'bg-green-100 border-green-500'
                  : option === state.selectedAnswer
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
          onClick={handleNextQuestion}
          className="w-full p-3 mt-4 text-white bg-blue-500 rounded-lg hover:bg-blue-600"
        >
          Next Word
        </button>
      )}
      <div className="text-sm text-gray-500 text-center">
        Word {state.currentQuestionIndex + 1} of {state.game.total_questions}
      </div>
    </div>
  );
}
