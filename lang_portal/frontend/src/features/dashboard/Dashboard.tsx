import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { dashboardApi } from '@/services/api'

interface LastStudySession {
  id: number
  group_id: number
  created_at: string
  study_activity_id: number
  group_name: string
}

interface StudyProgress {
  total_words_studied: number
  total_available_words: number
}

interface QuickStats {
  success_rate: number
  total_study_sessions: number
  total_active_groups: number
  study_streak_days: number
}

export default function Dashboard() {
  const [lastSession, setLastSession] = useState<LastStudySession | null>(null)
  const [progress, setProgress] = useState<StudyProgress | null>(null)
  const [stats, setStats] = useState<QuickStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [lastSessionRes, progressRes, statsRes] = await Promise.all([
          dashboardApi.getLastStudySession(),
          dashboardApi.getStudyProgress(),
          dashboardApi.getQuickStats(),
        ])

        setLastSession(lastSessionRes.data)
        setProgress(progressRes.data)
        setStats(statsRes.data)
      } catch (error) {
        console.error('Error fetching dashboard data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchDashboardData()
  }, [])

  if (loading) {
    return <div>Loading dashboard...</div>
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Dashboard</h1>

      {lastSession && (
        <Card>
          <CardHeader>
            <CardTitle>Last Study Session</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h3 className="font-medium">Group</h3>
              <Link
                to={`/groups/${lastSession.group_id}`}
                className="text-primary hover:underline"
              >
                {lastSession.group_name}
              </Link>
            </div>
            <div>
              <h3 className="font-medium">Date</h3>
              <p className="text-muted-foreground">
                {new Date(lastSession.created_at).toLocaleString()}
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {progress && (
        <Card>
          <CardHeader>
            <CardTitle>Study Progress</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm font-medium">
                  {progress.total_words_studied} of {progress.total_available_words} words studied
                </span>
                <span className="text-sm font-medium">
                  {Math.round((progress.total_words_studied / progress.total_available_words) * 100)}%
                </span>
              </div>
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary transition-all"
                  style={{
                    width: `${(progress.total_words_studied / progress.total_available_words) * 100}%`,
                  }}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {stats && (
        <Card>
          <CardHeader>
            <CardTitle>Quick Stats</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <h3 className="font-medium">Success Rate</h3>
                <p className="text-2xl font-bold">{stats.success_rate}%</p>
              </div>
              <div>
                <h3 className="font-medium">Study Sessions</h3>
                <p className="text-2xl font-bold">{stats.total_study_sessions}</p>
              </div>
              <div>
                <h3 className="font-medium">Active Groups</h3>
                <p className="text-2xl font-bold">{stats.total_active_groups}</p>
              </div>
              <div>
                <h3 className="font-medium">Study Streak</h3>
                <p className="text-2xl font-bold">{stats.study_streak_days} days</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="pt-6">
          <Link
            to="/study_activities"
            className="block w-full py-3 text-center bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
          >
            Start Studying
          </Link>
        </CardContent>
      </Card>
    </div>
  )
}
