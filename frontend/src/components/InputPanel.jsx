/**
 * Input Panel Component
 * Text input area for floor plan description.
 */

import React, { useState } from 'react';
import { FileText, Loader, Wand2 } from 'lucide-react';

const InputPanel = ({ onGenerate, loading }) => {
  const [text, setText] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (text.trim()) {
      onGenerate(text);
    }
  };

  const exampleText = `The balcony is at the north corner with the master room to the south. It is approximately 12 feet wide by 5 feet deep, for a total square footage of 60. The bathroom is in the northeast corner with the common room to the south and the living room to the west. It is approximately 12 feet wide by 5 feet deep, for a total square footage of 60. The living room is at the northwest corner, with the bathroom to the east and the kitchen to the south. It is approximately 15 feet wide by 20 feet deep, for a total square footage of 300.`;

  const loadExample = () => {
    setText(exampleText);
  };

  return (
    <div className="h-full flex flex-col bg-white border-r border-gray-200">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-primary-600" />
          <h2 className="text-lg font-semibold text-gray-900">
            Describe Your Floor Plan
          </h2>
        </div>
        <p className="mt-1 text-sm text-gray-500">
          Describe your floor plan in natural language
        </p>
      </div>

      {/* Input Area */}
      <form onSubmit={handleSubmit} className="flex-1 flex flex-col p-6">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Example: The living room is at the north corner with the kitchen to the south. It is approximately 15 feet wide by 20 feet deep..."
          className="flex-1 w-full px-4 py-3 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          disabled={loading}
        />

        {/* Actions */}
        <div className="mt-4 flex gap-3">
          <button
            type="button"
            onClick={loadExample}
            className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            disabled={loading}
          >
            Load Example
          </button>
          <button
            type="submit"
            disabled={loading || !text.trim()}
            className="flex-1 px-4 py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader className="w-5 h-5 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Wand2 className="w-5 h-5" />
                Generate Floor Plan
              </>
            )}
          </button>
        </div>

        {/* Tips */}
        <div className="mt-4 p-4 bg-blue-50 rounded-lg">
          <p className="text-sm font-medium text-blue-900 mb-2">
            💡 Tips for better results:
          </p>
          <ul className="text-sm text-blue-700 space-y-1 list-disc list-inside">
            <li>Mention room types (living room, bedroom, kitchen, etc.)</li>
            <li>Include positions (north, south, adjacent to, etc.)</li>
            <li>Add dimensions (X feet wide by Y feet deep)</li>
            <li>Specify relationships between rooms</li>
          </ul>
        </div>
      </form>
    </div>
  );
};

export default InputPanel;

