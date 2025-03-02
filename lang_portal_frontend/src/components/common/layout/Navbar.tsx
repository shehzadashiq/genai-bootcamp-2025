import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'

export default function Navbar() {
  return (
    <nav className="border-b">
      <div className="flex h-16 items-center px-4">
        <Link to="/" className="font-bold text-xl">
          Language Learning Portal
        </Link>
        <div className="ml-auto flex items-center space-x-4">
          <Button variant="ghost" asChild>
            <Link to="/dashboard">Dashboard</Link>
          </Button>
          <Button variant="ghost" asChild>
            <Link to="/study_activities">Study Activities</Link>
          </Button>
          <Button variant="ghost" asChild>
            <Link to="/words">Words</Link>
          </Button>
        </div>
      </div>
    </nav>
  )
}
