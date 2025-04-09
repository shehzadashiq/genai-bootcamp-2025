import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { wordsApi } from '@/services/api'

interface Group {
  id: number
  name: string
}

interface Word {
  id: number
  urdu: string
  urdlish: string
  english: string
  correct_count: number
  wrong_count: number
  groups: Group[]
}

export default function WordShow() {
  const { id } = useParams<{ id: string }>()
  const [word, setWord] = useState<Word | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchWord = async () => {
      if (!id) return

      try {
        const response = await wordsApi.getById(id)
        setWord(response.data)
      } catch (error) {
        console.error('Error fetching word:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchWord()
  }, [id])

  if (loading) {
    return <div>Loading word details...</div>
  }

  if (!word) {
    return <div>Word not found</div>
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold urdu-text text-4xl mb-6">{word.urdu}</h1>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Translations</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h3 className="font-medium">Urdlish</h3>
              <p className="text-muted-foreground">{word.urdlish}</p>
            </div>
            <div>
              <h3 className="font-medium">English</h3>
              <p className="text-muted-foreground">{word.english}</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Statistics</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h3 className="font-medium">Correct Answers</h3>
              <p className="text-muted-foreground">{word.correct_count}</p>
            </div>
            <div>
              <h3 className="font-medium">Wrong Answers</h3>
              <p className="text-muted-foreground">{word.wrong_count}</p>
            </div>
            <div>
              <h3 className="font-medium">Success Rate</h3>
              <p className="text-muted-foreground">
                {word.correct_count + word.wrong_count > 0
                  ? ((word.correct_count / (word.correct_count + word.wrong_count)) * 100).toFixed(1)
                  : 0}%
              </p>
            </div>
          </CardContent>
        </Card>

        {word.groups && word.groups.length > 0 && (
          <Card className="md:col-span-2">
            <CardHeader>
              <CardTitle>Word Groups</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {word.groups.map((group) => (
                  <Link
                    key={group.id}
                    to={`/groups/${group.id}`}
                    className="px-3 py-1 bg-primary/10 text-primary rounded-full hover:bg-primary/20 transition-colors"
                  >
                    {group.name}
                  </Link>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
