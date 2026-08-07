import Button from '../components/Button'

export default function NotFound() {
  return (
    <div className="text-center py-24">
      <div className="text-5xl mb-4">🧭</div>
      <h1 className="text-3xl font-bold text-slate-900 mb-2">Page not found</h1>
      <p className="text-slate-500 mb-6">The page you're looking for doesn't exist.</p>
      <Button to="/">Go home</Button>
    </div>
  )
}
