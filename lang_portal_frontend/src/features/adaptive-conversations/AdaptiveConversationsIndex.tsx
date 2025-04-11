import { useState, useEffect, useRef, ChangeEvent, KeyboardEvent } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { adaptiveConversationsApi, Message } from '@/services/adaptive-conversations-api'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

// Create a simple textarea component since we're missing the UI component
const Textarea = ({ 
  value, 
  onChange, 
  placeholder, 
  className, 
  onKeyDown 
}: { 
  value: string; 
  onChange: (e: ChangeEvent<HTMLTextAreaElement>) => void; 
  placeholder?: string; 
  className?: string; 
  onKeyDown?: (e: KeyboardEvent<HTMLTextAreaElement>) => void; 
}) => (
  <textarea
    value={value}
    onChange={onChange}
    placeholder={placeholder}
    className={`p-2 border rounded ${className}`}
    onKeyDown={onKeyDown}
  />
);

export default function AdaptiveConversationsIndex() {
  const [message, setMessage] = useState('')
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const [userId] = useState('user-1') // Default user ID
  const [knowledgeLevel, setKnowledgeLevel] = useState('beginner')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Scroll to bottom of messages when new ones are added
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Load conversation from local storage if available
  useEffect(() => {
    const savedConversationId = localStorage.getItem('adaptive_conversation_id')
    if (savedConversationId) {
      setConversationId(savedConversationId)
      loadConversationHistory(savedConversationId)
    }
  }, [])

  const loadConversationHistory = async (conversationId: string) => {
    try {
      setLoading(true)
      const history = await adaptiveConversationsApi.getConversationHistory(conversationId, userId)
      setMessages(history.messages)
    } catch (error) {
      console.error('Error loading conversation history:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSendMessage = async () => {
    if (!message.trim()) return

    try {
      // Add user message to the UI immediately
      const userMessage: Message = {
        text: message,
        role: 'user',
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, userMessage])
      setMessage('')
      setLoading(true)

      // Send message to API
      const response = await adaptiveConversationsApi.sendMessage({
        message,
        user_id: userId,
        conversation_id: conversationId,
        knowledge_level: knowledgeLevel,
      })

      // Update conversation ID if this is a new conversation
      if (!conversationId) {
        setConversationId(response.conversation_id)
        localStorage.setItem('adaptive_conversation_id', response.conversation_id)
      }

      // Add assistant response to the UI
      const assistantMessage: Message = {
        text: response.response,
        role: 'assistant',
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      console.error('Error sending message:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleStartNewConversation = () => {
    setConversationId(null)
    setMessages([])
    localStorage.removeItem('adaptive_conversation_id')
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-3xl font-bold">اردو گفتگو</h1>
        <div className="flex gap-2">
          <Select value={knowledgeLevel} onValueChange={setKnowledgeLevel}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="مہارت کی سطح" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="beginner">ابتدائی</SelectItem>
              <SelectItem value="intermediate">درمیانہ</SelectItem>
              <SelectItem value="advanced">ماہر</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={handleStartNewConversation}>نئی گفتگو شروع کریں</Button>
        </div>
      </div>

      <Card className="flex-1 mb-4 overflow-hidden">
        <div className="p-4 h-full overflow-y-auto" dir="rtl">
          <div className="space-y-4">
            {messages.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <p>اردو میں گفتگو شروع کرنے کے لیے پیغام بھیجیں</p>
              </div>
            ) : (
              messages.map((msg, index) => (
                <div
                  key={index}
                  className={`flex ${
                    msg.role === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg p-3 ${
                      msg.role === 'user'
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted'
                    }`}
                  >
                    <p className="text-right">{msg.text}</p>
                  </div>
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>
      </Card>

      <div className="flex gap-2" dir="rtl">
        <Textarea
          value={message}
          onChange={(e: ChangeEvent<HTMLTextAreaElement>) => setMessage(e.target.value)}
          placeholder="اردو میں پیغام لکھیں..."
          className="flex-1 resize-none"
          onKeyDown={(e: KeyboardEvent<HTMLTextAreaElement>) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              handleSendMessage()
            }
          }}
        />
        <Button
          onClick={handleSendMessage}
          disabled={loading || !message.trim()}
          className="h-auto"
        >
          {loading ? 'بھیج رہا ہے...' : 'بھیجیں'}
        </Button>
      </div>
    </div>
  )
}
