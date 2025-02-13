import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { studyActivitiesApi, groupsApi } from '@/services/api'

interface Group {
  id: number
  name: string
}

interface StudyActivity {
  id: number
  name: string
  thumbnail_url: string
  description: string
}

export default function StudyActivityLaunch() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [activity, setActivity] = useState<StudyActivity | null>(null)
  const [groups, setGroups] = useState<Group[]>([])
  const [selectedGroupId, setSelectedGroupId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [launching, setLaunching] = useState(false)

  useEffect(() => {
    const fetchData = async () => {
      if (!id) return

      try {
        const [activityRes, groupsRes] = await Promise.all([
          studyActivitiesApi.getById(id),
          groupsApi.getAll(),
        ])

        setActivity(activityRes.data)
        setGroups(groupsRes.data.items)

        // Pre-select the first group if available
        if (groupsRes.data.items.length > 0) {
          setSelectedGroupId(groupsRes.data.items[0].id)
        }
      } catch (error) {
        console.error('Error fetching data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [id])

  const handleLaunch = async () => {
    if (!id || !selectedGroupId || !activity) return

    setLaunching(true)
    try {
      const response = await studyActivitiesApi.create({
        group_id: selectedGroupId,
        study_activity_id: activity.id,
      })

      // Open activity in new tab if URL is provided
      if (activity.thumbnail_url) {
        window.open(activity.thumbnail_url, '_blank')
      }

      // Redirect to the study session page
      navigate(`/study_sessions/${response.data.id}`)
    } catch (error) {
      console.error('Error launching activity:', error)
      alert('Failed to launch activity. Please try again.')
    } finally {
      setLaunching(false)
    }
  }

  if (loading) {
    return <div>Loading activity details...</div>
  }

  if (!activity) {
    return <div>Activity not found</div>
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Launch {activity.name}</h1>

      <Card>
        <CardHeader>
          <CardTitle>Activity Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h3 className="font-medium">Description</h3>
            <p className="text-muted-foreground">{activity.description}</p>
          </div>
          {activity.thumbnail_url && (
            <div>
              <h3 className="font-medium mb-2">Preview</h3>
              <img
                src={activity.thumbnail_url}
                alt={activity.name}
                className="rounded-lg max-w-full h-auto"
              />
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Launch Settings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label htmlFor="group" className="block font-medium mb-2">
              Select Group
            </label>
            <select
              id="group"
              value={selectedGroupId || ''}
              onChange={(e) => setSelectedGroupId(Number(e.target.value))}
              className="w-full p-2 border rounded-md bg-background"
              disabled={launching}
            >
              {groups.map((group) => (
                <option key={group.id} value={group.id}>
                  {group.name}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={handleLaunch}
            disabled={!selectedGroupId || launching}
            className="w-full py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
          >
            {launching ? 'Launching...' : 'Launch Now'}
          </button>
        </CardContent>
      </Card>
    </div>
  )
}
