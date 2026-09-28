import { useEffect, useState } from 'react'
import { ImagePlus, X } from 'lucide-react'
import { checkImage } from '../image'
import PhotoCropper from './PhotoCropper'

/**
 * Campo opcional de foto no cadastro do pet. Ao escolher a imagem abre o
 * ajuste; o arquivo ja recortado e enviado depois que o pet e criado.
 */
function PhotoField({ file, onChange }) {
  const [preview, setPreview] = useState(null)
  const [cropSrc, setCropSrc] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!file) { setPreview(null); return }
    const url = URL.createObjectURL(file)
    setPreview(url)
    return () => URL.revokeObjectURL(url)
  }, [file])

  const closeCropper = () => {
    if (cropSrc) URL.revokeObjectURL(cropSrc)
    setCropSrc(null)
  }

  const handleFile = async (e) => {
    const chosen = e.target.files?.[0]
    e.target.value = ''
    if (!chosen) return
    setError('')
    try {
      setCropSrc(await checkImage(chosen))
    } catch (err) {
      setError(err.message)
    }
  }

  const handleCropped = (blob) => {
    closeCropper()
    onChange(new File([blob], 'foto.jpg', { type: 'image/jpeg' }))
  }

  return (
    <>
      <div className="photo-field">
        <label className="photo-drop">
          {preview ? <img src={preview} alt="Pre-visualizacao da foto" /> : <ImagePlus size={22} />}
          <input type="file" accept="image/*" onChange={handleFile} />
        </label>
        <div className="photo-field-text">
          <strong>{file ? 'Foto ajustada' : 'Foto do pet'}</strong>
          <span>{file ? 'Toque na foto para escolher outra' : 'Opcional · toque para escolher'}</span>
        </div>
        {file && (
          <button type="button" className="notif-icon" onClick={() => onChange(null)} aria-label="Tirar foto escolhida"><X size={16} /></button>
        )}
      </div>
      {error && <p className="error">{error}</p>}
      {cropSrc && <PhotoCropper src={cropSrc} onCancel={closeCropper} onConfirm={handleCropped} />}
    </>
  )
}

export default PhotoField
