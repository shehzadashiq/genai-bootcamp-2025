import { Link, useLocation } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { 
  LayoutDashboard, 
  BookOpen, 
  Type, 
  Users, 
  Calendar, 
  BarChart2, 
  NotebookPen,
  Settings 
} from 'lucide-react'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Study Activities', href: '/study_activities', icon: BookOpen },
  { name: 'Words', href: '/words', icon: Type },
  { name: 'Groups', href: '/groups', icon: Users },
  { name: 'Document Summary', href: 'http://localhost:8501/', icon: NotebookPen, external: true },
  { name: 'Study Sessions', href: '/study_sessions', icon: Calendar },
  { name: 'Stats', href: '/stats', icon: BarChart2 },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export default function Sidebar() {
  const location = useLocation()

  return (
    <div className="flex flex-col h-full bg-muted/50">
      <div className="px-3 py-4">
        <div className="space-y-1">
          {navigation.map((item) => (
            item.external ? (
              <a
                key={item.name}
                href={item.href}
                target="_blank"
                rel="noopener noreferrer"
                className={cn(
                  'group flex items-center gap-x-3 rounded-md p-2 text-sm leading-6',
                  'text-muted-foreground hover:bg-muted hover:text-foreground'
                )}
              >
                <item.icon className="h-5 w-5 shrink-0" aria-hidden="true" />
                {item.name}
              </a>
            ) : (
              <Link
                key={item.name}
                to={item.href}
                className={cn(
                  'group flex items-center gap-x-3 rounded-md p-2 text-sm leading-6',
                  location.pathname === item.href
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                )}
              >
                <item.icon className="h-5 w-5 shrink-0" aria-hidden="true" />
                {item.name}
              </Link>
            )
          ))}
        </div>
      </div>
    </div>
  )
}
