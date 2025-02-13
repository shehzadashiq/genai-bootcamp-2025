import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { settingsApi } from '@/services/api'
import { useTheme } from '@/providers/ThemeProvider'

export default function Settings() {
  const { theme, setTheme } = useTheme()
  const [resetting, setResetting] = useState(false)

  const handleResetHistory = async () => {
    if (!window.confirm('Are you sure you want to reset all study history? This cannot be undone.')) {
      return
    }

    setResetting(true)
    try {
      await settingsApi.resetHistory()
      window.location.reload()
    } catch (error) {
      console.error('Error resetting history:', error)
      alert('Failed to reset history. Please try again.')
    } finally {
      setResetting(false)
    }
  }

  const handleFullReset = async () => {
    if (!window.confirm('Are you sure you want to perform a full reset? This will delete ALL data and cannot be undone.')) {
      return
    }

    setResetting(true)
    try {
      await settingsApi.fullReset()
      window.location.reload()
    } catch (error) {
      console.error('Error performing full reset:', error)
      alert('Failed to perform full reset. Please try again.')
    } finally {
      setResetting(false)
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Settings</h1>

      <Card>
        <CardHeader>
          <CardTitle>Theme</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <button
              onClick={() => setTheme('light')}
              className={`px-4 py-2 rounded ${
                theme === 'light' ? 'bg-primary text-primary-foreground' : 'bg-muted'
              }`}
            >
              Light
            </button>
            <button
              onClick={() => setTheme('dark')}
              className={`px-4 py-2 rounded ${
                theme === 'dark' ? 'bg-primary text-primary-foreground' : 'bg-muted'
              }`}
            >
              Dark
            </button>
            <button
              onClick={() => setTheme('system')}
              className={`px-4 py-2 rounded ${
                theme === 'system' ? 'bg-primary text-primary-foreground' : 'bg-muted'
              }`}
            >
              System
            </button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Reset Options</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <button
            onClick={handleResetHistory}
            disabled={resetting}
            className="w-full px-4 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600 disabled:opacity-50"
          >
            {resetting ? 'Resetting...' : 'Reset History'}
          </button>
          <button
            onClick={handleFullReset}
            disabled={resetting}
            className="w-full px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50"
          >
            {resetting ? 'Resetting...' : 'Full Reset'}
          </button>
        </CardContent>
      </Card>
    </div>
  )
}
