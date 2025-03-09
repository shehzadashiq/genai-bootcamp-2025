import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { groupsApi } from '@/services/api'

interface Group {
  id: number
  name: string
  word_count: number
}

interface PaginationInfo {
  current_page: number
  total_pages: number
  total_items: number
  items_per_page: number
}

interface GroupsResponse {
  items: Group[]
  pagination: PaginationInfo
}

export default function GroupsIndex() {
  const [groups, setGroups] = useState<Group[]>([])
  const [pagination, setPagination] = useState<PaginationInfo | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchGroups = async () => {
      try {
        setLoading(true)
        setError(null)
        const response = await groupsApi.getAll(currentPage)
        const data = response.data
        setGroups(data.items || [])
        setPagination(data.pagination || null)
      } catch (error) {
        console.error('Error fetching groups:', error)
        setError('Failed to load groups. Please try again later.')
      } finally {
        setLoading(false)
      }
    }

    fetchGroups()
  }, [currentPage])

  if (loading) {
    return <div>Loading groups...</div>
  }

  if (error) {
    return (
      <div className="text-center py-8 text-red-500">
        <p>{error}</p>
      </div>
    )
  }

  const NoGroupsMessage = () => (
    <div className="text-center py-8 text-muted-foreground">
      <p>No groups available</p>
      <p className="text-sm mt-2">Create a group to get started!</p>
    </div>
  )

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Word Groups</h1>

      <Card>
        <CardHeader>
          <CardTitle>Group List</CardTitle>
        </CardHeader>
        <CardContent>
          {groups.length > 0 ? (
            <>
              <div className="relative overflow-x-auto">
                <table className="w-full text-sm text-left">
                  <thead className="text-xs uppercase bg-muted">
                    <tr>
                      <th className="px-6 py-3">Group Name</th>
                      <th className="px-6 py-3">Word Count</th>
                    </tr>
                  </thead>
                  <tbody>
                    {groups.map((group) => (
                      <tr key={group.id} className="border-b">
                        <td className="px-6 py-4">
                          <Link
                            to={`/groups/${group.id}`}
                            className="text-primary hover:underline"
                          >
                            {group.name}
                          </Link>
                        </td>
                        <td className="px-6 py-4">{group.word_count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {pagination && (
                <div className="mt-4 flex justify-between items-center">
                  <div className="text-sm text-muted-foreground">
                    Showing {groups.length} of {pagination.total_items} groups
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
            </>
          ) : (
            <NoGroupsMessage />
          )}
        </CardContent>
      </Card>
    </div>
  )
}
