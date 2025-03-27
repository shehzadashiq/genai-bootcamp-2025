import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { wordsApi } from '@/services/api'

interface Word {
  id: number
  urdu: string
  urdlish: string
  english: string
  correct_count: number
  wrong_count: number
}

interface PaginationInfo {
  current_page: number
  total_pages: number
  total_items: number
  items_per_page: number
}

interface WordsResponse {
  items: Word[]
  pagination: PaginationInfo
}

export default function WordsIndex() {
  const [words, setWords] = useState<Word[]>([])
  const [pagination, setPagination] = useState<PaginationInfo | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchWords = async () => {
      try {
        setLoading(true)
        setError(null)
        const response = await wordsApi.getAll(currentPage)
        const data = response.data
        setWords(data.items || [])
        setPagination(data.pagination || null)
      } catch (error) {
        console.error('Error fetching words:', error)
        setError('Failed to load words. Please try again later.')
      } finally {
        setLoading(false)
      }
    }

    fetchWords()
  }, [currentPage])

  if (loading) {
    return <div>Loading words...</div>
  }

  if (error) {
    return (
      <div className="text-center py-8 text-red-500">
        <p>{error}</p>
      </div>
    )
  }

  const NoWordsMessage = () => (
    <div className="text-center py-8 text-muted-foreground">
      <p>No words available</p>
      <p className="text-sm mt-2">Add some words to get started!</p>
    </div>
  )

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Words</h1>

      <Card>
        <CardHeader>
          <CardTitle>Word List</CardTitle>
        </CardHeader>
        <CardContent>
          {words.length > 0 ? (
            <>
              <div className="relative overflow-x-auto">
                <table className="w-full text-sm text-left">
                  <thead className="text-xs uppercase bg-muted">
                    <tr>
                      <th className="px-6 py-3">Urdu</th>
                      <th className="px-6 py-3">Urdlish</th>
                      <th className="px-6 py-3">English</th>
                      <th className="px-6 py-3">Correct</th>
                      <th className="px-6 py-3">Wrong</th>
                    </tr>
                  </thead>
                  <tbody>
                    {words.map((word) => (
                      <tr key={word.id} className="border-b">
                        <td className="px-6 py-4">
                          <Link
                            to={`/words/${word.id}`}
                            className="text-primary hover:underline font-nastaleeq text-lg"
                          >
                            {word.urdu}
                          </Link>
                        </td>
                        <td className="px-6 py-4">{word.urdlish}</td>
                        <td className="px-6 py-4">{word.english}</td>
                        <td className="px-6 py-4">{word.correct_count}</td>
                        <td className="px-6 py-4">{word.wrong_count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {pagination && (
                <div className="mt-4 flex justify-between items-center">
                  <div className="text-sm text-muted-foreground">
                    Showing {words.length} of {pagination.total_items} words
                  </div>
                  {pagination.total_pages > 1 && (
                    <div className="flex gap-2">
                      <button
                        onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                        disabled={currentPage === 1}
                        className="px-3 py-1 border rounded hover:bg-muted disabled:opacity-50"
                      >
                        Previous
                      </button>
                      <button
                        onClick={() => setCurrentPage(prev => Math.min(pagination.total_pages, prev + 1))}
                        disabled={currentPage === pagination.total_pages}
                        className="px-3 py-1 border rounded hover:bg-muted disabled:opacity-50"
                      >
                        Next
                      </button>
                    </div>
                  )}
                </div>
              )}
            </>
          ) : (
            <NoWordsMessage />
          )}
        </CardContent>
      </Card>
    </div>
  )
}
