import { useEffect } from 'react'
import AdaptiveConversationsIndex from '@/features/adaptive-conversations/AdaptiveConversationsIndex'

export default function AdaptiveConversations() {
  useEffect(() => {
    // Check if AWS credentials are configured
    const checkAwsConfig = async () => {
      try {
        // This is just a placeholder to show integration with the existing system
        // In a real implementation, you might want to check if the AWS services are accessible
        console.log('Adaptive Conversations initialized')
      } catch (error) {
        console.error('Error initializing Adaptive Conversations:', error)
      }
    }

    checkAwsConfig()
  }, [])

  return <AdaptiveConversationsIndex />
}
