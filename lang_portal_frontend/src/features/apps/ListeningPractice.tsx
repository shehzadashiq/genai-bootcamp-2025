import { useState, useRef, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

type Question = {
  id: number
  question: string
  options: string[]
  correct_answer: number
  text: string
  start_time: number
  end_time: number
}

export default function ListeningPractice() {
  const [youtubeUrl, setYoutubeUrl] = useState('')
  const [selectedLanguage] = useState('en')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [questions, setQuestions] = useState<Question[]>([])
  const [transcript, setTranscript] = useState<string>('')
  const [statistics, setStatistics] = useState<any>(null)
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, string>>({})
  const [downloadStatus, setDownloadStatus] = useState<string>('')
  const [videoId, setVideoId] = useState<string>('')
  const [showResults, setShowResults] = useState(false)
  const [score, setScore] = useState(0)
  const [noTranscriptError, setNoTranscriptError] = useState<boolean>(false)
  const playerContainerRef = useRef<HTMLDivElement>(null)

  // Format time in seconds to MM:SS format
  const formatTime = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = Math.floor(seconds % 60)
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
  }

  // Function to initialize the YouTube player
  const initializePlayer = (videoId: string) => {
    if (!playerContainerRef.current) return
    
    // Create an iframe element
    const iframe = document.createElement('iframe')
    iframe.width = '100%'
    iframe.height = '100%'
    iframe.src = `https://www.youtube.com/embed/${videoId}?enablejsapi=1`
    iframe.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture'
    iframe.allowFullscreen = true
    
    // Clear the container and append the iframe
    playerContainerRef.current.innerHTML = ''
    playerContainerRef.current.appendChild(iframe)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError(null)
    setNoTranscriptError(false)
    setDownloadStatus('Downloading transcript...')
    setQuestions([])
    setTranscript('')
    setStatistics(null)
    setSelectedAnswers({})
    setCurrentQuestionIndex(0)
    setShowResults(false)
    
    // Extract video ID from URL
    const videoIdMatch = youtubeUrl.match(/(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})/)
    
    if (!videoIdMatch) {
      setError('Invalid YouTube URL')
      setIsLoading(false)
      return
    }
    
    const extractedVideoId = videoIdMatch[1]
    setVideoId(extractedVideoId)
    
    // Initialize the player
    initializePlayer(extractedVideoId)

    const requestData = {
      url: youtubeUrl,
      language: selectedLanguage,
    }
    
    console.log('Sending request with data:', requestData)

    try {
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
      
      // Check if there's an error in the download response
      if (downloadData.error) {
        if (downloadData.error === 'No transcript available for this video') {
          setNoTranscriptError(true)
          setError('No transcript available for this video. Please try a different video.')
          setIsLoading(false)
          setDownloadStatus('')
          return
        } else {
          throw new Error(downloadData.error || 'Failed to download transcript')
        }
      }

      // Then, generate questions
      setDownloadStatus('Generating questions...')
      const questionsResponse = await fetch(`${import.meta.env.VITE_API_URL}/api/listening/questions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: youtubeUrl,
          language: selectedLanguage,
        }),
      })

      if (!questionsResponse.ok) {
        const errorData = await questionsResponse.json()
        throw new Error(errorData.message || 'Failed to generate questions')
      }

      const questionsData = await questionsResponse.json()
      console.log('Questions response:', questionsData)
      
      // Check if there's an error in the questions response
      if (questionsData.error) {
        if (questionsData.error === 'No transcript available for this video') {
          setNoTranscriptError(true)
          setError('No transcript available for this video. Please try a different video.')
          setIsLoading(false)
          setDownloadStatus('')
          return
        } else {
          throw new Error(questionsData.error || 'Failed to generate questions')
        }
      }
      
      // Make sure we have questions before proceeding
      if (!questionsData.questions || !Array.isArray(questionsData.questions) || questionsData.questions.length === 0) {
        throw new Error('No questions were generated. Please try a different video.')
      }
      
      setQuestions(questionsData.questions)

      // Finally, get the transcript
      setDownloadStatus('Retrieving transcript...')
      const transcriptResponse = await fetch(`${import.meta.env.VITE_API_URL}/api/listening/transcript`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: youtubeUrl,
          language: selectedLanguage,
        }),
      })

      if (!transcriptResponse.ok) {
        const errorData = await transcriptResponse.json()
        throw new Error(errorData.message || 'Failed to retrieve transcript')
      }

      const transcriptData = await transcriptResponse.json()
      console.log('Transcript response:', transcriptData)
      
      // Check if there's an error in the transcript response
      if (transcriptData.error) {
        if (transcriptData.error === 'No transcript available for this video') {
          setNoTranscriptError(true)
          setError('No transcript available for this video. Please try a different video.')
          setIsLoading(false)
          setDownloadStatus('')
          return
        } else {
          throw new Error(transcriptData.error || 'Failed to retrieve transcript')
        }
      }
      
      setTranscript(transcriptData.transcript)
      setStatistics(transcriptData.statistics)
      setDownloadStatus('')
      setIsLoading(false)

    } catch (err) {
      console.error('Error:', err)
      setError(err instanceof Error ? err.message : 'An error occurred')
      setIsLoading(false)
      setDownloadStatus('')
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

  const updateYouTubeEmbed = () => {
    if (!playerContainerRef.current || !videoId || !questions || questions.length === 0) return;
    
    const currentQuestion = questions[currentQuestionIndex];
    if (!currentQuestion) return;
    
    const startTime = currentQuestion.start_time || 0;
    
    // Create an iframe element
    const iframe = document.createElement('iframe');
    iframe.width = '100%';
    iframe.height = '100%';
    iframe.src = `https://www.youtube.com/embed/${videoId}?start=${startTime}&enablejsapi=1`;
    iframe.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture';
    iframe.allowFullscreen = true;
    
    // Clear the container and append the iframe
    playerContainerRef.current.innerHTML = '';
    playerContainerRef.current.appendChild(iframe);
  }

  useEffect(() => {
    if (videoId && playerContainerRef.current && questions && questions.length > 0) {
      updateYouTubeEmbed();
    } else if (videoId && playerContainerRef.current && noTranscriptError) {
      // If there's no transcript but we have a video ID, still show the YouTube player
      const iframe = document.createElement('iframe');
      iframe.width = '100%';
      iframe.height = '100%';
      iframe.src = `https://www.youtube.com/embed/${videoId}?enablejsapi=1`;
      iframe.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture';
      iframe.allowFullscreen = true;
      
      // Clear the container and append the iframe
      playerContainerRef.current.innerHTML = '';
      playerContainerRef.current.appendChild(iframe);
    }
  }, [videoId, currentQuestionIndex, questions, noTranscriptError]);

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
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700" htmlFor="youtube-url">YouTube URL</label>
              <input
                id="youtube-url"
                placeholder="https://www.youtube.com/watch?v=..."
                value={youtubeUrl}
                onChange={(e) => setYoutubeUrl(e.target.value)}
                required
                className="block w-full p-2 pl-10 text-sm text-gray-700 rounded-lg border border-gray-200 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <Button type="submit" disabled={isLoading}>
              {isLoading ? 'Loading...' : 'Start Practice'}
            </Button>

            {error && <div className="text-red-500 mt-2">{error}</div>}
            {downloadStatus && <div className="text-blue-500 mt-2">{downloadStatus}</div>}
          </form>
        </CardContent>
      </Card>

      {noTranscriptError && videoId && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>No Transcript Available</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <p>Unfortunately, this video does not have a transcript available. This could be because:</p>
              <ul className="list-disc pl-6 space-y-2">
                <li>The video owner has not provided captions</li>
                <li>The captions are not available in the selected language</li>
                <li>The video uses automatic captions which may not be accessible via the API</li>
              </ul>
              <p>You can still watch the video below, but the listening practice exercise cannot be created.</p>
              
              <div 
                ref={playerContainerRef} 
                className="w-full aspect-video mt-4"
              >
                {/* YouTube iframe will be inserted here */}
              </div>
              
              <Button onClick={() => {
                setYoutubeUrl('')
                setVideoId('')
                setNoTranscriptError(false)
                setError(null)
              }}>
                Try Another Video
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

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
                                    Your answer: {question.options[parseInt(userAnswer || '0')]}
                                  </p>
                                  {!isCorrect && (
                                    <p className="text-sm text-red-500 mt-1">
                                      Correct answer: {question.options[question.correct_answer]}
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
                  {transcript && typeof transcript === 'string' && transcript.split('\n').map((line, index) => (
                    <div key={index} className="p-2 hover:bg-muted rounded">
                      <div className="text-sm text-muted-foreground mb-1">
                        {formatTime(index * 5)}
                      </div>
                      <div>{line}</div>
                    </div>
                  ))}
                  {statistics && (
                    <div className="mt-4 p-4 bg-muted rounded">
                      <h3 className="text-lg font-medium mb-2">Statistics</h3>
                      {Object.entries(statistics).map(([key, value]) => (
                        <div key={key} className="flex justify-between py-1">
                          <span className="font-medium">{key.replace(/_/g, ' ')}</span>
                          <span>{String(value)}</span>
                        </div>
                      ))}
                    </div>
                  )}
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
                      <p>{statistics && typeof statistics.total_duration === 'number' ? formatTime(statistics.total_duration) : '0:00'}</p>
                    </div>
                    <div>
                      <h3 className="font-semibold">Word Count</h3>
                      <p>{statistics && typeof statistics.total_words === 'number' ? `${statistics.total_words} words` : '0 words'}</p>
                    </div>
                    <div>
                      <h3 className="font-semibold">Speaking Speed</h3>
                      <p>{statistics && typeof statistics.avg_words_per_minute === 'number' ? `${statistics.avg_words_per_minute} words per minute` : '0 words per minute'}</p>
                    </div>
                    <div>
                      <h3 className="font-semibold">Segments</h3>
                      <p>{statistics && typeof statistics.segments_count === 'number' ? `${statistics.segments_count} segments` : '0 segments'}</p>
                    </div>
                    <div>
                      <h3 className="font-semibold">Most Common Words</h3>
                      <div className="grid grid-cols-2 gap-2">
                        {statistics && statistics.top_words && typeof statistics.top_words === 'object' ? 
                          Object.entries(statistics.top_words).map(([word, count]) => (
                            <div key={word} className="flex justify-between">
                              <span>{word}</span>
                              <span className="text-muted-foreground">{String(count)}</span>
                            </div>
                          )) : 
                          <div className="text-muted-foreground">No data available</div>
                        }
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
