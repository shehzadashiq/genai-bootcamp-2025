import React from 'react';
import { SentenceFeedbackType } from '../types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle, AlertCircle } from 'lucide-react';

interface SentenceFeedbackProps {
  feedback: SentenceFeedbackType;
}

export const SentenceFeedback: React.FC<SentenceFeedbackProps> = ({ feedback }) => {
  return (
    <Card className={feedback.isValid ? 'border-green-200' : 'border-amber-200'}>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center text-lg">
          {feedback.isValid ? (
            <>
              <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
              <span>Valid Sentence</span>
            </>
          ) : (
            <>
              <AlertCircle className="h-5 w-5 text-amber-500 mr-2" />
              <span>Needs Improvement</span>
            </>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p>{feedback.feedback}</p>
        
        {feedback.similarPatterns.length > 0 && !feedback.isValid && (
          <div>
            <h4 className="font-medium mb-2">Suggested Patterns:</h4>
            <div className="space-y-2">
              {feedback.similarPatterns.map((pattern, index) => (
                <div 
                  key={index} 
                  className="p-3 bg-muted rounded-md"
                >
                  <div className="font-medium">{pattern.pattern}</div>
                  {pattern.example && (
                    <div className="mt-1 text-sm">
                      <span className="text-muted-foreground">Example: </span>
                      <span dir="rtl" lang="ur" className="inline-block">{pattern.example.split('(')[0].trim()}</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
