/**
 * Query Templates
 * 파라미터화된 질의 카드 (템플릿 탭)
 */

import { useState, useEffect } from 'react';
import { getTemplateOptions, type TemplateOptions } from '../../services/api';
import { QUERY_TEMPLATES } from './constants';

interface Props {
  onExecuteTemplate: (templateId: string, params: Record<string, string>) => void;
  isLoading: boolean;
}

export default function QueryTemplates({ onExecuteTemplate, isLoading }: Props) {
  const [options, setOptions] = useState<TemplateOptions | null>(null);
  const [paramValues, setParamValues] = useState<Record<string, Record<string, string>>>({});

  useEffect(() => {
    getTemplateOptions()
      .then(setOptions)
      .catch(() => {});
  }, []);

  const getOptionsForSource = (source: string): string[] => {
    if (!options) return [];
    switch (source) {
      case 'accelerators': return options.accelerators;
      case 'equipment_vendors': return options.equipment_vendors;
      case 'materials': return options.materials;
      case 'all_nodes': return options.all_nodes;
      default: return [];
    }
  };

  const setParam = (templateId: string, key: string, value: string) => {
    setParamValues(prev => ({
      ...prev,
      [templateId]: { ...prev[templateId], [key]: value },
    }));
  };

  const canExecute = (templateId: string): boolean => {
    const template = QUERY_TEMPLATES.find(t => t.id === templateId);
    if (!template) return false;
    return template.params.every(p => paramValues[templateId]?.[p.key]);
  };

  const handleExecute = (templateId: string) => {
    if (!canExecute(templateId)) return;
    onExecuteTemplate(templateId, paramValues[templateId]);
  };

  return (
    <div className="space-y-3">
      {QUERY_TEMPLATES.map((template) => (
        <div
          key={template.id}
          className="border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors"
        >
          <div className="flex items-start justify-between mb-2">
            <div>
              <h4 className="text-sm font-medium text-gray-800">{template.title}</h4>
              <p className="text-xs text-gray-500 mt-0.5">{template.desc}</p>
            </div>
          </div>

          <div className="flex items-end gap-3 mt-3">
            {template.params.map((param) => {
              const paramOptions = getOptionsForSource(param.optionSource);
              return (
                <div key={param.key} className="flex-1 min-w-0">
                  <label className="block text-[11px] text-gray-500 mb-1">{param.label}</label>
                  <select
                    value={paramValues[template.id]?.[param.key] || ''}
                    onChange={(e) => setParam(template.id, param.key, e.target.value)}
                    className="w-full px-2.5 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-1 focus:ring-nexus-500 focus:border-nexus-500 bg-white"
                  >
                    <option value="">선택...</option>
                    {paramOptions.map((opt) => (
                      <option key={opt} value={opt}>{opt}</option>
                    ))}
                  </select>
                </div>
              );
            })}

            <button
              onClick={() => handleExecute(template.id)}
              disabled={isLoading || !canExecute(template.id)}
              className="flex-shrink-0 px-4 py-1.5 text-sm bg-nexus-600 text-white rounded-md hover:bg-nexus-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              실행
            </button>
          </div>
        </div>
      ))}

      {!options && (
        <div className="text-center py-4">
          <div className="animate-spin w-5 h-5 border-2 border-gray-300 border-t-nexus-600 rounded-full mx-auto" />
          <p className="text-xs text-gray-400 mt-2">옵션 로딩 중...</p>
        </div>
      )}
    </div>
  );
}
