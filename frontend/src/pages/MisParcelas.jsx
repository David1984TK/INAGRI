import { useEffect, useState } from 'react'
import FranjaResumen from '../components/parcelas/FranjaResumen'
import TarjetaParcela, { TarjetaVacia } from '../components/parcelas/TarjetaParcela'
import VentanaAgregarDatos from '../components/parcelas/VentanaAgregarDatos'
import VentanaEliminarParcela from '../components/parcelas/VentanaEliminarParcela'
import VentanaParcela from '../components/parcelas/VentanaParcela'
import { obtenerMisParcelas, obtenerSensoresProductor } from '../services/parcelas'
import { obtenerUsuario } from '../services/sesion'
import './MisParcelas.css'

const TARJETAS_VACIAS = 3

export default function MisParcelas() {
  const usuario = obtenerUsuario()
  const idProductor = usuario?.id_productor ?? null
  const [datos, setDatos] = useState(null)
  const [fallo, setFallo] = useState(false)
  const [recarga, setRecarga] = useState(0)
  const [ventana, setVentana] = useState(null)
  const [sensores, setSensores] = useState(null)

  useEffect(() => {
    let vigente = true
    obtenerMisParcelas(idProductor)
      .then((respuesta) => {
        if (!vigente) return
        setDatos(respuesta)
        setFallo(false)
      })
      .catch((error) => {
        console.error(error)
        if (vigente) setFallo(true)
      })
    return () => {
      vigente = false
    }
  }, [idProductor, recarga])

  const parcelas = datos?.parcelas ?? []
  const cerrar = () => setVentana(null)
  const recargar = () => {
    setVentana(null)
    setRecarga((n) => n + 1)
  }

  function abrirAgregarDatos() {
    setSensores(null)
    setVentana({ tipo: 'agregar' })
    obtenerSensoresProductor(idProductor)
      .then(setSensores)
      .catch((error) => {
        console.error(error)
        setSensores([])
      })
  }

  return (
    <>
      <div className="pagina-encabezado">
        <h1>Mis parcelas</h1>
        <button type="button" className="boton boton-primario" onClick={() => setVentana({ tipo: 'nueva' })}>
          <i className="bi bi-plus-lg" aria-hidden="true" />
          Nueva parcela
        </button>
      </div>

      <FranjaResumen resumen={datos?.resumen} parcelas={parcelas} alAgregarDatos={abrirAgregarDatos} />

      {fallo && (
        <div className="aviso-carga" role="alert">
          <i className="bi bi-exclamation-circle" aria-hidden="true" />
          No se pudieron cargar las parcelas.
          <button type="button" className="boton boton-secundario" onClick={() => setRecarga((n) => n + 1)}>
            Reintentar
          </button>
        </div>
      )}

      <section className="parcelas" aria-label="Parcelas">
        {parcelas.length > 0
          ? parcelas.map((parcela) => (
              <TarjetaParcela
                key={parcela.id_parcela}
                parcela={parcela}
                alEditar={(p) => setVentana({ tipo: 'editar', parcela: p })}
                alEliminar={(p) => setVentana({ tipo: 'eliminar', parcela: p })}
              />
            ))
          : Array.from({ length: TARJETAS_VACIAS }, (_, i) => <TarjetaVacia key={i} />)}
      </section>

      {(ventana?.tipo === 'nueva' || ventana?.tipo === 'editar') && (
        <VentanaParcela
          parcela={ventana.parcela}
          idProductor={idProductor}
          nombreProductor={datos?.productor?.nombre ?? usuario?.nombre}
          alCerrar={cerrar}
          alGuardar={recargar}
        />
      )}
      {ventana?.tipo === 'eliminar' && (
        <VentanaEliminarParcela parcela={ventana.parcela} alCerrar={cerrar} alEliminar={recargar} />
      )}
      {ventana?.tipo === 'agregar' && <VentanaAgregarDatos sensores={sensores} alCerrar={cerrar} alGuardar={recargar} />}
    </>
  )
}
