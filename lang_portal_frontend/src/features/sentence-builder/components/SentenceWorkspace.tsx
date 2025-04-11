import React, { useRef } from 'react';
import { useDrag, useDrop } from 'react-dnd';
import { Word } from '../types';
import { Card, CardContent } from '@/components/ui/card';
import { X } from 'lucide-react';

interface DragItem {
  index: number;
  id: string;
  type: string;
}

interface WordCardProps {
  word: Word;
  index: number;
  onRemove: (index: number) => void;
  onReorder: (dragIndex: number, hoverIndex: number) => void;
}

const WordCard: React.FC<WordCardProps> = ({ word, index, onRemove, onReorder }) => {
  const ref = useRef<HTMLDivElement>(null);
  
  const [{ isDragging }, drag] = useDrag({
    type: 'WORD',
    item: () => ({ index, id: `word-${word.id}`, type: 'WORD' }),
    collect: (monitor) => ({
      isDragging: monitor.isDragging(),
    }),
  });
  
  const [, drop] = useDrop<DragItem>({
    accept: 'WORD',
    hover: (item, monitor) => {
      if (!ref.current) return;
      
      const dragIndex = item.index;
      const hoverIndex = index;
      
      if (dragIndex === hoverIndex) return;
      
      const hoverBoundingRect = ref.current.getBoundingClientRect();
      const hoverMiddleX = (hoverBoundingRect.right - hoverBoundingRect.left) / 2;
      const clientOffset = monitor.getClientOffset();
      
      if (!clientOffset) return;
      
      const hoverClientX = clientOffset.x - hoverBoundingRect.left;
      
      if (dragIndex < hoverIndex && hoverClientX < hoverMiddleX) return;
      if (dragIndex > hoverIndex && hoverClientX > hoverMiddleX) return;
      
      onReorder(dragIndex, hoverIndex);
      item.index = hoverIndex;
    },
  });
  
  drag(drop(ref));
  
  return (
    <div
      ref={ref}
      className={`inline-block mx-1 my-2 ${isDragging ? 'opacity-50' : 'opacity-100'}`}
    >
      <Card className="relative cursor-move">
        <button
          className="absolute top-1 right-1 p-1 rounded-full bg-muted hover:bg-muted-foreground/20 transition-colors"
          onClick={() => onRemove(index)}
        >
          <X className="h-3 w-3" />
        </button>
        <CardContent className="p-3 text-center">
          <div dir="rtl" lang="ur" className="text-lg font-medium">
            {word.urdu_word}
          </div>
          <div className="text-xs text-muted-foreground mt-1">
            {word.roman_urdu}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

interface SentenceWorkspaceProps {
  selectedWords: Word[];
  onRemoveWord: (index: number) => void;
  onReorderWord: (dragIndex: number, hoverIndex: number) => void;
}

export const SentenceWorkspace: React.FC<SentenceWorkspaceProps> = ({
  selectedWords,
  onRemoveWord,
  onReorderWord,
}) => {
  return (
    <div className="border rounded-lg p-4 min-h-[200px] flex flex-wrap items-start justify-end">
      {selectedWords.length === 0 ? (
        <div className="w-full text-center text-muted-foreground py-10">
          Select words from the word bank to build your sentence
        </div>
      ) : (
        <div className="w-full flex flex-wrap justify-end" dir="rtl">
          {selectedWords.map((word, index) => (
            <WordCard
              key={`${word.id}-${index}`}
              word={word}
              index={index}
              onRemove={onRemoveWord}
              onReorder={onReorderWord}
            />
          ))}
        </div>
      )}
    </div>
  );
};
