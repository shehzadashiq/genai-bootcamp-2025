import { Link, useLocation } from 'react-router-dom'
import { cn } from '@/lib/utils'

const navigation = [
  { name: 'Dashboard', href: '/dashboard' },
  { name: 'Study Activities', href: '/study_activities' },
  { name: 'Words', href: '/words' },
  { name: 'Groups', href: '/groups' },
  { name: 'Study Sessions', href: '/study_sessions' },
  { name: 'Stats', href: '/stats' },
  { name: 'Settings', href: '/settings' },
]

export default function Sidebar() {
  const location = useLocation()

  return (
    <div className="flex flex-col h-full bg-muted/50">
      <div className="px-3 py-4">
        <div className="space-y-1">
          {navigation.map((item) => (
            <Link
              key={item.name}
              to={item.href}
              className={cn(
                'group flex gap-x-3 rounded-md p-2 text-sm leading-6',
                location.pathname === item.href
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground'
              )}
            >
              {item.name}
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
