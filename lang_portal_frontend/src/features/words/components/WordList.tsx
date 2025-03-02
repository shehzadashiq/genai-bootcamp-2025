import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

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

interface WordListProps {
  fetchWords: (page: number) => Promise<any>
}

export default function WordList({ fetchWords }: WordListProps) {
  const [words, setWords] = useState<Word[]>([])
  const [pagination, setPagination] = useState<PaginationInfo | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true

    const loadWords = async () => {
      try {
        setLoading(true)
        const response = await fetchWords(currentPage)
        if (!mounted) return

        // Handle empty or invalid response
        if (!response?.data?.items) {
          setWords([])
          setPagination(null)
          return
        }

        const data: WordsResponse = response.data
        setWords(data.items)
        setPagination(data.pagination)
        setError(null)
      } catch (error) {
        console.error('Error fetching words:', error)
        if (mounted) {
          setError('Failed to load words')
          setWords([])
          setPagination(null)
        }
      } finally {
        if (mounted) {
          setLoading(false)
        }
      }
    }

    loadWords()

    return () => {
      mounted = false
    }
  }, [currentPage, fetchWords])

  if (loading) {
    return <div>Loading words...</div>
  }

  if (error) {
    return <div className="text-red-500">{error}</div>
  }

  if (words.length === 0) {
    return <div className="text-muted-foreground">No words reviewed yet</div>
  }

  return (
    <div>
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
                    className="text-primary hover:underline"
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
      {pagination && pagination.total_pages > 1 && (
        <div className="mt-4 flex justify-between items-center">
          <div className="text-sm text-muted-foreground">
            Showing {words.length} of {pagination.total_items} words
          </div>
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
        </div>
      )}
    </div>
  )
}
