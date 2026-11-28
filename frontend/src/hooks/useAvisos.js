import { useContext } from 'react'
import { AvisosContext } from '../context/avisos'

export function useAvisos() {
  return useContext(AvisosContext)
}
