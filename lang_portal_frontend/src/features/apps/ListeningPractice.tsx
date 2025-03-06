import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

interface Question {
  question: string
  timestamp: number
  text: string
  options: string[]
  correct_answer: string
}

interface TranscriptSegment {
  text: string
  start: number
  duration: number
}

interface Statistics {
  total_duration: number
  total_words: number
  avg_words_per_minute: number
  segments_count: number
  top_words: Record<string, number>
}

interface QuestionResponse {
  questions: Question[]
}

interface TranscriptResponse {
  transcript: TranscriptSegment[]
  statistics: Statistics
}

interface DownloadResponse {
  video_id: string
  message: string
}

export default function ListeningPractice() {
  const [videoUrl, setVideoUrl] = useState('')
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, string>>({})
  const [questions, setQuestions] = useState<Question[]>([])
  const [transcript, setTranscript] = useState<TranscriptSegment[]>([])
  const [statistics, setStatistics] = useState<Statistics | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [downloadStatus, setDownloadStatus] = useState<string>('')

  const handleSubmitUrl = async () => {
    try {
      setLoading(true)
      setError(null)
      setDownloadStatus('Downloading transcript...')

      const requestData = { url: videoUrl }
      console.log('Sending request with data:', requestData)

      // First download and store the transcript
      const downloadResponse = await fetch('http://localhost:8080/api/listening/download-transcript', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      })

      if (!downloadResponse.ok) {
        const errorData = await downloadResponse.json()
        console.error('Error response:', errorData)
        throw new Error(errorData.error || 'Failed to download transcript')
      }

      const downloadData: DownloadResponse = await downloadResponse.json()
      console.log('Download response:', downloadData)
      setDownloadStatus('Transcript downloaded successfully')

      // Then fetch questions
      setDownloadStatus('Generating questions...')
      const questionsResponse = await fetch('http://localhost:8080/api/listening/questions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      })

      if (!questionsResponse.ok) {
        const errorData = await questionsResponse.json()
        console.error('Error response:', errorData)
        throw new Error(errorData.error || 'Failed to load questions')
      }

      const questionsData: QuestionResponse = await questionsResponse.json()
      console.log('Questions response:', questionsData)
      setQuestions(questionsData.questions)

      // Finally fetch transcript and statistics
      setDownloadStatus('Loading transcript and statistics...')
      const transcriptResponse = await fetch('http://localhost:8080/api/listening/transcript', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      })

      if (!transcriptResponse.ok) {
        const errorData = await transcriptResponse.json()
        console.error('Error response:', errorData)
        throw new Error(errorData.error || 'Failed to load transcript')
      }

      const transcriptData: TranscriptResponse = await transcriptResponse.json()
      console.log('Transcript response:', transcriptData)
      setTranscript(transcriptData.transcript)
      setStatistics(transcriptData.statistics)
      setDownloadStatus('')

    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
      setDownloadStatus('')
    } finally {
      setLoading(false)
    }
  }

  const handleAnswerSelect = (value: string) => {
    setSelectedAnswers(prev => ({
      ...prev,
      [currentQuestionIndex]: value
    }))
  }

  const handleNextQuestion = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1)
    }
  }

  const handlePreviousQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1)
    }
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  if (error) {
    return (
      <div className="text-center py-8 text-red-500">
        <p>{error}</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Listening Practice</h1>

      <Card>
        <CardHeader>
          <CardTitle>Enter YouTube Video URL</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-4">
            <input
              type="text"
              className="flex-1 px-3 py-2 border rounded-md"
              value={videoUrl}
              onChange={(e) => setVideoUrl(e.target.value)}
              placeholder="https://www.youtube.com/watch?v=..."
            />
            <Button
              onClick={handleSubmitUrl}
              disabled={loading}
            >
              {loading ? 'Processing...' : 'Load Content'}
            </Button>
          </div>
          {downloadStatus && (
            <div className="text-sm text-blue-600">
              {downloadStatus}
            </div>
          )}
        </CardContent>
      </Card>

      {(questions.length > 0 || transcript.length > 0) && (
        <Tabs defaultValue="transcript" className="space-y-4">
          <TabsList>
            <TabsTrigger value="transcript">Transcript</TabsTrigger>
            <TabsTrigger value="questions">Questions</TabsTrigger>
            <TabsTrigger value="statistics">Statistics</TabsTrigger>
          </TabsList>

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

          <TabsContent value="questions">
            {questions.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>
                    Question {currentQuestionIndex + 1} of {questions.length}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div>
                    <h3 className="font-semibold mb-2">
                      {questions[currentQuestionIndex].question}
                    </h3>
                    <p className="text-muted-foreground italic">
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
                          value={option}
                          checked={selectedAnswers[currentQuestionIndex] === option}
                          onChange={() => handleAnswerSelect(option)}
                          className="h-4 w-4"
                        />
                        <span>{option}</span>
                      </label>
                    ))}
                  </div>

                  <div className="flex justify-between pt-4">
                    <Button
                      variant="outline"
                      onClick={handlePreviousQuestion}
                      disabled={currentQuestionIndex === 0}
                    >
                      Previous
                    </Button>
                    <Button
                      onClick={handleNextQuestion}
                      disabled={currentQuestionIndex === questions.length - 1}
                    >
                      Next
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
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
