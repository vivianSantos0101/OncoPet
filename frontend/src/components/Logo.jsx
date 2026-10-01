import logoUrl from '../assets/logo-oncopet.webp'

/**
 * Logo do OncoPet: pastor-alemao de pelo longo com uma orelha em pe e a outra
 * "quebrada", sobre o quadrado menta do tema (imagem em src/assets).
 * O icone da aba usa a mesma arte (public/favicon.png).
 *
 * title vazio: decorativo (o texto "OncoPet" ja esta ao lado).
 */
export function LogoMark({ size = 34, title = 'OncoPet' }) {
  return (
    <img className="logo-mark" src={logoUrl} width={size} height={size}
      alt={title} aria-hidden={title ? undefined : true} draggable="false" />
  )
}

export default LogoMark
