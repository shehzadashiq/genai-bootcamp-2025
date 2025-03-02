import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { dashboardApi } from '@/services/api'

interface QuickStats {
  success_rate: number
  total_study_sessions: number
  total_active_groups: number
  study_streak: number
}

export default function Stats() {
  const [stats, setStats] = useState<QuickStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await dashboardApi.getQuickStats()
        setStats(response.data)
      } catch (error) {
        console.error('Error fetching stats:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchStats()
  }, [])

  if (loading) {
    return <div>Loading stats...</div>
  }

  if (!stats) {
    return <div>Failed to load stats</div>
  }

  const statCards = [
    {
      title: 'Success Rate',
      value: `${stats.success_rate}%`,
      description: 'Average success rate across all study sessions',
    },
    {
      title: 'Study Sessions',
      value: stats.total_study_sessions,
      description: 'Total number of completed study sessions',
    },
    {
      title: 'Active Groups',
      value: stats.total_active_groups,
      description: 'Number of groups with recent activity',
    },
    {
      title: 'Study Streak',
      value: `${stats.study_streak} days`,
      description: 'Current consecutive days studying',
    },
  ]

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Statistics</h1>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {statCards.map((stat) => (
          <Card key={stat.title}>
            <CardHeader>
              <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <p className="text-xs text-muted-foreground mt-2">{stat.description}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Study Progress</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <p className="text-muted-foreground">
              More detailed statistics and progress tracking coming soon!
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
