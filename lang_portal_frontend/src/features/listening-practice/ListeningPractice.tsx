import React, { useState } from 'react';
import { Box, Button, TextField, Typography, Card, CardContent, Radio, RadioGroup, FormControlLabel, FormControl } from '@mui/material';
import { useQuery, useMutation } from '@tanstack/react-query';
import axios from 'axios';

interface Question {
  question: string;
  timestamp: number;
  text: string;
  options: string[];
  correct_answer: string;
}

interface QuestionResponse {
  questions: Question[];
}

const ListeningPractice: React.FC = () => {
  const [videoUrl, setVideoUrl] = useState('');
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, string>>({});

  const getQuestions = useMutation({
    mutationFn: async (url: string) => {
      const response = await axios.post<QuestionResponse>('/api/listening/questions', { url });
      return response.data;
    },
  });

  const handleSubmitUrl = () => {
    getQuestions.mutate(videoUrl);
  };

  const handleAnswerSelect = (value: string) => {
    setSelectedAnswers(prev => ({
      ...prev,
      [currentQuestionIndex]: value
    }));
  };

  const handleNextQuestion = () => {
    if (currentQuestionIndex < (getQuestions.data?.questions.length || 0) - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
    }
  };

  const handlePreviousQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1);
    }
  };

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Listening Practice
      </Typography>

      <Box sx={{ mb: 4 }}>
        <TextField
          fullWidth
          label="YouTube Video URL"
          value={videoUrl}
          onChange={(e) => setVideoUrl(e.target.value)}
          sx={{ mb: 2 }}
        />
        <Button
          variant="contained"
          onClick={handleSubmitUrl}
          disabled={getQuestions.isPending}
        >
          Load Questions
        </Button>
      </Box>

      {getQuestions.data?.questions && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Question {currentQuestionIndex + 1} of {getQuestions.data.questions.length}
            </Typography>
            
            <Typography variant="body1" sx={{ mb: 2 }}>
              {getQuestions.data.questions[currentQuestionIndex].question}
            </Typography>

            <Typography variant="body2" sx={{ mb: 2, fontStyle: 'italic' }}>
              Transcript: {getQuestions.data.questions[currentQuestionIndex].text}
            </Typography>

            <FormControl component="fieldset">
              <RadioGroup
                value={selectedAnswers[currentQuestionIndex] || ''}
                onChange={(e) => handleAnswerSelect(e.target.value)}
              >
                {getQuestions.data.questions[currentQuestionIndex].options.map((option, index) => (
                  <FormControlLabel
                    key={index}
                    value={option}
                    control={<Radio />}
                    label={option}
                  />
                ))}
              </RadioGroup>
            </FormControl>

            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between' }}>
              <Button
                variant="outlined"
                onClick={handlePreviousQuestion}
                disabled={currentQuestionIndex === 0}
              >
                Previous
              </Button>
              <Button
                variant="contained"
                onClick={handleNextQuestion}
                disabled={currentQuestionIndex === getQuestions.data.questions.length - 1}
              >
                Next
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default ListeningPractice;
