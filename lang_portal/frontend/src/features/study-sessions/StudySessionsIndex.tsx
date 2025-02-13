import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { studySessionsApi } from '@/services/api'
import StudySessionList from './components/StudySessionList'

export default function StudySessionsIndex() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Study Sessions</h1>

      <Card>
        <CardHeader>
          <CardTitle>All Study Sessions</CardTitle>
        </CardHeader>
        <CardContent>
          <StudySessionList fetchSessions={studySessionsApi.getAll} />
        </CardContent>
      </Card>
    </div>
  )
}
