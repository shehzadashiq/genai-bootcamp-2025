import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

interface VocabularyQuizProps {
  sessionId: string;
}

interface Word {
  id: number;
  urdu: string;
  urdlish: string;
  english: string;
}

interface QuizWord {
  word: Word;
  options: string[];
}

interface QuizScore {
  sessionId: number;
  totalWords: number;
  correctCount: number;
  accuracy: number;
  difficulty: string;
}

export const VocabularyQuiz: React.FC<VocabularyQuizProps> = ({ sessionId }) => {
  const navigate = useNavigate();
  const [words, setWords] = useState<QuizWord[]>([]);
  const [currentWordIndex, setCurrentWordIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState('');
  const [isAnswered, setIsAnswered] = useState(false);
  const [score, setScore] = useState<QuizScore | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  React.useEffect(() => {
    const fetchWords = async () => {
      try {
        const response = await axios.get(`http://localhost:8080/api/vocabulary-quiz/words/${sessionId}`);
        setWords(response.data);
        setLoading(false);
      } catch (err) {
        setError('Failed to load quiz words');
        setLoading(false);
      }
    };

    fetchWords();
  }, [sessionId]);

  const handleAnswer = async () => {
    const currentWord = words[currentWordIndex];
    const isCorrect = selectedAnswer === currentWord.word.english;

    try {
      await axios.post('http://localhost:8080/api/vocabulary-quiz/submit', {
        word_id: currentWord.word.id,
        session_id: parseInt(sessionId),
        answer: selectedAnswer,
        correct: isCorrect,
      });

      setIsAnswered(true);

      if (currentWordIndex === words.length - 1) {
        const scoreResponse = await axios.get(`http://localhost:8080/api/vocabulary-quiz/score/${sessionId}`);
        setScore(scoreResponse.data);
      }
    } catch (err) {
      setError('Failed to submit answer');
    }
  };

  const handleNext = () => {
    setSelectedAnswer('');
    setIsAnswered(false);
    setCurrentWordIndex((prev) => prev + 1);
  };

  if (loading) {
    return <div className="text-center p-4">Loading quiz...</div>;
  }

  if (error) {
    return <div className="text-center p-4 text-red-500">{error}</div>;
  }

  if (score) {
    return (
      <div className="max-w-xl mx-auto mt-8 p-6 bg-white rounded-lg shadow">
        <h2 className="text-2xl font-bold mb-4">Quiz Complete!</h2>
        <div className="space-y-4">
          <p className="text-xl">Your score: {score.accuracy}%</p>
          <p>Correct answers: {score.correctCount}</p>
          <p>Total questions: {score.totalWords}</p>
          <button
            onClick={() => navigate('/study_activities')}
            className="w-full px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Back to Activities
          </button>
        </div>
      </div>
    );
  }

  if (words.length === 0) {
    return <div className="text-center p-4">No words available for the quiz.</div>;
  }

  const currentWord = words[currentWordIndex];
  const progress = ((currentWordIndex + 1) / words.length) * 100;

  return (
    <div className="max-w-xl mx-auto mt-8 p-6 bg-white rounded-lg shadow">
      <div className="mb-6">
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-500 h-2 rounded-full"
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="mt-2 text-sm text-gray-600">
          Question {currentWordIndex + 1} of {words.length}
        </p>
      </div>

      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">{currentWord.word.urdu}</h2>
        <p className="text-gray-600">{currentWord.word.urdlish}</p>
      </div>

      <div className="space-y-3 mb-6">
        {currentWord.options.map((option) => (
          <label
            key={option}
            className={`block p-3 border rounded cursor-pointer ${
              isAnswered
                ? option === currentWord.word.english
                  ? 'bg-green-100 border-green-500'
                  : option === selectedAnswer
                  ? 'bg-red-100 border-red-500'
                  : 'border-gray-200'
                : selectedAnswer === option
                ? 'bg-blue-50 border-blue-500'
                : 'border-gray-200 hover:bg-gray-50'
            }`}
          >
            <input
              type="radio"
              name="answer"
              value={option}
              checked={selectedAnswer === option}
              onChange={(e) => setSelectedAnswer(e.target.value)}
              disabled={isAnswered}
              className="mr-2"
            />
            {option}
          </label>
        ))}
      </div>

      {!isAnswered ? (
        <button
          onClick={handleAnswer}
          disabled={!selectedAnswer}
          className="w-full px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          Submit Answer
        </button>
      ) : (
        <button
          onClick={handleNext}
          className="w-full px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
        >
          {currentWordIndex === words.length - 1 ? 'Finish Quiz' : 'Next Word'}
        </button>
      )}
    </div>
  );
};
