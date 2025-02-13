export interface StudySessionResponse {
  id: number
  activity_name?: string
  group_name?: string
  start_time?: string
  end_time?: string
  review_items_count: number
}

export interface Pagination {
  current_page: number
  total_pages: number
  total_items: number
  items_per_page: number
}

export interface PaginatedResponse<T> {
  items: T[]
  pagination: Pagination
}
