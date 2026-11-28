import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import ProveedorAvisos from './components/ProveedorAvisos'
import DetalleParcela from './pages/DetalleParcela'
import MisParcelas from './pages/MisParcelas'

function App() {
  return (
    <ProveedorAvisos>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/parcelas" element={<MisParcelas />} />
          <Route path="/parcelas/:id" element={<DetalleParcela />} />
        </Route>
        <Route path="*" element={<Navigate to="/parcelas" replace />} />
      </Routes>
    </ProveedorAvisos>
  )
}

export default App
