import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { groupsApi } from '@/services/api'
import WordList from '@/features/words/components/WordList'
import StudySessionList from '@/features/study-sessions/components/StudySessionList'

interface Group {
  id: number
  name: string
  word_count: number
}

export default function GroupShow() {
  const { id } = useParams<{ id: string }>()
  const [group, setGroup] = useState<Group | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchGroup = async () => {
      if (!id) return

      try {
        const response = await groupsApi.getById(id)
        setGroup(response.data)
      } catch (error) {
        console.error('Error fetching group:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchGroup()
  }, [id])

  if (loading) {
    return <div>Loading group details...</div>
  }

  if (!group) {
    return <div>Group not found</div>
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">{group.name}</h1>

      <Card>
        <CardHeader>
          <CardTitle>Group Statistics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <h3 className="font-medium">Total Words</h3>
              <p className="text-muted-foreground">{group.word_count}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Words in Group</CardTitle>
        </CardHeader>
        <CardContent>
          <WordList fetchWords={(page) => groupsApi.getWords(id, page)} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Study Sessions</CardTitle>
        </CardHeader>
        <CardContent>
          <StudySessionList fetchSessions={(page) => groupsApi.getStudySessions(id, page)} />
        </CardContent>
      </Card>
    </div>
  )
}
