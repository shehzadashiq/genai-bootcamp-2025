import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { groupsApi } from '@/services/api';

interface Group {
  id: number;
  name: string;
  word_count: number;
}

interface PaginationInfo {
  current_page: number;
  total_pages: number;
  total_items: number;
  items_per_page: number;
}

export const GroupsIndex: React.FC = () => {
  const [groups, setGroups] = useState<Group[]>([]);
  const [pagination, setPagination] = useState<PaginationInfo | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mergeByDifficulty, setMergeByDifficulty] = useState(true);

  const fetchGroups = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await groupsApi.getAll(currentPage, mergeByDifficulty);
      const data = response.data;
      setGroups(data.items || []);
      setPagination(data.pagination || null);
    } catch (err) {
      setError('Failed to load groups');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGroups();
  }, [currentPage, mergeByDifficulty]);

  if (loading) {
    return <div>Loading groups...</div>;
  }

  if (error) {
    return (
      <div>
        <p>Error: {error}</p>
        <button onClick={fetchGroups}>Try Again</button>
      </div>
    );
  }

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  const toggleMergeMode = () => {
    setMergeByDifficulty(!mergeByDifficulty);
  };

  const handleRefresh = () => {
    fetchGroups();
  };

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Word Groups</h1>

      <div className="flex justify-between items-center mb-4">
        <button 
          className="px-3 py-1 border rounded hover:bg-muted"
          onClick={toggleMergeMode}
        >
          {mergeByDifficulty ? "Show All Groups" : "Merge by Difficulty"}
        </button>
        
        <button 
          className="px-3 py-1 border rounded hover:bg-muted"
          onClick={handleRefresh}
        >
          Refresh
        </button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Group List</CardTitle>
        </CardHeader>
        <CardContent>
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  GROUP NAME
                </th>
                <th
                  scope="col"
                  className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  WORD COUNT
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {groups.map((group) => (
                <tr key={group.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-blue-600">
                    <Link to={`/groups/${group.id}`}>{group.name}</Link>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">
                    {group.word_count}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          
          <div className="mt-4 text-sm text-gray-500">
            Showing {groups.length} of {pagination?.total_items || groups.length} groups
          </div>
        </CardContent>
      </Card>

      {pagination && pagination.total_pages > 1 && (
        <div className="flex gap-2 justify-center mt-4">
          <button
            onClick={() => handlePageChange(Math.max(1, currentPage - 1))}
            disabled={currentPage === 1}
            className="px-3 py-1 border rounded hover:bg-muted disabled:opacity-50"
          >
            Previous
          </button>
          <span className="px-3 py-1">
            Page {currentPage} of {pagination.total_pages}
          </span>
          <button
            onClick={() => handlePageChange(Math.min(pagination.total_pages, currentPage + 1))}
            disabled={currentPage === pagination.total_pages}
            className="px-3 py-1 border rounded hover:bg-muted disabled:opacity-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};
