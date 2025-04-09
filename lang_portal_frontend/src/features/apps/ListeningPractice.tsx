import { useState, useRef, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

interface Question {
  question: string
  timestamp: number
  text: string
  options: string[]
  correct_answer: string
  audio_start: number
  audio_end: number
  explanation: string
}

interface TranscriptSegment {
  start: number
  duration: number
  text: string
}

interface Statistics {
  total_duration: number
  total_words: number
  avg_words_per_minute: number
  segments_count: number
  top_words: Record<string, number>
}

export default function ListeningPractice() {
  const [videoUrl, setVideoUrl] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [questions, setQuestions] = useState<Question[]>([])
  const [transcript, setTranscript] = useState<TranscriptSegment[]>([])
  const [statistics, setStatistics] = useState<Statistics | null>(null)
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, string>>({})
  const [downloadStatus, setDownloadStatus] = useState<string>('')
  const [videoId, setVideoId] = useState<string>('')
  const [showResults, setShowResults] = useState(false)
  const [score, setScore] = useState(0)
  const playerContainerRef = useRef<HTMLDivElement>(null)
  const playerTimerRef = useRef<number | null>(null)

  const handleSubmitUrl = async () => {
    try {
      setIsLoading(true)
      setError(null)
      setDownloadStatus('Downloading transcript...')
      setQuestions([])
      setTranscript([])
      setStatistics(null)
      setCurrentQuestionIndex(0)
      setSelectedAnswers({})
      
      // Extract video ID from URL
      const videoIdMatch = videoUrl.match(/(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})/)
      const extractedVideoId = videoIdMatch ? videoIdMatch[1] : ''
      
      if (!extractedVideoId) {
        throw new Error('Invalid YouTube URL')
      }
      
      setVideoId(extractedVideoId)

      const requestData = { url: videoUrl }
      console.log('Sending request with data:', requestData)

      // First, download the transcript
      const downloadResponse = await fetch(`${import.meta.env.VITE_API_URL}/api/listening/download-transcript`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      })

      if (!downloadResponse.ok) {
        const errorData = await downloadResponse.json()
        throw new Error(errorData.message || 'Failed to download transcript')
      }

      const downloadData = await downloadResponse.json()
      console.log('Download response:', downloadData)

      // Then, generate questions
      setDownloadStatus('Generating questions...')
      const questionsResponse = await fetch(`${import.meta.env.VITE_API_URL}/api/listening/questions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      })

      if (!questionsResponse.ok) {
        const errorData = await questionsResponse.json()
        throw new Error(errorData.message || 'Failed to generate questions')
      }

      const questionsData = await questionsResponse.json()
      console.log('Questions response:', questionsData)
      setQuestions(questionsData.questions)

      // Finally, get the transcript
      setDownloadStatus('Retrieving transcript...')
      const transcriptResponse = await fetch(`${import.meta.env.VITE_API_URL}/api/listening/transcript`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      })

      if (!transcriptResponse.ok) {
        const errorData = await transcriptResponse.json()
        throw new Error(errorData.message || 'Failed to retrieve transcript')
      }

      const transcriptData = await transcriptResponse.json()
      console.log('Transcript response:', transcriptData)
      setTranscript(transcriptData.transcript)
      setStatistics(transcriptData.statistics)
      setDownloadStatus('')

    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
      setDownloadStatus('')
    } finally {
      setIsLoading(false)
    }
  }

  const handleAnswerSelect = (value: string) => {
    console.log({
      questionIndex: currentQuestionIndex,
      value: value
    });

    setSelectedAnswers(prev => ({
      ...prev,
      [currentQuestionIndex]: value
    }));
  }

  const handleNextQuestion = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    }
  }

  const handlePreviousQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
    }
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }

  // Update the iframe when the current question changes
  useEffect(() => {
    if (videoId && playerContainerRef.current && questions.length > 0) {
      updateYouTubeEmbed();
    }
  }, [videoId, currentQuestionIndex, questions]);

  const updateYouTubeEmbed = () => {
    if (!playerContainerRef.current || !videoId || questions.length === 0) return;
    
    // Clear any existing timer
    if (playerTimerRef.current) {
      clearTimeout(playerTimerRef.current);
    }
    
    // Create the embed URL with controls
    const embedUrl = `https://www.youtube.com/embed/${videoId}?rel=0&modestbranding=1&controls=1`;
    
    // Create the iframe
    const iframe = document.createElement('iframe');
    iframe.width = '100%';
    iframe.height = '100%';
    iframe.src = embedUrl;
    iframe.title = 'YouTube video player';
    iframe.frameBorder = '0';
    iframe.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture';
    iframe.allowFullscreen = true;
    
    // Clear the container and append the iframe
    playerContainerRef.current.innerHTML = '';
    playerContainerRef.current.appendChild(iframe);
  }

  const checkAnswers = () => {
    const totalCorrect = questions.reduce((acc, question, index) => {
      const isCorrect = selectedAnswers[index] === String(question.correct_answer)
      return acc + (isCorrect ? 1 : 0)
    }, 0)
    
    setScore(totalCorrect)
    setShowResults(true)
    return totalCorrect
  }

  return (
    <div className="container mx-auto py-8">
      <Card>
        <CardHeader>
          <CardTitle>Listening Practice</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Enter YouTube URL"
                className="flex-1 px-3 py-2 border rounded-md"
                value={videoUrl}
                onChange={(e) => setVideoUrl(e.target.value)}
              />
              <Button onClick={handleSubmitUrl} disabled={isLoading}>
                {isLoading ? 'Loading...' : 'Start Practice'}
              </Button>
            </div>
            {error && <div className="text-red-500">{error}</div>}
            {downloadStatus && <div className="text-blue-500">{downloadStatus}</div>}
          </div>
        </CardContent>
      </Card>

      {questions.length > 0 && (
        <Tabs defaultValue="practice" className="mt-6">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="practice">Practice</TabsTrigger>
            <TabsTrigger value="transcript">Transcript</TabsTrigger>
            <TabsTrigger value="statistics">Statistics</TabsTrigger>
          </TabsList>

          <TabsContent value="practice">
            <Card>
              <CardHeader>
                <CardTitle>Question {currentQuestionIndex + 1} of {questions.length}</CardTitle>
              </CardHeader>
              <CardContent>
                {videoId && (
                  <>
                    <div className="space-y-6 mb-6">
                      {showResults ? (
                        <div className="space-y-4">
                          <h3 className="text-xl font-semibold">Quiz Results</h3>
                          <p className="text-lg font-medium mb-4">Your Score: {score} out of {questions.length}</p>
                          
                          <div className="space-y-4">
                            {questions.map((question, index) => {
                              const userAnswer = selectedAnswers[index];
                              const isCorrect = userAnswer === String(question.correct_answer);
                              
                              return (
                                <div 
                                  key={index} 
                                  className={`p-4 rounded-md ${isCorrect ? 'bg-green-50' : 'bg-red-50'}`}
                                >
                                  <p className="font-medium">{question.question}</p>
                                  <p className="text-sm text-gray-500 mt-1">Transcript: {question.text}</p>
                                  <p className="mt-2">
                                    Your answer: {question.options[parseInt(userAnswer)]}
                                  </p>
                                  {!isCorrect && (
                                    <p className="text-sm text-red-500 mt-1">
                                      Correct answer: {question.options[parseInt(question.correct_answer)]}
                                    </p>
                                  )}
                                  <div className="flex justify-end">
                                    {isCorrect ? (
                                      <span className="text-green-600">✓</span>
                                    ) : (
                                      <span className="text-red-600">✗</span>
                                    )}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                          
                          <Button 
                            className="mt-4"
                            onClick={() => {
                              setShowResults(false)
                              setSelectedAnswers({})
                              setCurrentQuestionIndex(0)
                            }}
                          >
                            Try Again
                          </Button>
                        </div>
                      ) : (
                        <>
                          <h3 className="text-lg font-medium">
                            Question {currentQuestionIndex + 1} of {questions.length}
                          </h3>
                          <div className="space-y-2">
                            <div className="flex justify-between items-center">
                              <p className="font-medium">{questions[currentQuestionIndex].question}</p>
                            </div>
                            <p className="text-sm text-muted-foreground">
                              Transcript: {questions[currentQuestionIndex].text}
                            </p>
                          </div>

                          <div className="space-y-2">
                            {questions[currentQuestionIndex].options.map((option, index) => (
                              <label
                                key={index}
                                className="flex items-center space-x-2 p-2 rounded hover:bg-muted cursor-pointer"
                              >
                                <input
                                  type="radio"
                                  name="answer"
                                  value={String(index)}
                                  checked={selectedAnswers[currentQuestionIndex] === String(index)}
                                  onChange={(e) => handleAnswerSelect(e.target.value)}
                                  className="h-4 w-4"
                                />
                                <span>{option}</span>
                              </label>
                            ))}
                          </div>
                        </>
                      )}
                    </div>

                    <div className="mt-8">
                      <div 
                        ref={playerContainerRef} 
                        className="w-full aspect-video mb-4"
                      >
                        {/* YouTube iframe will be inserted here */}
                      </div>
                    </div>

                    {!showResults && (
                      <div className="flex justify-between pt-4">
                        <Button
                          variant="outline"
                          onClick={handlePreviousQuestion}
                          disabled={currentQuestionIndex === 0}
                        >
                          Previous
                        </Button>
                        {currentQuestionIndex === questions.length - 1 ? (
                          <Button
                            onClick={checkAnswers}
                            disabled={!selectedAnswers[currentQuestionIndex]}
                          >
                            Submit
                          </Button>
                        ) : (
                          <Button
                            onClick={handleNextQuestion}
                            disabled={!selectedAnswers[currentQuestionIndex]}
                          >
                            Next
                          </Button>
                        )}
                      </div>
                    )}
                  </>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="transcript">
            <Card>
              <CardHeader>
                <CardTitle>Video Transcript</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4 max-h-[500px] overflow-y-auto">
                  {transcript.map((segment, index) => (
                    <div key={index} className="p-2 hover:bg-muted rounded">
                      <div className="text-sm text-muted-foreground mb-1">
                        {formatTime(segment.start)}
                      </div>
                      <div>{segment.text}</div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="statistics">
            {statistics && (
              <Card>
                <CardHeader>
                  <CardTitle>Video Statistics</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <h3 className="font-semibold">Duration</h3>
                      <p>{formatTime(statistics.total_duration)}</p>
                    </div>
                    <div>
                      <h3 className="font-semibold">Word Count</h3>
                      <p>{statistics.total_words} words</p>
                    </div>
                    <div>
                      <h3 className="font-semibold">Speaking Speed</h3>
                      <p>{statistics.avg_words_per_minute} words per minute</p>
                    </div>
                    <div>
                      <h3 className="font-semibold">Segments</h3>
                      <p>{statistics.segments_count} segments</p>
                    </div>
                    <div>
                      <h3 className="font-semibold">Most Common Words</h3>
                      <div className="grid grid-cols-2 gap-2">
                        {Object.entries(statistics.top_words).map(([word, count]) => (
                          <div key={word} className="flex justify-between">
                            <span>{word}</span>
                            <span className="text-muted-foreground">{count}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      )}
    </div>
  )
}
