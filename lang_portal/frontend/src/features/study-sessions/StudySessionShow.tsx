import { useEffect, useState, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { studySessionsApi } from '@/services/api'
import WordList from '@/features/words/components/WordList'
import { StudySessionResponse } from '@/types'

interface StudySession {
  id: number
  activity_name?: string
  group_name?: string
  start_time?: string
  end_time?: string
  review_items_count: number
}

export default function StudySessionShow() {
  const { id } = useParams<{ id: string }>()
  const [session, setSession] = useState<StudySessionResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

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
  }, [id]) // Only re-run if id changes

  const fetchWords = useCallback(
    (page: number) => studySessionsApi.getWords(id!, page),
    [id]
  )

  if (loading) {
    return <div>Loading study session details...</div>
  }

  if (error) {
    return <div className="text-red-500">{error}</div>
  }

  if (!session) {
    return <div>Study session not found</div>
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Study Session #{session.id}</h1>

      <Card>
        <CardHeader>
          <CardTitle>Session Details</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <h3 className="font-medium">Activity Name</h3>
              <p className="text-muted-foreground">{session.activity_name || 'Not available'}</p>
            </div>
            <div>
              <h3 className="font-medium">Group Name</h3>
              <p className="text-muted-foreground">{session.group_name || 'Not available'}</p>
            </div>
            <div>
              <h3 className="font-medium">Start Time</h3>
              <p className="text-muted-foreground">
                {session.start_time ? new Date(session.start_time).toLocaleString() : 'Not available'}
              </p>
            </div>
            <div>
              <h3 className="font-medium">End Time</h3>
              <p className="text-muted-foreground">
                {session.end_time ? new Date(session.end_time).toLocaleString() : 'Not available'}
              </p>
            </div>
            <div>
              <h3 className="font-medium">Review Items</h3>
              <p className="text-muted-foreground">{session.review_items_count}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Words Reviewed</CardTitle>
        </CardHeader>
        <CardContent>
          <WordList fetchWords={fetchWords} />
        </CardContent>
      </Card>
    </div>
  )
}
