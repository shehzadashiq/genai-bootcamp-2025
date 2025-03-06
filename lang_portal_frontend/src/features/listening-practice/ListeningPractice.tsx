import React, { useState, useEffect } from 'react';
import { Box, Button, TextField, Typography, Paper, FormControl, RadioGroup, FormControlLabel, Radio, CircularProgress } from '@mui/material';
import BugReportIcon from '@mui/icons-material/BugReport';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import { useQuery, useMutation } from '@tanstack/react-query';
import axios from 'axios';

interface Question {
  id: number;
  text?: string;  // For backward compatibility
  question?: string;  // New field name
  options: string[];
  correct_answer: string;
  audio_start: number;
  audio_end: number;
}

interface QuestionResponse {
  questions: Question[];
  error?: string;
}

const ListeningPractice: React.FC = () => {
  const [videoUrl, setVideoUrl] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, string>>({});
  const [showResults, setShowResults] = useState(false);
  const [showDebug, setShowDebug] = useState(false);

  const getQuestions = useMutation({
    mutationFn: async (url: string) => {
      try {
        setError(null);
        
        // First download the transcript
        const downloadResponse = await axios.post('/api/listening/download-transcript', { url });
        console.log('Download response:', downloadResponse.data);
        if (downloadResponse.data.error) {
          throw new Error(downloadResponse.data.error);
        }
        
        // Then get the questions
        const questionsResponse = await axios.post<QuestionResponse>('/api/listening/questions', { url });
        console.log('Raw questions response:', questionsResponse);
        console.log('Questions response data:', questionsResponse.data);
        if (questionsResponse.data.error) {
          throw new Error(questionsResponse.data.error);
        }
        
        if (!questionsResponse.data.questions?.length) {
          throw new Error('No questions were generated. Please try a different video.');
        }
        
        // Log each question's format
        questionsResponse.data.questions.forEach((q, i) => {
          console.log(`Question ${i + 1}:`, {
            id: q.id,
            text: q.text,
            question: q.question,
            optionsCount: q.options?.length,
            hasCorrectAnswer: Boolean(q.correct_answer),
            correctAnswerInOptions: q.options?.includes(q.correct_answer)
          });
        });
        
        // Get the transcript for display
        const transcriptResponse = await axios.post('/api/listening/transcript', { url });
        console.log('Transcript response:', transcriptResponse.data);
        if (transcriptResponse.data.error) {
          throw new Error(transcriptResponse.data.error);
        }
        
        return questionsResponse.data;
      } catch (error) {
        console.error('Error in getQuestions:', error);
        setError(error instanceof Error ? error.message : 'An unexpected error occurred');
        throw error;
      }
    },
    onSuccess: (data) => {
      console.log('Questions loaded successfully:', {
        questionCount: data.questions?.length,
        firstQuestion: data.questions?.[0]
      });
      // Reset quiz state when new questions are loaded
      setCurrentQuestionIndex(0);
      setSelectedAnswers({});
      setShowResults(false);
    }
  });

  // Debug logging for state changes
  useEffect(() => {
    if (getQuestions.data?.questions) {
      const answeredCount = Object.keys(selectedAnswers).length;
      const total = getQuestions.data.questions.length;
      
      console.log('Quiz State:', {
        questions: getQuestions.data.questions,
        currentQuestionIndex,
        totalQuestions: total,
        answeredCount,
        isLastQuestion: currentQuestionIndex === total - 1,
        hasAnsweredCurrentQuestion: Boolean(selectedAnswers[currentQuestionIndex]),
        hasAnsweredAllQuestions: answeredCount === total,
        selectedAnswers
      });
    }
  }, [currentQuestionIndex, selectedAnswers, getQuestions.data]);

  const handleSubmitUrl = () => {
    if (!videoUrl.trim()) {
      setError('Please enter a valid YouTube URL');
      return;
    }
    getQuestions.mutate(videoUrl);
  };

  const handleAnswerSelect = (value: string) => {
    console.log('Selecting answer:', {
      questionIndex: currentQuestionIndex,
      value,
      previousAnswers: selectedAnswers
    });
    
    setSelectedAnswers(prev => {
      const newAnswers = { ...prev, [currentQuestionIndex]: value };
      console.log('Updated answers:', newAnswers);
      return newAnswers;
    });
  };

  const handleNextQuestion = () => {
    if (!hasAnsweredCurrentQuestion) {
      console.log('Cannot proceed: current question not answered');
      return;
    }
    
    if (currentQuestionIndex < totalQuestions - 1) {
      console.log('Moving to next question:', currentQuestionIndex + 1);
      setCurrentQuestionIndex(prev => prev + 1);
    } else {
      console.log('Already at last question');
    }
  };

  const handlePreviousQuestion = () => {
    if (currentQuestionIndex > 0) {
      console.log('Moving to previous question:', currentQuestionIndex - 1);
      setCurrentQuestionIndex(prev => prev - 1);
    }
  };

  const handleSubmit = () => {
    if (!hasAnsweredAllQuestions) {
      console.log('Cannot submit: not all questions answered', {
        answered: answeredQuestionsCount,
        total: totalQuestions
      });
      return;
    }
    
    console.log('Submitting quiz:', {
      answers: selectedAnswers,
      questionCount: totalQuestions
    });
    setShowResults(true);
  };

  const calculateScore = () => {
    if (!getQuestions.data?.questions) return 0;
    let correct = 0;
    getQuestions.data.questions.forEach((question, index) => {
      if (selectedAnswers[index] === question.correct_answer) {
        correct++;
      }
    });
    return correct;
  };

  // Compute quiz state
  const totalQuestions = getQuestions.data?.questions?.length || 0;
  const currentQuestion = getQuestions.data?.questions?.[currentQuestionIndex];
  const answeredQuestionsCount = Object.keys(selectedAnswers).length;
  
  const isLastQuestion = currentQuestionIndex === totalQuestions - 1;
  const hasAnsweredCurrentQuestion = Boolean(selectedAnswers[currentQuestionIndex]);
  const hasAnsweredAllQuestions = totalQuestions > 0 && answeredQuestionsCount === totalQuestions;
  
  const showSubmitButton = isLastQuestion && hasAnsweredAllQuestions;
  const showNextButton = !isLastQuestion && hasAnsweredCurrentQuestion;
  const showPreviousButton = currentQuestionIndex > 0;

  // Debug effect for button state
  useEffect(() => {
    console.log('Button state:', {
      isLastQuestion,
      showSubmitButton,
      showNextButton,
      hasAnsweredCurrentQuestion,
      hasAnsweredAllQuestions,
      currentIndex: currentQuestionIndex,
      totalQuestions,
      answeredCount: answeredQuestionsCount
    });
  }, [
    isLastQuestion,
    showSubmitButton,
    showNextButton,
    hasAnsweredCurrentQuestion,
    hasAnsweredAllQuestions,
    currentQuestionIndex,
    totalQuestions,
    answeredQuestionsCount
  ]);

  return (
    <>
      {/* Fixed Debug Button */}
      <Box
        sx={{
          position: 'fixed',
          top: 16,
          right: 16,
          zIndex: 1000,
          bgcolor: 'background.paper',
          borderRadius: 1,
          boxShadow: 2,
        }}
      >
        <Button
          variant="contained"
          size="small"
          color="info"
          onClick={() => setShowDebug(!showDebug)}
          startIcon={showDebug ? <ExpandLessIcon /> : <BugReportIcon />}
        >
          {showDebug ? 'Hide Debug' : 'Debug'}
        </Button>
      </Box>

      {/* Debug Panel - Fixed Position */}
      {showDebug && (
        <Box
          sx={{
            position: 'fixed',
            top: 70,
            right: 16,
            width: '400px',
            maxWidth: '90vw',
            maxHeight: '80vh',
            overflowY: 'auto',
            zIndex: 1000,
            bgcolor: 'background.paper',
            borderRadius: 1,
            boxShadow: 3,
          }}
        >
          <Paper 
            elevation={3}
            sx={{ 
              p: 2,
              bgcolor: '#f5f5f5',
              border: '1px solid #e0e0e0',
            }}
          >
            <Typography variant="subtitle2" gutterBottom color="primary">
              Debug Information
            </Typography>
            <Box sx={{ 
              fontFamily: 'monospace',
              whiteSpace: 'pre-wrap',
              fontSize: '0.875rem',
              color: '#37474f'
            }}>
              {`Current Index: ${currentQuestionIndex}
Total Questions: ${totalQuestions}
Is Last Question: ${isLastQuestion}
Show Submit Button: ${showSubmitButton}
Show Next Button: ${showNextButton}
Has Answered Current: ${hasAnsweredCurrentQuestion}
Has Answered All: ${hasAnsweredAllQuestions}
Answered Count: ${answeredQuestionsCount}
Selected Answers: ${JSON.stringify(selectedAnswers, null, 2)}
Current Question: ${JSON.stringify(currentQuestion, null, 2)}`}
            </Box>
          </Paper>
        </Box>
      )}

      <Box sx={{ maxWidth: 800, mx: 'auto', p: 3 }}>
        <Typography variant="h4" gutterBottom>
          Urdu Listening Practice
        </Typography>

        {/* URL Input Section */}
        <Box sx={{ mb: 4 }}>
          <TextField
            fullWidth
            label="YouTube Video URL"
            value={videoUrl}
            onChange={(e) => setVideoUrl(e.target.value)}
            error={Boolean(error)}
            helperText={error || ''}
            sx={{ mb: 2 }}
          />
          <Button
            variant="contained"
            onClick={handleSubmitUrl}
            disabled={getQuestions.isPending}
          >
            {getQuestions.isPending ? 'Loading...' : 'Generate Questions'}
          </Button>
        </Box>

        {/* Loading State */}
        {getQuestions.isPending && (
          <Box sx={{ textAlign: 'center', my: 4 }}>
            <CircularProgress />
            <Typography sx={{ mt: 2 }}>
              Generating questions...
            </Typography>
          </Box>
        )}

        {/* Quiz Section */}
        {getQuestions.data?.questions && !showResults && (
          <Box sx={{ mt: 4 }}>
            {/* Question Display */}
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Question {currentQuestionIndex + 1}:
              </Typography>
              <Typography paragraph>
                {currentQuestion?.question}
              </Typography>

              {/* Options */}
              {currentQuestion && (
                <FormControl component="fieldset" fullWidth>
                  <RadioGroup
                    value={selectedAnswers[currentQuestionIndex] || ''}
                    onChange={(e) => handleAnswerSelect(e.target.value)}
                  >
                    {currentQuestion.options.map((option, index) => (
                      <FormControlLabel
                        key={index}
                        value={option}
                        control={<Radio />}
                        label={option}
                        sx={{
                          mb: 1,
                          p: 1,
                          borderRadius: 1,
                          '&:hover': {
                            bgcolor: 'action.hover',
                          },
                        }}
                      />
                    ))}
                  </RadioGroup>
                </FormControl>
              )}
            </Paper>

            {/* Navigation Controls */}
            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Button
                variant="outlined"
                onClick={handlePreviousQuestion}
                disabled={!showPreviousButton}
              >
                Previous
              </Button>

              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="body2" color="text.secondary">
                  Question {currentQuestionIndex + 1} of {totalQuestions}
                </Typography>
                {isLastQuestion && !hasAnsweredAllQuestions && (
                  <Typography variant="caption" color="error.main">
                    {totalQuestions - answeredQuestionsCount} question(s) unanswered
                  </Typography>
                )}
              </Box>

              {showSubmitButton ? (
                <Button
                  variant="contained"
                  color="success"
                  onClick={handleSubmit}
                  disabled={!hasAnsweredAllQuestions}
                >
                  Submit Quiz
                </Button>
              ) : (
                <Button
                  variant="contained"
                  onClick={handleNextQuestion}
                  disabled={!hasAnsweredCurrentQuestion}
                >
                  Next
                </Button>
              )}
            </Box>
          </Box>
        )}

        {/* Results Section */}
        {showResults && getQuestions.data?.questions && (
          <Box sx={{ mt: 4 }}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h5" gutterBottom>
                Quiz Results
              </Typography>
              <Typography variant="h6" color="primary">
                Score: {calculateScore()} out of {totalQuestions}
              </Typography>
              
              {getQuestions.data.questions.map((question, index) => (
                <Box key={index} sx={{ mt: 3, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                  <Typography variant="subtitle1" gutterBottom>
                    Question {index + 1}: {question.question}
                  </Typography>
                  <Typography color={selectedAnswers[index] === question.correct_answer ? 'success.main' : 'error.main'}>
                    Your Answer: {selectedAnswers[index]}
                  </Typography>
                  <Typography color="success.main">
                    Correct Answer: {question.correct_answer}
                  </Typography>
                </Box>
              ))}
              
              <Button
                variant="contained"
                onClick={() => {
                  setShowResults(false);
                  setSelectedAnswers({});
                  setCurrentQuestionIndex(0);
                  setVideoUrl('');
                }}
                sx={{ mt: 3 }}
              >
                Try Another Video
              </Button>
            </Paper>
          </Box>
        )}
      </Box>
    </>
  );
};

export default ListeningPractice;
