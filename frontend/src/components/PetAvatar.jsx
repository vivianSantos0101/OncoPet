import { useState } from 'react'
import { Camera, X } from 'lucide-react'
import api, { getErrorMessage } from '../api'
import { checkImage, uploadPetPhoto } from '../image'
import PhotoCropper from './PhotoCropper'

/**
 * Foto do pet (ou a inicial do nome, se nao houver foto).
 * editable: vira botao para enviar/trocar a foto (abre o ajuste antes de enviar)
 * e mostra o "x" para remover.
 */
function PetAvatar({ pet, size = 50, radius = 16, editable = false, onChanged, onError }) {
  const [busy, setBusy] = useState(false)
  const [cropSrc, setCropSrc] = useState(null)
  const style = { width: size, height: size, borderRadius: radius, fontSize: Math.round(size * 0.4) }
  const content = pet.photo_url
    ? <img src={pet.photo_url} alt={`Foto de ${pet.name}`} />
    : pet.name.charAt(0).toUpperCase()

  if (!editable) return <div className="pet-avatar" style={style}>{content}</div>

  const run = async (action) => {
    setBusy(true)
    try {
      onChanged?.(await action())
    } catch (err) {
      onError?.(err.response ? getErrorMessage(err, 'Erro ao salvar a foto') : err.message)
    } finally {
      setBusy(false)
    }
  }

  const closeCropper = () => {
    if (cropSrc) URL.revokeObjectURL(cropSrc)
    setCropSrc(null)
  }

  const handleFile = async (e) => {
    const file = e.target.files?.[0]
    e.target.value = ''  // permite escolher o mesmo arquivo de novo
    if (!file) return
    try {
      setCropSrc(await checkImage(file))
    } catch (err) {
      onError?.(err.message)
    }
  }

  const handleCropped = (blob) => {
    closeCropper()
    run(() => uploadPetPhoto(api, pet.id, blob))
  }

  const handleRemove = () => run(async () => (await api.delete(`/pets/${pet.id}/photo`)).data)

  return (
    <div className="avatar-edit">
      <label className={`pet-avatar ${busy ? 'is-busy' : ''}`} style={style} title={pet.photo_url ? 'Trocar foto' : 'Adicionar foto'}>
        {content}
        <input type="file" accept="image/*" onChange={handleFile} disabled={busy} aria-label={`Foto de ${pet.name}`} />
        <span className="avatar-badge" aria-hidden="true"><Camera size={14} /></span>
      </label>
      {pet.photo_url && !busy && (
        <button type="button" className="avatar-remove" onClick={handleRemove} aria-label="Remover foto" title="Remover foto">
          <X size={12} />
        </button>
      )}
      {cropSrc && <PhotoCropper src={cropSrc} onCancel={closeCropper} onConfirm={handleCropped} />}
    </div>
  )
}

export default PetAvatar
