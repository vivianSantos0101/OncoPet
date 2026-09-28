// Utilitarios da foto do pet: recorte no navegador e envio para a API.

export const PHOTO_SIZE = 600  // a foto final e um quadrado de 600x600

function loadImage(src) {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => resolve(img)
    img.onerror = () => reject(new Error('Esse arquivo nao e uma imagem valida (use JPG, PNG ou WEBP)'))
    img.src = src
  })
}

/** Confere se o arquivo abre como imagem antes de mostrar o recorte. */
export async function checkImage(file) {
  if (!file.type.startsWith('image/')) {
    throw new Error('Escolha um arquivo de imagem (JPG, PNG ou WEBP)')
  }
  const url = URL.createObjectURL(file)
  try {
    await loadImage(url)
    return url  // quem chamar deve liberar com URL.revokeObjectURL
  } catch (err) {
    URL.revokeObjectURL(url)
    throw err
  }
}

/**
 * Recorta a area escolhida (pixels da imagem ja girada) e devolve um JPEG
 * quadrado de PHOTO_SIZE px. rotation em graus (0, 90, 180, 270).
 */
export async function cropImage(src, area, rotation = 0, size = PHOTO_SIZE) {
  const img = await loadImage(src)
  const rad = (rotation * Math.PI) / 180
  const sin = Math.abs(Math.sin(rad))
  const cos = Math.abs(Math.cos(rad))
  const rotW = img.width * cos + img.height * sin
  const rotH = img.width * sin + img.height * cos

  // 1) desenha a imagem inteira ja girada
  const rotated = document.createElement('canvas')
  rotated.width = Math.round(rotW)
  rotated.height = Math.round(rotH)
  const rctx = rotated.getContext('2d')
  rctx.translate(rotW / 2, rotH / 2)
  rctx.rotate(rad)
  rctx.drawImage(img, -img.width / 2, -img.height / 2)

  // 2) copia so a area escolhida, no tamanho final
  const out = document.createElement('canvas')
  out.width = size
  out.height = size
  const octx = out.getContext('2d')
  octx.fillStyle = '#ffffff'
  octx.fillRect(0, 0, size, size)
  octx.drawImage(rotated, area.x, area.y, area.width, area.height, 0, 0, size, size)

  return new Promise((resolve, reject) => {
    out.toBlob(b => (b ? resolve(b) : reject(new Error('Nao foi possivel gerar a foto'))), 'image/jpeg', 0.88)
  })
}

/** Envia a foto (ja recortada) do pet. Retorna o pet atualizado. */
export async function uploadPetPhoto(api, petId, blob) {
  const form = new FormData()
  form.append('file', blob, 'foto.jpg')
  const res = await api.put(`/pets/${petId}/photo`, form)
  return res.data
}
