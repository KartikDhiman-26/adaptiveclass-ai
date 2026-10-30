import React, { useState, useRef } from 'react';
import { 
  X, UploadCloud, FileSpreadsheet, CheckCircle2, 
  AlertTriangle, ArrowRight, Database
} from 'lucide-react';
import { api } from '../api';

interface DataUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadSuccess?: (summary: { filename: string; rows: number; class_id?: number; class_name?: string }) => void;
}

export const DataUploadModal: React.FC<DataUploadModalProps> = ({
  isOpen,
  onClose,
  onUploadSuccess
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [validationResult, setValidationResult] = useState<{
    valid: boolean;
    rowCount: number;
    detectedColumns: string[];
    sampleErrors: Array<{ row: number; error: string }>;
  } | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  if (!isOpen) return null;

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelected(e.target.files[0]);
    }
  };

  const handleFileSelected = async (file: File) => {
    setSelectedFile(file);
    setIsProcessing(true);
    setErrorMessage(null);
    setValidationResult(null);

    try {
      const res = await api.validateDataset(file);
      setValidationResult({
        valid: res.valid,
        rowCount: res.row_count,
        detectedColumns: res.detected_columns,
        sampleErrors: res.sample_errors || []
      });
    } catch (err: any) {
      console.error("Dataset validation error:", err);
      setErrorMessage(err.message || "Failed to validate dataset schema");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleConfirmImport = async () => {
    if (!selectedFile) return;
    setIsProcessing(true);
    setErrorMessage(null);

    try {
      const res = await api.uploadDataset(selectedFile);
      if (onUploadSuccess) {
        onUploadSuccess({
          filename: res.filename || selectedFile.name,
          rows: res.row_count || validationResult?.rowCount || 0,
          class_id: res.class_id,
          class_name: res.class_name
        });
      }
      onClose();
    } catch (err: any) {
      console.error("Dataset upload error:", err);
      setErrorMessage(err.message || "Failed to ingest dataset into PostgreSQL");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div 
      className="fixed inset-0 z-50 overflow-y-auto bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-150"
      role="dialog"
      aria-modal="true"
      aria-labelledby="upload-modal-title"
    >
      <div className="bg-[#202020] rounded-2xl border border-[#343434] max-w-xl w-full shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="bg-[#171717] px-6 py-4.5 flex items-center justify-between border-b border-[#343434]">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-[#0B1B14] border border-[#20372B] flex items-center justify-center text-[#A31C1B]">
              <UploadCloud className="w-5 h-5 text-[#A31C1B]" />
            </div>
            <div>
              <h3 id="upload-modal-title" className="text-base font-bold text-[#F5F2EF]">
                Import Student Dataset
              </h3>
              <p className="text-xs text-[#B7B3B0] font-mono mt-0.5">
                AI-assisted column mapping & validation
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            aria-label="Close dialog"
            className="text-[#898582] hover:text-[#F5F2EF] p-1.5 rounded-lg hover:bg-[#343434] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-5">
          {/* Dropzone */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all ${
              isDragging
                ? 'border-[#A31C1B] bg-[#261214]/60 ring-2 ring-[#A31C1B]/30'
                : 'border-[#343434] bg-[#171717] hover:border-[#A31C1B]/70 hover:bg-[#0B1B14]/40'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".xlsx,.xlsm,.csv,.json"
              onChange={handleFileInputChange}
              className="hidden"
            />
            
            <div className="w-12 h-12 rounded-xl bg-[#0B1B14] border border-[#20372B] text-[#A31C1B] flex items-center justify-center mx-auto mb-3 shadow-inner">
              <FileSpreadsheet className="w-6 h-6 text-[#A31C1B]" />
            </div>

            <h4 className="text-sm font-semibold text-[#F5F2EF]">
              {selectedFile ? selectedFile.name : 'Drop Excel, CSV, or JSON dataset here'}
            </h4>
            <p className="text-xs text-[#898582] mt-1 max-w-sm mx-auto">
              Drag and drop your academic workbook or click to browse local files
            </p>

            {/* Supported formats */}
            <div className="flex items-center justify-center space-x-2 mt-4 font-mono text-[10px]">
              <span className="px-2 py-0.5 rounded bg-[#0B1B14] text-[#B7B3B0] border border-[#20372B]">
                .XLSX
              </span>
              <span className="px-2 py-0.5 rounded bg-[#0B1B14] text-[#B7B3B0] border border-[#20372B]">
                .CSV
              </span>
              <span className="px-2 py-0.5 rounded bg-[#0B1B14] text-[#B7B3B0] border border-[#20372B]">
                .JSON
              </span>
            </div>
          </div>

          {/* Validation Feedback & Preview */}
          {isProcessing && (
            <div className="p-4 rounded-xl bg-[#0B1B14] border border-[#20372B] text-xs text-[#B7B3B0] flex items-center space-x-3">
              <span className="w-4 h-4 rounded-full border-2 border-[#A31C1B] border-t-transparent animate-spin" />
              <span>Analyzing schema headers and validating records against PostgreSQL...</span>
            </div>
          )}

          {errorMessage && (
            <div className="p-3.5 rounded-xl bg-red-950/40 border border-red-800/60 text-xs text-red-200 flex items-start space-x-2.5">
              <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-red-300">Validation Error</p>
                <p className="text-[11px] mt-0.5 text-red-200/90 font-mono">{errorMessage}</p>
              </div>
            </div>
          )}

          {validationResult && !isProcessing && (
            <div className="space-y-3 p-4 rounded-xl bg-[#171717] border border-[#343434] text-xs">
              <div className="flex items-center justify-between pb-3 border-b border-[#343434]">
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span className="font-semibold text-[#F5F2EF]">Validation Passed</span>
                </div>
                <span className="font-mono text-[11px] text-[#A31C1B] font-bold">
                  {validationResult.rowCount.toLocaleString()} rows verified
                </span>
              </div>

              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-[#898582] block mb-1.5">
                  Mapped Schema Columns:
                </span>
                <div className="flex flex-wrap gap-1">
                  {validationResult.detectedColumns.map((col) => (
                    <span 
                      key={col}
                      className="px-2 py-0.5 rounded bg-[#0B1B14] text-[#B7B3B0] font-mono text-[10px] border border-[#20372B]"
                    >
                      {col}
                    </span>
                  ))}
                </div>
              </div>

              <div className="pt-2 flex items-center space-x-2 text-[11px] text-[#B7B3B0]">
                <Database className="w-3.5 h-3.5 text-emerald-400" />
                <span>Ready to insert into PostgreSQL 17</span>
              </div>
            </div>
          )}

          {/* Teacher Agency Note */}
          <div className="p-3 bg-[#0B1B14] rounded-xl border border-[#20372B] text-[11px] text-[#898582] flex items-center space-x-2">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
            <span>Uploaded data updates continuous analytics while preserving historical baselines.</span>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="bg-[#171717] px-6 py-4 flex items-center justify-end space-x-3 border-t border-[#343434]">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-semibold text-[#B7B3B0] hover:text-[#F5F2EF] hover:bg-[#343434] transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirmImport}
            disabled={!validationResult || isProcessing}
            className="px-5 py-2.5 rounded-xl bg-[#A31C1B] hover:bg-[#C12A29] active:bg-[#7F1717] text-[#F5F2EF] font-bold text-xs transition-colors flex items-center space-x-2 disabled:opacity-40 disabled:cursor-not-allowed shadow-md shadow-[#A31C1B]/20"
          >
            <span>Confirm & Import Dataset</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
