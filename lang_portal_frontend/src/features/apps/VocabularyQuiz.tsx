import { useEffect, useState } from 'react'
import { vocabularyQuizApi } from '../vocabulary-quiz/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
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
    id: number
  }[]
}

interface QuizResult {
  total_questions: number
  correct_answers: number
  score_percentage: number
}

interface ApiQuizWord {
  word_id?: number;
  word: {
    id: number;
    urdu: string;
    english: string;
  };
  options: string[];
}

export default function VocabularyQuiz() {
  const [groups, setGroups] = useState<Group[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [quizState, setQuizState] = useState<QuizState | null>(null)
  const [quizResult, setQuizResult] = useState<QuizResult | null>(null)

  useEffect(() => {
    const fetchGroups = async () => {
      try {
        setLoading(true)
        setError(null)
        // Use merge_by_difficulty=true to get merged groups
        const response = await groupsApi.getAll(1, true)
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
      
      const response = await vocabularyQuizApi.startQuiz(groupId, 10, 'medium')
      const data = response.data
      
      // Transform API response to match our component's expected format
      const transformedWords: QuizWord[] = data.words.map((apiWord: ApiQuizWord) => ({
        id: apiWord.word_id || apiWord.word.id, // Use word_id if available, fallback to word.id
        urdu: apiWord.word.urdu,
        options: apiWord.options.map((option, index) => ({
          id: index,
          text: option
        }))
      }))
      
      setQuizState({
        sessionId: data.session_id,
        words: transformedWords,
        currentIndex: 0,
        answers: []
      })
    } catch (error) {
      console.error('Error starting quiz:', error)
      setError('Failed to start quiz')
    } finally {
      setLoading(false)
    }
  }

  const submitAnswer = async (wordId: number, selectedId: number) => {
    if (!quizState) return

    console.log(`Submitting answer - wordId: ${wordId}, selectedId: ${selectedId}`);
    
    // Create a unique answer object with its own identifier
    const newAnswer = { word_id: wordId, selected_id: selectedId, id: Date.now() };
    
    const newAnswers = [
      ...quizState.answers,
      newAnswer
    ]

    if (quizState.currentIndex === quizState.words.length - 1) {
      // Last question, submit the quiz
      try {
        setLoading(true)
        
        // Remove the id property from each answer before sending to the backend
        const answersToSubmit = newAnswers.map(({ word_id, selected_id }) => ({
          word_id,
          selected_id
        }));
        
        console.log('Submitting quiz with answers:', answersToSubmit);
        
        const response = await vocabularyQuizApi.submitQuiz(quizState.sessionId, answersToSubmit)
        const result = response.data
        console.log('Quiz result:', result);
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
              <p className="text-4xl font-bold mb-2 font-nastaleeq text-center urdu-text">{currentWord.urdu}</p>
              <br></br>
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
