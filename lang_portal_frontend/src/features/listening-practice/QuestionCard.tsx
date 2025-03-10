import React from 'react';
import { Box, Paper, Typography, FormControl, RadioGroup, FormControlLabel, Radio, Button } from '@mui/material';

interface Question {
  id: string;
  text: string;
  options: string[];
  correctAnswer: string;
  explanation: string;
  relatedText: string;
  metadata?: {
    similarity_score?: number;
    language?: string;
    source?: string;
    timestamp?: string;
  };
}

interface QuestionCardProps {
  question: Question;
  showResults: boolean;
  onShowResults: () => void;
}

export const QuestionCard: React.FC<QuestionCardProps> = ({ question, showResults, onShowResults }) => {
  const [selectedAnswer, setSelectedAnswer] = React.useState<string>('');

  const handleAnswerChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSelectedAnswer(event.target.value);
  };

  const isCorrect = selectedAnswer === question.correctAnswer;

  return (
    <Paper sx={{ p: 3, mb: 2 }}>
      <Box>
        <Typography variant="h6" gutterBottom>
          {question.text}
        </Typography>

        <FormControl component="fieldset" sx={{ width: '100%', mb: 2 }}>
          <RadioGroup
            value={selectedAnswer}
            onChange={handleAnswerChange}
          >
            {question.options.map((option, index) => (
              <FormControlLabel
                key={index}
                value={option}
                control={<Radio />}
                label={option}
                disabled={showResults}
                sx={{
                  ...(showResults && {
                    color: option === question.correctAnswer ? 'success.main' : 
                           (option === selectedAnswer ? 'error.main' : 'text.primary')
                  })
                }}
              />
            ))}
          </RadioGroup>
        </FormControl>

        {!showResults && selectedAnswer && (
          <Button
            variant="contained"
            color="primary"
            onClick={onShowResults}
            fullWidth
          >
            Check Answer
          </Button>
        )}

        {showResults && (
          <Box sx={{ mt: 2 }}>
            <Typography
              variant="subtitle1"
              color={isCorrect ? 'success.main' : 'error.main'}
              gutterBottom
            >
              {isCorrect ? 'Correct!' : 'Incorrect'}
            </Typography>

            <Typography variant="body1" gutterBottom>
              {question.explanation}
            </Typography>

            {question.relatedText && (
              <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Related Text:
                </Typography>
                <Typography variant="body2">
                  {question.relatedText}
                </Typography>
                {question.metadata?.similarity_score && (
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                    Similarity Score: {Math.round(question.metadata.similarity_score * 100)}%
                  </Typography>
                )}
              </Box>
            )}
          </Box>
        )}
      </Box>
    </Paper>
  );
};

export default QuestionCard;
