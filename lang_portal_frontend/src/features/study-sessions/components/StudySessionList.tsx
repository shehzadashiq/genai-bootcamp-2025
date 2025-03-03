import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

interface StudySession {
  id: number
  activity_name: string
  group_name: string
  start_time: string
  end_time: string
  review_items_count: number
}

interface PaginationInfo {
  current_page: number
  total_pages: number
  total_items: number
  items_per_page: number
}

interface StudySessionsResponse {
  items: StudySession[]
  pagination: PaginationInfo
}

interface StudySessionListProps {
  fetchSessions: (page: number) => Promise<any>
}

export default function StudySessionList({ fetchSessions }: StudySessionListProps) {
  const [sessions, setSessions] = useState<StudySession[]>([])
  const [pagination, setPagination] = useState<PaginationInfo | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadSessions = async () => {
      try {
        setLoading(true)
        setError(null)
        const response = await fetchSessions(currentPage)
        const data = response.data
        setSessions(data.items || [])
        setPagination(data.pagination || null)
      } catch (error) {
        console.error('Error fetching study sessions:', error)
        setError('Failed to load study sessions')
        setSessions([])
        setPagination(null)
      } finally {
        setLoading(false)
      }
    }

    loadSessions()
  }, [currentPage, fetchSessions])

  if (loading) {
    return <div>Loading study sessions...</div>
  }

  if (error) {
    return <div className="text-red-500">{error}</div>
  }

  if (!sessions || sessions.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-muted-foreground mb-4">No study sessions found</p>
        <p className="text-sm">Start a new session by selecting a study activity</p>
      </div>
    )
  }

  return (
    <div>
      <div className="relative overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="text-xs uppercase bg-muted">
            <tr>
              <th className="px-6 py-3">ID</th>
              <th className="px-6 py-3">Activity</th>
              <th className="px-6 py-3">Group</th>
              <th className="px-6 py-3">Start Time</th>
              <th className="px-6 py-3">End Time</th>
              <th className="px-6 py-3">Review Items</th>
            </tr>
          </thead>
          <tbody>
            {sessions.map((session) => (
              <tr key={session.id} className="border-b">
                <td className="px-6 py-4">
                  <Link
                    to={`/study_sessions/${session.id}`}
                    className="text-primary hover:underline"
                  >
                    {session.id}
                  </Link>
                </td>
                <td className="px-6 py-4">{session.activity_name}</td>
                <td className="px-6 py-4">{session.group_name}</td>
                <td className="px-6 py-4">{new Date(session.start_time).toLocaleString()}</td>
                <td className="px-6 py-4">{new Date(session.end_time).toLocaleString()}</td>
                <td className="px-6 py-4">{session.review_items_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {pagination && (
        <div className="mt-4 flex justify-between items-center">
          <div className="text-sm text-muted-foreground">
            Showing {sessions.length} of {pagination.total_items} sessions
          </div>
          {pagination.total_pages > 1 && (
            <div className="flex gap-2">
              <button
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                disabled={currentPage === 1}
                className="px-3 py-1 border rounded hover:bg-muted disabled:opacity-50"
              >
                Previous
              </button>
              <button
                onClick={() => setCurrentPage(prev => Math.min(pagination.total_pages, prev + 1))}
                disabled={currentPage === pagination.total_pages}
                className="px-3 py-1 border rounded hover:bg-muted disabled:opacity-50"
              >
                Next
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
