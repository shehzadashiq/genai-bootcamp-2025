import React, { useState, useCallback } from 'react';
import { Box, TextField, Typography, Alert, AlertTitle, InputAdornment, IconButton, LinearProgress, List, ListItem, ListItemText, Container, Grid, Slider, Select, MenuItem, InputLabel, FormHelperText, FormControl } from '@mui/material';
import { useMutation } from '@tanstack/react-query';
import api from '../../api/config';
import SearchIcon from '@mui/icons-material/Search';
import { TabContext, TabList, TabPanel } from '@mui/lab';
import { Tab } from '@mui/material';
import axios from 'axios';
import { extractVideoId } from '../../utils/youtube';
import QuestionCard from './QuestionCard';

interface TranscriptSegment {
  text: string;
  start: number;
  duration: number;
}

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

interface ErrorState {
  message: string;
  code: string;
  details: string[] | null;
}

interface TranscriptResponse {
  data: {
    status: string;
    transcript?: TranscriptSegment[];
    metadata?: {
      video_id: string;
      language: string;
      duration: number;
      word_count: number;
      segment_count: number;
    };
    message?: string;
    code?: string;
  };
}

interface QuestionResponse {
  data: {
    status: string;
    questions?: Question[];
    metadata?: {
      video_id: string;
      count: number;
      generated_at: string;
      source: string;
      model: string;
      similarity_threshold?: number;
      language?: string;
      embedding_model?: string;
    };
    message?: string;
    code?: string;
    required_permissions?: string[];
  };
}

