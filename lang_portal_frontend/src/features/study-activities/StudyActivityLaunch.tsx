import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { studyActivitiesApi, groupsApi } from '@/services/api'
import { StudySessionResponse } from '@/types'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

interface Group {
  id: number
  name: string
}

interface StudyActivity {
  id: number
  name: string
  url: string
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

        console.log('Activity:', activityRes.data)
        console.log('Groups:', groupsRes.data)

        setActivity(activityRes.data)
        if (groupsRes.data.items && groupsRes.data.items.length > 0) {
          setGroups(groupsRes.data.items)
          setSelectedGroupId(groupsRes.data.items[0].id)
        } else {
          console.error('No groups found')
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
      const { data } = await studyActivitiesApi.create({
        group_id: selectedGroupId,
        study_activity_id: activity.id,
      })

      console.log('Created session:', data)

      // Open activity in new tab if URL is provided
      if (activity.url) {
        window.open(activity.url, '_blank')
      }

      // Redirect to the study session page
      navigate(`/study_sessions/${data.id}`)
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
              <h3 className="font-medium">Preview</h3>
              <img
                src={activity.thumbnail_url}
                alt={activity.name}
                className="mt-2 rounded-lg border"
              />
            </div>
          )}

          <div>
            <h3 className="font-medium">Select Group</h3>
            <Select
              value={selectedGroupId?.toString() || ''}
              onValueChange={(value) => setSelectedGroupId(Number(value))}
            >
              <SelectTrigger className="w-full mt-2">
                <SelectValue placeholder="Select a group" />
              </SelectTrigger>
              <SelectContent>
                {groups.map((group) => (
                  <SelectItem key={group.id} value={group.id.toString()}>
                    {group.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <Button
            className="w-full"
            onClick={handleLaunch}
            disabled={launching || !selectedGroupId}
          >
            {launching ? 'Launching...' : 'Launch Activity'}
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
