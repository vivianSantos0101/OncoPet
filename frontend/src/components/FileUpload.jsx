import { useState, useRef } from 'react'
import api, { getErrorMessage } from '../api'

function FileUpload({ onUploaded }) {
  const [isDragging, setIsDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const fileInputRef = useRef(null)

  const handleUpload = async (file) => {
    setError('')
    setUploading(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      const res = await api.post('/uploads/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      onUploaded(res.data)
    } catch (err) {
      setError(getErrorMessage(err, 'Erro no upload'))
    } finally {
      setUploading(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleUpload(file)
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => setIsDragging(false)

  const handleClick = () => fileInputRef.current?.click()

  const handleFileSelect = (e) => {
    const file = e.target.files[0]
    if (file) handleUpload(file)
  }

  return (
    <div>
      <div
        onClick={handleClick}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        style={{
          border: `2px dashed ${isDragging ? 'var(--mint)' : 'var(--border)'}`,
          borderRadius: 'var(--radius)',
          padding: '32px 24px',
          textAlign: 'center',
          cursor: 'pointer',
          background: isDragging ? 'var(--mint-light)' : '#fafafa',
          transition: 'all 0.2s',
          marginBottom: 12,
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleFileSelect}
          accept=".jpg,.jpeg,.png,.gif,.pdf,.doc,.docx,.xls,.xlsx,.dcm"
          style={{ display: 'none' }}
        />
        {uploading ? (
          <p style={{ color: 'var(--mint-dark)', fontWeight: 600 }}>Enviando...</p>
        ) : (
          <>
            <p style={{ fontWeight: 600, color: 'var(--text)' }}>
              Arraste um arquivo aqui
            </p>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>
              ou clique para selecionar (JPG, PNG, PDF, DOC - max 20MB)
            </p>
          </>
        )}
      </div>
      {error && <p className="error">{error}</p>}
    </div>
  )
}

export default FileUpload
