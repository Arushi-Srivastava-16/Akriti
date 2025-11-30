/**
 * Main App Component
 */

import React, { useState, useEffect } from 'react';
import { Home, AlertCircle, CheckCircle } from 'lucide-react';
import InputPanel from './components/InputPanel';
import FloorPlanCanvas from './components/FloorPlanCanvas';
import { parseText, generateSVG, exportSVG, healthCheck } from './services/api';

function App() {
  const [loading, setLoading] = useState(false);
  const [svgCode, setSvgCode] = useState(null);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [apiHealth, setApiHealth] = useState(null);

  // Check API health on mount
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const health = await healthCheck();
        setApiHealth(health);
      } catch (err) {
        console.error('API health check failed:', err);
      }
    };
    checkHealth();
  }, []);

  const handleGenerate = async (text) => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      // Step 1: Parse text to JSON
      console.log('Parsing text...');
      const parseResult = await parseText(text);
      console.log('Parse result:', parseResult);

      // Step 2: Generate SVG from JSON
      console.log('Generating SVG...');
      const generateResult = await generateSVG(parseResult.json);
      console.log('Generate result:', generateResult);

      // Step 3: Display SVG
      setSvgCode(generateResult.svg);
      setSuccess('Floor plan generated successfully!');

    } catch (err) {
      console.error('Generation error:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to generate floor plan');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format) => {
    if (!svgCode) return;

    try {
      const blob = await exportSVG(svgCode, format);
      
      // Download file
      const url = window.URL.createObjectURL(new Blob([blob]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `floorplan.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();

      setSuccess(`Exported as ${format.toUpperCase()}!`);
    } catch (err) {
      console.error('Export error:', err);
      setError('Failed to export floor plan');
    }
  };

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center">
              <Home className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">Akriti</h1>
              <p className="text-sm text-gray-500">AI Floor Plan Generator</p>
            </div>
          </div>

          {/* API Status */}
          {apiHealth && (
            <div className="flex items-center gap-2 text-sm">
              <div className={`w-2 h-2 rounded-full ${apiHealth.status === 'ok' ? 'bg-green-500' : 'bg-red-500'}`} />
              <span className="text-gray-600">
                {apiHealth.model_loaded ? 'Model Loaded' : 'Model Not Loaded (Using Placeholder)'}
              </span>
            </div>
          )}
        </div>
      </header>

      {/* Notifications */}
      {error && (
        <div className="mx-6 mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h3 className="text-sm font-medium text-red-900">Error</h3>
            <p className="text-sm text-red-700 mt-1">{error}</p>
          </div>
          <button
            onClick={() => setError(null)}
            className="text-red-600 hover:text-red-800"
          >
            ×
          </button>
        </div>
      )}

      {success && (
        <div className="mx-6 mt-4 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
          <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm text-green-700">{success}</p>
          </div>
          <button
            onClick={() => setSuccess(null)}
            className="text-green-600 hover:text-green-800"
          >
            ×
          </button>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: Input Panel */}
        <div className="w-1/3 min-w-[400px]">
          <InputPanel onGenerate={handleGenerate} loading={loading} />
        </div>

        {/* Right: Floor Plan Canvas */}
        <div className="flex-1">
          <FloorPlanCanvas svgCode={svgCode} onExport={handleExport} />
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 px-6 py-3">
        <p className="text-xs text-center text-gray-500">
          Akriti Floor Plan Generator v0.1.0 | Powered by CodeT5
        </p>
      </footer>
    </div>
  );
}

export default App;

