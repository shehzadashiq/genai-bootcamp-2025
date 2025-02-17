import { useEffect, useState, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { studySessionsApi, vocabularyQuizApi } from '@/services/api'
import { StudySessionResponse } from '@/types'
import { ActivityRouter } from './ActivityRouter'

export default function StudySessionShow() {
  const { id } = useParams<{ id: string }>()
  const [session, setSession] = useState<StudySessionResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [quizStarted, setQuizStarted] = useState(false)
  const [quizSessionId, setQuizSessionId] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true

    const fetchSession = async () => {
      if (!id) return

      try {
        const response = await studySessionsApi.getById(id)
        if (mounted) {
          console.log('Received session data:', response.data)
          setSession(response.data)
        }
      } catch (error) {
        console.error('Error fetching study session:', error)
        if (mounted) {
          setError('Failed to load study session')
        }
      } finally {
        if (mounted) {
          setLoading(false)
        }
      }
    }

    fetchSession()

    return () => {
      mounted = false
    }
  }, [id])

  const startQuiz = useCallback(async () => {
    if (!session?.group_id) return;
    
    try {
      setLoading(true);
      setError(null);

      // Start the quiz using the current session
      console.log('Starting quiz for session:', id);
      const startResponse = await vocabularyQuizApi.startQuiz(session.group_id, 10);

      console.log('Started quiz:', startResponse);
      setQuizSessionId(startResponse.session_id.toString());
      setQuizStarted(true);
    } catch (err) {
      console.error('Failed to start quiz:', err);
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unknown error occurred');
      }
    } finally {
      setLoading(false);
    }
  }, [session?.group_id, id]);

  if (loading) {
    return <div>Loading study session details...</div>
  }

  if (error) {
    return <div className="text-red-500">{error}</div>
  }

  if (!session) {
    return <div>Study session not found</div>
  }

  if (!quizStarted && session.activity_name === 'Vocabulary Quiz') {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold">Study Session #{session.id}</h1>
        <Card>
          <CardHeader>
            <CardTitle>Start Quiz</CardTitle>
          </CardHeader>
          <CardContent>
            <button
              onClick={startQuiz}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
              disabled={loading}
            >
              {loading ? 'Starting Quiz...' : 'Start Quiz'}
            </button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Study Session #{session.id}</h1>
      <ActivityRouter session={session} quizSessionId={quizSessionId} />
    </div>
  );
}
