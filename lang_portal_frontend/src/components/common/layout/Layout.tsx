import { Outlet } from 'react-router-dom'
import Navbar from './Navbar'
import Sidebar from './Sidebar'

export default function Layout() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-8 animate-fade-in">
           <div className="max-w-7xl mx-auto">
             <Outlet />
           </div>
        </main>
      </div>
    </div>
  )
}
