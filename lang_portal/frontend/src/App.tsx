import { Routes, Route } from 'react-router-dom'
import Layout from '@/components/common/layout/Layout'
import Dashboard from '@/features/dashboard/Dashboard'
import StudyActivitiesIndex from '@/features/study-activities/StudyActivitiesIndex'
import StudyActivityShow from '@/features/study-activities/StudyActivityShow'
import StudyActivityLaunch from '@/features/study-activities/StudyActivityLaunch'
import WordsIndex from '@/features/words/WordsIndex'
import WordShow from '@/features/words/WordShow'
import GroupsIndex from '@/features/groups/GroupsIndex'
import GroupShow from '@/features/groups/GroupShow'
import StudySessionsIndex from '@/features/study-sessions/StudySessionsIndex'
import StudySessionShow from '@/features/study-sessions/StudySessionShow'
import Settings from '@/features/settings/Settings'
import Stats from '@/features/stats/Stats'
import { ThemeProvider } from '@/providers/ThemeProvider'

function App() {
  return (
    <ThemeProvider>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="study_activities" element={<StudyActivitiesIndex />} />
          <Route path="study_activities/:id" element={<StudyActivityShow />} />
          <Route path="study_activities/:id/launch" element={<StudyActivityLaunch />} />
          <Route path="words" element={<WordsIndex />} />
          <Route path="words/:id" element={<WordShow />} />
          <Route path="groups" element={<GroupsIndex />} />
          <Route path="groups/:id" element={<GroupShow />} />
          <Route path="study_sessions" element={<StudySessionsIndex />} />
          <Route path="study_sessions/:id" element={<StudySessionShow />} />
          <Route path="settings" element={<Settings />} />
          <Route path="stats" element={<Stats />} />
        </Route>
      </Routes>
    </ThemeProvider>
  )
}

export default App
