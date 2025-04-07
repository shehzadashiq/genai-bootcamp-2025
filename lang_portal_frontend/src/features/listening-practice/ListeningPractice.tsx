import React, { useState, useCallback, useEffect } from 'react';
import { Box, Button, TextField, Typography, Paper, FormControl, RadioGroup, FormControlLabel, Radio, CircularProgress, Alert, Tabs, Tab } from '@mui/material';
import { useMutation } from '@tanstack/react-query';
import api from '../../api/config';

interface Question {
  id: number;
  question: string;
  options: string[];
  correct_answer: string;
  audio_start: number;
  audio_end: number;
}

interface QuestionResponse {
  questions: Question[];
  error?: string;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel = (props: TabPanelProps) => {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`listening-tabpanel-${index}`}
      aria-labelledby={`listening-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
};

const ListeningPractice: React.FC = () => {
  // State management
  const [videoUrl, setVideoUrl] = useState('');
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, string>>({});
  const [showResults, setShowResults] = useState(false);
  const [currentTab, setCurrentTab] = useState(0);
  const [transcript, setTranscript] = useState<any>(null);

  // API mutations
  const getQuestions = useMutation({
    mutationFn: async (url: string) => {
      console.log('Fetching questions for URL:', url);
      const response = await api.post<QuestionResponse>('/listening/questions', { url });
      const data = response.data;
      console.log('Questions data received:', {
        totalQuestions: data.questions.length,
        questions: data.questions,
        currentIndex: currentQuestionIndex,
        isLastQuestion: currentQuestionIndex >= data.questions.length - 1
      });
      return data;
    },
    onSuccess: (data) => {
      console.log('Questions loaded successfully:', {
        questions: data.questions,
        currentQuestionIndex,
        isLastQuestion: currentQuestionIndex >= data.questions.length - 1,
        hasAnsweredCurrentQuestion: Boolean(selectedAnswers[currentQuestionIndex]),
        hasAnsweredAllQuestions: data.questions.length > 0 && Object.keys(selectedAnswers).length === data.questions.length
      });
    }
  });

  const getTranscript = useMutation({
    mutationFn: async (url: string) => {
      console.log('Fetching transcript for URL:', url);
      const response = await api.post('/listening/transcript', { url });
      console.log('Transcript data received:', response.data);
      setTranscript(response.data);
      return response.data;
    }
  });

  // Computed state
  const questions = getQuestions.data?.questions || [];
  const currentQuestion = questions[currentQuestionIndex];
  const totalQuestions = questions.length;
  const isLastQuestion = currentQuestionIndex >= totalQuestions - 1;
  const hasAnsweredCurrentQuestion = Boolean(selectedAnswers[currentQuestionIndex]);
  const hasAnsweredAllQuestions = totalQuestions > 0 && Object.keys(selectedAnswers).length === totalQuestions;

  useEffect(() => {
    console.log("Question state updated:", {
      currentIndex: currentQuestionIndex,
      totalQuestions,
      currentQuestion,
      selectedAnswer: selectedAnswers[currentQuestionIndex] || "None",
      showResults,
      hasAnsweredCurrentQuestion,
    });
  }, [currentQuestionIndex, selectedAnswers, showResults]);

  useEffect(() => {
    console.log('Navigation state:', {
      currentQuestionIndex,
      totalQuestions,
      isLastQuestion: currentQuestionIndex === totalQuestions - 1
    });
  }, [currentQuestionIndex, totalQuestions]);

  // Debug logging
  console.log({
    questions,
    currentQuestionIndex,
    currentQuestion,
    totalQuestions,
    isLastQuestion,
    hasAnsweredCurrentQuestion,
    hasAnsweredAllQuestions,
    selectedAnswers
  });

  // Event handlers
  const handleUrlSubmit = useCallback(() => {
    if (!videoUrl.trim()) {
      getQuestions.reset();
      return;
    }
    console.log('Submitting URL:', videoUrl);
    setCurrentQuestionIndex(0);
    setSelectedAnswers({});
    setShowResults(false);
    getQuestions.mutate(videoUrl);
    getTranscript.mutate(videoUrl);
  }, [videoUrl]);

  const handleAnswerSelect = useCallback((answer: string) => {
    console.log('Answer Selection:', {
      answer,
      questionIndex: currentQuestionIndex,
      totalQuestions,
      isLastQuestion: currentQuestionIndex >= totalQuestions - 1
    });
    setSelectedAnswers(prev => {
      const newAnswers = { ...prev, [currentQuestionIndex]: answer };
      console.log('Updated Answers:', {
        answers: newAnswers,
        totalAnswered: Object.keys(newAnswers).length,
        totalQuestions,
        hasAnsweredAll: Object.keys(newAnswers).length === totalQuestions
      });
      return newAnswers;
    });
  }, [currentQuestionIndex, totalQuestions]);

  const handleNextQuestion = useCallback(() => {
    const nextIndex = Math.min(currentQuestionIndex + 1, totalQuestions - 1);
    console.log('Navigation - Next:', {
      currentIndex: currentQuestionIndex,
      nextIndex,
      totalQuestions,
      isLastQuestion: nextIndex >= totalQuestions - 1,
      questions: questions.length,
      hasAnsweredCurrentQuestion: Boolean(selectedAnswers[currentQuestionIndex])
    });
    setCurrentQuestionIndex(nextIndex);
  }, [currentQuestionIndex, totalQuestions, questions, selectedAnswers]);

  const handlePreviousQuestion = useCallback(() => {
    const prevIndex = Math.max(currentQuestionIndex - 1, 0);
    console.log('Navigation - Previous:', {
      currentIndex: currentQuestionIndex,
      prevIndex,
      totalQuestions,
      questions: questions.length
    });
    setCurrentQuestionIndex(prevIndex);
  }, [currentQuestionIndex, totalQuestions, questions]);

  const handleQuizSubmit = useCallback(() => {
    setShowResults(true);
  }, []);

  // Render functions
  const renderUrlInput = () => (
    <Box sx={{ mb: 4 }}>
      <TextField
        fullWidth
        label="YouTube Video URL"
        value={videoUrl}
        onChange={(e) => setVideoUrl(e.target.value)}
        disabled={getQuestions.isPending}
        error={getQuestions.isError}
        helperText={getQuestions.isError ? getQuestions.error?.message : ''}
        sx={{ mb: 2 }}
      />
      <Button
        variant="contained"
        onClick={handleUrlSubmit}
        disabled={getQuestions.isPending || !videoUrl.trim()}
      >
        {getQuestions.isPending ? 'Loading Content...' : 'Load Content'}
      </Button>
    </Box>
  );

  const renderQuestion = () => {
    console.log("Rendering Question:", {
      currentIndex: currentQuestionIndex,
      totalQuestions,
      currentQuestion,
      selectedAnswer: selectedAnswers[currentQuestionIndex] || "None",
      showResults,
      hasAnsweredCurrentQuestion,
    });
  
    if (!currentQuestion) return null;
  
    return (
      <Box sx={{ mb: 4 }}>
        {/* Debug Info Box */}
        <Paper sx={{ p: 2, mb: 3, bgcolor: '#f5f5f5' }}>
          <Typography variant="subtitle2" color="textSecondary">Debug Info:</Typography>
          <Box component="code" sx={{ display: 'block', whiteSpace: 'pre-wrap', fontSize: '0.875rem' }}>
            {`Current Question: ${currentQuestionIndex + 1}
Total Questions: ${totalQuestions}
Is Last Question: ${isLastQuestion}
Has Answered Current: ${hasAnsweredCurrentQuestion}
Selected Answer: ${selectedAnswers[currentQuestionIndex] || "None"}
Show Results: ${showResults}`}
          </Box>
        </Paper>

        <Typography variant="h6" gutterBottom>
          Question {currentQuestionIndex + 1} of {totalQuestions}
          Current Index: {currentQuestionIndex}
          Current Question: {currentQuestion}
          Selected Answer: {selectedAnswers[currentQuestionIndex]}
          ShowResults: {showResults}
          Has Answered Current: {hasAnsweredCurrentQuestion}
        </Typography>
  
        <Typography gutterBottom sx={{ direction: 'rtl', textAlign: 'right', fontSize: '1.2rem', mb: 3 }}>
          {currentQuestion.question}
        </Typography>

        <Typography variant="h6" gutterBottom>
          Question {currentQuestionIndex + 1} of {totalQuestions}
        </Typography>
  
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
                label={<Typography sx={{ direction: 'rtl', textAlign: 'right' }}>{option}</Typography>}
                disabled={showResults}
                sx={{
                  mb: 1,
                  p: 1,
                  borderRadius: 1,
                  '&:hover': { bgcolor: 'action.hover' },
                }}
              />
            ))}
          </RadioGroup>
        </FormControl>
      </Box>
    );
  };
  
  

  const renderNavigation = () => {
    // Force show submit button on last question (4 of 4)
    const showSubmitButton = currentQuestionIndex === (totalQuestions - 1);
    
    return (
      <Box sx={{ display: 'flex', gap: 2, mb: 4, justifyContent: 'space-between', alignItems: 'center' }}>
        <Button
          variant="outlined"
          onClick={handlePreviousQuestion}
          disabled={currentQuestionIndex === 0}
        >
          Previous
        </Button>
        <Typography variant="body2" color="text.secondary">
          Question {currentQuestionIndex + 1} of {totalQuestions}
        </Typography>
        {showSubmitButton ? (
          <Button
            variant="contained"
            onClick={handleQuizSubmit}
            disabled={!hasAnsweredCurrentQuestion}
            color="success"
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
    );
  };

  const renderResults = () => {
    if (!showResults) return null;

    const score = Object.entries(selectedAnswers).reduce((acc, [index, answer]) => {
      const question = questions[parseInt(index)];
      return acc + (answer === question.correct_answer ? 1 : 0);
    }, 0);

    return (
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Quiz Results
        </Typography>
        <Typography variant="h5" gutterBottom>
          Your Score: {score} out of {totalQuestions} ({Math.round(score / totalQuestions * 100)}%)
        </Typography>
        {questions.map((question, index) => {
          const isCorrect = selectedAnswers[index] === question.correct_answer;
          return (
            <Box key={index} sx={{ mb: 2, p: 2, bgcolor: 'rgba(255, 192, 203, 0.2)', borderRadius: 1 }}>
              <Typography variant="subtitle1" sx={{ mb: 1 }}>
                {question.question}
              </Typography>
              <Typography color={isCorrect ? "success.main" : "error.main"}>
                Your answer: {selectedAnswers[index]}
              </Typography>
              {!isCorrect && (
                <Typography color="success.main" sx={{ mt: 1 }}>
                  Correct answer: {question.correct_answer}
                </Typography>
              )}
            </Box>
          );
        })}
        <Button
          variant="contained"
          onClick={() => {
            setVideoUrl('');
            setCurrentQuestionIndex(0);
            setSelectedAnswers({});
            setShowResults(false);
            getQuestions.reset();
          }}
          sx={{ mt: 2 }}
        >
          Try Another Video
        </Button>
      </Paper>
    );
  };

  const renderTranscript = () => {
    if (!transcript) return null;
    return (
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="body1" component="pre" sx={{ 
          whiteSpace: 'pre-wrap',
          direction: 'rtl',
          textAlign: 'right',
          fontFamily: 'inherit'
        }}>
          {transcript.transcript}
        </Typography>
      </Paper>
    );
  };

  const renderStatistics = () => {
    if (!transcript) return null;
    return (
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>Statistics</Typography>
        <Typography>Duration: {transcript.total_duration}s</Typography>
        <Typography>Word Count: {transcript.word_count}</Typography>
        <Typography>Average Words per Minute: {transcript.words_per_minute}</Typography>
      </Paper>
    );
  };

  const renderDebugInfo = () => (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>Debug Information</Typography>
      <pre style={{ whiteSpace: 'pre-wrap', overflow: 'auto', backgroundColor: '#f5f5f5', padding: '1rem', borderRadius: '4px' }}>
        {JSON.stringify({
          currentIndex: currentQuestionIndex,
          totalQuestions,
          currentQuestion: currentQuestion ? {
            question: currentQuestion.question,
            options: currentQuestion.options
          } : null,
          selectedAnswer: selectedAnswers[currentQuestionIndex] || "None",
          showResults,
          hasAnsweredCurrentQuestion,
          isLastQuestion
        }, null, 2)}
      </pre>
    </Paper>
  );

  // Handle error state
  if (getQuestions.data?.error) {
    return (
      <Box sx={{ maxWidth: 800, mx: 'auto', p: 3 }}>
        <Typography variant="h4" gutterBottom>
          Urdu Listening Practice
        </Typography>
        {renderUrlInput()}
        <Alert severity="error" sx={{ mt: 2 }}>
          {getQuestions.data.error}
          <Button
            variant="contained"
            onClick={() => {
              setVideoUrl('');
              getQuestions.reset();
            }}
            sx={{ mt: 2, display: 'block' }}
          >
            Try Again
          </Button>
        </Alert>
      </Box>
    );
  }

  // Main render
  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Urdu Listening Practice
      </Typography>

      {renderUrlInput()}

      {(getQuestions.isPending || getTranscript.isPending) && (
        <Box sx={{ textAlign: 'center', my: 4 }}>
          <CircularProgress />
          <Typography sx={{ mt: 2 }}>
            Loading content...
          </Typography>
        </Box>
      )}

      {(getQuestions.isError || getTranscript.isError) && (
        <Alert severity="error" sx={{ mb: 4 }}>
          {getQuestions.error?.message || getTranscript.error?.message || 'Failed to load content'}
        </Alert>
      )}

      {getQuestions.isSuccess && questions.length > 0 && (
        <Box sx={{ width: '100%', mb: 4 }}>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs 
              value={currentTab} 
              onChange={(_, newValue) => setCurrentTab(newValue)}
              aria-label="listening practice tabs"
            >
              <Tab label="Questions" />
              <Tab label="Transcript" />
              <Tab label="Statistics" />
              <Tab label="Debug Info" />
            </Tabs>
          </Box>
          <TabPanel value={currentTab} index={0}>
            {renderQuestion()}
            {renderNavigation()}
            {renderResults()}
          </TabPanel>
          <TabPanel value={currentTab} index={1}>
            {renderTranscript()}
          </TabPanel>
          <TabPanel value={currentTab} index={2}>
            {renderStatistics()}
          </TabPanel>
          <TabPanel value={currentTab} index={3}>
            {renderDebugInfo()}
          </TabPanel>
        </Box>
      )}

      {getQuestions.isSuccess && questions.length === 0 && (
        <Alert severity="warning">
          No questions could be generated for this video. Please try another video.
        </Alert>
      )}
    </Box>
  );
};

export default ListeningPractice;
