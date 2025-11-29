import { useRef, useState, useCallback } from 'react';
import { MdAttachFile, MdClose, MdDescription } from 'react-icons/md';
import { useValidation } from '@/hooks/useValidation';
import { useToast } from '@/hooks/useToast';

interface DocumentUploadProps {
  onFileSelect: (file: File, content: string) => void;
  onFileRemove: () => void;
  selectedFile: File | null;
  disabled?: boolean;
  className?: string;
}

// Allowed file types for document upload
const ALLOWED_FILE_TYPES = [
  'text/plain',
  'application/pdf', 
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'text/markdown'
];

const ALLOWED_EXTENSIONS = ['.txt', '.pdf', '.docx', '.md'];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB limit

export function DocumentUpload({
  onFileSelect,
  onFileRemove,
  selectedFile,
  disabled = false,
  className = ''
}: DocumentUploadProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const { error: showError } = useToast();

  const validateFile = useCallback((file: File): string | null => {
    // Check file size
    if (file.size > MAX_FILE_SIZE) {
      return `File size must be less than ${MAX_FILE_SIZE / 1024 / 1024}MB`;
    }

    // Check file type
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(fileExtension)) {
      return `Only ${ALLOWED_EXTENSIONS.join(', ')} files are supported`;
    }

    if (!ALLOWED_FILE_TYPES.includes(file.type) && file.type !== '') {
      return `File type ${file.type} is not supported`;
    }

    return null;
  }, []);

  const processFile = useCallback(async (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = (e) => {
        const result = e.target?.result;
        if (typeof result === 'string') {
          resolve(result);
        } else {
          reject(new Error('Failed to read file content'));
        }
      };
      
      reader.onerror = () => {
        reject(new Error('Failed to read file'));
      };
      
      // For text files, read as text
      if (file.type.startsWith('text/') || file.name.endsWith('.md')) {
        reader.readAsText(file);
      } else {
        // For other files like PDF, DOCX, we'll need backend processing
        // For now, just read as text to get basic content
        reader.readAsText(file);
      }
    });
  }, []);

  const handleFileSelect = useCallback(async (file: File) => {
    const validation = validateFile(file);
    if (validation) {
      showError('Invalid File', validation);
      return;
    }

    setIsProcessing(true);
    try {
      const content = await processFile(file);
      onFileSelect(file, content);
    } catch (error) {
      showError('File Processing Failed', 'Could not process the selected file');
    } finally {
      setIsProcessing(false);
    }
  }, [validateFile, processFile, onFileSelect, showError]);

  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  }, [handleFileSelect]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    if (disabled) return;
    
    const file = e.dataTransfer.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  }, [disabled, handleFileSelect]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled) {
      setIsDragOver(true);
    }
  }, [disabled]);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleButtonClick = useCallback(() => {
    if (!disabled) {
      fileInputRef.current?.click();
    }
  }, [disabled]);

  const handleRemoveFile = useCallback(() => {
    onFileRemove();
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [onFileRemove]);

  return (
    <div className={`space-y-2 ${className}`}>
      {/* File Input (Hidden) */}
      <input
        ref={fileInputRef}
        type="file"
        accept={ALLOWED_EXTENSIONS.join(',')}
        onChange={handleFileInputChange}
        className="hidden"
        disabled={disabled}
      />

      {/* Selected File Display */}
      {selectedFile && (
        <div className="flex items-center gap-2 p-2 bg-[#444444] border border-[#666666] rounded-lg">
          <MdDescription className="text-blue-400" size={16} />
          <span className="text-white text-sm flex-1 truncate">
            {selectedFile.name}
          </span>
          <span className="text-gray-400 text-xs">
            {(selectedFile.size / 1024).toFixed(1)}KB
          </span>
          {!disabled && (
            <button
              onClick={handleRemoveFile}
              className="text-gray-400 hover:text-white p-1 rounded"
              aria-label="Remove file"
            >
              <MdClose size={14} />
            </button>
          )}
        </div>
      )}

      {/* Upload Area */}
      {!selectedFile && (
        <div
          className={`
            border-2 border-dashed rounded-lg p-4 text-center transition-colors cursor-pointer
            ${isDragOver 
              ? 'border-blue-400 bg-blue-400/10' 
              : 'border-[#666666] hover:border-[#888888]'
            }
            ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
          `}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={handleButtonClick}
        >
          <div className="flex flex-col items-center gap-2">
            <MdAttachFile 
              size={24} 
              className={isDragOver ? 'text-blue-400' : 'text-gray-400'} 
            />
            <div className="text-sm text-gray-300">
              {isProcessing ? (
                <span>Processing file...</span>
              ) : (
                <>
                  <span className="text-white">Click to upload</span> or drag and drop
                  <br />
                  <span className="text-xs text-gray-400">
                    Supports: {ALLOWED_EXTENSIONS.join(', ')} (max {MAX_FILE_SIZE / 1024 / 1024}MB)
                  </span>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}