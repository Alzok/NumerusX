import { Outlet } from 'react-router-dom'

export default function Layout() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b">
        <div className="px-6 py-4">
          <h1 className="text-xl font-semibold">NumerusX</h1>
        </div>
      </header>
      <main className="container mx-auto">
        <Outlet />
      </main>
    </div>
  )
}
