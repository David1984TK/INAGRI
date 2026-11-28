import { useEffect } from 'react'

// Cierra un menú al hacer clic fuera de `ref` o al presionar Escape.
export function useCerrarAlSalir(ref, abierto, alCerrar) {
  useEffect(() => {
    if (!abierto) return

    function alPresionar(evento) {
      if (ref.current && !ref.current.contains(evento.target)) alCerrar()
    }
    function alTeclear(evento) {
      if (evento.key === 'Escape') alCerrar()
    }

    document.addEventListener('mousedown', alPresionar)
    document.addEventListener('keydown', alTeclear)
    return () => {
      document.removeEventListener('mousedown', alPresionar)
      document.removeEventListener('keydown', alTeclear)
    }
  }, [ref, abierto, alCerrar])
}
