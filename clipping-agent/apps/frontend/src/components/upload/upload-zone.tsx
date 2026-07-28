'use client'

import { useState, useCallback } from 'react'

interface UploadZoneProps {
  onFileSelected: (file: File) => void
  onUrlSubmit: (url: string) => void
}

export function UploadZone({ onFileSelected, onUrlSubmit }: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [url, setUrl] = useState('')
  const [isUploading, setIsUploading] = useState(false)

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(e.type === 'dragenter' || e.type === 'dragover')
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file && file.type.startsWith('video/')) {
      setIsUploading(true)
      onFileSelected(file)
    }
  }, [onFileSelected])

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setIsUploading(true)
      onFileSelected(file)
    }
  }, [onFileSelected])

  return (
    <div className="space-y-6">
      <label
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`flex flex-col items-center justify-center border-2 border-dashed rounded-xl p-12 text-center transition-colors cursor-pointer ${
          isDragging ? 'border-[#3b82f6] bg-blue-500/5' : 'border-[#3a3a3a] hover:border-[#5a5a5a]'
        }`}
      >
        <input type="file" accept="video/*" onChange={handleFileInput} className="hidden" />
        <div className="text-3xl mb-4 text-[#a0a0a0]">📁</div>
        {isUploading ? (
          <p className="text-[#3b82f6] font-medium">Uploading...</p>
        ) : (
          <>
            <p className="text-[#f5f5f5] font-medium mb-1">Drop video here or click to browse</p>
            <p className="text-sm text-[#6b6b6b]">MP4, MOV, AVI up to 4GB</p>
          </>
        )}
      </label>

      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-[#2a2a2a]" />
        </div>
        <div className="relative flex justify-center">
          <span className="px-4 text-sm text-[#6b6b6b] bg-[#0a0a0a]">or paste a URL</span>
        </div>
      </div>

      <div className="flex gap-3">
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://youtube.com/watch?v=..."
          className="flex-1 h-10 px-3 rounded-md bg-[#1c1c1c] border border-[#2a2a2a] text-sm text-[#f5f5f5] placeholder:text-[#6b6b6b] focus:outline-none focus:border-[#3b82f6]"
        />
        <button
          onClick={() => url && onUrlSubmit(url)}
          disabled={!url}
          className="h-10 px-6 rounded-md bg-[#3b82f6] text-white text-sm font-medium disabled:opacity-50 hover:bg-[#2563eb] transition-colors"
        >
          Import
        </button>
      </div>
    </div>
  )
}
