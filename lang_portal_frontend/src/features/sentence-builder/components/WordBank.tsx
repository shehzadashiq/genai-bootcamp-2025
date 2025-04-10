import React from 'react';
import { Word, WordCategory } from '../types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';

interface WordBankProps {
  categories: WordCategory[];
  wordsByCategory: Record<number, Word[]>;
  onSelectWord: (word: Word) => void;
  activeCategory: number | null;
  setActiveCategory: (id: number) => void;
}

export const WordBank: React.FC<WordBankProps> = ({
  categories,
  wordsByCategory,
  onSelectWord,
  activeCategory,
  setActiveCategory,
}) => {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Word Bank</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {categories.map((category) => (
              <Button
                key={category.id}
                variant={activeCategory === category.id ? "default" : "outline"}
                size="sm"
                onClick={() => setActiveCategory(category.id)}
              >
                {category.name}
              </Button>
            ))}
          </div>

          <ScrollArea className="h-[400px] pr-4">
            {activeCategory && wordsByCategory[activeCategory] ? (
              <div className="grid grid-cols-1 gap-2">
                {wordsByCategory[activeCategory].map((word) => (
                  <Card
                    key={word.id}
                    className="cursor-pointer hover:bg-accent transition-colors"
                    onClick={() => onSelectWord(word)}
                  >
                    <CardContent className="p-3">
                      <div className="text-right mb-1" dir="rtl" lang="ur">
                        <span className="text-lg font-medium">{word.urdu_word}</span>
                      </div>
                      <div className="text-sm text-muted-foreground">
                        <div>{word.roman_urdu}</div>
                        <div>{word.english_translation}</div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                {activeCategory
                  ? "No words available in this category"
                  : "Select a category to view words"}
              </div>
            )}
          </ScrollArea>
        </div>
      </CardContent>
    </Card>
  );
};
