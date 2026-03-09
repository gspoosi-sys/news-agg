export default function Header() {
  return (
    <header className="sticky top-0 z-10 bg-white/80 backdrop-blur-sm border-b border-gray-200">
      <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900 tracking-tight">Balanced News</h1>
          <p className="text-xs text-gray-500 mt-0.5">Stay informed, not overwhelmed</p>
        </div>
        <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full font-medium">
          Positivity-first
        </span>
      </div>
    </header>
  );
}
