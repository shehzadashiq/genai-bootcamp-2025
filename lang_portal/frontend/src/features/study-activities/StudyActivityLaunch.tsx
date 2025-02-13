import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { studyActivitiesApi } from '@/services/api'

interface StudyActivity {
  id: string
  name: string
  url: string
}

interface Group {
  id: string
  name: string
}

export default function StudyActivityLaunch() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [activity, setActivity] = useState<StudyActivity | null>(null)
  const [groups, setGroups] = useState<Group[]>([])
  const [selectedGroup, setSelectedGroup] = useState<string>('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      if (!id) return

      try {
        const activityRes = await studyActivitiesApi.getById(id)
        setActivity(activityRes.data)
        // In a real app, you would fetch groups from an API
        setGroups([
          { id: '1', name: 'Basic Vocabulary' },
          { id: '2', name: 'Intermediate Words' },
          { id: '3', name: 'Advanced Phrases' },
        ])
      } catch (error) {
        console.error('Error fetching activity:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [id])

  const handleLaunch = async () => {
    if (!activity || !selectedGroup) return

    try {
      await studyActivitiesApi.create({
        activityId: activity.id,
        groupId: selectedGroup,
      })

      // Open the activity URL in a new tab
      window.open(activity.url, '_blank')
      
      // Navigate back to the activity details page
      navigate(`/study_activities/${id}`)
    } catch (error) {
      console.error('Error launching activity:', error)
    }
  }

  if (loading) {
    return <div>Loading...</div>
  }

  if (!activity) {
    return <div>Activity not found</div>
  }

  return (
    <div className="max-w-md mx-auto space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Launch {activity.name}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label htmlFor="group" className="block text-sm font-medium mb-2">
              Select Group
            </label>
            <select
              id="group"
              value={selectedGroup}
              onChange={(e) => setSelectedGroup(e.target.value)}
              className="w-full p-2 border rounded-md"
            >
              <option value="">Select a group...</option>
              {groups.map((group) => (
                <option key={group.id} value={group.id}>
                  {group.name}
                </option>
              ))}
            </select>
          </div>

          <Button
            onClick={handleLaunch}
            disabled={!selectedGroup}
            className="w-full"
          >
            Launch Now
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
