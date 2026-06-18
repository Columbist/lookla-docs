export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <p className="text-6xl mb-4">💇</p>
        <h1 className="text-2xl font-bold text-gray-800 mb-2">404</h1>
        <p className="text-gray-500 mb-6">Η σελίδα δεν βρέθηκε</p>
        <a href="/" className="px-4 py-2 bg-pink-600 text-white rounded-lg hover:bg-pink-700">Αρχική</a>
      </div>
    </div>
  );
}
