import { Routes, Route } from 'react-router-dom'
import Layout from '@/components/common/layout/Layout'
import Dashboard from '@/features/dashboard/Dashboard'
import StudyActivitiesIndex from '@/features/study-activities/StudyActivitiesIndex'
import StudyActivityShow from '@/features/study-activities/StudyActivityShow'
import StudyActivityLaunch from '@/features/study-activities/StudyActivityLaunch'
import WordsIndex from '@/features/words/WordsIndex'
import WordShow from '@/features/words/WordShow'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="study_activities" element={<StudyActivitiesIndex />} />
        <Route path="study_activities/:id" element={<StudyActivityShow />} />
        <Route path="study_activities/:id/launch" element={<StudyActivityLaunch />} />
        <Route path="words" element={<WordsIndex />} />
        <Route path="words/:id" element={<WordShow />} />
      </Route>
    </Routes>
  )
}

export default App
