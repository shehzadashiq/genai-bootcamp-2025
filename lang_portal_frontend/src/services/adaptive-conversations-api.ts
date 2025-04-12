import axios from 'axios'

// Types
export interface SendMessageRequest {
  message: string
  user_id: string
  conversation_id: string | null
  knowledge_level: string
  topic?: string
}

export interface AdaptiveConversationResponse {
  conversation_id: string
  response: string
  knowledge_level: string
}

export interface Message {
  text: string
  role: 'user' | 'assistant'
  timestamp: string
}

export interface ConversationHistoryResponse {
  conversation_id: string
  user_id: string
  messages: Message[]
}

// API service
const API_URL = `${import.meta.env.VITE_API_URL}/api/adaptive-conversations`

export const adaptiveConversationsApi = {
  /**
   * Send a message to the adaptive conversation system
   */
  sendMessage: async (request: SendMessageRequest): Promise<AdaptiveConversationResponse> => {
    const response = await axios.post(`${API_URL}/message`, request)
    return response.data
  },

  /**
   * Get conversation history
   */
  getConversationHistory: async (
    conversationId: string,
    userId: string
  ): Promise<ConversationHistoryResponse> => {
    const response = await axios.get(
      `${API_URL}/history/${conversationId}?user_id=${userId}`
    )
    return response.data
  },
}
