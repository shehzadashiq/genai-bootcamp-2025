import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { groupsApi } from '@/services/api'

interface Group {
  id: number
  name: string
  word_count: number
}

interface QuizWord {
  id: number
  urdu: string
  options: {
    id: number
    text: string
  }[]
}

interface QuizState {
  sessionId: number
  words: QuizWord[]
  currentIndex: number
  answers: {
    word_id: number
    selected_id: number
  }[]
}

interface QuizResult {
  total_questions: number
  correct_answers: number
  score_percentage: number
}

export default function VocabularyQuiz() {
  const [groups, setGroups] = useState<Group[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedGroup, setSelectedGroup] = useState<number | null>(null)
  const [quizState, setQuizState] = useState<QuizState | null>(null)
  const [quizResult, setQuizResult] = useState<QuizResult | null>(null)

  useEffect(() => {
    const fetchGroups = async () => {
      try {
        setLoading(true)
        setError(null)
        const response = await groupsApi.getAll()
        const data = response.data
        setGroups(data.items || [])
      } catch (error) {
        console.error('Error fetching groups:', error)
        setError('Failed to load word groups')
      } finally {
        setLoading(false)
      }
    }

    fetchGroups()
  }, [])

  const startQuiz = async (groupId: number) => {
    try {
      setLoading(true)
      setError(null)
      const response = await fetch('http://localhost:8080/api/vocabulary-quiz/start/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          group_id: groupId,
          word_count: 10
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to start quiz')
      }

      const data = await response.json()
      setQuizState({
        sessionId: data.session_id,
        words: data.words,
        currentIndex: 0,
        answers: []
      })
      setSelectedGroup(groupId)
    } catch (error) {
      console.error('Error starting quiz:', error)
      setError('Failed to start quiz')
    } finally {
      setLoading(false)
    }
  }

  const submitAnswer = async (wordId: number, selectedId: number) => {
    if (!quizState) return

    const newAnswers = [
      ...quizState.answers,
      { word_id: wordId, selected_id: selectedId }
    ]

    if (quizState.currentIndex === quizState.words.length - 1) {
      // Last question, submit the quiz
      try {
        setLoading(true)
        const response = await fetch('http://localhost:8080/api/vocabulary-quiz/submit/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            session_id: quizState.sessionId,
            answers: newAnswers
          }),
        })

        if (!response.ok) {
          throw new Error('Failed to submit quiz')
        }

        const result = await response.json()
        setQuizResult(result)
        setQuizState(null)
      } catch (error) {
        console.error('Error submitting quiz:', error)
        setError('Failed to submit quiz')
      } finally {
        setLoading(false)
      }
    } else {
      // Move to next question
      setQuizState({
        ...quizState,
        currentIndex: quizState.currentIndex + 1,
        answers: newAnswers
      })
    }
  }

  const resetQuiz = () => {
    setQuizState(null)
    setQuizResult(null)
    setSelectedGroup(null)
  }

  if (loading) {
    return <div>Loading...</div>
  }

  if (error) {
    return (
      <div className="text-center py-8 text-red-500">
        <p>{error}</p>
      </div>
    )
  }

  if (quizResult) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold">Quiz Results</h1>

        <Card>
          <CardHeader>
            <CardTitle>Your Score</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-center">
              <p className="text-4xl font-bold text-primary">
                {quizResult.score_percentage.toFixed(1)}%
              </p>
              <p className="text-muted-foreground mt-2">
                {quizResult.correct_answers} correct out of {quizResult.total_questions} questions
              </p>
            </div>
            <Button className="w-full" onClick={resetQuiz}>
              Start New Quiz
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (quizState) {
    const currentWord = quizState.words[quizState.currentIndex]
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold">Vocabulary Quiz</h1>

        <Card>
          <CardHeader>
            <CardTitle>
              Question {quizState.currentIndex + 1} of {quizState.words.length}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-center mb-8">
              <p className="text-4xl font-bold mb-2">{currentWord.urdu}</p>
              <p className="text-muted-foreground">Select the correct English translation</p>
            </div>
            <div className="grid grid-cols-1 gap-3">
              {currentWord.options.map((option) => (
                <Button
                  key={option.id}
                  variant="outline"
                  className="w-full text-lg py-6"
                  onClick={() => submitAnswer(currentWord.id, option.id)}
                >
                  {option.text}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Vocabulary Quiz</h1>

      <Card>
        <CardHeader>
          <CardTitle>Select a Group</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-muted-foreground mb-4">
            Choose a word group to start your vocabulary quiz
          </p>
          <div className="grid grid-cols-1 gap-3">
            {groups.map((group) => (
              <Button
                key={group.id}
                variant="outline"
                className="w-full text-lg py-6"
                onClick={() => startQuiz(group.id)}
              >
                {group.name} ({group.word_count} words)
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
