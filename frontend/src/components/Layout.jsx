import { Outlet } from 'react-router-dom'
import BarraNavegacion from './BarraNavegacion'

export default function Layout() {
  return (
    <>
      <BarraNavegacion />
      <main className="contenido">
        <Outlet />
      </main>
    </>
  )
}
