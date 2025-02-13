import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { dashboardApi } from '@/services/api'

interface LastStudySession {
  activity: string
  timestamp: string
  correct: number
  wrong: number
  groupId: string
}

interface StudyProgress {
  totalWordsStudied: number
  totalWords: number
  masteryPercentage: number
}

interface QuickStats {
  successRate: number
  totalStudySessions: number
  totalActiveGroups: number
  studyStreak: number
}

export default function Dashboard() {
  const [lastSession, setLastSession] = useState<LastStudySession | null>(null)
  const [progress, setProgress] = useState<StudyProgress | null>(null)
  const [stats, setStats] = useState<QuickStats | null>(null)

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
      }
    }

    fetchDashboardData()
  }, [])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <Button asChild>
          <Link to="/study_activities">Start Studying</Link>
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {/* Last Study Session */}
        <Card>
          <CardHeader>
            <CardTitle>Last Study Session</CardTitle>
          </CardHeader>
          <CardContent>
            {lastSession ? (
              <div className="space-y-2">
                <p>Activity: {lastSession.activity}</p>
                <p>Time: {new Date(lastSession.timestamp).toLocaleString()}</p>
                <p>Correct: {lastSession.correct}</p>
                <p>Wrong: {lastSession.wrong}</p>
                <Button variant="outline" asChild>
                  <Link to={`/groups/${lastSession.groupId}`}>View Group</Link>
                </Button>
              </div>
            ) : (
              <p>No recent study sessions</p>
            )}
          </CardContent>
        </Card>

        {/* Study Progress */}
        <Card>
          <CardHeader>
            <CardTitle>Study Progress</CardTitle>
          </CardHeader>
          <CardContent>
            {progress ? (
              <div className="space-y-2">
                <p>Words Studied: {progress.totalWordsStudied}/{progress.totalWords}</p>
                <p>Mastery: {progress.masteryPercentage}%</p>
                <div className="h-2 bg-secondary rounded-full">
                  <div
                    className="h-full bg-primary rounded-full"
                    style={{ width: `${progress.masteryPercentage}%` }}
                  />
                </div>
              </div>
            ) : (
              <p>Loading progress...</p>
            )}
          </CardContent>
        </Card>

        {/* Quick Stats */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Stats</CardTitle>
          </CardHeader>
          <CardContent>
            {stats ? (
              <div className="space-y-2">
                <p>Success Rate: {stats.successRate}%</p>
                <p>Total Study Sessions: {stats.totalStudySessions}</p>
                <p>Active Groups: {stats.totalActiveGroups}</p>
                <p>Study Streak: {stats.studyStreak} days</p>
              </div>
            ) : (
              <p>Loading stats...</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