export default function ListeningPractice() {
  // State management
  const [videoInput, setVideoInput] = useState('');
  const [videoUrl, setVideoUrl] = useState('');
  const [showResults, setShowResults] = useState(false);
  const [currentTab, setCurrentTab] = useState<string>('0');
  const [currentQuestionTab, setCurrentQuestionTab] = useState<string>('0');
  const [transcript, setTranscript] = useState<TranscriptSegment[] | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [error, setError] = useState<ErrorState | null>(null);
  const [loading, setLoading] = useState(false);
  const [language, setLanguage] = useState('en');
  const [similarityThreshold, setSimilarityThreshold] = useState(0.7);

  // API mutations
  const downloadTranscript = useMutation<TranscriptResponse, Error, { videoId: string; language: string }>({
    mutationFn: ({ videoId, language }) =>
      api.post('/api/transcript/', { video_id: videoId, language })
  });

  const getQuestions = useMutation<QuestionResponse, Error, { videoId: string; language: string; similarityThreshold: number }>({
    mutationFn: ({ videoId, language, similarityThreshold }) =>
      api.post('/api/questions/', {
        video_id: videoId,
        language,
        similarity_threshold: similarityThreshold
      })
  });

  // Event handlers
  const handleTabChange = (_event: React.SyntheticEvent, newValue: string) => {
    setCurrentTab(newValue);
  };

  const handleQuestionTabChange = (_event: React.SyntheticEvent, newValue: string) => {
    setCurrentQuestionTab(newValue);
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter') {
      handleSubmit();
    }
  };

  const handleSubmit = useCallback(async () => {
    setError(null);
    setLoading(true);
    setTranscript(null);
    setQuestions([]);

    const videoId = extractVideoId(videoInput);
    if (!videoId) {
      setError({
        message: 'Invalid YouTube URL or video ID',
        code: 'INVALID_VIDEO_ID',
        details: ['Please enter a valid YouTube URL or video ID']
      });
      setLoading(false);
      return;
    }

    try {
      const transcriptResponse = await downloadTranscript.mutateAsync({
        videoId,
        language
      });

      if (transcriptResponse.data.status === 'error') {
        throw new Error(transcriptResponse.data.message || 'Failed to download transcript');
      }

      if (!transcriptResponse.data.transcript) {
        throw new Error('No transcript data received');
      }

      setTranscript(transcriptResponse.data.transcript);
      setVideoUrl(`https://www.youtube.com/watch?v=${videoId}`);

      const questionsResponse = await getQuestions.mutateAsync({
        videoId,
        language,
        similarityThreshold
      });

      if (questionsResponse.data.status === 'error') {
        throw new Error(questionsResponse.data.message || 'Failed to generate questions');
      }

      if (!questionsResponse.data.questions) {
        throw new Error('No questions data received');
      }

      setQuestions(questionsResponse.data.questions);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const errorMessage = err.response?.data?.message || err.message;
        const errorCode = err.response?.data?.code || 'UNKNOWN_ERROR';
        const errorDetails = err.response?.data?.details || null;
        
        setError({
          message: errorMessage,
          code: errorCode,
          details: errorDetails
        });
      } else {
        setError({
          message: err instanceof Error ? err.message : 'An unknown error occurred',
          code: 'UNKNOWN_ERROR',
          details: null
        });
      }
    } finally {
      setLoading(false);
    }
  }, [videoInput, language, similarityThreshold, downloadTranscript, getQuestions]);

  // Render functions
  const renderSettings = () => (
    <Grid container spacing={2} sx={{ mb: 3 }}>
      <Grid item xs={12} sm={6}>
        <FormControl fullWidth>
          <InputLabel id="language-select-label">Language</InputLabel>
          <Select
            labelId="language-select-label"
            value={language}
            label="Language"
            onChange={(e) => setLanguage(e.target.value)}
            disabled={loading}
          >
            <MenuItem value="en">English</MenuItem>
            <MenuItem value="es">Spanish</MenuItem>
            <MenuItem value="fr">French</MenuItem>
            <MenuItem value="de">German</MenuItem>
            <MenuItem value="it">Italian</MenuItem>
            <MenuItem value="pt">Portuguese</MenuItem>
            <MenuItem value="nl">Dutch</MenuItem>
            <MenuItem value="pl">Polish</MenuItem>
            <MenuItem value="ru">Russian</MenuItem>
            <MenuItem value="ja">Japanese</MenuItem>
            <MenuItem value="ko">Korean</MenuItem>
            <MenuItem value="zh">Chinese</MenuItem>
          </Select>
          <FormHelperText>Select the language of the video transcript</FormHelperText>
        </FormControl>
      </Grid>
      <Grid item xs={12} sm={6}>
        <Box>
          <Typography gutterBottom>Similarity Threshold: {similarityThreshold}</Typography>
          <Slider
            value={similarityThreshold}
            onChange={(_event, value) => setSimilarityThreshold(value as number)}
            min={0}
            max={1}
            step={0.1}
            marks
            disabled={loading}
            aria-label="Similarity Threshold"
          />
          <FormHelperText>
            Adjust how closely questions should match the transcript content (higher = more relevant but fewer questions)
          </FormHelperText>
        </Box>
      </Grid>
    </Grid>
  );

  // Display loading state
  const renderLoading = () => {
    if (!loading) return null;
    return (
      <Box sx={{ width: '100%', mt: 2, mb: 2 }}>
        <LinearProgress />
        <Typography variant="body2" color="text.secondary" align="center" sx={{ mt: 1 }}>
          {questions.length > 0 ? 'Generating more questions...' : 'Generating questions...'}
        </Typography>
      </Box>
    );
  };

  // Display error state
  const renderError = () => {
    if (!error) return null;
    return (
      <Alert
        severity="error"
        onClose={() => setError(null)}
        sx={{ mb: 4 }}
      >
        <AlertTitle>Error</AlertTitle>
        {error.message}
        {error.details && error.details.length > 0 && (
          <Box sx={{ mt: 1 }}>
            <Typography variant="caption" component="div">Required permissions:</Typography>
            <List dense>
              {error.details.map((permission, index) => (
                <ListItem key={index}>
                  <ListItemText
                    primary={permission}
                    primaryTypographyProps={{ variant: 'caption' }}
                  />
                </ListItem>
              ))}
            </List>
          </Box>
        )}
      </Alert>
    );
  };

  // Render transcript
  const renderTranscript = () => {
    if (!transcript) {
      return (
        <Alert severity="info">
          <AlertTitle>No Transcript</AlertTitle>
          Enter a YouTube URL to view the transcript
        </Alert>
      );
    }

    return (
      <List>
        {transcript.map((segment, index) => (
          <ListItem key={index} divider>
            <ListItemText
              primary={segment.text}
              secondary={`${Math.floor(segment.start)}s - ${Math.floor(segment.start + segment.duration)}s`}
            />
          </ListItem>
        ))}
      </List>
    );
  };

  // Render statistics
  const renderStatistics = () => {
    if (!transcript) return null;

    const totalDuration = transcript.reduce((acc, segment) => acc + segment.duration, 0);
    const wordCount = transcript.reduce((acc, segment) => acc + segment.text.split(/\s+/).length, 0);
    const segmentCount = transcript.length;

    return (
      <List>
        <ListItem>
          <ListItemText primary="Duration" secondary={`${Math.floor(totalDuration)} seconds`} />
        </ListItem>
        <ListItem>
          <ListItemText primary="Word Count" secondary={wordCount} />
        </ListItem>
        <ListItem>
          <ListItemText primary="Segment Count" secondary={segmentCount} />
        </ListItem>
      </List>
    );
  };

  // Render debug info
  const renderDebugInfo = () => {
    if (!transcript || !questions.length) return null;

    return (
      <List>
        <ListItem>
          <ListItemText
            primary="Video URL"
            secondary={videoUrl}
          />
        </ListItem>
        <ListItem>
          <ListItemText
            primary="Language"
            secondary={language}
          />
        </ListItem>
        <ListItem>
          <ListItemText
            primary="Similarity Threshold"
            secondary={similarityThreshold}
          />
        </ListItem>
        <ListItem>
          <ListItemText
            primary="Questions Generated"
            secondary={questions.length}
          />
        </ListItem>
      </List>
    );
  };

  return (
    <Container maxWidth="md">
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Listening Practice
        </Typography>
        
        {/* Settings */}
        {renderSettings()}
        
        {/* Video URL input */}
        <TextField
          fullWidth
          label="YouTube Video URL"
          variant="outlined"
          value={videoInput}
          onChange={(e) => setVideoInput(e.target.value)}
          onKeyDown={handleKeyPress}
          error={Boolean(error)}
          helperText={error?.message || ''}
          disabled={loading}
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton
                  onClick={handleSubmit}
                  disabled={!videoInput.trim() || loading}
                >
                  <SearchIcon />
                </IconButton>
              </InputAdornment>
            ),
          }}
          sx={{ mb: 2 }}
        />
        
        {/* Loading and error states */}
        {renderLoading()}
        {renderError()}
        
        {/* Results */}
        {questions.length > 0 && (
          <Box sx={{ width: '100%', typography: 'body1' }}>
            <TabContext value={currentTab}>
              <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                <TabList
                  onChange={handleTabChange}
                  aria-label="content tabs"
                  variant="scrollable"
                  scrollButtons="auto"
                >
                  <Tab label="Questions" value="0" />
                  <Tab label="Transcript" value="1" />
                  <Tab label="Statistics" value="2" />
                  <Tab label="Debug Info" value="3" />
                </TabList>
              </Box>
              
              <TabPanel value="0">
                <Box sx={{ width: '100%', typography: 'body1' }}>
                  <TabContext value={currentQuestionTab}>
                    <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                      <TabList
                        onChange={handleQuestionTabChange}
                        aria-label="question tabs"
                        variant="scrollable"
                        scrollButtons="auto"
                      >
                        {questions.map((_, index) => (
                          <Tab
                            key={index}
                            label={`Question ${index + 1}`}
                            value={index.toString()}
                          />
                        ))}
                      </TabList>
                    </Box>
                    {questions.map((question, index) => (
                      <TabPanel key={index} value={index.toString()}>
                        <QuestionCard
                          question={question}
                          showResults={showResults}
                          onShowResults={() => setShowResults(true)}
                        />
                      </TabPanel>
                    ))}
                  </TabContext>
                </Box>
              </TabPanel>
              
              <TabPanel value="1">
                {renderTranscript()}
              </TabPanel>
              
              <TabPanel value="2">
                {renderStatistics()}
              </TabPanel>
              
              <TabPanel value="3">
                {renderDebugInfo()}
              </TabPanel>
            </TabContext>
          </Box>
        )}

        {/* No questions generated */}
        {!loading && questions.length === 0 && transcript && (
          <Alert severity="warning">
            No questions could be generated for this video. Please try another video or adjust the similarity threshold.
          </Alert>
        )}
      </Box>
    </Container>
  );
}
